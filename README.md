# ac7maker
Tools for creating AC7 rhythm files for Casio keyboards (especially CT-X keyboards)

### ac7maker.py
This is a python script which takes a JSON file defining a rhythm pattern as input,
reads standard MIDI files containing the music data for each element of the rhythm,
and outputs a Casio-format AC7 file to the standard output.

### sysex_comms.py
A python script which reads a AC7 rhythm from the standard input and uploads it
to a Casio CT-X keyboard over a MIDI connection. This is Linux-only and assumes that
the keyboard is the first enumerated MIDI connection (that is, it is on device
`/dev/midi1`). On Windows, the "Casio Data Manager" program
from Casio is a good alternative.

### Help.html
An interactive HTML file which defines the JSON format expected by `ac7maker.py`.
Opens in any browser.

### examples/
A directory with example rhythms ready to be made with `ac7maker.py`. The
following command will create files `ex01.AC7` and `ex02.AC7` which can be copied
to a USB stick and saved to the keyboard:
```
  python ac7maker.py examples/example-1.json > ex01.AC7
  python ac7maker.py examples/example-2.json > ex02.AC7
```

On a Linux system with a MIDI connection to the keyboard, the following
will upload the rhythms without need for a USB stick:
```
  python ac7maker.py examples/example-1.json > ex01.AC7 ; python sysex_comms.py 294 < ex01.AC7
  python ac7maker.py examples/example-2.json > ex02.AC7 ; python sysex_comms.py 295 < ex02.AC7
```

## Prerequisites
Python 3 should be installed, ideally version 3.7 or newer. Beyond that, no special libraries
are needed.
