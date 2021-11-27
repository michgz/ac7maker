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
  def SingleParameter(cls, parameter: int, category: int, values: list, *, block0=0, block1=0, compare=False):
    self = ParameterSequence()
    self._type = 1
    self._parameter = {'parameter': parameter, 'category': category, 'default': 0}
    self._values = values
    self._block0 = block0
    self._block1 = block1
    if category == 3:
      self._parameter_set = 32
      self._memory=3
    else:
      self._parameter_set = 0
      self._memory=1
    self._compare = compare
    return self
    
  @classmethod
  def SingleValue(cls, parameters: list, category:int, value: int, default=0, *, block0=0, block1=0):
    self = ParameterSequence()
    self._type = 2
    self._parameters = [{'parameter': x, 'category': category, 'default': default} for x in parameters]
    self._value = value
    self._block0 = block0
    self._block1 = block1
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
        
    @property
    def is_velocity(self):
      return (self._velocity >= 0)
      
    @property
    def label(self):
      if self.is_velocity:
        return "Velocity"
      else:
        return "C{0}P{1}".format(self._set['category'], self._set['parameter'])
      
    @property
    def is_note(self):
      # This type of quantity is never a note.
      return False
      
    def __index__(self):
      if self._velocity >= 0:
        return self._velocity
      else:
        return self._set['data']
  
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
              {'parameter': self._parameter["parameter"], 'data': x, 'category': self._parameter["category"], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': self._block1},
              None
            )
            for x in self._values
          ])

      else:
        return iter(
          [
            ParameterSequence.ParameterSequenceValue(
              {'parameter': self._parameter["parameter"], 'data': x, 'category': self._parameter["category"], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': self._block1},
              None
            )
            for x in self._values
          ])
    elif self._type == 2:
      return iter(
        [
          ParameterSequence.ParameterSequenceValue(
            {'parameter': x['parameter'], 'data': self._value, 'category': x['category'], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': self._block1},
            {'parameter': x['parameter'], 'data': x['default'], 'category': x['category'], 'memory': self._memory, 'parameter_set': self._parameter_set, 'block0': self._block0, 'block1': self._block1}
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
      if self._compare:
        return iter([None] + list(self._values))
      else:
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
    
  @property
  def category(self):
    if self._type == 1:
      return self._parameter['category']
    elif self._type == 2:
      return self._parameters[0]['category']
    else:
      return None
    

class Note():
  def __init__(self, note):
    self._note = note
  @property
  def is_note(self):
    return True
  @property
  def is_velocity(self):
    return False
  def __index__(self):
    return self._note
  @property
  def label(self):
    return "Note"
  @property
  def note(self):
    return self._note


class NotesSequence:
  
  def __init__(self, notes):
    self._notes = notes
      
  def __iter__(self):
    return iter(list([Note(x) for x in self._notes]))



class ParametersSequence:
  """
  Multiple, possibly nested, ParameterSequence sequences
  """
  
  def __init__(self, notes, params1, params2=None):
    self._notes = [60]
    self._params1 = params1
    self._params2 = params2
    
    
  def __iter__(self):
    
    
    Param_Is_List = False
    
    if self._params1 is None:
      PARAMS = ParameterSequence.SingleParameter(29, 12, [1], compare = True)
    elif isinstance(self._params1, list):
      Param_Is_List = True
      if len(self._notes) != len(self._params1):
        raise Exception("A list-type parameter must be same length as the notes list")
      PARAMS = self._params1[0]
    else:
      PARAMS = self._params1
    
    if Param_Is_List:
      PARAMS = self._params1[i]
    
    if self._params2 is None:
      return itertools.product(NotesSequence(self._notes), PARAMS.Writes)
    else:
      return itertools.product(NotesSequence(self._notes), PARAMS.Writes, self._params2.Writes)













class ResultMeasurement:
  def __init__(self):
    self._type = 0
  
  AMPLITUDE = 1
  PITCH = 2
  
  # res: result (float)
  # rate: in Hz
  @classmethod
  def AmplitudeMeasurement(cls, res, *, rate=48000, frame_count=1024):
    self = cls()
    self._type = self.AMPLITUDE
    self._value = res
    self._rate = rate
    self._frame_count = frame_count
    return self
    
  # res: result (units of Hz)
  # rate: in Hz
  @classmethod
  def PitchMeasurementHz(cls, res, *, rate=48000, frame_count=1024):
    self = cls()
    self._type = self.PITCH
    self._value = res
    self._rate = rate
    self._frame_count = frame_count
    return self
  
  @property
  def pitch_in_hz(self):
    if self._type == self.PITCH:
      return self._pitch
    else:
      raise Exception
      
  @property
  def pitch_in_semitones(self):
    if self._type == self.PITCH:
      return 69. + 12.*numpy.log2(self._pitch/440.)
    else:
      raise Exception
    
    
  def __repr__(self):
    if self._type == self.AMPLITUDE:
      return "AmplitudeMeasurement(value={0}, rate={1})".format(self._value, self._rate)
    elif self._type == self.PITCH:
      return "PitchMeasurement(value={0}, rate={1})".format(self._value, self._rate)
    else:
      raise Exception("Unknown measurement type")

  @property
  def value(self):
    if self._type == self.AMPLITUDE:
      return self._value
    elif self._type == self.PITCH:
      return self.pitch_in_semitones()
    else:
      raise Exception("Unknown measurement type")

  def __float__(self):
    if self._type == self.AMPLITUDE:
      return self._value
    elif self._type == self.PITCH:
      return self.pitch_in_semitones()
    else:
      raise Exception("Unknown measurement type")

class ResultWaveform:
  def __init__(self):
    self._type = 0
    self._is_fitted = 0
    self._fit_parameters = None
  
  AMPLITUDE_VS_TIME = 21
  PITCH_VS_TIME = 22
  AMPLITUDE_VS_VELOCITY = 23
  SPECTRUM = 24
  
  @classmethod
  def AmplitudeWaveform(cls, t, x):
    self = cls()
    self._type = cls.AMPLITUDE_VS_TIME
    self.x = t
    self.y = x
    return self

  @classmethod
  def PitchWaveform(cls, t, p):
    self = cls()
    self._type = cls.PITCH_VS_TIME
    self.x = t
    self.y = p
    return self

  @classmethod
  def VelocityWaveform(cls, v, x):
    self = cls()
    self._type = cls.AMPLITUDE_VS_VELOCITY
    self.x = v
    self.y = x
    return self

  @classmethod
  def SpectrumWaveform(cls, f, x):
    self = cls()
    self._type = cls.SPECTRUM
    self.x = f
    self.y = x
    return self

  def FitShape(self):
    
    if self._type == AMPLITUDE_VS_VELOCITY:
      # Fit a quadratic relationship
      i = [x for x in self.x if x >= 20 and x != 127]
      self._fit_parameters = numpy.polyfit(self.x[i], self.y[i], 2)
      self._is_fitted = True
    else:
      pass # No other fits defined
      

  def Compare(self, ToCompare):
    
    if self._type == AMPLITUDE_VS_VELOCITY:
      if not ToCompare or not ToCompare._is_fitted:
        raise Exception("Not prepared comparison")
      fit_results = []
      for i, y in enumerate(self.y):
        roots = [x for x in (numpy.poly1d(ToCompare._fit_parameters) - y).roots if x >= 0.]
        z = -1
        if len(roots) == 1:
          if roots[0] > 129.:
            # No solution found
            pass
          elif roots[0] > 127.:
            z = 127
          else:
            z = int(numpy.round(roots[0]))
        fit_results.append(z)
      self.fitted_y = numpy.array(fit_results)

    elif self._type == AMPLITUDE_VS_TIME:
      pass


    else:
      pass   # No other fittings






class ResultPoint:
  def __init__(self):
    self._waveform = ''
    self._note = 60
    self._param1 = 0
    self._is_compare = False
    self._output_waveform = None
    self._output = ''
    self._frame_count = -1
    
    
    pass
    
  @property
  def waveform(self):
    return self._output_waveform
  @property
  def note(self):
    return self._note
  @property
  def param1(self):
    return self._param1
    
    













