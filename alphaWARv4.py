"""Added logic to keep track of the signals from the previous epoch to speed up the FFT"""
import io
import sys
import time
import argparse
original_stdout = sys.stdout 
sys.stdout = io.StringIO()
import pygame
sys.stdout = original_stdout
import numpy as np
import matplotlib.pyplot as plt
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
    
    
def calculate_alpha_power(data, board_id, normalize='max'):
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
    
    
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=120, help='Total duration to collect data, in seconds.')
    parser.add_argument('--epoch_duration', type=float, default=1, help='Duration of an instance of data collection')
    parser.add_argument('--port1', type=str, default='/dev/cu.usbserial-DM01HWJ7', help='Absolute path of Open BCI dongle 1 (usually in /dev/).')
    parser.add_argument('--port2', type=str, default='/dev/cu.usbserial-DM01IK21', help='Absolute path of OpenBCI dongle 2 (usually in /dev/).')
    parser.add_argument('--add_sound', type=bool, default=False, help='Whether to add sonification to the game')
    parser.add_argument('--stressful_feedback_path', type=str, default='', help='Absolute path to the audio file containing stressful feedback')
    parser.add_argument('--width', type=int, default=1440, help='Width of the Pygame window.')
    parser.add_argument('--height', type=int, default=800, help='Height of the Pygame window.')
    parser.add_argument('--font_size', type=int, default=36, help='Font size for text in the Pygame window.')
    return parser.parse_args()


def initialize_pygame(width, height, font_size):
    pygame.init()  
    pygame.font.init()
    font = pygame.font.Font(None, font_size)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Tug of War') 
    return font, screen
    
    
def initialize_board(serial_port, board_id):
    params = BrainFlowInputParams()
    params.serial_port = serial_port
    board = None
    try:
        board = BoardShim(board_id, params)
        board.prepare_session()
        board.start_stream()
    except Exception as e:
        print(f"Couldn't initialize the board on port {serial_port}. Error: {e}")
    return board


def game_loop(board1, board2, screen, font, epoch_duration):
    speed = 30
    rope_width = 250
    rope_height = 10
    player1 = pygame.Rect(100, 250, 10, 300)
    player2 = pygame.Rect(1340, 250, 10, 300)
    rope = pygame.Rect(595, 400, rope_width, rope_height)
    quit_game = False
    winner = ''

    while not quit_game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    quit_game = True

        screen.fill((255, 255, 255))
        pygame.draw.rect(screen, (0, 0, 0), rope)
        pygame.draw.rect(screen, (255, 0, 0), player1)
        pygame.draw.rect(screen, (0, 0, 255), player2)

        # logic for A and D key controls when either board is None
        keys = pygame.key.get_pressed()
        if board1 is None or board2 is None:
            if keys[pygame.K_a]:
                rope.move_ip(-speed, 0)
            elif keys[pygame.K_d]:
                rope.move_ip(speed, 0)

        if not (board1 is None and board2 is None):
            try:
                data1 = np.hstack((data1_old, board1.get_board_data()[1:9, :])) if board1 else data1_old
                data2 = np.hstack((data2_old, board2.get_board_data()[1:9, :])) if board2 else data2_old

                if data1.shape[1] > 256:
                    data1 = data1[:, -256:]
                if data2.shape[1] > 256:
                    data2 = data2[:, -256:]
                
                time.sleep(epoch_duration)
                
                data1_old, data2_old = data1, data2  
            except Exception as e:
                print(f"Couldn't read data due to {e}")

            if data1.size and data2.size:
                alpha_power1 = calculate_alpha_power(data1, board_id1) if data1.size else 0
                alpha_power2 = calculate_alpha_power(data2, board_id2) if data2.size else 0

                diff = alpha_power2 - alpha_power1
                diff = 2 / (1 + np.exp(-15*diff)) - 1
                print(diff, alpha_power1, alpha_power2)
                
                # game logic
                rope.move_ip(diff * speed, 0)
                pygame.display.flip()
                
                # drawing
                screen.fill((255, 255, 255))
                pygame.draw.rect(screen, (0, 0, 0), rope)
                pygame.draw.rect(screen, (255, 0, 0), player1)
                pygame.draw.rect(screen, (0, 0, 255), player2)
                
                if rope.right < player1.left or rope.left > player2.right:
                    if rope.right < player1.left:
                        winner = 'Player 1'
                    elif rope.left > player2.right:
                        winner = 'Player 2'
                    
                    pygame.display.flip()
                    text = font.render(f'Game Over! {winner} is the winner.', True, (0, 0, 0))
                    screen.blit(text, (200, 200)) 
                    text2 = font.render('Press space to play again or escape to quit.', True, (0, 0, 0))
                    screen.blit(text2, (200, 250))

        pygame.display.flip()  
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


def main():
    try:
        args = parse_arguments()
        font, screen = initialize_pygame(args.width, args.height, args.font_size)
        
        board1 = initialize_board(args.port1, BoardIds.CYTON_BOARD.value)
        board2 = initialize_board(args.port2, BoardIds.CYTON_BOARD.value)
        
        game_loop(board1, board2, screen, font, args.epoch_duration) 
    
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr) 
    
    finally:
        if 'board1' in locals() and board1 is not None:
            board1.stop_stream()
            board1.release_session()
        if 'board2' in locals() and board2 is not None:
            board2.stop_stream()
            board2.release_session()
        pygame.quit()


if __name__ == '__main__':
    main()
