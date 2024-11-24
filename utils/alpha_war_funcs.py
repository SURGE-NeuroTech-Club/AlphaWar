from brainflow.board_shim import BoardShim, BrainFlowInputParams, BrainFlowError, BoardIds
import serial.tools.list_ports
import time
import pygame
import pygame.font
import pygame.mixer
import numpy as np


def list_all_com_ports():
    known_vid_pid_pairs = [(0x0403, 0x6015)]
    ports = list(serial.tools.list_ports.comports())
    compatible_ports = []

    for port in ports:
        if (port.vid, port.pid) in known_vid_pid_pairs:
            compatible_ports.append(port.device)
    
    # if not compatible_ports:
    #     print("No compatible devices found. Please ensure the dongle is connected with the switch set toward the dongle's male connector, and that the board switch is in 'PC' mode.")
    return compatible_ports
    # return ["COM6", "COM10"]

def display_button(screen, text, rect, font):
    pygame.draw.rect(screen, (180, 180, 180), rect)
    button_text = font.render(text, True, (0, 0, 0))
    screen.blit(button_text, button_text.get_rect(center=rect.center))
    
def scan_ports_and_assign(existing_player_1_port=None, existing_player_2_port=None):
    available_ports = list_all_com_ports()

    # If Player 1 already has a port assigned, keep it as Player 1's port
    if existing_player_1_port in available_ports:
        player_1_port = existing_player_1_port
        available_ports.remove(player_1_port)
    else:
        player_1_port = available_ports.pop(0) if available_ports else None

    # Assign the next available port to Player 2, ensuring it’s not Player 1’s port
    player_2_port = existing_player_2_port if (existing_player_2_port in available_ports) else (available_ports[0] if available_ports else None)

    return player_1_port, player_2_port

def calculate_alpha_power(data, board_id, normalize='betaalpha'):
    """
    Calculate the alpha power of EEG data with different normalization options.
    
    Parameters:
    - data: numpy array, shape (n_channels, n_samples)
        The EEG data where each row represents a channel and each column represents a sample.
    - board_id: int
        The board ID for getting the sampling rate using BoardShim.
    - normalize: str, optional
        Normalization method. Options are:
        - 'max': Normalizes by the maximum FFT value for each channel.
        - 'norm': Normalizes by the vector norm of the power spectrum for each channel.
        - 'betaalpha': Returns the ratio of raw beta power (12-30 Hz) to raw alpha power (8-12 Hz).
        
    Returns:
    - float: The calculated alpha power, normalized based on the specified method.
    """
    # Compute the power spectrum for each channel
    ps = np.abs(np.fft.fft(data, axis=1))**2
    freqs = np.fft.fftfreq(data.shape[1], 1 / BoardShim.get_sampling_rate(board_id))
    
    # Define the alpha and beta frequency ranges
    alpha_range = (freqs >= 8) & (freqs <= 12)
    beta_range = (freqs > 12) & (freqs <= 30)
    
    # Calculate the alpha power for each channel by summing the power in the alpha band
    alpha_powers = np.sum(ps[:, alpha_range], axis=1)
    
    # Normalization or ratio calculations based on the specified method
    if normalize == 'max':
        # Normalize by the maximum FFT value per channel
        normalization_factor = np.max(ps, axis=1)
        normalized_alpha_powers = alpha_powers / normalization_factor
        return np.sum(normalized_alpha_powers)
    
    elif normalize == 'norm':
        # Normalize by the vector norm of the power spectrum for each channel
        normalization_factor = np.linalg.norm(ps, axis=1)
        normalized_alpha_powers = alpha_powers / normalization_factor
        return np.sum(normalized_alpha_powers)
    
    elif normalize == 'betaalpha':
        # Calculate the ratio of beta power to alpha power across all channels
        beta_powers = np.sum(ps[:, beta_range], axis=1)
        total_alpha_power = np.sum(alpha_powers)
        total_beta_power = np.sum(beta_powers)
        
        # Avoid division by zero
        if total_alpha_power == 0:
            return 0
        beta_alpha_ratio = total_beta_power / total_alpha_power
        return beta_alpha_ratio
    
    else:
        raise ValueError("The normalize parameter must be 'max', 'norm', or 'betaalpha'")



class BrainFlowBoardSetup:
    """
    A class to manage the setup, configuration, and control of a BrainFlow board.
    This class provides methods for initializing, configuring, and streaming data from the board.
    It also enables access to all attributes and methods from the BoardShim instance (even if not explicitly defined in this class).
    
    Attributes:
        name (str): A user-friendly name or identifier for the board setup instance.
        board_id (int): The ID of the BrainFlow board to use.
        serial_port (str): The serial port to which the BrainFlow board is connected.
        master_board (int): The ID of the master board (if using playback or synthetic boards).
        params (BrainFlowInputParams): Instance of BrainFlowInputParams representing the board's input parameters.
        board (BoardShim): Instance of BoardShim representing the active board.
        session_prepared (bool): Flag indicating if the session has been prepared.
        streaming (bool): Flag indicating if the board is actively streaming data.
        eeg_channels (list): List of EEG channel indices for the board (empty if not applicable).
        sampling_rate (int): Sampling rate of the board.
    """

    _id_counter = 0  # Class-level variable to assign default IDs

    def __init__(self, board_id, serial_port=None, master_board=None, name=None, **kwargs):
        """
        Initializes the BrainFlowBoardSetup class with the given board ID, serial port, master board, and additional parameters.

        Args:
            board_id (int): The ID of the BrainFlow board to be used.
            serial_port (str, optional): The serial port to which the BrainFlow board is connected.
            master_board (int, optional): The master board ID, used for playback or synthetic boards.
            name (str, optional): A user-friendly name or identifier for this instance. Defaults to 'Board X'.
            **kwargs: Additional keyword arguments to be set as attributes on the BrainFlowInputParams instance.
        """
        self.instance_id = BrainFlowBoardSetup._id_counter  # Unique identifier for each instance
        BrainFlowBoardSetup._id_counter += 1
        
        self.board_id = board_id
        self.serial_port = serial_port
        self.master_board = master_board

        # Assign default name if not provided, based on the class-level ID counter
        self.name = name or f"Board {BrainFlowBoardSetup._id_counter}"
        BrainFlowBoardSetup._id_counter += 1

        # Initialize BrainFlow input parameters
        self.params = BrainFlowInputParams()
        self.params.serial_port = self.serial_port
        
        if board_id in [BoardIds.PLAYBACK_FILE_BOARD.value, BoardIds.SYNTHETIC_BOARD.value]:
            self.params.other_info = f"instance_id_{self.instance_id}"  # Add unique instance ID to 'other_info' -> allows for multiple instances of essentially the same board
            
        if self.master_board is not None:
            self.params.master_board = self.master_board  # Set master board if provided

        # Retrieve EEG channels and sampling rate based on the provided board or master board
        try:
            self.eeg_channels, self.sampling_rate = self.get_board_info()
        except BrainFlowError as e:
            print(f"Error getting board info for board {self.board_id}: {e}")
            self.eeg_channels = []
            self.sampling_rate = None

        # Apply additional parameters
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
            else:
                print(f"Warning: {key} is not a valid parameter for BrainFlowInputParams")

        # Initialize board and state flags
        self.board = None
        self.session_prepared = False
        self.streaming = False
    
    def __getattr__(self, name):
        """
        Delegates attribute access to the BoardShim instance if the attribute is not found in the current instance.
        This allows access to BoardShim-specific attributes that may not be directly defined in the BrainFlowBoardSetup class.

        Args:
            name (str): The name of the attribute to be accessed.

        Returns:
            The attribute from the BoardShim instance if it exists.

        Raises:
            AttributeError: If the attribute is not found in the current instance or the BoardShim instance.
        """
        if self.board is not None and hasattr(self.board, name):
            return getattr(self.board, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def get_board_info(self):
        """
        Retrieves the EEG channels and sampling rate for the board. Uses the master board if provided.

        Returns:
            tuple: A tuple containing EEG channels (list) and sampling rate (int).

        Raises:
            ValueError: If a master_board is provided for a board that doesn't support it.
        """
        if self.board_id not in [BoardIds.PLAYBACK_FILE_BOARD.value, BoardIds.SYNTHETIC_BOARD.value] and self.master_board:
            raise ValueError(f"Master board is only used for PLAYBACK_FILE_BOARD (-3) and SYNTHETIC_BOARD (-1). But {self.board_id} was provided.")

        board_to_use = self.master_board if self.master_board is not None else self.board_id
        board_descr = BoardShim.get_board_descr(board_to_use)
        
        eeg_channels = board_descr.get("eeg_channels", [])
        sampling_rate = BoardShim.get_sampling_rate(board_to_use)
        
        return eeg_channels, sampling_rate
    
    def find_device_ports(self):
        """
        Finds all compatible BrainFlow devices by checking the available serial ports based on VID/PID.

        This method iterates over available serial ports on the computer and directly adds ports 
        with known OpenBCI VID/PID pairs to the list of compatible devices without testing each connection.

        Returns:
            list: A list of dictionaries containing 'port', 'serial_number', and 'description' for each compatible device.
                Returns an empty list if no devices are found.
        """
        # Known VID/PID pairs for OpenBCI boards
        openbci_vid_pid_pairs = [
            (0x0403, 0x6015),  # Cyton with FTDI chip
            (0x04D8, 0xF372)   # Ganglion
        ]

        BoardShim.disable_board_logger()
        ports = list(serial.tools.list_ports.comports())
        compatible_ports = []

        # Iterate over all available ports
        for port in ports:
            # Check if the port's VID and PID match any known OpenBCI VID/PID pairs
            if (port.vid, port.pid) in openbci_vid_pid_pairs:
                device_info = {
                    'port': port.device,
                    'serial_number': port.serial_number,
                    'description': port.description
                }
                print(f"Compatible device found: Serial Number: {port.serial_number}, Description: {port.description}")
                compatible_ports.append(device_info)

        if not compatible_ports:
            raise Exception("No compatible BrainFlow devices found.")
        
        BoardShim.enable_board_logger()
        return compatible_ports

    def setup(self):
        """
        Prepares the session and starts the data stream from the BrainFlow board.

        If no serial port is provided during initialization, this method attempts to auto-detect
        a compatible device. Once the board is detected or provided, it prepares the session and starts streaming.

        Raises:
            BrainFlowError: If the board fails to prepare the session or start streaming.
        """
        if self.master_board is None:
            if self.board_id in [BoardIds.PLAYBACK_FILE_BOARD.value, BoardIds.SYNTHETIC_BOARD.value]:
                self.serial_port = ''
            if self.serial_port is None:
                print("No serial port provided, attempting to auto-detect...")
                ports_info = self.find_device_ports()
                if self.instance_id != 0:
                    self.serial_port = ports_info[self.instance_id - 1]['port'] if ports_info else None
                else:
                    self.serial_port = ports_info[self.instance_id]['port'] if ports_info else None
                if not self.serial_port:
                    print("No compatible device found. Setup failed.")
                    return
        elif self.master_board is not None:
            self.serial_port = ''
        else:
            print("No serial port provided and master board is not set. Setup failed.")
            return
        
        self.params.serial_port = self.serial_port
        self.board = BoardShim(self.board_id, self.params)
        try:
            time.sleep(2)
            self.board.prepare_session()
            self.session_prepared = True
            self.board.start_stream(450000)
            self.streaming = True # Flag to indicate if streaming is active
            print(f"[{self.name}, {self.serial_port}] Board setup and streaming started successfully.")
        except BrainFlowError as e:
            print(f"[{self.name}, {self.serial_port}] Error setting up board: {e}")
            self.board = None

    def show_params(self):
        """
        Prints the current parameters of the BrainFlowInputParams instance.
        This method provides a simple way to inspect the current input parameters
        being used to configure the BrainFlow board.
        """
        print(f"[{self.name}] Current BrainFlow Input Parameters:")
        for key, value in vars(self.params).items():
            print(f"{key}: {value}")

    def get_sampling_rate(self):
        """
        Retrieves the sampling rate of the BrainFlow board.

        Returns:
            int: The sampling rate of the BrainFlow board.
        """
        return self.sampling_rate
    
    def is_streaming(self):
        """
        Checks if the BrainFlow board is currently streaming data.

        Returns:
            bool: True if the board is streaming, False otherwise.
        """
        return self.streaming
    
    def get_board_name(self):
        """
        Retrieves the name of the BrainFlow board.

        Returns:
            str: The name of the board, useful for logging or display purposes.
        """
        return self.name
    
    def get_board_data(self):
        """
        Retrieves all accumulated data from the BrainFlow board and clears it from the buffer.

        Returns:
            numpy.ndarray: The current data from the BrainFlow board if the board is set up.
            None: If the board is not set up.
        """
        if self.board is not None:
            return self.board.get_board_data()
        else:
            print("Board is not set up.")
            return None

    def get_current_board_data(self, num_samples):
        """
        Retrieves the most recent num_samples data from the BrainFlow board without clearing it from the buffer.

        Args:
            num_samples (int): Number of recent samples to fetch.

        Returns:
            numpy.ndarray: The latest num_samples data from the BrainFlow board if the board is set up.
            None: If the board is not set up.
        """
        if self.board is not None:
            return self.board.get_current_board_data(num_samples)
        else:
            print("Board is not set up.")
            return None

    def insert_marker(self, marker, verbose=True):
        """
        Inserts a marker into the data stream at the current time. Useful for tagging events in the data stream.

        Args:
            marker (float): The marker value to be inserted.
            verbose (bool): Whether to print a confirmation message. Default is True.
        """
        if self.board is not None and self.streaming:
            try:
                self.board.insert_marker(marker)
                if verbose:
                    print(f"[{self.name}] Marker {marker} inserted successfully.")
            except BrainFlowError as e:
                print(f"[{self.name}] Error inserting marker: {e}")
        else:
            print("Board is not streaming, cannot insert marker.")

    def stop(self):
        """
        Stops the data stream and releases the session of the BrainFlow board.

        This method safely stops the data stream and releases any resources used by the BrainFlow board.
        It also resets the streaming and session flags.
        """
        try:
            if hasattr(self, 'board') and self.board is not None:
                if self.streaming:
                    self.board.stop_stream()
                    self.streaming = False
                    print(f"[{self.name}, {self.serial_port}] Streaming stopped.")
                if self.session_prepared:
                    self.board.release_session()
                    self.session_prepared = False
                    print(f"[{self.name}, {self.serial_port}] Session released.")
        except BrainFlowError as e:
            if "BOARD_NOT_CREATED_ERROR:15" not in str(e):
                print(f"[{self.name}, {self.serial_port}] Error stopping board: {e}")        

    def __del__(self):
        """
        Ensures that the data stream is stopped and the session is released when the object is deleted.
        This method ensures that the session is properly released and resources are freed when the object is garbage collected.
        """
        self.stop()

