import time
import pygame
import pygame.font
import pygame.mixer
import numpy as np
import matplotlib.pyplot as plt
from utils.alpha_war_funcs import *
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds

# Set the board IDs and serial ports for the players
player_1_name = 'Player 1'
player_1_board_id = BoardIds.SYNTHETIC_BOARD.value # BoardIds.CYTON_BOARD.value

player_2_name = 'Player 2'
player_2_board_id = BoardIds.SYNTHETIC_BOARD.value #BoardIds.CYTON_BOARD.value

# Set the duration of each epoch in seconds
epoch_duration = 2

# Method for normalizing alpha power.
alpha_normalization = 'betaalpha'  
# - 'max': Returns the sum of alpha power across channels, with each channel's alpha power normalized by the channel's maximum FFT power.
# - 'norm': Returns the sum of alpha power across channels, with each channel's alpha power normalized by the vector norm of its power spectrum.
# - 'betaalpha': Returns the ratio of total beta power (12-30 Hz) to total alpha power (8-12 Hz) across all channels.



pygame.init()
# Initialize Pygame mixer
pygame.mixer.init(frequency=20, size=-16, channels=2)

def main():
    # Set the font
    pygame.font.init()
    
    width, height = 1440, 800
    
    label_font = pygame.font.Font(None, 24)
    alpha_font = pygame.font.Font(None, 28)
    font = pygame.font.Font(None, 36)
    winner = ''
    rope_width = 250
    rope_height = 10
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Tug of War')
    
    # Set up the players and the rope
    player1 = pygame.Rect(100, 250, 10, 300)
    player2 = pygame.Rect(1340, 250, 10, 300)

    player_1_serial_port, player_2_serial_port = None, None
    button_width, button_height = 200, 50
    ports_assigned = False
    no_devices_message = None  # Initialize error message

    # Centered button positions
    scan_button_rect = pygame.Rect((width - button_width) // 2, (height - button_height) // 2 - 100, button_width, button_height)
    start_button_rect = pygame.Rect((width - button_width) // 2, (height - button_height) // 2 + 100, button_width, button_height)

    # Main loop for setting up before the game starts
    setup_running = True
    while setup_running:
        screen.fill((255, 255, 255))
        display_button(screen, "Scan Ports", scan_button_rect, font)

        # Display the assigned ports if available
        if player_1_serial_port:
            port_text = f"Player 1: {player_1_serial_port}"
            if player_2_serial_port:
                port_text += f" | Player 2: {player_2_serial_port}"
            else:
                port_text += " | Waiting for Player 2..."
            ports_assigned_text = label_font.render(port_text, True, (0, 0, 0))
            text_rect = ports_assigned_text.get_rect(center=(width // 2, height // 2))
            screen.blit(ports_assigned_text, text_rect)

        # Display Start button only if both players are connected
        if player_1_serial_port and player_2_serial_port:
            ports_assigned = True
            display_button(screen, "Start", start_button_rect, font)

        # Display "No compatible devices found" message if no devices are found
        if no_devices_message:
            no_devices_text = label_font.render(no_devices_message, True, (255, 0, 0))
            no_devices_text_rect = no_devices_text.get_rect(center=(width // 2, height // 2 + 200))
            screen.blit(no_devices_text, no_devices_text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if scan_button_rect.collidepoint(event.pos):
                    # Scan ports and update the error message if no devices are found
                    player_1_serial_port, player_2_serial_port = scan_ports_and_assign(player_1_serial_port, player_2_serial_port)
                    if not player_1_serial_port and not player_2_serial_port:
                        no_devices_message = "No compatible devices found. Please ensure the dongle is connected with the switch set toward the dongle's male connector, and that the board switch is in 'PC' mode."
                    else:
                        no_devices_message = None  # Clear message if devices are found
                elif start_button_rect.collidepoint(event.pos) and ports_assigned:
                    setup_running = False  # Exit setup loop and start game
                    
    # Clear the screen and display "Initializing..." message
    screen.fill((255, 255, 255))
    init_message = label_font.render("Initializing, please wait...", True, (0, 0, 0))
    message_rect = init_message.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(init_message, message_rect)
    pygame.display.flip()

    # Set up the BrainFlow boards
    board1 = BrainFlowBoardSetup(board_id=player_1_board_id, name=player_1_name, serial_port=player_1_serial_port)
    board2 = BrainFlowBoardSetup(board_id=player_2_board_id, name=player_2_name, serial_port=player_2_serial_port)

    # Connect and stream from the boards
    time.sleep(1)
    board1.setup()
    
    time.sleep(1)
    board2.setup()
    
    # Check if both boards are connected and streaming
    if board1.is_streaming() and board2.is_streaming():
        print('Both players connected')
    else:
        raise Exception('Error connecting both players')
    
    board1_srate = board1.get_sampling_rate()
    board2_srate = board2.get_sampling_rate()
    
    samples_per_epoch1 = int(epoch_duration * board1_srate)
    samples_per_epoch2 = int(epoch_duration * board2_srate)
    
    # Display initial message
    init_message = label_font.render("Initializing, please wait...", True, (0, 0, 0))

    # Display the message on the screen
    screen.fill((255, 255, 255))
    message_rect = init_message.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(init_message, message_rect)
    # screen.blit(init_message, (50, 50))  # Adjust (50, 50) to your preferred position
    pygame.display.flip()  # Update the display to show the message
    
    time.sleep(epoch_duration + 1)
    print('Collecting data...')

    # Variables to track the average alpha power and history
    alpha_power1_sum = 0.0
    alpha_power2_sum = 0.0
    count = 0
    history_length = 100  # Number of data points to display
    alpha_history1 = []
    alpha_history2 = []

    # Game loop
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
                data1 = board1.get_current_board_data(samples_per_epoch1)[1:9, :] 
                data2 = board2.get_current_board_data(samples_per_epoch2)[1:9, :] 
                time.sleep(epoch_duration)  
            except:
                print("Couldn't read data...")

            if data1.size and data2.size: 
                alpha_power1 = calculate_alpha_power(data1, player_1_board_id, normalize=alpha_normalization)
                alpha_power2 = calculate_alpha_power(data2, player_2_board_id, normalize=alpha_normalization)

                # Update cumulative sum and count for averages
                alpha_power1_sum += alpha_power1
                alpha_power2_sum += alpha_power2
                count += 1

                # Calculate averages
                avg_alpha_power1 = alpha_power1_sum / count
                avg_alpha_power2 = alpha_power2_sum / count

                # Update alpha power history
                if len(alpha_history1) >= history_length:
                    alpha_history1.pop(0)
                    alpha_history2.pop(0)
                alpha_history1.append(alpha_power1)
                alpha_history2.append(alpha_power2)

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

                # Line graph for alpha power history
                graph_x_start = 200
                graph_y_start = 650
                graph_width = 1000
                graph_height = 100

                # Draw background for the graph
                pygame.draw.rect(screen, (230, 230, 230), (graph_x_start, graph_y_start, graph_width, graph_height))

                # Draw x-axis and y-axis
                pygame.draw.line(screen, (0, 0, 0), (graph_x_start, graph_y_start + graph_height), (graph_x_start + graph_width, graph_y_start + graph_height), 2)  # x-axis
                pygame.draw.line(screen, (0, 0, 0), (graph_x_start, graph_y_start), (graph_x_start, graph_y_start + graph_height), 2)  # y-axis

                # Check if we have enough data points to plot the graph
                if len(alpha_history1) >= 2 and len(alpha_history2) >= 2:
                    
                    # Determine dynamic max_alpha and min_alpha based on data, rounded to ensure integer values
                    min_alpha = int(min(min(alpha_history1), min(alpha_history2)) - 2)
                    # max_alpha = int(max(max(alpha_history1), max(alpha_history2)) * 1.1)  # Add 10% buffer above
                    raw_max_alpha = max(max(alpha_history1), max(alpha_history2)) * 1.1  # Add 10% buffer above the maximum data point
                    max_alpha = int(np.ceil(raw_max_alpha))  # Round up to the nearest integer


                    # Ensure integer tick interval
                    tick_interval = max(1, (max_alpha - min_alpha) // 4)  # Choose an interval to divide the range into 4 or more ticks

                    max_alpha = min_alpha + (tick_interval * 4)
                    
                    # Scale the points for each player's alpha power history
                    points1 = [(graph_x_start + i * (graph_width // history_length), graph_y_start + graph_height - int(((alpha - min_alpha) / (max_alpha - min_alpha)) * graph_height)) for i, alpha in enumerate(alpha_history1)]
                    points2 = [(graph_x_start + i * (graph_width // history_length), graph_y_start + graph_height - int(((alpha - min_alpha) / (max_alpha - min_alpha)) * graph_height)) for i, alpha in enumerate(alpha_history2)]

                    # Draw lines for both players' alpha power history
                    pygame.draw.lines(screen, (255, 0, 0), False, points1, 2)
                    pygame.draw.lines(screen, (0, 0, 255), False, points2, 2)

                    # Add y-axis labels and tick marks
                    for i in range(5):
                        # y_value = min_alpha + (max_alpha - min_alpha) * (i / 4)
                        y_value = min_alpha + (tick_interval * i)
                        y_position = graph_y_start + graph_height - int(((y_value - min_alpha) / (max_alpha - min_alpha)) * graph_height)
                        tick_label = label_font.render(f"{y_value:.1f}", True, (0, 0, 0))
                        screen.blit(tick_label, (graph_x_start - 40, y_position - tick_label.get_height() // 2))
                        pygame.draw.line(screen, (0, 0, 0), (graph_x_start - 5, y_position), (graph_x_start, y_position), 2)

                    # Add x-axis labels and tick marks for epochs (starting from 0 on the left and incrementing by 5)
                    for i in range(0, history_length, 5):
                        x_position = graph_x_start + i * (graph_width // history_length)
                        tick_label = label_font.render(f"{i}", True, (0, 0, 0))
                        screen.blit(tick_label, (x_position - tick_label.get_width() // 2, graph_y_start + graph_height + 5))
                        pygame.draw.line(screen, (0, 0, 0), (x_position, graph_y_start + graph_height), (x_position, graph_y_start + graph_height + 5), 2)

                # Add x-axis label
                x_label = label_font.render(f"Epochs ({epoch_duration}s each)", True, (0, 0, 0))
                screen.blit(x_label, (graph_x_start + graph_width // 2 - x_label.get_width() // 2, graph_y_start + graph_height + 25))

                # Add y-axis label
                y_label = label_font.render("Alpha Power", True, (0, 0, 0))
                screen.blit(y_label, (graph_x_start - 155, graph_y_start + graph_height // 2 - y_label.get_height() // 2))
                
                center_offset = 300  # Distance from the center
                bar_max_width = 300  # Maximum width for the bars
                
                # Display current and average alpha power values
                alpha_text1 = alpha_font.render(f'{board1.get_board_name()} Alpha Power: {alpha_power1:.2f} (Avg: {avg_alpha_power1:.2f})', True, (255, 0, 0))
                alpha_text2 = alpha_font.render(f'{board2.get_board_name()} Alpha Power: {alpha_power2:.2f} (Avg: {avg_alpha_power2:.2f})', True, (0, 0, 255))
                screen.blit(alpha_text1, ((width // 2) - center_offset - bar_max_width, 70))
                screen.blit(alpha_text2, ((width // 2) + 200, 70))

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