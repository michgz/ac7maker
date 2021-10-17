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



"""
A basic template for Category 5 parameter sets. All Split pointers here are set
as zero; at least 1 needs to be set to something else for this to be useable.
"""
CAT5_BASIC = b'\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f' \
             b'\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00' \
             b'\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f\x00\x00\x00\x7f\x00\x7f' \
             b'\x40\x40\x40\x80\x4a\x4a\x40\x40\x40\x80\x40\x40\x40\x40\x80\x40' \
             b'\x40\x00\x50\x02\x02\x00'











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
    self.end_category = 12


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
    self.input = 'velocity'
    
    
    
    """
    output:      the output value to measure. Can be 'freq' (frequency) or 'ampl'
                 (amplitude).
    """
    self.output = 'ampl'
    
    
    self.parameter = {'parameter': 5, 'category': 3, 'min':0, 'max': 127}
    
    
    
    # Now some internal variables
    self._datetime = None
    self._is_complete = False
    self._info = ""
    self._results = None






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
        cat3 = f2.read()[0x20:-4]
    elif self.waveform == 'white':
      with open(os.path.join(os.path.dirname(__file__), "..", "calibration tones", "CALWHITE.TON"), "rb") as f2:
        cat3 = f2.read()[0x20:-4]
    else:
      raise Exception("Invalid waveform")
    
    
    internal.sysex_comms_internal.upload_ac7_internal(DEST-801, cat3, category=3, memory=1, fs=f_midi)



    # Open PyAudio for doing the recording

    SAMPLE_TIME = 1.0   # units of seconds. Used to scale FFT bins to Hz
    RATE = 44100    # units of Hz. Probably only certain values are allowed, e.g.
                    #  24000, 44100, 48000, 96000, ....
    FRAMES = 1024

    p = pyaudio.PyAudio()

    NOTES = [60]
    VARS = None
    if self.input == 'velocity':
      VARS = range(0,128,10)
      
    PARAMS = None
    PARAMS = [44,64,84]
    
    os.write(f_midi, struct.pack("8B", 0xB0, 0x00, 65, 0xB0, 0x20, 0, 0xC0, DEST-801))


    RESULTS = numpy.zeros((len(NOTES), len(PARAMS), len(VARS)))

    for i, NOTE in enumerate(NOTES):   # Try at various different pitches
      for j, PARAM in enumerate(PARAMS):
        for k, VAR in enumerate(VARS):
          
          VEL = 0x7F
          if self.input == 'velocity':
            VEL = VAR
          
          
          internal.sysex_comms_internal.set_single_parameter(self.parameter['parameter'], PARAM, category=self.parameter['category'], memory=3, parameter_set=32, fs=f_midi)
          
          time.sleep(0.1)
          os.write(f_midi, struct.pack("3B", 0x90, NOTE, VEL))
          time.sleep(0.1)

          x = p.open(format=pyaudio.paFloat32,
                      channels=2,
                      rate=RATE,
                      input=True,
                      input_device_index=pulse_device_index,
                      start=True,
                      frames_per_buffer=FRAMES)
          frame_count = 32*1024
          v = x.read(frame_count)
          x.close()

          result = numpy.frombuffer(v, dtype=numpy.float32)
          result = numpy.reshape(result, (frame_count, 2))
          result = result[:, 0]


          os.write(f_midi, struct.pack("3B", 0x80, NOTE, 0x7F))
          time.sleep(0.6)
      
          RESULTS[i][j][k] = self.measure_amplitude(result, RATE)

    
    os.close(f_midi)
    p.terminate()
    
    self._results = {'inputs': [{'name': 'notes', 'parameter': None, 'values': NOTES},
                                {'name': 'velocity_sense', 'parameter': {'parameter': 5, 'category': 3, 'min':0, 'max': 127}, 'values': PARAMS},
                                {'name': 'velocity', 'parameter': None, 'values': VARS}],
                     'output': {'name': 'amplitude', 'values': RESULTS} }
    
  
  
  def save_results(self, output_dir=None):
    if self._is_complete:
      if output_dir is None:
        # Output directory name. Make up a random number combined with the date
        output_dir = self._datetime.strftime("%Y%m%d") + "_{0:07x}".format(random.randint(0, 0xFFFFFFF))
      
      
      os.mkdir(output_dir)
      with open(os.path.join(output_dir, "Info.txt"), "w") as f1:
        f1.write(self._info)
        
      with open(os.path.join(output_dir, "Results.csv"), "w") as f1:
        

        for i, NOTE in enumerate(self._results['inputs'][0]['values']):
          f1.write("\n\nNOTE:\n")


          f1.write(",")
          for k, VEL in enumerate(self._results['inputs'][2]['values']):
            f1.write("{0},".format(VEL))
          f1.write("\n")
          
          
          
          for j, PARAM in enumerate(self._results['inputs'][1]['values']):
            f1.write("{0},".format(PARAM))
            for k, VEL in enumerate(self._results['inputs'][2]['values']):
              f1.write("{0},".format(self._results['output']['values'][i][j][k]))
            f1.write("\n")
  




if __name__=="__main__":
  # Example
  ex = Experiment()
  ex.notes = range(0,128)
  ex.run()
  ex.save_results()



