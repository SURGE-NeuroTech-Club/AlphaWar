import time
import pygame
import sys
import pygame.font
import argparse
import pygame.mixer
import numpy as np
import matplotlib.pyplot as plt
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

pygame.init()
# Initialize Pygame mixer
pygame.mixer.init(frequency=20, size=-16, channels=2)
 
def generate_sine_wave(frequency, duration=0.5, volume=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = volume * np.sin(2 * np.pi * frequency * t)
    return wave.astype(np.float32)
 
def generate_sawtooth_wave(frequency, duration=0.5, volume=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = volume * 2 * (t * frequency - np.floor(1/2 + t * frequency))
    return wave.astype(np.float32)
 
def play_sound_for_rope_position(rope_position):
    frequency = 100 + 10 * abs(rope_position)**3      # Base frequency plus a factor of the rope position
    if rope_position > 0:
        waveform = generate_sine_wave(frequency)
    else:
        waveform = generate_sawtooth_wave(frequency)
    sound = pygame.sndarray.make_sound(waveform.repeat(2).reshape((-1, 2)).copy(order='C'))
    sound.play()

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



def calculate_alpha_power(data, board_id, normalize='betaalpha'):
    """
    Parameters:
     - normalize: {'max', 'norm', 'betaalpha'} How to normalize the alpha powers. 'max' uses the maximum FFT value,
       'norm' uses the vector norm, and 'betaalpha' returns the ratio of raw beta power to raw alpha power.
    """
    ps = np.abs(np.fft.fft(data, axis=1))**2
    freqs = np.fft.fftfreq(data.shape[1], 1 / BoardShim.get_sampling_rate(board_id))
    
    alpha_range = (freqs >= 8) & (freqs <= 12)
    beta_range = (freqs > 12) & (freqs <= 30)
    
    alpha_powers = np.sum(ps[:, alpha_range], axis=1)
    
    if normalize == 'max':
        normalization_factor = np.max(ps, axis=1)
        normalized_alpha_powers = alpha_powers / normalization_factor
        return np.sum(normalized_alpha_powers)
    elif normalize == 'norm':
        normalization_factor = norm(ps, axis=1)
        normalized_alpha_powers = alpha_powers / normalization_factor
        return np.sum(normalized_alpha_powers)
    elif normalize == 'betaalpha':
        beta_powers = np.sum(ps[:, beta_range], axis=1)
        beta_alpha_ratio = np.sum(beta_powers) / np.sum(alpha_powers)
        return beta_alpha_ratio
    else:
        raise ValueError("the normalize parameter must be 'max', 'norm', or 'betaalpha'")
    
 # Initialize Pygame
pygame.init()
def main(): 
    #usb_ids =  
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=120, help='Total duration to collect data, in seconds.')
    parser.add_argument('--epoch_duration', type=float, default=1, help='Duration of an instance of data collection')
    parser.add_argument('--port1', type=str, default='/dev/cu.usbserial-DM01IK21', help='Absolute path of Open BCI dongle 1 (usually in /dev/).')
    parser.add_argument('--port2', type=str, default='/dev/cu.usbserial-DQ00859S', help='Absolute path of OpenBCI dongle 2 (usually in /dev/).')
    args = parser.parse_args()
    duration = args.duration 
    epoch_duration = args.epoch_duration
    port1 = args.port1
    port2 = args.port2

    # # Location of the 'rope'
    # location = 0
    # # The amount by which to move the 'rope' to win
    # threshold = 10


    # Set the font
    pygame.font.init()
    font = pygame.font.Font(None, 36)
    winner = ''

    # pygame.mixer.init()
    # Load the MP3 file
    # pygame.mixer.music.load('/Users/Kya_Masoumi/git/myGitHub/BCI-hack/Dalhousie University 2.m4a')
    # Set the window size
    width, height = 1440, 800
    rope_width = 250
    rope_height = 10

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Tug of War')

    # set up the players and the rope
    player1 = pygame.Rect(100, 250, 10, 300)
    player2 = pygame.Rect(1340, 250, 10, 300)

    params1 = BrainFlowInputParams()
    params1.serial_port = port1
    board_id1 = BoardIds.CYTON_BOARD.value
    BoardShim.enable_dev_board_logger()
    board1 = BoardShim(board_id1, params1)
    time.sleep(3)
    params2 = BrainFlowInputParams()
    params2.serial_port = port2
    board_id2 = BoardIds.CYTON_BOARD.value
    BoardShim.enable_dev_board_logger()
    board2 = BoardShim(board_id2, params2)
    print('both boards initialized')
    board1.prepare_session()
    board2.prepare_session()

    board1.start_stream()
    board2.start_stream()
    print('Collecting data...')

    # game loop
    quit_game = False
    while not quit_game:
        print('Starting game loop')
        # initialize the game state
        speed = 30
        rope = pygame.Rect(595, 400, rope_width, rope_height)
        rope_control = 0

        #start data
        running = True
        while running:
            # event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                        running = False
                        quit_game = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        quit_game = True
            pygame.display.flip()
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
                diff = int(alpha_power2 > alpha_power1) * 2 - 1
                diff = round(diff, 3)
                print(diff, alpha_power1, alpha_power2)

                # # Modify rope_control based on input_var
                # if diff < 0:
                #     rope_control = -1
                # elif diff > 0:
                #     rope_control = 1
                # else:
                #     rope_control = 0
                # game logic
                rope.move_ip(diff * speed, 0)
                    #time.sleep(0.02)

                pygame.display.flip()
        
                # # Check if the rope is within 200 pixels of the finish lines
                # if abs(rope.right - player1.left) <= 200 or abs(rope.left - player2.right) <= 200:
                #     # Play the MP3 file
                #     pygame.mixer.music.play()

                # drawing
                screen.fill((255, 255, 255))
                pygame.draw.rect(screen, (0, 0, 0), rope)
                pygame.draw.rect(screen, (255, 0, 0), player1)
                pygame.draw.rect(screen, (0, 0, 255), player2)

                play_sound_for_rope_position((rope.left + rope.right)/2)

                # Check if the rope has completely passed one of the player markers
                if rope.right < player1.left or rope.left > player2.right:
                    # Determine the winner.
                    if rope.right < player1.left:
                        winner = 'Player 1'
                    elif rope.left > player2.right:
                        winner = 'Player 2'

                    running = False
                    pygame.display.flip()


                if not running:
                    text = font.render('Game Over! ' + winner + ' is the winner.', True, (0, 0, 0))
                    screen.blit(text, (200, 200)) 
                    text2 = font.render('Press space to play again or escape to quit.', True, (0, 0, 0))
                    screen.blit(text2, (200, 250))
                pygame.display.flip()


        # Game over, wait for user to press space to play again or escape to quit
        game_over = True
        while game_over and not quit_game:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = False
                    quit_game = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_over = False
                        quit_game = True
                    elif event.key == pygame.K_SPACE:
                        game_over = False

    board1.stop_stream()
    board1.release_session()

    board2.stop_stream()
    board2.release_session()

    pygame.quit()

if __name__ == '__main__':
    main()