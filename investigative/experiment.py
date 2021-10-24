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
             b'\x40\x40\x40\x80\x4a\x4a\x40\x40\x40\x80\x40\x40\x40\x40\x80\x40' \
             b'\x40\x00\x50\x02\x02\x00'



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





class ParameterSequence:
  """
  A sequence of parameter writes, either different values to a single parameter
  or the same value to multiple parameters.
  """
  
  def __init__(self):
    self._writes = dict()
    self._type = -1
    self._compare = False
    
  @classmethod
  def SingleParameter(cls, parameter: int, category: int, values: list, *, block0=0, compare=False):
    self = ParameterSequence()
    self._type = 1
    self._parameter = {'parameter': parameter, 'category': category, 'default': 0}
    self._values = values
    self._block0 = block0
    if category == 3:
      self._parameter_set = 32
      self._memory=3
    else:
      self._parameter_set = 0
      self._memory=1
    self._compare = compare
    return self
    
  @classmethod
  def SingleValue(cls, parameters: list, category:int, value: int, default=0, *, block0=0):
    self = ParameterSequence()
    self._type = 2
    self._parameters = [{'parameter': x, 'category': category, 'default': default} for x in parameters]
    self._value = value
    self._block0 = block0
    if category == 3:
      self._parameter_set = 32
      self._memory=3
    else:
      self._parameter_set = 0
      self._memory=1
    return self
  
  @classmethod
  def Velocities(cls, velocities: list):
    self = ParameterSequence()
    self._type = 3
    self._velocities = velocities
    self._block0 = 0
    return self
  
  class ParameterSequenceValue:
    def __init__(self, set_dict, unset_dict, velocity=-1):
      self._set = set_dict
      self._unset = unset_dict
      self._velocity = velocity
    
    @property
    def set_write(self):
      return self._set
    
    @property
    def unset_write(self):
      return self._unset
      
    @property
    def velocity(self):
      if self._velocity >= 0:
        return self._velocity
      else:
        return 0x7F
  
  def __len__(self):
    the_length = 0
    if self._type == 1:
      the_length = len(self._values)
      if self._compare:
        the_length += 1
    elif self._type == 2:
      the_length = len(self._parameters)
    elif self._type == 3:
      the_length = len(self._velocities)
    else:
      raise Exception
      
    return the_length
    
  
  @property
  def Writes(self):
    if self._type == 1:
      if self._compare:
        return iter(
          [None] + 
          [
            ParameterSequence.ParameterSequenceValue(
              {'parameter': self._parameter["parameter"], 'data': x, 'category': self._parameter["category"], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': 0},
              None
            )
            for x in self._values
          ])

      else:
        return iter(
          [
            ParameterSequence.ParameterSequenceValue(
              {'parameter': self._parameter["parameter"], 'data': x, 'category': self._parameter["category"], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': 0},
              None
            )
            for x in self._values
          ])
    elif self._type == 2:
      return iter(
        [
          ParameterSequence.ParameterSequenceValue(
            {'parameter': x['parameter'], 'data': self._value, 'category': x['category'], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': 0},
            {'parameter': x['parameter'], 'data': x['default'], 'category': x['category'], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': 0}
          )
          for x in self._parameters
        ])
    elif self._type == 3:
      return iter(
        [
          ParameterSequence.ParameterSequenceValue(
            None, None, v
          )
          for v in self._velocities
        ])
    else:
      raise Exception("Wrong type")

  @property
  def Values(self):
    if self._type == 1:
      return iter(self._values)
    elif self._type == 2:
      return iter([x['parameter'] for x in self._parameters])
    elif self._type == 3:
      return self._velocities
    else:
      raise Exception("Wrong type")

  @property
  def width(self):
    return 1


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
    self.waveform = 'white'
    
    
    
    
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
                 'ampl_env': amplitude envelope
                 'pitch_env': pitch envelope
                 'spectrum':   frequency spectrum (only with 'white' input waveform).
    """
    self.output = 'spectrum'
    
    
    
    """
    compare:     a boolean, indicating if readings need to be compared against
                 subsequent readings. Useful for example with spectrum readings.    
    """
    self.compare = True
    
        
    
    self.parameter = {'parameter': 118, 'category': 3, 'min':0, 'max': 127}
    
    
    
    # Now some internal variables
    self._datetime = None
    self._is_complete = False
    self._info = ""
    self._results = None
    self._waveforms_out = None




  # Some pre-set split/waveform values
  SPLIT_SINE = 1
  WAVEFORM_SINE = 1
  
  

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
      peak = 0.
    elif (n+2) > len(Px):
      peak = rate/2.   # Nyquist
    else:
      pp = numpy.polyfit(  f[n-1:n+2],   numpy.log10(Px[n-1:n+2]), 2)
      #print(pp)
        
      peak_hz = - pp[1] / (2. * pp[0])
      # Translate from Hz to MIDI note (floating point!)
      
      
      peak =     12.0*numpy.log2(  peak_hz / 440. )   + 69.  # Units of semitones
        
    return peak


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
      else:
        # Amplitude envelope with an obvious shape.
        cat3[0x60:0x7C] = b'\x80\x02\xA0\x00' \
                          b'\x80\x01\xFF\x00' \
                          b'\x80\x01\x20\x00' \
                          b'\xFF\x03\x80\x00' \
                          b'\x00\x02\x60\x00' \
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
        else:
          raise Exception
      internal.sysex_comms_internal.upload_ac7_internal(0, cat5, category=5, memory=1, fs=f_midi)


    if self.end_category >= 12:
      
      cat12 = bytearray(CAT12_BASIC)
      if self.waveform == 'sine':
        cat12[0x10:0x12] = struct.pack("<H", self.WAVEFORM_SINE)
      else:
        raise Exception
      internal.sysex_comms_internal.upload_ac7_internal(0, cat12, category=12, memory=1, fs=f_midi)




    # Open PyAudio for doing the recording

    SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
    RATE = 44100    # units of Hz. Probably only certain values are allowed, e.g.
                    #  24000, 44100, 48000, 96000, ....
    FRAMES = 1024

    p = pyaudio.PyAudio()

    NOTES = [60]
    VARS = None
    if self.input == 'velocity':
      #VARS = ParameterSequence.Velocities(range(0, 128, 1))
      VARS = ParameterSequence.Velocities([127])
    else:
      VARS = ParameterSequence.Velocities([127])
      
      
    PARAMS = None
    #PARAMS = [44,64,84]
    
    
    #PARAMS = [0,1,2]
    
    
    PARAMS = ParameterSequence.SingleParameter(118, 3, [7,9,11,13], compare = True)
    
    
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




    RESULTS = numpy.zeros((len(NOTES), len(PARAMS), len(VARS)))
    WAVEFORMS = []

    for i, NOTE in enumerate(NOTES):   # Try at various different pitches
      for j, PARAM in enumerate(PARAMS.Writes):
        for k, VAR in enumerate(VARS.Writes):
          
          VEL = 0x7F
          if self.input == 'velocity':
            VEL = VAR.velocity
          
          
          #internal.sysex_comms_internal.set_single_parameter(self.parameter['parameter'], PARAM, category=self.parameter['category'], memory=3, parameter_set=32, fs=f_midi)
          
          #internal.sysex_comms_internal.set_single_parameter(5, 127, category=3, memory=3, parameter_set=32, fs=f_midi)
          
          if j == 1:
            internal.sysex_comms_internal.set_single_parameter(117, 1, category=3, memory=3, parameter_set=32, fs=f_midi)
          
          if PARAM is not None:
            try:
              internal.sysex_comms_internal.set_single_parameter(**PARAM.set_write, fs=f_midi)
              pass
            except internal.sysex_comms_internal.SysexTimeoutError:
              print("Problem writing parameter {0}".format(PARAM))
              continue
          
          
          is_env = self.output.endswith("_env")
          

          frame_count = 64*1024
          if self.output == 'ampl':
            frame_count = 2*1024


          v = bytes()
          tot_frames = 0


          time.sleep(0.3)
          os.write(f_midi, struct.pack("3B", 0x90, NOTE, VEL))
            
            
          while tot_frames < frame_count:
            time.sleep(0.1)

          os.write(f_midi, struct.pack("3B", 0x80, NOTE, 0x7F))
          time.sleep(0.6)


          result = numpy.frombuffer(v, dtype=numpy.float32)
          result = numpy.reshape(result[:65536], (32*1024, 2))
          result = result[:, 0]


          if self.input == 'sine':
            RESULTS[i][j][k] = self.measure_amplitude(result, RATE)
          else:
            RESULTS[i][j][k] = 0.


              
          if self.output.endswith("_env"):
                
                
            
            
            if self.output == "pitch_env":
              fs = 48000.

            else:
              pass
            
            fs = 48000.
            
            # Calculate the hilbert signal, with a bit of high-pass filtering. The filtering
            # requires a pitch of at least about C-2.
            bb = scipy.signal.butter(100., 4, btype='high', output='sos', fs=fs)
            hx = scipy.signal.hilbert(scipy.signal.sosfilt(bb, result))
            
            # Get the amplitude
            WAVE_RATE = 100.   # samples per second
            dx = scipy.signal.decimate(numpy.abs(hx), int(numpy.round(fs/WAVE_RATE)), ftype='fir')
            
            # Align with the first -6dB point
            max_d = numpy.max(dx)
            i_3 = max(0, min([x for x in range(0, len(dx)) if dx[x] > (max_d/2.)])-48)
            i_4 = len(dx)
            
            # Get the pitch
            fx = numpy.diff(numpy.unwrap(numpy.angle(hx))) / (2.0*numpy.pi) * fs
            gx = scipy.signal.savgol_filter(fx, 481, 1)  # Smooth the signal. Is this needed?
            ix = scipy.signal.decimate(gx, int(numpy.round(fs/WAVE_RATE)), ftype='fir')
            
            
            # Amplitude aligned with the -6dB point
            jx = dx[i_3:i_4]
            tx = numpy.array(range(len(jx)))/WAVE_RATE
            
            if len(ix) != len(dx):
              raise Exception
            
            
            for ii in range(len(ix)):
              # Clear values that are too quiet to be sure
              if dx[ii] < 0.02:
                ix[ii] = numpy.nan
            kx = ix[i_3:i_4]
            
           
            print(kx)
            
            WAVEFORMS.append({'ampl_t': tx, 'ampl_x': jx, 'freq_t': tx, 'freq_x': kx})

          elif self.output == 'spectrum':
            
            fs = 48000.
            
            
            f, Px = scipy.signal.welch(result, fs=fs, nperseg = 2*1024)
            WAVEFORMS.append({'spectrum_f': f, 'spectrum_x': Px})
            
            
          #internal.sysex_comms_internal.set_single_parameter(PARAM, 0, category=12, memory=3, parameter_set=0, fs=f_midi)

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
      
      
    
    
    
    self._results = RESULTS
    self._var1 = PARAMS
    self._var2 = VARS
    if len(WAVEFORMS) > 0:
      self._waveforms_out = WAVEFORMS
    
  
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
        

        for i, NOTE in enumerate([60]):
          f1.write("\n\nNOTE:\n")


          for _ in range(self._var1.width):
            f1.write(",")
          for X in self._var2.Values:
            f1.write("{0},".format(X))
          f1.write("\n")
          
          for j, Y in enumerate(self._var1.Values):
            f1.write("{0},".format(Y))
            for k, X in enumerate(self._var2.Values):
              f1.write("{0},".format(self._results[i][j][k]))

            f1.write("\n")


              
      if self._waveforms_out is not None:

        plt.clf()
        for j, w in enumerate(self._waveforms_out):
          if self.output == 'spectrum':
            if self.compare:
              if j >= 1:
                plt.semilogy(w['spectrum_f'], w['spectrum_x']/self._waveforms_out[0]['spectrum_x'])
            else:
              plt.semilogy(w['spectrum_f'], w['spectrum_x'])
          else:
            #t = numpy.array(range(0,len(w)))/(48000./480.)
            plt.plot(w['ampl_t'], w['ampl_x'])
        if self.output == "pitch_env":
          plt.ylim([0,600])
        if self.output == 'spectrum':
          plt.xlim([0,6000])
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


