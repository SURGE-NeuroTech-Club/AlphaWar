"""Added the ability to compete using brain graphs/networks, taking this game past alpha waves and justifying a name change to `Brain War`"""
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
from dtaidistance import dtw
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from scipy.ndimage import gaussian_filter1d
    
    
class SmallBrainGraph:
    def __init__(self, signals, threshold_percentage=50, distance_metric='euclidean'):
        self.signals = signals
        self.threshold_percentage = threshold_percentage
        self.distance_metric = distance_metric
        self.corr = self._get_corr_matrix()
        self.adj, self.D, self.L, self.lrw = self._get_brain_graph()
        
        
    def retrain(self, signals):
        self.__init__(signals=signals)
        
        
    def _get_corr_matrix(self):
        """
        Calculate the correlation matrix for a set of time signals.
        """
        signals = self.signals
        if self.distance_metric == 'euclidean':
            # Vectorized calculation of Euclidean distances
            sq_norms = np.sum(signals**2, axis=1).reshape(-1, 1)
            distance_matrix = np.sqrt(sq_norms + sq_norms.T - 2 * np.dot(signals, signals.T))
        elif self.distance_metric == 'dtw':
            # DTW calculations 
            num_signals = signals.shape[0]
            distance_matrix = np.zeros((num_signals, num_signals))
            for i in range(num_signals):
                for j in range(i + 1, num_signals): 
                    distance, paths = dtw.distance(signals[i], signals[j], use_pruning=True, use_c=True)
                    distance_matrix[i, j] = distance_matrix[j, i] = distance
        else:
            raise ValueError("Unsupported distance metric.")
        
        correlation_matrix = 1 / (1 + distance_matrix)  
        np.fill_diagonal(correlation_matrix, 1)
        
        return correlation_matrix
    
    
    def _get_brain_graph(self, signals=None):
        """Calculates the random walk Laplacian of the brain graph/network."""
        if signals is not None:
            self.signals = signals
        num_signals = self.signals.shape[0]
        adj = np.abs(self.corr) - np.eye(num_signals)
        adj[adj < np.percentile(adj, self.threshold_percentage)] = 0
        D = np.diag(adj.sum(axis=1))
        D_inv = np.linalg.pinv(D)
        L = D - adj
        lrw = np.eye(num_signals) - np.dot(D_inv, adj)
        return adj, D, L, lrw

        
    def signal_smoothness(self, signals, metric='diriclet'):
        """
        Parameters:
        - signals (np.array): Matrix of signal values with rows as individual signals.
        - type (str): 'dirichlet' for Dirichlet energy, 'tvg' for total variation.
        """
        # dirichlet energy
        if metric == 'dirichlet':
            smoothness_values = signals.T * (self.L @ signals)
            avg_smoothness = smoothness_values.mean()
            return avg_smoothness
        # total variation of a graph signal
        elif metric == 'tvg':
            variation_values = []
            for signal in signals:
                TV_g = 0
                N = self.adj.shape[0]  
                for i in range(N):
                    for j in range(i + 1, N):
                        if self.adj[i, j] > 0:  
                            TV_g += self.adj[i, j] * np.abs(signal[i] - signal[j])
                variation_values.append(TV_g)
            avg_smoothness = mean(variation_values)
            return avg_smoothness

    
def get_alpha_power(signals, board_id, normalize='betaalpha'):
    """
    Parameters:
     - normalize: {'max', 'norm', 'betaalpha'} How to normalize the alpha powers. 'max' uses the maximum FFT value,
       'norm' uses the vector norm, and 'betaalpha' returns the ratio of raw beta power to raw alpha power.
    """
    ps = np.abs(np.fft.fft(signals, axis=1))**2
    freqs = np.fft.fftfreq(signals.shape[1], 1 / BoardShim.get_sampling_rate(board_id))
    
    alpha_range = (freqs >= 8) & (freqs <= 12)
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
        beta_range = (freqs > 12) & (freqs <= 30)
        beta_powers = np.sum(ps[:, beta_range], axis=1)
        beta_alpha_ratio = np.sum(beta_powers) / np.sum(alpha_powers)
        return beta_alpha_ratio
    else:
        raise ValueError("the normalize parameter must be 'max', 'norm', or 'betaalpha'")


def init_pygame(width, height, font_size):
    pygame.init()  
    pygame.font.init()
    font = pygame.font.Font(None, font_size)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Brain War') 
    return font, screen
    
    
def init_board(serial_port, board_id):
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


def get_dom_freq(signals, board_id):
    """
    For future SSVEP use
    Calculate the dominant frequency across all signals in an array.
    """
    ps = np.abs(np.fft.fft(signals, axis=1))**2
    total_ps = np.sum(ps, axis=0)
    smooth_ps = gaussian_filter1d(total_ps, sigma=0.5)
    freqs = np.fft.fftfreq(signals.shape[1], 1 / BoardShim.get_sampling_rate(board_id))
    idx_max_power = np.argmax(smooth_ps)
    dom_freq = freqs[idx_max_power]
    return dom_freq
    

def alpha_war(board1, board2, screen, font, epoch_duration):
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

        if board1 is not None and board2 is not None:
            data1 = data2 = None
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

            if data1 is not None and data2 is not None and data1.size and data2.size:
                alpha_power1 = get_alpha_power(data1, board_id1) if data1.size else 0
                alpha_power2 = get_alpha_power(data2, board_id2) if data2.size else 0

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


def network_war():
    """Placeholder"""
    # Add a mechanism to initialize a brain graph
    #   - Players should be able to start initializing when they feel ready
    # start tug of war with signal smoothness as the difference metric 
    pass


def parse_args():
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
    parser.add_argument('--game_type', type=str, default='alpha_war', help='The type of game to launch. Options are "alpha_war" and "brain_war".')
    return parser.parse_args()


def main():
    args = parse_args()
    font, screen = init_pygame(args.width, args.height, args.font_size)
    
    board1 = init_board(args.port1, BoardIds.CYTON_BOARD.value)
    board2 = init_board(args.port2, BoardIds.CYTON_BOARD.value)
    
    if args.game_type == 'alpha_war':
        alpha_war(board1, board2, screen, font, args.epoch_duration) 
    elif args.game_type == 'network_war':
        network_war()
    else:
        raise ValueError (f"The specified game type, {args.game_type} is not one of the defined game types")

    if 'board1' in locals() and board1 is not None:
        try:
            board1.stop_stream()
            board1.release_session()
        except Exception as e:
            print(type(board1), e)
        # board1.stop_stream()
        # board1.release_session()
    if 'board2' in locals() and board2 is not None:
        try:
            board2.stop_stream()
            board2.release_session()
        except Exception as e:
            print(type(board2), e)
        # board2.stop_stream()
        # board2.release_session()
        pygame.quit()


if __name__ == '__main__':
    main()
