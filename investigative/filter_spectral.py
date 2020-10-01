import struct
import time
import sys
import os

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
# on my machine (Ubuntu 18.04)


# There is a choice to set in pulseaudio or ALSA. They seem to override each other, so only do one:
if False:
  os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(3830)) # Default = 3830, maximum=65536
else:
  os.system("amixer -c 0 cset iface=MIXER,name='Capture Volume' {0}".format(46)) # Default = 46, maximum=46
  os.system("amixer -c 0 cset iface=MIXER,name='Line Boost Volume' {0}".format(1)) # Default = 0, maximum=3

# Open MIDI

f = os.open('/dev/midi1', os.O_RDWR)

USE_SINE = False

# Set volume and pan in the keyboard. Writing this combination overrides the
# physical volume control, meaning this test should be repeatable.
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 33) + b'\xf7')
time.sleep(0.2)
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
time.sleep(0.2)

if USE_SINE:
  # Set "SINE LEAD"
  os.write(f, b'\xb0\x00' + struct.pack('B', 2) + b'\xc0' + struct.pack('B', 80))
else:
  # Set "EDM SW WHITE"
  os.write(f, b'\xb0\x00' + struct.pack('B', 15) + b'\xc0' + struct.pack('B', 96))
  time.sleep(0.2)
  # Set Memory=3, Category=3 (Tones), Parameter set = 32 (currently selected MIDI In Channel 1), Parameter 20 Block 5
  # This sets Release time to minimum, so it doesn't overlap with the next tone
  os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x05\x00\x14\x00\x00\x00\x00\x00\x7f\x07\xf7')
  
  # Set Parameters 56-58 (reverb, chorus and delay send) to 0.
  os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x38\x00\x00\x00\x00\x00\x00\xf7')
  time.sleep(0.2)
  os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x39\x00\x00\x00\x00\x00\x00\xf7')
  time.sleep(0.2)
  os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3A\x00\x00\x00\x00\x00\x00\xf7')
  time.sleep(0.2)
  
time.sleep(0.2)

# Select the notes to be played -- only used if USE_SINE is true
notes = range(15, 75, 5)
output = ''

# Select the parameter values to try
#params = [-1, 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]
params = [-1] + list(range(0,16,2))

# An array to put results into -- only used if USE_SINE is true
ar = numpy.zeros([len(params),len(notes)])


SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
RATE = 48000    # units of Hz. Probably only certain values are allowed, e.g.
                #  24000, 44100, 48000, 96000, ....

p = pyaudio.PyAudio()

x = p.open(format=pyaudio.paInt16,
            channels=2,
            rate=RATE,
            input=True,
            start=False)



b = []


for j in range(len(params)):
  
  pm = params[j]
  print('Doing parameter {0}'.format(pm))

  FILTER_TYPE = 5
  PARAM_1 = pm
  PARAM_2 = 0
  PARAM_3 = 0

  # Set Memory=3, Category=3 (Tones), Parameter set = 32 (currently selected MIDI In Channel 1), Parameters 117-119
  if pm < 0:
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00u\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00v\x00\x00\x00\x00\x00' + struct.pack('B', 12) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00w\x00\x00\x00\x00\x00' + struct.pack('B', 12) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00x\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7')
    time.sleep(0.1)
  else:
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00u\x00\x00\x00\x00\x00' + struct.pack('B', FILTER_TYPE) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00v\x00\x00\x00\x00\x00' + struct.pack('B', PARAM_1) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00w\x00\x00\x00\x00\x00' + struct.pack('B', PARAM_2) + b'\xf7')
    time.sleep(0.1)
    os.write(f, b'\xf0\x44\x19\x01\x7f\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00x\x00\x00\x00\x00\x00' + struct.pack('B', PARAM_3) + b'\xf7')
    time.sleep(0.1)


  if USE_SINE:
    for k in range(len(notes)):


      nn = notes[k]
      


      # MIDI note on
      os.write(f, b'\x90' + struct.pack('B', nn) + b'\x6e')
      time.sleep(0.1)

      lx = []

      x.start_stream()

      #Read chunks
      for i in range(1):
        y = x.read(round(RATE*SAMPLE_TIME))
        w = 0
        while w+4 <= len(y):
          (l, r) = struct.unpack('<2h', y[w:w+4]) # left & right samples
          lx.append(l)
          w += 4

        #with open('y.bin', 'wb') as f1:
        #  f1.write(y)



      x.stop_stream()

      # MIDI note off
      os.write(f, b'\x80' + struct.pack('B', nn) + b'\x7f')
      time.sleep(0.4)

      ly = numpy.abs(numpy.fft.fft(lx))
      excl = 4   # Ignore a certain number of readings around 0 (DC) since there is
                 # often a big spike there
      idx = numpy.argmax(ly[excl:-excl])+excl
      if idx > RATE*SAMPLE_TIME/2:
        idx = RATE*SAMPLE_TIME - idx
      ampl = numpy.sqrt(numpy.mean(numpy.square(lx-numpy.mean(lx))))
      output += '{0} {1} {2} {3}\n'.format(nn, 2.0*numpy.max(ly)/len(ly), ampl, idx/SAMPLE_TIME)
      ar[j,k] = ampl

  else:
    
    nn = 60   # Minimum 60 (EDM SW WHT doesn't play any lower than this!!)
    
    # MIDI note on
    os.write(f, b'\x90' + struct.pack('B', nn) + b'\x6e')
    time.sleep(0.1)

    x.start_stream()

    lx = []

    #Read chunks - currently just use 1
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
    b.append(pw)

plt.figure()

output_2 = ''
if USE_SINE:

  # Post-process into a tabular text format

  for k in range(len(notes)):
    true_freq = 440.*numpy.power(2., (notes[k]-69)/12.)
    output_2 += '{0} '.format(true_freq)
    for j in range(len(params)):
      output_2 += '{0} '.format(ar[j,k])
    output_2 += '\n'
else:

  # Post-process into a tabular text format, and also display as a
  # pyplot graph in dB.

  idx_0 = 0   # Which index to use as comparison
  
  
  for k in range(len(b[0])):
    true_freq = fr[k]
    output_2 += '{0} '.format(true_freq)
    for j in range(len(params)):
      if j != idx_0:
        output_2 += '{0} '.format(10.*numpy.log10(b[j][k]/b[idx_0][k]))
        
    output_2 += '\n'
  for j in range(len(params)):
    if j != idx_0:
      c = []
      for k in range(len(b[0])):
        c.append(10.*numpy.log10(b[j][k]/b[idx_0][k]))
      plt.plot(fr, c, label='{0}'.format(params[j]))
  plt.xlim(0,2500)  # Most interesting stuff happens under 2.5kHz
  plt.legend(loc='lower right')
        
    

with open('Out.txt', 'w') as f2:
  f2.write(output)
with open('Out_2.txt', 'w') as f3:
  f3.write(output_2)

# Show the plot -- will be empty if USE_SINE is true. Just close it
plt.show()



# Finished. Tidy everything up.
os.close(f)

x.close()

p.terminate()


