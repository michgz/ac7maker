# Investigative Directory
This directory contains scripts to help investigate the behaviour of the keyboard. They are
very specific to my computer setup so they shouldn't be expected to work on other systems
without a lot of changes.

## filter_spectral.py
A program for investigating the effect of different filter parameters on tones. The keyboard
should be connected through USB MIDI, and the headphone jack connected to the Line In sound
input. The script plays a white noise both with and without filtering and analyses the
spectral changes with a Welch transform.

## check_override.py
A script to prove that filter effects applied through a rhythm (i.e. the 0x35 atom) can
override the two specified in the tone definition (parameters 117-120). The setup is the
same as above, the tone 375 "EDM SE WHITE" must be copied to user tone 801 so that it can
be programmatically edited, and the "ac7maker" program must have special handling added
to cope with a special "var_35_1" variable.
