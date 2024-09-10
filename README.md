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
   - `alphaWAR.py` is the working version of the game.

3. **Connect the OpenBCI boards:**
   - For **Mac** users: 
     1. Open `System Information` and locate the OpenBCI board under **USB**. 
     2. Copy the serial number and update it in the code on lines 88–89.
   - For **Windows** users: 
     1. Open **Device Manager** and find the OpenBCI board under **Ports (COM & LPT)**.
     2. Update the serial number in the code on lines 88–89.

4. **Run the game:**
   `
   python alphaWAR.py --duration <duration_in_seconds> --epoch_duration <epoch_duration_in_seconds>
   `
   - Turn down your speaker volume. The game uses sound cues!

## How It Works

1. Two OpenBCI boards are connected to the computer using the BrainFlow library.
2. Players wear EEG headsets, and the game measures their **alpha wave** activity (8-12 Hz) during each epoch.
3. The player with higher alpha power pulls the virtual rope towards their side.
4. The game ends when the rope reaches one player’s side, determining the winner.
5. Sound effects indicate the rope’s position, providing additional feedback.

## Game Controls

- **Space Bar**: Replay the game after a match.
- **Escape**: Quit the game.

## Notes

- Make sure your OpenBCI boards are properly connected and the correct ports are selected in the code.
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
