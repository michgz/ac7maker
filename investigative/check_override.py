#! /usr/bin/python3


# This script investigates the override behaviour of rhythm filter definitions
# versus tone filter definitions



import struct
import time
import sys
import os
import json

import ac7maker
import sysex_comms

import numpy
import scipy.signal as signal

# If pyaudio is not installed, type (for Ubuntu 18.04):
#   > sudo apt-get install portaudio19-dev python-pyaudio
#   > pip3 install PyAudio
#
import pyaudio

#If matplotlib is not install, type
#   > pip3 install matplotlib
#
import matplotlib.pyplot as plt

# First, set capture volumes. This is highly dependent on audio setup. It works
# on my machine


# There is a choice to set in pulseaudio or ALSA. They seem to override each other.
if False:
  os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(3830)) # Default = 3830, maximum=65536
else:
  os.system("amixer -c 0 cset iface=MIXER,name='Capture Volume' {0}".format(20)) # Default = 46, maximum=46
  os.system("amixer -c 0 cset iface=MIXER,name='Line Boost Volume' {0}".format(2)) # Default = 0, maximum=3

# Open MIDI

f = os.open('/dev/midi1', os.O_RDWR)


# Set volume and pan in the keyboard. Writing this combination overrides the
# physical volume control
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 22) + b'\xf7')
time.sleep(0.2)
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
time.sleep(0.2)




# Set "EDM SW WHITE"
# This requires that sound 375 must be saved as user Tone 1 (801) before running this script
os.write(f, b'\xb0\x00' + struct.pack('B', 65) + b'\xc0' + struct.pack('B', 0))
time.sleep(0.2)
# Set Memory=1, Category=3 (Tones), Parameter set = 0, Parameter 20 Block 5
# This sets Release time to minimum
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x14\x00\x00\x00\x00\x00\x7f\x07\xf7')
time.sleep(0.2)

# Set Parameters 56-58 (reverb, chorus and delay send) to 0.
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x00\x00\x00\x00\x00\xf7')
time.sleep(0.2)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x39\x00\x00\x00\x00\x00\x00\xf7')
time.sleep(0.2)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3A\x00\x00\x00\x00\x00\x00\xf7')
time.sleep(0.2)


# Set tone filters on
# Block 0
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00u\x00\x00\x00\x00\x00' + struct.pack('B', 6) + b'\xf7')
time.sleep(0.1)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00v\x00\x00\x00\x00\x00' + struct.pack('B', 10) + b'\xf7')
time.sleep(0.1)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00w\x00\x00\x00\x00\x00' + struct.pack('B', 24) + b'\xf7')
time.sleep(0.1)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00x\x00\x00\x00\x00\x00' + struct.pack('B', 15) + b'\xf7')
time.sleep(0.1)
# Block 1
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00u\x00\x00\x00\x00\x00' + struct.pack('B', 6) + b'\xf7')
time.sleep(0.1)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00v\x00\x00\x00\x00\x00' + struct.pack('B', 16) + b'\xf7')
time.sleep(0.1)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00w\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7')
time.sleep(0.1)
os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00x\x00\x00\x00\x00\x00' + struct.pack('B', 15) + b'\xf7')
time.sleep(0.1)


notes = [60]
output = ''

#ar = numpy.zeros([len(params),len(notes)])


SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
RATE = 48000    # units of Hz. Probably only certain values are allowed, e.g.
                #  24000, 44100, 48000, 96000, ....

p = pyaudio.PyAudio()

x = p.open(format=pyaudio.paInt16,
            channels=2,
            rate=RATE,
            input=True,
            start=False)



b_1 = []


for j in range(2):

  # Select Tone (again)
  # Set "EDM SW WHITE"
  # This requires that sound 375 must be saved as user Tone 1 (801) before running this script
  os.write(f, b'\xb0\x00' + struct.pack('B', 65) + b'\xc0' + struct.pack('B', 0))
  time.sleep(0.2)




  # Set Memory=1, Category=3 (Tones), Parameter set = 0, Parameters 117-120
  if j == 0:
    # Set tone filters off (Default)
    # Block 0
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00u\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00v\x00\x00\x00\x00\x00' + struct.pack('B', 12) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00w\x00\x00\x00\x00\x00' + struct.pack('B', 12) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00x\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7')
    time.sleep(0.1)
    # Block 1
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x01\x00u\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x01\x00v\x00\x00\x00\x00\x00' + struct.pack('B', 12) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x01\x00w\x00\x00\x00\x00\x00' + struct.pack('B', 12) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x01\x00x\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7')
    time.sleep(0.1)
  else:
    # No action to tone filters
    # (Remain on)
    pass
    
  # Select notes to play
  nn = notes[0]
    
  # MIDI note on
  os.write(f, b'\x90' + struct.pack('B', nn) + b'\x6e')
  time.sleep(0.1)

  x.start_stream()

  lx = []

  #Read chunks
  for i in range(1):
    y = x.read(round(RATE*SAMPLE_TIME))
    w = 0
    while w+4 <= len(y):
      (l, r) = struct.unpack('<2h', y[w:w+4]) # left & right samples
      lx.append(l)
      w += 4

  x.stop_stream()

  # MIDI note off
  os.write(f, b'\x80' + struct.pack('B', nn) + b'\x7f')
  time.sleep(0.5)
  
  fr, pw = signal.welch(lx, RATE)
  b_1.append(pw)

plt.figure()

idx_0 = 0

for j in range(2):
  if j != idx_0:
    c = []
    for k in range(len(b_1[0])):
      c.append(10.*numpy.log10(b_1[j][k]/b_1[idx_0][k]))
    plt.plot(fr, c, label='{0}'.format(j))
plt.xlim(0,5000)  # Frequency range to show
plt.legend(loc='lower right')

plt.show()


os.close(f)



# Now create two rhythms with different filters
with open('test-2.json') as f2:
  b = json.load(f2)
  


i = 0

for pm in range(2):
  

  if pm >= 0:
    b["rhythm"]["parts"][7]["patch"] = pm
  else:
    b["rhythm"]["parts"][7]["patch"] = 99
  b["rhythm"]["parts"][7]["bank_msb"] = 0
  
  if pm > 0:
    b["rhythm"]["elements"][1]["var_35"]   = b'\x0c\x00' + struct.pack('<4B', 6, 72, 0, 15)
    b["rhythm"]["elements"][1]["var_35_1"] = b'\x0c\x01' + struct.pack('<4B', 5, 92, 88, 15) # Note: needs a special version of ac7maker to handle this atom!
    b["rhythm"]["name"] = "Tst-{0:03d}".format(pm)
  else:
    b["rhythm"]["elements"][1]["var_35"] = []
    b["rhythm"]["elements"][1]["var_35_1"] = []

  c = ac7maker.ac7maker(b)

  with open('A{0}.AC7'.format(294+i), 'wb') as f3:
    f3.write(c)

  sysex_comms.upload_ac7(294+i, c)
  i += 1




i = 0

while True:

  ch = input("Play Rhythm {0} with chord Cmaj, then press enter to continue (q+Enter to quit)...".format(294+i))
  if ch == 'q' or ch == 'Q':
    break

  x.start_stream()
  rms = 0.
  have_got_low = False
  have_got_high = False
  THRESHOLD = 100.
  # Wait for a low RMS followed by a high RMS
  while not have_got_high:
    y = x.read(round(RATE*0.05))
    w = 0
    lx = []
    while w+4 <= len(y):
      (l, r) = struct.unpack('<2h', y[w:w+4]) # left & right samples
      lx.append(l)
      w += 4
    rms = numpy.sqrt(numpy.mean(numpy.square(lx) - numpy.mean(lx)))
    print(rms)
    if have_got_low:
      if rms > THRESHOLD:
        have_got_high = True
    else:
      if rms < THRESHOLD:
        have_got_low = True
    
  y = x.read(round(RATE*SAMPLE_TIME))
  w = 0
  lx = []
  while w+4 <= len(y):
    (l, r) = struct.unpack('<2h', y[w:w+4]) # left & right samples
    lx.append(l)
    w += 4

  x.stop_stream()

  fr, pw = signal.welch(lx, RATE)

  b_1.append(pw)

  i += 1



plt.figure()
for kk in range(2,len(b_1)):
  plt.plot(fr, 10*numpy.log10(numpy.divide(b_1[kk],b_1[idx_0])), label='{0}'.format(kk))
plt.xlim(0,5000)  # Most interesting stuff happens in this region
plt.legend(loc='upper right')
plt.show()


x.close()

p.terminate()
