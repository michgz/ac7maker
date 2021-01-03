import sys

# We're importing from a sibling directory.
sys.path.append('..')
sys.path.append('../internal')

import struct
import time
import os
import os.path
import datetime
from sysex_comms_internal import upload_ac7_internal
from sysex_comms_internal import set_single_parameter

import numpy
import scipy.signal as signal

# If pyaudio is not installed, type (for Ubuntu 18.04):
#   > sudo apt-get install portaudio19-dev python-pyaudio
#   > pip3 install PyAudio
#
import pyaudio

# If crcmod is not installed, type:
#   > pip3 install crcmod
#
import crcmod

#If matplotlib is not install, type
#   > pip3 install matplotlib
#
import matplotlib.pyplot as plt


# Set the raw MIDI device name to use.
DEVICE_NAME = '/dev/midi1'




# Turn a tone bulk data into a tone file. Not needed if uploading with
# upload_ac7_internal (that just accepts the bulk data).
def make_tone_into_file(x):
  c = b'CT-X3000' + b'\x00'*8
  c += b'TONH' + b'\x00'*4
  crc = crcmod.predefined.PredefinedCrc('crc-32')
  crc.update(x)
  c += struct.pack('<I', crc.crcValue)
  c += struct.pack('<I', len(x))
  c += x
  c += b'EODA'
  return c
  

# Create a tone structure based on arbitrary wavetable type and number.
# Everything else is just default, including DSP which will be empty.
#
# "wavtab1" defines the sound that is created. "wavtab2" is also specified; it
# can be 0x00, or the same as "wavtab1", or something different. In most
# cases it doesn't make much audible difference to the sound.
#
# Some special values of "wavtab1" are listed below. These do not correspond
# to any of the built-in tones (at least, on the CT-X3000/5000) so they are
# only accessible by uploading a custom-built tone. These appear to be
# provided specifically for the purposes of tuning filters, exactly what
# we're attempting to do here:
#
#     8  octave sine sweep
#   738  white noise
#   739  pink noise
#
def arb_tone(wavtab1, wavtab2=0x00, name = 'No Name \x00       ', type_of_wavetable=0x00):
  c = b''
  for x in [wavtab1, wavtab2]:
    c += b'\x00\x02\x80\x00' *31
    c += b'\x80' * 4
    c += b'\x7f'
    c += b'\x00'
    c += struct.pack('<H', x)
    c += b'\x7f' * 3
    c += struct.pack('<B', type_of_wavetable)
  reverb_send = 0  # for testing purposes make this zero. In most use-cases, a small non-zero number is best
  chorus_send = 0
  delay_send = 0
  c += struct.pack('3B', chorus_send, reverb_send, delay_send)
  c += b'\x40' * 4 + b'\x48' * 2 + b'\x40' * 11
  c += b'\xff\x00'
  
  # Now do the DSP. Just put in an empty one.
  c += b'MonoEQ1B        '
  for x in [0x3FFF, 0x3FFF, 0x3FFF, 0x3FFF]:
    c += struct.pack('<H', x) + b'\x00' * 16
  
  c += b'\x00\x08'
  c += b'\x64' * 3 + b'\x00\x02' + b'\x00' * 8 + b'\x01' + b'\x00' * 7 + b'\x04' + b'\x00' * 4 + b'\x01\x00'
  c += struct.pack('<I', 0x830C0)
  c += struct.pack('<I', 0x830C0)
  c += struct.pack('<B', 0x85)
  c += struct.pack('<B', 8)    # 9 if DSP required
  c += bytes((name[:15] + '\x00').ljust(16, ' '), 'latin-1')
  c += b'\x64\x7f\x02\x02\x02\x7f\x02\x7f\x02\x7f\x00\x00\x7f\x02\x02\x00\x00\x00'
  
  return c



# First, set capture volumes. This is highly dependent on audio setup. It works
# on my machine (Ubuntu 18.04)


# There is a choice to set in pulseaudio or ALSA. They seem to override each other, so only do one:
if False:
  os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(3830)) # Default = 3830, maximum=65536
else:
  os.system("amixer -c 2 cset iface=MIXER,name='Capture Volume' {0}".format(46)) # Default = 46, maximum=46
  os.system("amixer -c 2 cset iface=MIXER,name='Line Boost Volume' {0}".format(1)) # Default = 0, maximum=3

# Possible values:
#  'Sine'     : use a Sine signal, with RMS detection
#  'EDMWht'   : use the EDM SE WHITE noise signal, with spectral analysis
#  'Arb'      : use an arbitrary tone signal (such as white or pink noise),
#                  with spectral analysis
METHOD = 'Arb'


# Define the user tone to write to. Must lie in range 801-900. Only used
# in 'Arb' method
USER_TONE = 801


if METHOD=='Arb':
  # Create a white noise tone
  t = arb_tone(738, name = "WhtNoise")
  with open("WhtNoise.TON", "wb") as f1:
    f1.write(make_tone_into_file(t))

  upload_ac7_internal(USER_TONE-801+0, t, category=3, memory=1)

  # Create a pink noise tone
  t = arb_tone(739, name = "PnkNoise")
  with open("PnkNoise.TON", "wb") as f1:
    f1.write(make_tone_into_file(t))

  upload_ac7_internal(USER_TONE-801+1, t, category=3, memory=1)


# Create a folder for outputs
dir_name = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
os.mkdir(dir_name)



# Create a folder for outputs
dir_name = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
os.mkdir(dir_name)


# Open MIDI

f = os.open(DEVICE_NAME, os.O_RDWR)

# Set volume and pan in the keyboard. Writing this combination overrides the
# physical volume control, meaning this test should be repeatable.
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 33) + b'\xf7')
time.sleep(0.2)
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
time.sleep(0.2)

if METHOD=='Sine':
  # Set "SINE LEAD"
  os.write(f, b'\xb0\x00' + struct.pack('B', 2) + b'\xc0' + struct.pack('B', 80))
elif METHOD=='Arb':
  # Set user tone
  os.write(f, b'\xb0\x00' + struct.pack('B', 65) + b'\xc0' + struct.pack('B', USER_TONE-801+0))  # For pink noise, change "+0" to "+1"
  time.sleep(0.2)
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


SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
RATE = 48000    # units of Hz. Probably only certain values are allowed, e.g.
                #  24000, 44100, 48000, 96000, ....

p = pyaudio.PyAudio()

x = p.open(format=pyaudio.paInt16,
            channels=2,
            rate=RATE,
            input=True,
            start=False)


Filter_Types = [1,2,3,4,5,6,7,8]
Parameters_To_Sweep = [1,2,3]
Plot_Divisor = 3   # When plotting, keep only every 3rd trace


for FILTER_TYPE in Filter_Types:

  for PARAMETER_TO_SWEEP in Parameters_To_Sweep:

    output = ''
    b = []


    if PARAMETER_TO_SWEEP == 1:
      params = [-1] + list(range(0,23))
    elif PARAMETER_TO_SWEEP == 2:
      params = [-1] + list(range(0,25))
    elif PARAMETER_TO_SWEEP == 3:
      params = [-1] + list(range(0,16))
    else:
      raise Exception("Parameter to Sweep must be 1, 2 or 3")


    # Set the default parameter values (used for the non-swept parameters)
    DEFAULT_1 = 12
    DEFAULT_2 = 12
    DEFAULT_3 = 0

    if FILTER_TYPE==1:
      DEFAULT_3 = 8
    elif FILTER_TYPE==2:
      DEFAULT_3 = 8
    elif FILTER_TYPE==3:
      DEFAULT_3 = 6
    elif FILTER_TYPE==4:
      DEFAULT_2 = 24
      DEFAULT_3 = 12
    elif FILTER_TYPE==5:
      DEFAULT_2 = 24
      DEFAULT_3 = 12
    elif FILTER_TYPE==6:
      DEFAULT_2 = 24
      DEFAULT_3 = 6
    elif FILTER_TYPE==7:
      DEFAULT_3 = 0


    # An array to put results into -- only used if USE_SINE is true
    ar = numpy.zeros([len(params),len(notes)])


    for j in range(len(params)):
      
      pm = params[j]
      print('Doing parameter {0}'.format(pm))


      if PARAMETER_TO_SWEEP == 1:
        PARAM_1 = pm
        PARAM_2 = DEFAULT_2
        PARAM_3 = DEFAULT_3
      elif PARAMETER_TO_SWEEP == 2:
        PARAM_1 = DEFAULT_1
        PARAM_2 = pm
        PARAM_3 = DEFAULT_3
      elif PARAMETER_TO_SWEEP == 3:
        PARAM_1 = DEFAULT_1
        PARAM_2 = DEFAULT_2
        PARAM_3 = pm

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


      if METHOD=='Sine':
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
        
        nn = 60   # Minimum 60 for METHOD 'EDMWht' (EDM SW WHT doesn't play any lower than this!!)
        
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
    output_3 = ''
    if METHOD=='Sine':

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
        
        # Output 3 will hold the absolute magnitude of the comparison sample
        output_3 += '{0} '.format(true_freq)
        for j in range(len(params)):
          if j == idx_0:
            output_3 += '{0} '.format(10.*numpy.log10(b[j][k]))
            
        output_3 += '\n'
      for j in range(len(params)):
        if j != idx_0:
          if Plot_Divisor==0 or j%Plot_Divisor == 0:
            c = []
            for k in range(len(b[0])):
              c.append(10.*numpy.log10(b[j][k]/b[idx_0][k]))
            plt.plot(fr, c, label='{0}'.format(params[j]))
      plt.xlim(0,2500)  # Most interesting stuff happens under 2.5kHz
      plt.legend(loc='lower right')
            
        

    with open(os.path.join(dir_name, 'Out_FILTER_{0}_sweeping_{1}.txt'.format(FILTER_TYPE, PARAMETER_TO_SWEEP)), 'w') as f2:
      f2.write(output)
    with open(os.path.join(dir_name, 'Out_FILTER_{0}_sweeping_{1}_2.txt'.format(FILTER_TYPE, PARAMETER_TO_SWEEP)), 'w') as f3:
      f3.write(output_2)
    with open(os.path.join(dir_name, 'Out_FILTER_{0}_sweeping_{1}_3.txt'.format(FILTER_TYPE, PARAMETER_TO_SWEEP)), 'w') as f4:
      f4.write(output_3)

    # Show the plot -- will be empty if METHOD is 'Sine'. Just close it
    #plt.show()


    if METHOD!='Sine':
      plt.savefig(os.path.join(dir_name, "FILTER_{0}_sweeping_{1}.png".format(FILTER_TYPE, PARAMETER_TO_SWEEP)))



# Finished. Tidy everything up.
os.close(f)

x.close()

p.terminate()

