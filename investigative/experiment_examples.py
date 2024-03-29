from experiment import Experiment, ParameterSequence
import pickle



"""
Example 1:   Tries different relationships between velocity and sound amplitude.

             The relationship is defined by Category 12 Parameter 29 and follows the
             "key follow" pattern of options. The default value is 0, which represents
             an identity mapping. By comparing the value of 0 with another value, we
             can work out exactly what mapping is represented by a particular "key
             follow" value.
"""
def Example1():
  expt = Experiment()
  expt.end_category = 12
  expt.waveform = 'sine'
  expt.notes = [60]
  expt.input = 'velocity'
  expt.output = 'ampl'
  expt.compare = True

  # Define the values to write to parameter 29 Category 12. In this example, only
  # one value (90) is written.
  expt.parameter_sequence = ParameterSequence.SingleParameter(29, 12, [90], compare = True)

  expt.run()
  expt.analyse()
  expt.save_results()


"""
Example 2:     Measures attack time

"""

def Example2():
  expt = Experiment()
  expt.end_category = 3
  expt.waveform = 'sine'
  expt.output = 'ampl_ampl_env'
  expt.stage = 5  # 1 or 2 supported at this stage.
  expt.notes = [60]
  expt.parameter_sequence =  ParameterSequence.SingleParameter(19, 3, list(range(0,256,20)), block1=0, block0=expt.stage)

  expt.run()
  expt.save_results()


"""
Example 3:     Spectral analysis

"""

def Example3():
  expt = Experiment()
  expt.end_category = 12
  expt.waveform = 'white'
  expt.output = 'spectrum'
  expt.compare = True
  expt.parameter_sequence = ParameterSequence.SingleParameter(9, 12, [40, 50, 60], compare=True)

  expt.run()
  expt.save_results()



"""
Low-pass filter
"""

def Example4():
  expt = Experiment()
  expt.end_category = 3
  expt.waveform = 'white'
  expt.output = 'spectrum'
  expt.compare = True
  expt.parameter_sequence = ParameterSequence.SingleParameter(14, 3, [40, 60, 80, 100], compare=True)
  expt.notes = [60]

  expt.run()
  expt.save_results()
  
  
  


if __name__=="__main__":
  Example1()
