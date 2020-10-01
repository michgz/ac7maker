# Investigative Directory
This directory contains scripts to help investigate the behaviour of the keyboard. They are
very specific to my computer setup so they shouldn't be expected to work on other systems
without a lot of changes. They're just put here in case the are helpful to somebody.

## filter_spectral.py
A program for investigating the effect of different filter parameters on tones. The keyboard
should be connected through USB MIDI, and the headphone jack connected to the Line In sound
input. The script plays a white noise (specifically, tone 375 "EDM SE WHITE") both with and
without filtering and analyses the spectral changes with a Welch transform.
