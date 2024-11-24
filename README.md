# AlphaWar

**AlphaWar** is an EEG-based game where two players use their brain's alpha waves to engage in a virtual tug-of-war. Harness the power of hyper-scanning technology and battle your opponent by focusing your mind and increasing your alpha wave activity!

## Installation

1. **Clone the repository:**
   `
   git clone https://github.com/YourRepo/AlphaWar.git
   cd AlphaWar
   `

2. **Setup the game:**
   - Ensure you have Python and the required libraries installed. Install dependencies using:
     `
     pip install -r requirements.txt
     `

## How It Works

1. Players wear and connect OpenBCI EEG headsets, and the game measures their **alpha wave** activity (8-12 Hz) during each epoch.
2. The player with higher alpha power pulls the virtual rope *towards* their side.
3. The game ends when the rope reaches one player’s side, determining the winner.

## Running The Game
1. **Select the BCItoolkit mamba environment:**
   - In VSCode, press `ctrl + shift + p`, then enter/select "Python: Select Interpreter" -> find and select "Python 3.10.15 ('BCItoolkit')"
2. **Open `AlphaWar.py` & Adjust any Settings**
   - Any config adjustments will be at the top of script, immediately after imports
     - Adjust the board ID: 
       - `BoardIds.CYTON_BOARD.value` should be used if using the OpenBCI Cyton Boards
       - `BoardIds.SYNTHETIC_BOARD.value` is used for testing - this uses Simulated data
     - (Optional) Adjust player names - this can be any string 
3. **Start the Game!**
   - Once you have adjusted any necessary configuration Click the small 'play' arrow in the top right to start the game.
   - You will see a window pop up and big "Scan Ports" button
     - Plug player 1's Cyton Dongle in and click "Scan Ports" - this will assign that board to player 1
     - Then, plug in player 2's Cyton Dongle and click "Scan Ports" again - this will assign the second board to player 2
    - Once both players have been assigned, click "Start" to begin the game!

## Game Controls
- **Space Bar**: Replay the game after a match.
- **Escape**: Quit the game.

## Trouble-Shooting:
- "No compatible devices found..." when scanning ports
  1. Ensure the switch on the dongle is set towards the male USB end and that the board's switch is set to "Off".
  2. Then unplug the dongle and plug it back in.
  3. Set the switch on the board to "PC".
  5. Click "Scan Ports" again


## How It Works

1. Two OpenBCI boards are connected to the computer using a custom class built off the BrainFlow library.
2. Players wear EEG headsets, and the game measures their **alpha wave** activity (8-12 Hz) during each epoch.
3. The player with higher alpha power pulls the virtual rope *towards* their side.
4. The game ends when the rope reaches one player’s side, determining the winner.

## Game Controls

- **Space Bar**: Replay the game after a match.
- **Escape**: Quit the game.

## Notes

- Focus on calming your mind to increase alpha waves—practice mindfulness for a competitive edge!

## Credits

This is a fork of the [original repository](https://github.com/KyaMas/AlphaWar)

This game was developed during a hackathon by:

- [Kya Masoumi-Ravandi](https://github.com/KyaMas)
- Can Sozuer
- Shihui Gao
- Noof Al Shehhi
- Danella Calina

For more information on their project check out `Hackathon Presentation.pptx`
