# ac7maker
Tools for creating AC7 rhythm files for Casio keyboards (especially CT-X keyboards)

## ac7maker.py
This is a python script which takes a JSON file defining a rhythm pattern as input,
and outputs a Casio-format AC7 file to the standard output.

## sysex_comms.py
A python script which can upload rhythms to a Casio CT-X keyboard connected over
MIDI. This is Linux-only and assumes that the keyboard is on device `/dev/midi1`. On
Windows, the "Casio Data Manager" program from Casio works perfectly well.

## Help.html
An interactive HTML file which defines the JSON format expected by `ac7maker.py`.
Open in any browser.

## examples/
A directory with example rhythms ready to be compiled with `ac7maker.py`. Type:
```
  python3 ac7maker.py examples/example-1.json > ex01.AC7
  python3 ac7maker.py examples/example-2.json > ex02.AC7
```

The files `ex01.AC7` and `ex02.AC7` can be copied to the keyboard on a USB stick and
played. On a Linux system with a MIDI connection to the keyboard, the following
will upload the rhythms without need for the USB stick:
```
  python3 ac7maker.py examples/example-1.json > ex01.AC7 ; python3 sysex_comms.py 294 < ex01.AC7
  python3 ac7maker.py examples/example-2.json > ex02.AC7 ; python3 sysex_comms.py 295 < ex02.AC7
```
