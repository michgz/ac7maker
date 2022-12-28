'''
Check effect of System EQ parameters
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


from internal.sysex_comms_internal import get_single_parameter, set_single_parameter


if False:
    for P in [160,161,162,163,164,165,166,167,168,169,192,193,194,195,196,197,198,199,200]:
        X = get_single_parameter(P, category=2, memory=3)
        print(f"Param {P}: {X}")


p = pyaudio.PyAudio()

SOURCE_IDX = None

N = p.get_device_count()
print(f"{N} devices")
for NN in range(N):
    DEV = p.get_device_info_by_index(NN)
    print(DEV)
    if DEV['name'] == 'pulse' and DEV['maxInputChannels'] >= 2:
        SOURCE_IDX = DEV['index']




'''
Param 160: 0         # freq of low bass Values 0-2?
Param 161: 12         # Low Bass. Takes values 0-~25?
Param 162: 16
Param 163: 12         # Bass. Takes values 0-~25?
Param 164: 5
Param 165: 12         # Mid (3kHz). Takes values 0-~25?
Param 166: 0
Param 167: 12         # Treble. Takes values 0-~25?
Param 168: 74         # -6 to +6dB wideband boost/cut
Param 169: 127        # 0 to -Inf dB wideband cut. 75 ~= -6dB
Param 192: 4
Param 193: 0
Param 194: 53         # +12 to -Inf wideband boost/cut
Param 195: 0
Param 196: 127
Param 197: 0
Param 198: 15
Param 199: 15
Param 200: 0



Param 164: frequency of Mid.
 0  1.0
 1  1.0
 2  1.6
 3  2.0 
 4   2.7
 5    3khz
 6   3.8



Param 166: frequency of Treble
  
  See plots




'''



# Set the raw MIDI device name to use.
DEVICE_NAME = '/dev/midi1'



# First, set capture volumes. This is highly dependent on audio setup. It works
# on my machine (Ubuntu 22.04)


# There is a choice to set in pulseaudio or ALSA. They seem to override each other, so only do one:
#if False:
#  os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(3830)) # Default = 3830, maximum=65536
#else:
#  os.system("amixer -c 0 cset iface=MIXER,name='Capture Volume',index=1 {0}".format(35)) # Default = 46, maximum=46
#  #os.system("amixer -c 0 cset iface=MIXER,name='Line Boost Volume',index=1 {0}".format(0)) # Default = 0, maximum=3


os.system("pactl set-source-volume @DEFAULT_SOURCE@ {0}%".format(25))




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


os.write(f, struct.pack('BBB', 0xB0, 10, 64))  # Pan centre. 0 = louder, 127=none
time.sleep(0.2)

nn = 60

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



PARAM = 200
VALS = [0, 1,3,12,15,0]


LX_ALL = []



if SOURCE_IDX is not None:




    #p = pyaudio.PyAudio()

    x = p.open(format=pyaudio.paInt16,
                channels=2,
                rate=RATE,
                input=True,
                input_device_index=SOURCE_IDX,
                start=False,
                stream_callback=callback_audio)






    for NV, VV in enumerate(VALS):


        if NV == 0:
            set_single_parameter(165, 22, category=2, memory=3,  fs=f)
        elif NV  == len(VALS)-1:
            set_single_parameter(165, 12, category=2, memory=3,  fs=f)



        set_single_parameter(PARAM, VV, category=2, memory=3,  fs=f)
        time.sleep(0.5)



        lx = []
        mm = 0
        

        # MIDI note on
        os.write(f, b'\x90' + struct.pack('B', nn) + b'\x6e')


        time.sleep(0.1)
        x.start_stream()

        time.sleep(1.0)

        x.stop_stream()

        # MIDI note off
        os.write(f, b'\x80' + struct.pack('B', nn) + b'\x7f')
        time.sleep(0.1)
        #do_mod(f, nn, 0)
        time.sleep(1.5)

        LX_ALL.append(lx)


    os.close(f)

    x.close()

p.terminate()

if len(LX_ALL) >= 2:
  
  
    f_def, P_def = welch(LX_ALL[-1], fs=RATE)
    
    plt.clf()
    
    LEG = []
    
    for N in range(len(LX_ALL)-1):
      
        _, P = welch(LX_ALL[N], fs=RATE)
        
        plt.plot(f_def, 10.*numpy.log10(P/P_def))
        LEG.append(str(VALS[N]))
        
    plt.xlim([0, 16000])
    plt.legend(LEG)
    plt.show()
    
    
    

