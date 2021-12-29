"""
Class for performing generic automated experiments on CT-X synthesis parameters.
"""

# Standard library imports
import os
import os.path
import sys
import struct
import random
import datetime
import time
import itertools


# Import from this project
sys.path.append('..')
sys.path.append('../internal')

import internal.sysex_comms_internal

# Installed library imports
import pyaudio
import numpy
import scipy
import scipy.signal
from matplotlib import pyplot as plt



"""
A basic template for Category 5 parameter sets. All Split pointers here are set
as zero; at least 1 needs to be set to something else for this to be useable.
"""
CAT5_BASIC = b'\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f' \
             b'\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00' \
             b'\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f' \
             b'\x40\x40\x40\x80\x4a\x40\x40\x40\x40\x80\x40\x40\x40\x40\x80\x40' \
             b'\x40\x00\x80\x02\x00\x00'



CAT12_BASIC = b'\x00\x00\x40\x00\x00\x20\x00\x02\x00\x20\x00\x02\x00\x20\x00\x02' \
              b'\x00\x00\x00\x00\x00\x7f\x80\x80\x40\x80\x00\x00\x00\x00\x80\x7f' \
              b'\x80\x80\x40\x80\x00\x00\x00\x00\x80\x7f\x80\x80\x40\x80\x00\x00' \
              b'\x00\x00\x80\x7f\x80\x80\x40\x80\x00\x00\x00\x00\x80\x7f\x80\x80' \
              b'\x40\x80\x00\x00\x00\x00\x80\x7f\x80\x80\x40\x80\x00\x00\x00\x00' \
              b'\x80\x7f\x80\x80\x40\x80\x00\x00\x00\x00\x80\x7f\x80\x80\x40\x80' \
              b'\x00\x00\x00\x00\x80\x7f\x80\x80\x40\x80\x00\x00\x00\x00\x00\x7f' \
              b'\x80\x80\x40\x80\x00\x00\x00\x00\x00\x7f\x80\x80\x40\x80\x00\x00' \
              b'\x00\x00\x00\x7f\x80\x80\x40\x80\x00\x00\x00\x00\x00\x7f\x80\x80' \
              b'\x40\x80\x00\x00\x00\x00\x00\x7f\x80\x80\x40\x80\x00\x00\x00\x00' \
              b'\x00\x7f\x80\x80\x40\x80\x00\x00\x00\x00\x00\x7f\x80\x80\x40\x80' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00' \
              b'\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00' \
              b'\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00' \
              b'\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00' \
              b'\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00\x00\x20\x00\x00' \
              b'\x00\x20\x00\x00\x00\x20\x00\x00\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x02' \
              b'\x00\x00\x00\x02\x00\x00\x00\x02\x80\x3f\x00\x00\x80\x3f\x90\x01' \
              b'\x80\x3f\x90\x01\x80\x3f\x90\x01\x80\x3f\x90\x01\x00\x00\xbc\x02' \
              b'\x00\x00\xf4\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
              b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7f\x02\x80\x02' \
              b'\x02\x7f\x02\x02\x7f\x02\x7f\x02\x7f\x02\x02\x02\x7f\x02\x02\x7f' \
              b'\x40\x00\x7f\x02'



CAT10_BASIC = b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x00\x00\x00\x7f\x00\x7f\x02\x1f\x00\x00\x00\x7f\x00\x7f\x02\x1f' \
              b'\x40\x00\x00\x80\x48\x48\x40\x00\x00\x80\x40\x40\x00\x00\x80\x40' \
              b'\x40\x00\x52\x00\x7f\x00'





from experiment_internal import ParameterSequence, ParametersSequence, ResultMeasurement, ResultWaveform, ResultPoint



class Experiment:
  
  def __init__(self):
    
    
    """
    end_category:  the last category in the experimental "chain". Parameters can
                   only be changed in this category and earlier categories. There
                   are 4 possible values for this parameter:
                   
                   3 (Tone):    only parameters in category 3 can be changed.
                   5 (Melody):  only parameters in categories 5 & 3 can be changed.
                   12 (Split):  only parameters in categories 12, 5 & 3 can be changed.
                   15 (Waveform):only parameters in categories 15, 12, 5 & 3 can be changed.
    """
    self.end_category = 3


    """
    waveform:    either 'white' or 'sine'. 'white' (white noise) is suitable for
                 measuring frequency response/filter response. 'sine' is better
                 for measuring frequency and amplitude.
    """
    self.waveform = 'sine'
    
    
    
    
    """
    notes:       MIDI note numbers to use. Can be a range, e.g. range(0,128).
    """
    self.notes = [60]
    
    
    
    """
    input:       the value to vary. Can be 'velocity' or 'note'.
    """
    self.input = 'note'
    
    
    
    """
    output:      the output value to measure. Can be 'freq' (frequency) or 'ampl'
                 (amplitude).
                 'ampl_env': amplitude envelope (measuring slopes and rise/fall times)
                 'ampl_ampl_env': amplitude envelope (measuring amplitudes)
                 'pitch_env': pitch envelope
                 'spectrum':   frequency spectrum (only with 'white' input waveform).
    """
    self.output = 'ampl_env'
    
    
    
    """
    stage:       only for use with envelope outputs. Determines the stage of the
                 envelope to experiment on, starting at 1. For amplitude envelope
                 takes values 1..6, for pitch takes values 1..2.
    """
    self.stage = 2
    
    
    
    """
    compare:     a boolean, indicating if readings need to be compared against
                 subsequent readings. Useful for example with spectrum readings.    
    """
    self.compare = False
    
        
    
    """
    parameter_sequence:   The sequence used for the second sweep type. None means
                          use a default
    """
    self.parameter_sequence = None


    
    # Now some internal variables
    self._datetime = None
    self._is_complete = False
    self._info = ""
    self._results = None
    self._fit_results = None
    self._waveforms_out = None





  # Some pre-set split/waveform values
  SPLIT_SINE = 1
  WAVEFORM_SINE = 1
  SPLIT_WHITE = 7
  WAVEFORM_WHITE = 3
  
  

  """
  measure_frequency()
  
  inputs:   data -- audio data
            rate -- sample rate in Hz
            
            
  outputs:  frequency in semitones (middle C = 60)
  """
  @staticmethod
  def measure_frequency(data, rate=1.):


    Px = numpy.abs(scipy.fft.rfft(data))
    f = scipy.fft.rfftfreq(data.shape[0], 1./rate)
    
    # Some people say the best way to estimate frequency is using a quadratic fit to 
    # FFT result values in dB. Try that here.
    
    
    n = numpy.argmax(Px)
    
    if n < 1:
      peak_hz = 0.
    elif (n+2) > len(Px):
      peak_hz = rate/2.   # Nyquist
    else:
      pp = numpy.polyfit(  f[n-1:n+2],   numpy.log10(Px[n-1:n+2]), 2)
      #print(pp)
        
      peak_hz = - pp[1] / (2. * pp[0])

    return peak_hz


  @staticmethod
  def measure_amplitude(data, rate=1.):
    #dx = numpy.argmax(numpy.abs(stft(data, nperseg=1024)[2]), axis=1)
    ex = scipy.signal.decimate(numpy.abs(scipy.signal.hilbert(data)), 480, ftype='fir')
    
    # We now have a time-varying amplitude. For now, just average to get a single
    # number
    return numpy.average(ex) 
    

  @staticmethod
  def measure_lowpass_6db(freq, rel_ampl):
    
    for i, x in enumerate(rel_ampl):
      if x < 0.1:   # Doesn't this make it -20dB?? 
        return freq[i]
    # If we get here we haven't found any result
    return freq[-1]



  @staticmethod
  def measure_lowpass_cutoff(data, rate=1.):
    i = 0
    bx = []
    while i+2048 <= len(data):
    
      mx = data[i:i+2048]
    
      fr, pw = scipy.signal.welch(mx, RATE, nperseg=32)
      
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

    return numpy.average(bx)

  @staticmethod
  def measure_attack_time(t, data, stage=2):
    
    if stage == 2:  # exponential decay after initial attack
    
      max_i = numpy.argmax(data)
      min_i = numpy.argmin(data[max_i:]) + max_i
      
      if (min_i - max_i) < 4:
        # Not enough data
        return None

      #print(t)
      #print(data)
      #print(numpy.log(data))

      pp = numpy.polyfit(t[max_i+2:min_i-1], numpy.log(data[max_i+2:min_i-1]), 1)
      pp[0] = -pp[0]
      
      #print(pp)
    
    elif stage == 1:
      # Linear attack
      
      max_i = numpy.argmax(data)
      min_i = max_i
      while min_i > 0:  # Find -10dB point
        min_i -= 1
        if data[min_i] < 0.1*data[max_i]:
          min_i += 1
          break
        else:
          pass
      if (max_i - min_i) < 5:
        # Not enough data
        return None
        
      pp = numpy.polyfit(t[min_i+1:max_i-2], data[min_i+1:max_i-2], 1)
      #print(pp)

    elif stage >= 5:

      max_d = numpy.max(data)
      
      i_4 = max([x for x in range(len(data)) if data[x] > max_d*0.8])+1
      try:
        i_5 = min([x for x in range(len(data)) if x > i_4 and data[x] < max_d*0.05])
      except ValueError:
        # Probably just never gets to the noise floor (max_d*0.05). Use the end, ignoring the
        # last few values.
        i_5 = len(data) - 4

      if i_5 - i_4 < 3:
        raise Exception("Not enough points")

      pp = numpy.polyfit(t[i_4:i_5], numpy.log(data[i_4:i_5]), 1)
      pp[0] = -pp[0]

      return pp
    else:
      raise Exception ("Only stages 1 & 2 supported at this time")
    
    return pp


  def suggest_frame_count(self):
    if self.output == 'ampl':
      return 8*1024
    else:
      return 64*1024


  def run(self):
    self._datetime = datetime.datetime.now()
    self._is_complete = True
    self._info += "Test run at: {0}\n\n".format(self._datetime.isoformat())
    self._waveforms_out = None
    
    DEST = 801




    if not sys.platform.startswith('linux'):
      raise Exception("Terminating. This is an investigative script that probably needs Linux in order to work correctly.")


    pulse_device_index = None

    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
      d = p.get_device_info_by_index(i)
      if d['name'] == 'pulse' and d['maxInputChannels'] >= 1:
        pulse_device_index = i
        break

    p.terminate()

    if pulse_device_index is None:
      raise Exception("Terminating. Could not find pulseAudio as an input device")

    
    f_midi = os.open('/dev/midi1', os.O_RDWR)
    os.write(f_midi, struct.pack("BBB", 0xB0, 123, 0))   # All Notes Off


    # Set capture volumes. This is highly dependent on audio setup.

    os.system("amixer -D pulse cset iface=MIXER,name='Capture Volume' {0}".format(10000)) # Default = 3830, maximum=65536



    # Set volume and pan in the keyboard. Writing this combination overrides the
    # physical volume control, meaning this test should be repeatable.
    os.write(f_midi, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00' + struct.pack('B', 33) + b'\xf7')
    time.sleep(0.2)
    os.write(f_midi, b'\xf0\x44\x19\x01\x7F\x01\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00' + struct.pack('B', 64) + b'\xf7')
    time.sleep(0.2)


    
    if self.waveform == 'sine':
      with open(os.path.join(os.path.dirname(__file__), "..", "calibration tones", "CALSINE.TON"), "rb") as f2:
        cat3 = bytearray(f2.read()[0x20:-4])
    elif self.waveform == 'white':
      with open(os.path.join(os.path.dirname(__file__), "..", "calibration tones", "CALWHITE.TON"), "rb") as f2:
        cat3 = bytearray(f2.read()[0x20:-4])
    else:
      raise Exception("Invalid waveform")
    
    
    if self.end_category >=5:
      # We're pointing to a next category. Set the "melody" pointer to the user memory value (900)
      cat3[0x87] = 0
      cat3[0x82:0x84] = struct.pack("<H", 900)
      cat3[0x10F] = 0
      cat3[0x10A:0x10C] = struct.pack("<H", 900)
    
    
    if self.output.endswith("_env"):
      
      
      if self.output == "pitch_env":
        # Normal amplitude envelope with extended release
        cat3[0x60:0x7C] = b'\x00\x02\x80\x00' \
                          b'\x00\x02\x80\x00' \
                          b'\x00\x02\x80\x00' \
                          b'\x00\x02\x80\x00' \
                          b'\x00\x02\x80\x00' \
                          b'\xA0\x02\x80\x00' \
                          b'\x00\x02\x80\x00'
      
        cat3[0x00:0x0C] = b'\x00\x02\x60\x00' \
                          b'\x80\x02\xA0\x00' \
                          b'\x80\x02\x60\x00'
      elif self.output == "ampl_ampl_env":

        cat3[0x60:0x7C] = b'\x00\x02\x00\x00' \
                          b'\x00\x02\x00\x00' \
                          b'\x00\x02\x00\x00' \
                          b'\x00\x02\x00\x00' \
                          b'\x00\x02\x00\x00' \
                          b'\x00\x02\x00\x00' \
                          b'\x00\x02\x00\x00'
      
      else:
        # Amplitude envelope with an obvious shape.
        cat3[0x60:0x7C] = b'\x80\x02\x00\x00' \
                          b'\x00\x02\xFF\x00' \
                          b'\x80\x01\x20\x00' \
                          b'\xFF\x03\x80\x00' \
                          b'\x00\x02\x60\x00' \
                          b'\x00\x02\x80\x00' \
                          b'\x00\x02\x80\x00'
        if self.stage != 1:
          # Not testing the first stage, so just make it as quick as possible
          cat3[0x62] = 0x80
          
        if self.stage >= 5:
          # Not testing anything until the release, so just make it default
          cat3[0x60:0x7C] = b'\x00\x02\x80\x00' \
                            b'\x00\x02\x80\x00' \
                            b'\x00\x02\x80\x00' \
                            b'\x00\x02\x80\x00' \
                            b'\x00\x02\x80\x00' \
                            b'\x00\x02\x80\x00' \
                            b'\x00\x02\x80\x00'
                          
                          
    internal.sysex_comms_internal.upload_ac7_internal(DEST-801, cat3, category=3, memory=1, fs=f_midi)

    
    if self.end_category >= 5:
      
      cat5 = bytearray(CAT5_BASIC)
      if self.end_category >= 12:
        cat5[0x00:0x02] = struct.pack("<H", 1500)
      else:
        if self.waveform == 'sine':
          cat5[0x00:0x02] = struct.pack("<H", self.SPLIT_SINE)
        elif self.waveform == 'white':
          cat5[0x00:0x02] = struct.pack("<H", self.SPLIT_WHITE)
        else:
          raise Exception

      internal.sysex_comms_internal.upload_ac7_internal(0, cat5, category=5, memory=1, fs=f_midi)


    if self.end_category >= 12:
      
      cat12 = bytearray(CAT12_BASIC)
      if self.waveform == 'sine':
        cat12[0x10:0x12] = struct.pack("<H", self.WAVEFORM_SINE)
      elif self.waveform == 'white':
        cat12[0x10:0x12] = struct.pack("<H", self.WAVEFORM_WHITE)
      else:
        raise Exception
      internal.sysex_comms_internal.upload_ac7_internal(0, cat12, category=12, memory=1, fs=f_midi)




    # Open PyAudio for doing the recording

    SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
    RATE = 48000    # units of Hz. Probably only certain values are allowed, e.g.
                    #  24000, 44100, 48000, 96000, ....
    FRAMES = 1024

    p = pyaudio.PyAudio()

    NOTES = self.notes
    VARS = None
    if self.input == 'velocity':
      VARS = ParameterSequence.Velocities(range(5, 128, 10))
      #VARS = ParameterSequence.Velocities([127])
    else:
      #VARS = ParameterSequence.Velocities([127])
      VARS = None   # "Empty" parameter sweep
      
      
    PARAMS = None
    #PARAMS = [44,64,84]
    
    
    #PARAMS = [0,1,2]
    
    
    Param_Is_List = False
    
    if self.parameter_sequence is None:
      PARAMS = ParameterSequence.SingleParameter(29, 12, [1], compare = True)
    elif isinstance(self.parameter_sequence, list):
      Param_Is_List = True
      if len(NOTES) != len(self.parameter_sequence):
        raise Exception("A list-type parameter must be same length as the notes list")
      PARAMS = self.parameter_sequence[0]
    else:
      PARAMS = self.parameter_sequence
    
    
    os.write(f_midi, struct.pack("8B", 0xB0, 0x00, 65, 0xB0, 0x20, 0, 0xC0, DEST-801))


    v = bytes()
    tot_frames = 0

    def audio_callback(in_data, frame_count, time_info, status):
        nonlocal tot_frames
        nonlocal v
        v +=(in_data)
        tot_frames += frame_count
        return (None, pyaudio.paContinue)


    
    x = p.open(format=pyaudio.paFloat32,
                channels=2,
                rate=RATE,
                input=True,
                input_device_index=pulse_device_index,
                start=True,
                frames_per_buffer=FRAMES,
                stream_callback=audio_callback)




    if VARS is None:
      RESULTS = numpy.zeros((len(NOTES), len(PARAMS), 1))
    else:
      RESULTS = numpy.zeros((len(NOTES), len(PARAMS), len(VARS)))
    WAVEFORMS = []
    FRAME_COUNTS = []
    
   




    POINTS = []
    
    COMPARE_WAVEFORM = None



    SEQS = ParametersSequence(NOTES, self.parameter_sequence, VARS)
    
    #for (a, b, c) in SEQS:
    #  print(a)
    # # if b is not None:
    #    print(b.set_write)
    #  print(c)
    
    



    #internal.sysex_comms_internal.set_single_parameter(42, 0, category=12, memory=1, parameter_set=0, block0=0, fs=f_midi)

    #for i, NOTE in enumerate(NOTES):   # Try at various different pitches
    #  if Param_Is_List:
    #    PARAMS = self.parameter_sequence[i]
    #  for j, PARAM in enumerate(PARAMS.Writes):
    #    
    #    vx = []
    #    vy = []
        
        
    #    for k, VAR in enumerate(VARS.Writes):


    for SEQ_POINT in SEQS:


      VEL = 0x7F
      for XX in SEQ_POINT:
        if XX is not None:
          if XX.is_velocity:
            VEL = XX.velocity
          
          
      NOTE = None
      for XX in SEQ_POINT:
        if XX is not None:
          if XX.is_note:
            NOTE = XX.note
      
      if NOTE is None:
        raise Exception("No note specified within the sequence")
      
      

      
      for XX in SEQ_POINT:
        if XX is not None and not XX.is_velocity and not XX.is_note:
          try:
            internal.sysex_comms_internal.set_single_parameter(**XX.set_write, fs=f_midi)
            pass
          except internal.sysex_comms_internal.SysexTimeoutError:
            print("Problem writing parameter {0}".format(XX))
            continue
          

      
      is_env = self.output.endswith("_env")
      is_env_release = is_env and self.stage >= 5
      

        
        
      frame_count = self.suggest_frame_count()


      v = bytes()
      tot_frames = 0


      time.sleep(0.2)
      os.write(f_midi, struct.pack("3B", 0x90, NOTE, VEL))
      
      if self.output == 'ampl':
        time.sleep(0.1)
        v = bytes()
        tot_frames = 0
      
      if is_env_release:
        time.sleep(0.2)
      else:
        while tot_frames < frame_count:
          time.sleep(0.1)

      os.write(f_midi, struct.pack("3B", 0x80, NOTE, 0x7F))
      
      if is_env_release:
        while tot_frames < frame_count:
          time.sleep(0.1)
      else:
        time.sleep(0.2)


      result = numpy.frombuffer(v, dtype=numpy.float32)
      result = numpy.reshape(result[:frame_count], (frame_count//2, 2))
      result = result[:, 0]




      TheMeasurement = None
      
      if self.waveform == 'sine':
        if self.output == 'ampl':
          TheMeasurement = ResultMeasurement.AmplitudeMeasurement(self.measure_amplitude(result, RATE), rate=RATE)
          TheMeasurement._frame_count = frame_count
        elif self.output == 'pitch':
          TheMeasurement = ResultMeasurement.PitchMeasurement(self.measure_frequency(result, RATE), rate=RATE)
          TheMeasurement._frame_count = frame_count
        #RESULTS[i][j][k] = TheMeasurement.value
      else:
        #RESULTS[i][j][k] = 0.
        pass



      TheWaveform = None

      
      FRAME_COUNTS.append(frame_count)
      
      if self.output.endswith("_env"):
            
            
        
        
        if self.output == "pitch_env":
          fs = float(RATE)

        else:
          pass
        
        fs = float(RATE)
        
        # Calculate the hilbert signal, with a bit of high-pass filtering. The filtering
        # requires a pitch of at least about C-2 (100Hz)
        bb = scipy.signal.butter(100., 4, btype='high', output='sos', fs=fs)
        hx = scipy.signal.hilbert(scipy.signal.sosfilt(bb, result))
        
        # Get the amplitude.
        # First we down-sample the hilbert signal. For high-frequency inputs 
        #  (>>1kHz) we down-sample to 1kHz, otherwise to 100Hz.
        if NOTE >= 95:
          WAVE_RATE = 1000.  # samples per second
        else:
          WAVE_RATE = 100.   # samples per second
        dx = scipy.signal.decimate(numpy.abs(hx), int(numpy.round(fs/WAVE_RATE)), ftype='fir')
        
        # Align zero in time to the start of the initial slope.
        max_d = numpy.max(dx)
        i_7 = min([x for x in range(0, len(dx)) if dx[x] > (max_d*0.80)])
        try:
          i_8 = max([x for x in range(0, i_7) if dx[x] < (max_d*0.20)])+1
        except ValueError:
          # Probably a constant signal.
          i_8 = i_7
        if len(range(i_8, i_7)) <= 2:
          # Slope is too steep. Just count it as immediate.
          i_2 = i_8
          t_zero = i_2
        else:
          # Fit a linear regression and find the zero crossing.
          pp = numpy.polyfit( range(i_8, i_7),   dx[i_8:i_7],  1)
          t_zero = -pp[1] / pp[0]
          i_2 = int(numpy.floor(t_zero))

        i_4 = len(dx)
        
        # Get the pitch
        fx = numpy.diff(numpy.unwrap(numpy.angle(hx))) / (2.0*numpy.pi) * fs
        gx = scipy.signal.savgol_filter(fx, 481, 1)  # Smooth the signal. Is this needed?
        ix = scipy.signal.decimate(gx, int(numpy.round(fs/WAVE_RATE)), ftype='fir')
        
        
        # Amplitude aligned with the start point
        i_3 = max(0, i_2-12)
        jx = dx[i_3:i_4]
        tx = (numpy.array(range(len(jx)))   -   (t_zero-i_3) )/WAVE_RATE
        
        if len(ix) != len(dx):
          raise Exception
        
        
        for ii in range(len(ix)):
          # Clear values that are too quiet to be sure
          if dx[ii] < 0.02:
            ix[ii] = numpy.nan
        kx = ix[i_3:i_4]
        
       
        #print(kx)
        #print(f"Start point = {i_3}")
        #print(f"Max val = {max_d}")
        
        WAVEFORMS.append({'ampl_t': tx, 'ampl_x': jx, 'freq_t': tx, 'freq_x': kx})
        if self.output == 'pitch_env':
          TheWaveform = ResultWaveform.PitchWaveform(tx, kx)
        else:
          TheWaveform = ResultWaveform.AmplitudeWaveform(tx, jx)

      elif self.output == 'spectrum':
        
        fs = 48000.
        
        
        f, Px = scipy.signal.welch(result, fs=fs, nperseg = 2*1024)
        #WAVEFORMS.append({'spectrum_f': f, 'spectrum_x': Px})
        TheWaveform = ResultWaveform.SpectrumWaveform(f, Px)
        
        
      #internal.sysex_comms_internal.set_single_parameter(PARAM, 0, category=12, memory=3, parameter_set=0, fs=f_midi)

      result = ResultPoint()
      result._note = NOTE
      result._params = SEQ_POINT
      result._output_waveform = TheWaveform
      result._output = self.output
      result._input = self.input
      result._frame_count = frame_count
      result._velocity = VEL
      result._measurement = TheMeasurement
      POINTS.append(result)
      
      # if self.input == 'velocity' and self.output == 'ampl':
        # vx.append(VEL)
        # vy.append(TheMeasurement.value)
        
        
          
            
            
    j = 0  # This stuff needs to be sorted out......
    #if self.input == 'velocity' and self.output == 'ampl':
    #  if TheWaveform is not None:
    #    raise Exception("ERROR. Have a waveform from somewhere else")
    #  TheWaveform = ResultWaveform.VelocityWaveform(vx, vy)
      
    #if j == 0 and self.compare:
    #  if TheWaveform is not None:
    #    TheWaveform.FitShape()
    #  COMPARE_WAVEFORM = TheWaveform
    #else:
    #  if TheWaveform is not None and self.compare:
    #    TheWaveform.Compare(COMPARE_WAVEFORM)




    x.stop_stream()
    x.close()
    
    os.close(f_midi)
    p.terminate()
    
    

    
    
    #self._results = {'inputs': [{'name': 'notes', 'parameter': None, 'values': NOTES},
    #                            {'name': 'velocity_sense', 'parameter': {'parameter': 5, 'category': 3, 'min':0, 'max': 127}, 'values': PARAMS.Values},
    #                            {'name': 'velocity', 'parameter': None, 'values': VARS}],
    #                 'output': {'name': 'amplitude', 'values': RESULTS} }
    
    if self.output == 'spectrum' and self.compare:
      # Fill in the Results matrix with compared values
      
      for j, w in enumerate(WAVEFORMS):
        
        if j >= 1:
          RESULTS[0][j][0] = self.measure_lowpass_6db(w['spectrum_f'], w['spectrum_x']/WAVEFORMS[0]['spectrum_x'])
      
    
    FIT_RESULTS = None
    


    if self.output == 'ampl_env' and len(WAVEFORMS) > 0:
      # Fit the second stage in the attack. With the settings above, it should be
      # a falling exponential
      
      
      AXIS_1_LEN = len(WAVEFORMS)//len(NOTES)
      FIT_RESULTS = numpy.zeros((len(NOTES), AXIS_1_LEN, 2))
      
      #for i,w in enumerate(WAVEFORMS):
      
      #  p = self.measure_attack_time(w['ampl_t'], w['ampl_x'], self.stage)
      #  FIT_RESULTS[i//AXIS_1_LEN][i%AXIS_1_LEN] = p

    elif self.output == 'ampl_ampl_env' and len(WAVEFORMS) > 0:
      # Fit the maximum amplitude
      
      
      AXIS_1_LEN = len(WAVEFORMS)//len(NOTES)
      FIT_RESULTS = numpy.zeros((len(NOTES), AXIS_1_LEN, 1))
      
      for i,w in enumerate(WAVEFORMS):
      
      
        if self.stage == 4:
          p = numpy.median(w['ampl_x'])  # Median removes extraneous peaks
        else:
          p = numpy.max(w['ampl_x'])
        FIT_RESULTS[i//AXIS_1_LEN][i%AXIS_1_LEN][0] = p




    self._fit_results = FIT_RESULTS
    self._results = RESULTS
    self._var1 = self.parameter_sequence
    self._var2 = VARS
    #if len(WAVEFORMS) > 0:
    #  self._waveforms_out = WAVEFORMS
    dt_finished = datetime.datetime.now()
    self._info += "Finished: " + dt_finished.isoformat() + "   (total {0:0.2f} seconds)\n\n".format((dt_finished - self._datetime).total_seconds())
    self._info += "Frame counts:  "
    for ff in FRAME_COUNTS:
      self._info += "{0}  ".format(ff)
    self._info += "\n\n"
    self._points = POINTS




  def analyse(self):
    
    
    S = set()
    for P in self._points:
      
      
      print(P._params)
      
      S.add(    tuple([(None if x is None else int(x)) for x in P._params])   )
    
    
    if len(set([len(x) for x in S])) != 1:
      raise Exception("Results don't all have the same number of parameters")
    
    
    LEN_PARAMS = len(S.pop())
    
    PARAM_DETAILS = []
    
    for i in range(LEN_PARAMS):
      
      T = set()
      for SS in S:
        T.add(SS[i])
      
      if len(T) == 0:
        raise Exception("Something went wrong")
      
      is_simple = False
      is_compared = False
      if len(T) == 1:
        is_simple = True
      else:
        
        if self.compare and None in T:
          is_compared = True
        
        
      
      
      PARAM_DETAILS.append({'simple': is_simple, 'compared': is_compared})
      
    
    
    if self.output == 'ampl' and self.input == 'velocity' and self.compare:
      
      
      # Find the primary parameter. It is not simple, not compared and velocity.
      
      
      primary_param = -1
      
      for i in range(LEN_PARAMS):
      
        if self._points[0]._params[i] is not None:
          if self._points[0]._params[i].is_velocity:
            if not PARAM_DETAILS[i]['simple'] and not PARAM_DETAILS[i]['compared']:
              primary_param = i
      
      
      if primary_param < 0:
        raise Exception("Didn't find primary parameter")
        
      # Every non-primary parameter should be either compared or simple
      for i in range(LEN_PARAMS):
        if i != primary_param:
          if not PARAM_DETAILS[i]['simple'] and not PARAM_DETAILS[i]['compared']:
            raise Exception("Whoops! A non-primary parameter is not simple and not compared!")
            
      
      U = set()
      
      for SS in S:
        
        
        U.add (    SS[0:primary_param]   + (-1,)  + SS[primary_param+1:]   )
        
        
      # U is now S with the primary parameter removed.
      
      
      
      FIT_RESULTS = []
      
      
      for UU in U:
        
        if not None in UU:
          
          
          VV = ()
          for i in range(LEN_PARAMS):
            
            if i == primary_param:
              VV += (-1, )
            elif PARAM_DETAILS[i]['compared']:
              VV += (None, )
            elif PARAM_DETAILS[i]['simple']:
              VV += (UU[i], )
            else:
              raise Exception("Fallen through the cracks")
          
          # VV is the comparison.
          
          X1 = []
          Y1 = []
          X2 = []
          Y2 = []
          
          for FF in self._points:
            
            add_U = True
            add_V = True
            
            for j in range(LEN_PARAMS):
              if UU[j] != -1 and (FF._params[j] is None or UU[j] != int(FF._params[j])):
                add_U = False
              if VV[j] != -1 and (FF._params[j] is not None and VV[j] != int(FF._params[j])):
                add_V = False
            
            print(list(map(lambda x: None if x is None else int(x), FF._params)))
            print(f"add_U: {add_U}")
            print(f"add_V: {add_V}")
            
            
            if add_U:
              X1.append(float(int(FF._params[primary_param])))
              Y1.append(float(FF._measurement))
              
            if add_V:
              X2.append(float(int(FF._params[primary_param])))
              Y2.append(float(FF._measurement))
              
        

      
          if len(X1) > 0 and len(Y2) > 0 and len(X2) > 0 and len(Y1) > 0:
      
     
      
            dv = []
            dx = []
            for i, x in enumerate(X2):
              if x >= 20 and x != 127:
                dv.append(Y2[i])
                dx.append(x)
            
            
            
            nn = numpy.polyfit(dx,dv,2)
            #self._info += "  Got a quadratic fit between velocity and amplitude for the comparison trace. Fit parameters:   " + str(nn)   + "\n"
            
            print(nn)
            
            if True: # plot results
              dy = []
              for i,x in enumerate(X2):
                dy.append(   numpy.poly1d(nn)(x)   )
              plt.plot(X2,dy)
              plt.show()
            
            
            
            # Find the roots
            
            
            VS = []
            
            for j, y in enumerate(X1):
              roots = [x for x in (numpy.poly1d(nn) - Y1[j]).roots if x >= 0.]
              ROOT = None
              if len(roots) == 1:
                if roots[0] > 129.:
                  # No solution found
                  pass
                elif roots[0] > 127.:
                  ROOT = 127
                else:
                  ROOT = int(numpy.round(roots[0]))
              else:
                raise Exception("Bad root")
              VS.append(ROOT)
                  
                  
                  
              fit = {'nonprimary_params': tuple([x for x in UU if x>=0]), 'primary_param': X1[j], 'unfitted': Y1[j], 'fitted': ROOT}
              FIT_RESULTS.append(fit)
            
            
            print(VS)
            
            
            plt.clf()
            plt.plot(X1, VS, '.')
            plt.show()
            
              

      self._fit_results = FIT_RESULTS





  
  def save_results(self, output_dir=None):
    
    if self._is_complete:
      if output_dir is None:
        # Output directory name. Make up a random number combined with the date
        output_dir = self._datetime.strftime("%Y%m%d") + "_{0:07x}".format(random.randint(0, 0xFFFFFFF))
      
      
      os.mkdir(output_dir)
      with open(os.path.join(output_dir, "Info.txt"), "w") as f1:
        f1.write(self._info)
        
        
      print("Outputting to " + os.path.abspath(output_dir))
        
      with open(os.path.join(output_dir, "Results.csv"), "w") as f1:
        
        
        f1.write("\n\nResult points:\n\n")
        
        for i in range(len(self._points[0]._params)):  # assume all points have the same number of parameters
          
          LAB = ""
          for PP in self._points:
            XX = PP._params[i]
            if XX is not None:
              LAB = XX.label
              break
          f1.write("{0},".format(LAB))
        f1.write("\n")
        
        
        for PP in self._points:
          for XX in PP._params:
            if XX is None:
              f1.write(",")
            else:
              f1.write("{0},".format(int(XX)))
          YY = PP._measurement
          if YY is None:
            f1.write(",")
          else:
            f1.write("{0},".format(float(YY)))
          f1.write("\n")
        f1.write("\n\n")
        
        

        # for i, NOTE in enumerate(self.notes):
          # f1.write("\n\nNOTE:\n")
          # if isinstance(self._var1, list):
            # VAR1 = self._var1[i]
          # else:
            # VAR1 = self._var1

          # for _ in range(VAR1.width):
            # f1.write(",")
          # for X in self._var2.Values:
            # if X is None:
              # f1.write("Compare,")
            # else:
              # f1.write("{0},".format(X))
          # f1.write("\n")
          
          # for j, Y in enumerate(VAR1.Values):
            # if Y is None:
              # f1.write("Compare,")
            # else:
              # f1.write("{0},".format(Y))
            # for k, X in enumerate(self._var2.Values):
              # f1.write("{0},".format(self._results[i][j][k]))

            # f1.write("\n")



        # if self._fit_results is not None:
          # for i, NOTE in enumerate(self.notes):
            
            # if isinstance(self._var1, list):
              # VAR1 = self._var1[i]
            # else:
              # VAR1 = self._var1
            # f1.write("\n\n\nFIT RESULTS\n-----------\n\nNOTE:\n")


            # for _ in range(VAR1.width):
              # f1.write(",")
            # for X in self._var2.Values:
              # if X is None:
                # f1.write("Compare,")
              # else:
                # f1.write("{0},".format(X))
            # f1.write("\n")
            
            # for j, Y in enumerate(VAR1.Values):
              # if Y is None:
                # f1.write("Compare,")
              # else:
                # f1.write("{0},".format(Y))
              # if self.output == 'ampl_env':
                # _i = enumerate([0,1]) # In this case, the last axis is slope/intercept
              # else:
                # _i = enumerate(self._var2.Values)
              # for k, X in _i:
                # f1.write("{0},".format(self._fit_results[i][j][k]))

              # f1.write("\n")


        # if self._waveforms_out is not None:
        
          # max_len = -1
          # try:
            # max_len = max([len(x['ampl_x']) for x in self._waveforms_out])
          # except KeyError:
            # pass

          # if max_len < 0:
            # try:
              # max_len = max([len(x['spectrum_x']) for x in self._waveforms_out])
            # except KeyError:
              # pass


          # if self.output == 'ampl':
            # for i in range(max_len):
              # if i >= len(self._waveforms_out[0]['ampl_t']):
                # f1.write(",")
              # else:
                # f1.write("{0},".format(self._waveforms_out[0]['ampl_t'][i]))
              # for x in self._waveforms_out:
                # if i >= len(x['ampl_x']):
                  # f1.write(",")
                # else:
                  # try:
                    # f1.write("{0},".format(x['ampl_x'][i]))
                  # except KeyError:
                    # print(i)
                    # print(x)
                    # raise
            # f1.write("\n")




        if self._fit_results is not None and len(self._fit_results) > 0:
          
          f1.write("\n\nFITTING:\n\n")
          
          for _ in range(len(self._fit_results[0]['nonprimary_params'])):
            f1.write(",")
          f1.write("X,Unfitted,Y\n")
          for FF in self._fit_results:
            f1.write(",".join(map(str, FF['nonprimary_params'])))
            f1.write(",{0},{1},{2}\n".format(FF['primary_param'], FF['unfitted'], FF['fitted']))




      if self._waveforms_out is not None:

        AXIS_1_LEN = len(self._waveforms_out)//len(self.notes)
        
        if AXIS_1_LEN > 0:

          for i, NOTE in enumerate(self.notes):

            plt.clf()
            for j, w in enumerate(self._waveforms_out):
              if j//AXIS_1_LEN == i:  # Make sure it's for the relevant note
                if self.output == 'spectrum':
                  if self.compare:
                    if j >= 1:
                      plt.semilogy(w['spectrum_f'], w['spectrum_x']/self._waveforms_out[0]['spectrum_x'])
                  else:
                    plt.semilogy(w['spectrum_f'], w['spectrum_x'])
                elif self.output == 'ampl_env' or self.output == 'ampl_ampl_env':
                  #t = numpy.array(range(0,len(w)))/(48000./480.)
                  gg = plt.plot(w['ampl_t'], w['ampl_x'])
                  
                  # Now fit an exponential, and draw it as dots of the same colour
                  if self.output != 'ampl_ampl_env':
                    cc = gg[0].get_color()
                    
                    p = self._fit_results[i][j%AXIS_1_LEN][:]
                    
                    if self.stage == 2:
                      tt = numpy.array([0.1, 0.2, 0.3, 0.4, 0.5])
                      xx = numpy.exp(-p[0]*tt + p[1])
                    elif self.stage == 1:
                      tt = numpy.array([0.02, 0.04, 0.06])
                      xx = p[0]*tt + p[1]
                    else:
                      tt = numpy.array([0.25,0.3,0.35])
                      xx = numpy.exp(-p[0]*tt + p[1])
                    #print(tt)
                    #print(xx)
                    plt.plot(tt, xx, '.', color=cc)
                
              
            
          if self.output == "pitch_env":
            plt.ylim([0,600])
          if self.output == 'spectrum':
            plt.xlim([0,6000])
          if len(self.notes) > 1:
            plt.title("NOTE: {0}".format(NOTE))
          plt.savefig(os.path.join(output_dir, "{0}.png".format(random.randint(0, 0xFFFFFF))))
            
              
      if self.output == "ampl_env":
        
        plt.clf()
        for i, NOTE in enumerate(self.notes):
          
          if isinstance(self.parameter_sequence, list):
            PARAM = self.parameter_sequence[i]
          else:
            PARAM = self.parameter_sequence
          
          yy = []
          for k in range(self._fit_results.shape[1]):
            yy.append(self._fit_results[i][k][0])
          
          #plt.plot(list(PARAM.Values), yy, '.-', label="NOTE {0}".format(NOTE))
        
        xx_2 = numpy.linspace(plt.axis()[0], plt.axis()[1], 50)
        
        # CAT = self.parameter_sequence.category
        # pp_2 = None
        # if CAT==12:        
          # pp_2 = [0.01, -3.9]   # Current best fit of amplitude envelope slope for Category 12 Parameter 56
          # if self.stage >= 5:
            # pp_2 = [0.01, -2.0]
        # elif CAT==3:
          # pp_2  = [0.02166, -11.]    # Current best fit of amplitude envelope slope for Category 3 Parameter 20
        # if pp_2:
          # yy_2 = numpy.exp(pp_2[0]* xx_2 + pp_2[1])
          # plt.plot(xx_2, yy_2, 'k--', label="_")
        
        # plt.legend()
        # plt.savefig(os.path.join(output_dir, "{0}.png".format(random.randint(0, 0xFFFFFF))))
          
      elif self.output == "ampl_ampl_env":
        
        plt.clf()
        for i, NOTE in enumerate(self.notes):
          
          if isinstance(self.parameter_sequence, list):
            PARAM = self.parameter_sequence[i]
          else:
            PARAM = self.parameter_sequence
          
          yy = []
          for k in range(self._fit_results.shape[1]):
            yy.append(self._fit_results[i][k][0])
          
          plt.plot(list(PARAM.Values), yy, '.-', label="NOTE {0}".format(NOTE))
        
        plt.legend()
        plt.savefig(os.path.join(output_dir, "{0}.png".format(random.randint(0, 0xFFFFFF))))
          
        
  




if __name__=="__main__":
  # Example
  ex = Experiment()
  ex.notes = range(0,128)
  ex.run()
  ex.save_results()
  if False: # only for velocity test
    pp = numpy.polyfit(ex._var2.Values, numpy.sqrt(ex._results[0][0][:]), 1)
    print(pp)
    
    for i in range(0,128):
      print("{0: 3d}    {1:0.3f}  {2:0.3f}".format( i, ex._results[0][0][i],   numpy.power(pp[0]*i+pp[1],2)-ex._results[0][0][i]))


