from brainflow.board_shim import BoardShim
from brainflow import BrainFlowInputParams
from brainflow import BoardIds
import time

BoardShim.enable_dev_board_logger()

# make a function to print data
def process_data(sample):
    print("Received sample:", sample.channels_data)

params = BrainFlowInputParams()
params.serial_port = '/dev/cu.usbserial-DM01HOSQ'
board = BoardShim(BoardIds.CYTON_BOARD, params)

params2 = BrainFlowInputParams()
params2.serial_port = '/dev/cu.usbserial-DM01HWJ7'
board2 = BoardShim(BoardIds.CYTON_BOARD, params2)
print('here')

board.prepare_session()
board2.prepare_session()
print('here f')

board.start_stream()
board2.start_stream()


print('here')
time.sleep(10)

data = board.get_board_data()  # get all data and remove it from internal buffer
data2 = board2.get_board_data()  # get all data and remove it from internal buffer
board.stop_stream()
board2.stop_stream()

board.release_session()
board2.release_session()


# print the first 8 columns of data
print("data: ", data[1:9])

print("data 2: ", data2[1:9])

