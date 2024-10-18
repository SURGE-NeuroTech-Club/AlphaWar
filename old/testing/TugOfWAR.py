import time
import pygame
import sys
import pygame.font
import argparse
import numpy as np
import matplotlib.pyplot as plt
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
import pygame.mixer


# Initialize Pygame
pygame.init()
# Initialize Pygame mixer
pygame.mixer.init(frequency=20, size=-16, channels=2)
 
def generate_sine_wave(frequency, duration=0.5, volume=0.5, sample_rate=256):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = volume * np.sin(2 * np.pi * frequency * t)
    return wave.astype(np.float32)
 
def generate_sawtooth_wave(frequency, duration=0.5, volume=0.5, sample_rate=256):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = volume * 2 * (t * frequency - np.floor(1/2 + t * frequency))
    return wave.astype(np.float32)
 
def play_sound_for_rope_position(rope_position):
    frequency = 440 + 10 * abs(rope_position)**3  # Base frequency plus a factor of the rope position
    if rope_position > 0:
        waveform = generate_sine_wave(frequency)
    else:
        waveform = generate_sawtooth_wave(frequency)
    sound = pygame.sndarray.make_sound(waveform.repeat(2).reshape((-1, 2)).copy(order='C'))
    sound.play()

# load the sounds
buzzer_sound = pygame.mixer.Sound('buzzer.wav')
def play_buzzer_sound():
    pygame.mixer.Sound.play(buzzer_sound)

bell_sound = pygame.mixer.Sound('bell.wav')
def play_bell_sound():
    pygame.mixer.Sound.play(bell_sound)

winner_sound = pygame.mixer.Sound('winner.wav')
def play_winner_sound():
    pygame.mixer.Sound.play(winner_sound)

# Set the font
pygame.font.init()
font = pygame.font.Font(None, 36)
winner = ''

# Set the window size
width, height = 1440, 800
rope_width = 250
rope_height = 10

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Tug of War')

# set up the players and the rope
player1 = pygame.Rect(100, 250, 10, 300)
player2 = pygame.Rect(1340, 250, 10, 300)

# input_p1 = 0 # avg alpha of player 1
# input_p2 = 0 # avg alpha of player 2
# input_var = input_p1 - input_p2
# threshold = 0

# game loop
quit_game = False
while not quit_game:
    # initialize the game state
    speed = 1
    rope = pygame.Rect(595, 400, rope_width, rope_height)
    rope_control = 0

    #start data
    
    # game loop
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
                
        
            # this can be removed once inputs are connected
                elif event.key == pygame.K_a:
                    rope_control = -1
                elif event.key == pygame.K_d:
                    rope_control = 1
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_a, pygame.K_d):
                    rope_control = 0

        #  # Modify rope_control based on input_var
        # if input_var < threshold:
        #     rope_control = -1
        # elif input_var > threshold:
        #     rope_control = 1
        # else:
        #     rope_control = 0
                    
        play_sound_for_rope_position((rope.left + rope.right)/2)
        

        # game logic
        if rope_control < 0:
            rope.move_ip(-speed, 0)
            #time.sleep(0.02)
        elif rope_control > 0:
            rope.move_ip(speed, 0)
            #time.sleep(0.02)

        # Check if the rope has completely passed one of the player markers
        # Determine the winner.
        if rope.right <= player1.left or rope.left >= player2.right:
            if rope.right <= player1.left:
                winner = 'Player 1'
                play_winner_sound()
            elif rope.left >= player2.right:
                winner = 'Player 2'
                play_winner_sound()
            running = False
            play_winner_sound()


        # drawing
        screen.fill((255, 255, 255))
        pygame.draw.rect(screen, (0, 0, 0), rope)
        pygame.draw.rect(screen, (255, 0, 0), player1)
        pygame.draw.rect(screen, (0, 0, 255), player2)

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

#end data collection 

# quit the game
pygame.quit()