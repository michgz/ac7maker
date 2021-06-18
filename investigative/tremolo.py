'''
Test the tremolo feature of Tones
'''



import pyaudio
import os
import struct
import time

from scipy.signal import decimate, hilbert, stft, chirp, welch
import numpy
import matplotlib.pyplot as plt
import textwrap


import sys

# We're importing from a sibling directory.
sys.path.append('..')
sys.path.append('../internal')


from internal.sysex_comms_internal import get_single_parameter



# Set the raw MIDI device name to use.
DEVICE_NAME = '/dev/midi1'



# First, set capture volumes. This is highly dependent on audio setup. It works
# on my machine (Ubuntu 18.04)


# There is a choice to set in pulseaudio or ALSA. They seem to override each other, so only do one:
if False:
  os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(3830)) # Default = 3830, maximum=65536
else:
  os.system("amixer -c 0 cset iface=MIXER,name='Capture Volume',index=1 {0}".format(35)) # Default = 46, maximum=46
  #os.system("amixer -c 0 cset iface=MIXER,name='Line Boost Volume',index=1 {0}".format(0)) # Default = 0, maximum=3



# Exactly one of these should be selected. Chooses analysis of Tremolo, Vibrato, or Filter.
TREM = 0
VIB = 0
FILT = 1


TREM_MOD = 0

MOD_FORM = 0  # 0=CC 01, 1 = Polyphonic pressure, 2 = Channel pressure,3 = all


def do_mod(f, nn, v):
  if MOD_FORM == 1:
    os.write(f, b'\xA0' + struct.pack('BB', nn, v))
  elif MOD_FORM == 2:
    os.write(f, b'\xD0' + struct.pack('B', v))
  elif MOD_FORM == 3:
    os.write(f, b'\xA0' + struct.pack('BB', nn, v))
    os.write(f, b'\xD0' + struct.pack('B', v))
    os.write(f, b'\xB0\x01' + struct.pack('B', v))
  else:
    os.write(f, b'\xB0\x01' + struct.pack('B', v))




# Open MIDI

f = os.open(DEVICE_NAME, os.O_RDWR)

# Set volume and pan in the keyboard. Writing this combination overrides the
# physical volume control, meaning this test should be repeatable.
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 33) + b'\xf7')
time.sleep(0.2)
os.write(f, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
time.sleep(0.2)



# Set the tone. 83/63 = WHITE NOISE
BANK_MSB = 63
PATCH = 83

os.write(f, struct.pack('BBBBBBBB', 0xB0, 0, BANK_MSB, 0xB0, 0x20, 0, 0xC0, PATCH))
time.sleep(0.2)

if False:
  # - Now don't do this.
  #
  # Now overwrite parameter 228. This overwrites most aspects of the tone with another one.
  #  We are using "calibration" tones (numbers 800-810) which don't have a way of selecting
  #  with patch/bank. They need to be selected with parameter 228.
  #     800 = plain sine
  #     809 = silence
  PARAM_228 = 800
  BLOCK_0 = 32


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00' + struct.pack('BB', BLOCK_0%128, BLOCK_0//128) + b'\x64\x01\x00\x00\x00\x00' + struct.pack('BB', PARAM_228%128, PARAM_228//128) + b'\xf7'
  os.write(f, pkt)



if TREM:

  # Now write a couple of parameters to get tremolo working


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x42\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'
  os.write(f, pkt)


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x43\x00\x00\x00\x00\x00' + struct.pack('B', 8) + b'\xf7'  # Rate
  os.write(f, pkt)



  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x4b\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7'  # Peak-to-trough. <64 unused?? 64 = 0dB, 127=Inf dB.  100~=4:1 (12dB), 90~=2:1 (6dB)
  os.write(f, pkt)


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x49\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'   # Delay to start of swell (amount of time without trem)
  os.write(f, pkt)


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x4a\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'    # Time for swell. 0=immediate, 127 = slow
  os.write(f, pkt)


  #pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x48\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'    # Depth in response to channel pressure (after-touch -- D0).
  #os.write(f, pkt)


  #pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x47\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'    # Depth when modulated. 0=-ve .. 8=none .. 16=+ve.    32..96=none. 97=+ve .. 119=none .. 127=-ve.
  #os.write(f, pkt)

  #pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x46\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'    # Depth when **not** modulated???
  #os.write(f, pkt)

  #pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x45\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'    # ??
  #os.write(f, pkt)



  #pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x44\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'    # ??
  #os.write(f, pkt)




  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x4c\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.05)
  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x4d\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.05)
  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x4e\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.05)

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x4f\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.05)








if VIB:


  # Vibrato

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x3B\x00\x00\x00\x00\x00' + struct.pack('B', 5) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.1)

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x3C\x00\x00\x00\x00\x00' + struct.pack('B', 15) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.1)

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x3D\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.1)

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x3E\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.1)

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x3F\x00\x00\x00\x00\x00' + struct.pack('B', 100) + b'\xf7'
  os.write(f, pkt)
  time.sleep(0.1)


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x40\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7'  # Affects MODulation (CC 01)
  os.write(f, pkt)
  time.sleep(0.1)

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x41\x00\x00\x00\x00\x00' + struct.pack('B', 40) + b'\xf7'    # channel pressure (after-touch -- D0).
  os.write(f, pkt)
  time.sleep(0.1)
  



if FILT:
  

  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x42\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'
  os.write(f, pkt)


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x43\x00\x00\x00\x00\x00' + struct.pack('B', 8) + b'\xf7'  # Rate
  os.write(f, pkt)
  
  
  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x44\x00\x00\x00\x00\x00' + struct.pack('B', 5) + b'\xf7'
  os.write(f, pkt)
  
  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x45\x00\x00\x00\x00\x00' + struct.pack('B', 5) + b'\xf7' 
  os.write(f, pkt)
  
  
  
  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x46\x00\x00\x00\x00\x00' + struct.pack('B', 0) + b'\xf7'  # Depth
  os.write(f, pkt)
  


  pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x48\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7'
  os.write(f, pkt)


  

MOD = 127




time.sleep(0.2)


SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
RATE = 48000    # units of Hz. Probably only certain values are allowed, e.g.
                #  24000, 44100, 48000, 96000, ....


mm = 0
lx = []

def callback_audio(in_data,      # recorded data if input=True; else None
         frame_count,  # number of frames
         time_info,    # dictionary
         status_flags):
  global mm
  global lx
  
  w = 0
  while w+4 <= len(in_data):
    (l, r) = struct.unpack('<2h', in_data[w:w+4]) # left & right samples
    lx.append(l)
    w += 4
  
  
  
  mm += 1
  
  if mm >= 14*12:
    return (None, pyaudio.paComplete)
  
  return (None, pyaudio.paContinue)






p = pyaudio.PyAudio()

x = p.open(format=pyaudio.paInt16,
            channels=2,
            rate=RATE,
            input=True,
            input_device_index=2,
            start=False,
            stream_callback=callback_audio)



nn = 88



if TREM and TREM_MOD:
  it = range(0,128,5)
else:
  it = [0]
  
  
for ii in it:


  mm  = 0
  lx = []



  if TREM and TREM_MOD:
    pkt = b'\xf0\x44\x19\x01\x7F\x01\x03\x03\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00' + b'\x47\x00\x00\x00\x00\x00' + struct.pack('B', ii) + b'\xf7'
    os.write(f, pkt)




  x.start_stream()

  time.sleep(0.5)

  # MIDI note on
  os.write(f, b'\x90' + struct.pack('B', nn) + b'\x6e')


  if True:
    time.sleep(2.6)


    do_mod(f, nn, MOD)
    time.sleep(3.9)
    
    
  else:
    time.sleep(1.3)


    do_mod(f, nn, MOD//4)
    time.sleep(1.3)


    do_mod(f, nn, MOD//2)
    time.sleep(1.3)
    
    
    do_mod(f, nn, 3*MOD//4)
    time.sleep(1.3)


    do_mod(f, nn, MOD)
    time.sleep(1.3)


  # MIDI note off
  os.write(f, b'\x80' + struct.pack('B', nn) + b'\x7f')
  time.sleep(0.1)
  do_mod(f, nn, 0)
  time.sleep(1.5)


  time.sleep(2.5)


  x.stop_stream()


  if TREM:
    # Get the "amplitude" of the recorded signal
    dx = numpy.argmax(numpy.abs(stft(lx, nperseg=1024)[2]), axis=1)
    ex = decimate(numpy.abs(hilbert(lx)), 480, ftype='fir')
    gx = []

  if VIB:
    # Get the "pitch" of the recorded signal
    fx = stft(lx, nperseg=1024)
    #dx = numpy.argmax(numpy.abs(fx[2]), axis=1)
    
    
    dx = numpy.argmax(numpy.abs(fx[2]), axis=0)
    
    ex = decimate(numpy.abs(hilbert(lx)), 480, ftype='fir')
    
    gx = numpy.abs(fx[2][:][256])



    # Re-calculate the pitch. The one above is probably okay, but this is a bit
    # more explicit
    dx = []


    for j in range(0, numpy.abs(fx[2]).shape[1]):
    #  
      hx = numpy.abs(fx[2])[:,j]
      dx.append(numpy.argmax(hx))
      #print(hx)
    #  plt.plot(hx)
    #  plt.show()



  if FILT:
    
    i = 0
    bx = []
    while i+2048 <= len(lx):
    
      mx = lx[i:i+2048]
    
      fr, pw = welch(mx, RATE, nperseg=32)
      
      if max(pw) < 20.:
        # Not enough signal to find the cutoff frequency
        bx.append(0)
      
      else:
        # Crude approximation of the 3dB bandwidth
        
        j = numpy.argmax(pw)
        targ = max(pw) * 0.6  # 3dB is .707. Make it a bit lower to account for spikiness
        
        while (pw[j] > targ):
          j += 1
          
        if j < len(fr):
          bx.append(fr[j])
        else:
          bx.append(20000)
      
      i += 2048




  if TREM and TREM_MOD:
    with open("7.csv", "a") as f1:
      f1.write("{0},".format(ii))
      for llx in dx:
        f1.write("{0:f},".format(llx))
      f1.write("\n")

# Finished. Tidy everything up.
os.close(f)

x.close()

p.terminate()

if VIB:
  plt.plot(dx)
  plt.show()


if TREM:
  plt.plot(ex)
  plt.show()

if FILT:
  plt.plot(bx)
  plt.show()

# plt.plot(gx)
# plt.show()


