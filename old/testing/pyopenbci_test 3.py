import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds


def plot_powers(freqs, ps, alpha_power):
    """
    Parameters
     - freqs:
     - ps: 
    """
    fig, axs = plt.subplots(2, 4, figsize=(20, 10))
    for i, ax in enumerate(axs.flatten()):
        ax.plot(freqs[:len(freqs) // 2], ps[:len(ps) // 2])  
        ax.set_title(f'Channel {i+1} (Alpha Power: {alpha_power:.2f})')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Power')

    plt.tight_layout()
    plt.show()


def calculate_alpha_power(data, board_id):
    ps = np.abs(np.fft.fft(data, axis=1))**2
    freqs = np.fft.fftfreq(data.shape[1], 1 / BoardShim.get_sampling_rate(board_id))
    alpha_range = (freqs >= 8) & (freqs <= 12)
    alpha_powers = np.sum(ps[:, alpha_range], axis=1)
    max_fft_values = np.max(ps, axis=1)
    normalized_alpha_powers = alpha_powers / max_fft_values
    return np.sum(normalized_alpha_powers)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=120, help='Total duration to collect data, in seconds.')
    parser.add_argument('--epoch_duration', type=float, default=1, help='Duration of an instance of data collection')
    parser.add_argument('--port1', type=str, default='/dev/cu.usbserial-DM01IK21', help='Path of dongle 1 in /dev/.')
    parser.add_argument('--port2', type=str, default='/dev/cu.usbserial-DM01HWJ7', help='Path of dongle 2 in /dev/.')
    args = parser.parse_args()
    duration = args.duration 
    epoch_duration = args.epoch_duration
    port1 = args.port1
    port2 = args.port2

    # Location of the 'rope'
    location = 0
    # The amount by which to move the 'rope' to win
    threshold = 10

    # INITIALIZE VISUALS HERE 

    params1 = BrainFlowInputParams()
    params1.serial_port = port1
    board_id1 = BoardIds.CYTON_BOARD.value
    BoardShim.enable_dev_board_logger()
    board1 = BoardShim(board_id1, params1)

    params2 = BrainFlowInputParams()
    params2.serial_port = port2
    board_id2 = BoardIds.CYTON_BOARD.value
    BoardShim.enable_dev_board_logger()
    board2 = BoardShim(board_id2, params2)

    board1.prepare_session()
    board2.prepare_session()

    board1.start_stream()
    board2.start_stream()
    print('Collecting data...')

    for _ in range(duration):
          
        try:
            data1 = board1.get_board_data()[1:9, :]   
            data2 = board2.get_board_data()[1:9, :] 
            time.sleep(epoch_duration)  
        except:
            print("Couldn't read data...")

        if data1.size and data2.size: 

            alpha_power1 = calculate_alpha_power(data1, board_id1)
            alpha_power2 = calculate_alpha_power(data2, board_id2)

            # 1 if 2>1, -1 if 1>2
            # Could be set to some other function of the difference to move the rope by varying amounts
            diff = int(alpha_power2 >= alpha_power1) * 2 - 1
            location += diff
            # ADD THE VISUAL DISPLAY AND UPDATE SEQUENCE HERE 
            print(diff, alpha_power2, alpha_power1)
            if np.abs(location) >= threshold:
                pass
                # ADD THE GAME ENDING SEQUENCE HERE 
            
    if _ == duration - 1:
        pass
        # ADD THE TIMES UP SEQUENCE HERE

    board1.stop_stream()
    board1.release_session()

    board2.stop_stream()
    board2.release_session()

if __name__ == '__main__':
    main()