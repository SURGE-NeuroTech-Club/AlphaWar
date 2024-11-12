import time
import pygame
import sys
import pygame.font
import argparse
import pygame.mixer
import numpy as np
import matplotlib.pyplot as plt
from alpha_war_funcs import *
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

pygame.init()
# Initialize Pygame mixer
pygame.mixer.init(frequency=20, size=-16, channels=2)
    
# Initialize Pygame
player_1_board_id = BoardIds.SYNTHETIC_BOARD.value #BoardIds.CYTON_BOARD.value
player_1_serial_port = 'COM4'

player_2_board_id = BoardIds.SYNTHETIC_BOARD.value #BoardIds.CYTON_BOARD.value
player_2_serial_port = 'COM9'

epoch_duration = 1

pygame.init()

def main(): 
    # Set the font
    pygame.font.init()
    font = pygame.font.Font(None, 36)
    alpha_font = pygame.font.Font(None, 28)
    winner = ''
    width, height = 1440, 800
    rope_width = 250
    rope_height = 10

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Tug of War')

    # set up the players and the rope
    player1 = pygame.Rect(100, 250, 10, 300)
    player2 = pygame.Rect(1340, 250, 10, 300)
    
    board1 = BrainFlowBoardSetup(board_id=player_1_board_id, name='Player 1', serial_port=player_1_serial_port)
    board2 = BrainFlowBoardSetup(board_id=player_2_board_id, name='Player 2', serial_port=player_2_serial_port)
    
    board1.setup()
    board2.setup()
    
    time.sleep(2)
    print('Collecting data...')

    # Variables to track the average alpha power
    alpha_power1_sum = 0.0
    alpha_power2_sum = 0.0
    count = 0

    # game loop
    quit_game = False
    while not quit_game:
        print('Starting game loop')
        speed = 30
        rope = pygame.Rect(595, 400, rope_width, rope_height)

        running = True
        while running:
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
                alpha_power1 = calculate_alpha_power(data1, player_1_board_id)
                alpha_power2 = calculate_alpha_power(data2, player_2_board_id)

                # Update cumulative sum and count for averages
                alpha_power1_sum += alpha_power1
                alpha_power2_sum += alpha_power2
                count += 1

                # Calculate averages
                avg_alpha_power1 = alpha_power1_sum / count
                avg_alpha_power2 = alpha_power2_sum / count

                # Rope movement based on alpha power difference
                diff = int(alpha_power2 > alpha_power1) * 2 - 1
                rope.move_ip(diff * speed, 0)
                pygame.display.flip()

                # Clear screen
                screen.fill((255, 255, 255))
                
                # Draw the rope and players
                pygame.draw.rect(screen, (0, 0, 0), rope)
                pygame.draw.rect(screen, (255, 0, 0), player1)
                pygame.draw.rect(screen, (0, 0, 255), player2)
                
                # Define the maximum alpha power for scaling
                max_alpha_power = max(alpha_power1, alpha_power2, 1)  # Prevent division by zero
                
                # Bar settings
                bar_height = 30
                bar_max_width = 300  # Maximum width for the bars
                center_offset = 200  # Distance from the center

                # Calculate bar widths relative to max alpha power
                bar_width1 = int((alpha_power1 / max_alpha_power) * bar_max_width)
                bar_width2 = int((alpha_power2 / max_alpha_power) * bar_max_width)

                # Draw the bar graphs closer to the center
                pygame.draw.rect(screen, (255, 0, 0), ((width // 2) - center_offset - bar_width1, 100, bar_width1, bar_height))
                pygame.draw.rect(screen, (0, 0, 255), ((width // 2) + center_offset, 100, bar_width2, bar_height))

                # Display current and average alpha power values
                alpha_text1 = alpha_font.render(f'{board1.get_board_name()} Alpha Power: {alpha_power1:.2f} (Avg: {avg_alpha_power1:.2f})', True, (255, 0, 0))
                alpha_text2 = alpha_font.render(f'{board2.get_board_name()} Alpha Power: {alpha_power2:.2f} (Avg: {avg_alpha_power2:.2f})', True, (0, 0, 255))
                screen.blit(alpha_text1, ((width // 2) - center_offset - 200, 70))
                screen.blit(alpha_text2, ((width // 2) + center_offset, 70))

                pygame.display.flip()

                # Check if the rope has completely passed one of the player markers
                if rope.right < player1.left or rope.left > player2.right:
                    winner = 'Player 1' if rope.right < player1.left else 'Player 2'
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

    board1.stop()
    board2.stop()
    pygame.quit()



if __name__ == '__main__':
    main()