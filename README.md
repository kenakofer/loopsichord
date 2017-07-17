# Loopsichord

Loopsichord is a powerful digital instrument with focus on the mouse, looping, colors and visualizations. It takes the layout of a traditional keyboard into the second dimension by lining up diatonic major scales above and below each other, with related keys adjacent. The looping feature allows anyone to build musical layers of harmony in an accessible, powerful, and visually elegant way.

The thing that sets the loopsichord apart from other digital instruments is that the primary expressive control is in the mouse. Furthermore, it is easily accessible to making music without prior introduction to music or the instrument. It is also useful as an educational tool for experientially learning the musical theory of scales and how they relate to one another. And importantly, it is awesome, fun, and usable for experienced musiscians.

## Running

```python3```, ```pygame```, ```pyaudio```, and ```numpy``` packages are required. Execute ```run.py``` to run the application. Press ESC to quit.

A mouse with a left click, right click, and clickable scroll wheel, as well as a keyboard, are needed to access all the capabilities.

If the audio is consistently jittery, try closing some programs on your computer. Additionally, setting ```BUFFER_SIZE=2048``` in ```constants.py``` should give a significant speed boost for marginal losses in responsiveness.

---

## Features
### Basic sounds:
 - Articulate a note
 - Slur one note into another
 - Snap to the occupied diatonic scale by default
 - Switch seamlessly between any of the 12 diatonic major keys by vertical movement of the mouse
 - Snap to chromatic notes
 - Disable pitch snapping, allowing pitches outside of the 12 semitones
 - Increase/decrease volume
 - Pan limitlessly around the instrument: left for lower pitch, right for higher, up for scales with more flats on the circle of fifths, and down for more sharps. 
 - There is no privileged key signature: C is as easy to play in as Db
 - Colorful and responsive drawing of the currently playing note(s)
### Loop tracks:
 - Enable/disable recording to a new or existing loop track
 - Enable/disable playing of recorded tracks individually or globally (with visual reenactment as well)
 - Adjust volume of track
 - Shift track forward or backward by one beat or one sample buffer(~40th of a second)
 - Copy existing track onto a new track (and mutes the copy)
 - Multiply loop length while copying a track
 - Combine multiple tracks into one
 - Delete track
 - Select a range of tracks to apply the above operations at once
 - Unlimited tracks with negligible additional system load
 - Color-coded thumbnails of the volumes and pitches within each track
 - Save and load the tracks in a .loops file
 - Export the track samples to a wav file (channels are saved individually for easier external editing)
### Other:
 - Instruction menu on startup or keypress
 - Adjustable metronome settings (before loops are present)
 - Uses buffering of images wherever possible to reduce CPU load
 - Just and equal temperament capabilities
 - ```constants.py``` contains many configurable options for the UI and backend
 
 ---
 
## Features that will be added soon:
 - Adjustable harmonics
 - Adjustable loop length after loops exist
 - Optional beat alignment to assist with rhythmic precision (quantizing)
 - Swapping custom scales in and out of the UI (e.g. whole tone, harmonic minor)
 - Loading samples from arbitrary wav data


