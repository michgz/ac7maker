'''
Write an arbitrary control map to a Roland A-PRO controller keyboard. This will be
used to control synth settings in the CT-X.
'''


import struct
import os
import sys


DEVICE_NAME = 'hw:1,0,1'
# Note: any responses will come on hw:1,0,2






class Messages:
  NoAssign = 0
  Note = 1
  ChannelPressure = 3
  PolyphonicPressure = 5
  ControlChange = 7
  EncoderSimulate = 9
  ProgramChangeMinMax = 10 # TODO: implement this
  ProgramChange = 12 # TODO: implement this
  BankProgramChange = 13 # TODO: implement this
  RPN = 15 # TODO: implement this
  NRPN = 17 # TODO: implement this
  RealTime = 19 # TODO: implement this
  SysEx = 20 # TODO: implement this
  FreeMsg = 22 # TODO: implement this
  Tempo = 24 # TODO: implement this
  MapTitle = 0x7F


class Controls:
  Rotary1 = 0
  Rotary2 = 1
  Rotary3 = 2
  Rotary4 = 3
  Rotary5 = 4
  Rotary6 = 5
  Rotary7 = 6
  Rotary8 = 7
  Rotary9 = 8
  Slider1 = 9
  Slider2 = 10
  Slider3 = 11
  Slider4 = 12
  Slider5 = 13
  Slider6 = 14
  Slider7 = 15
  Slider8 = 16
  Slider9 = 17
  Pad1 = 18
  Pad2 = 19
  Pad3 = 20
  Pad4 = 21
  Pad5 = 22
  Pad6 = 23
  Pad7 = 24
  Pad8 = 25
  Button1 = 26
  Button2 = 27
  Button3 = 28
  Button4 = 29
  Transport1 = 30  # Previous
  Transport2 = 31  # Rewind
  Transport3 = 32  # Fast forward
  Transport4 = 33  # Next
  Transport5 = 34  # Stop
  Transport6 = 35  # Play
  Transport7 = 36  # Pause
  Transport8 = 37  # Record
  Transport9 = 38  # V-link/hold
  Pedal1 = 39   # Hold
  Pedal2 = 40   # Expression
  Bend = 41
  Modulation = 42
  Aftertouch = 43
  MAX = 43

class ButtonMode:
  # The following apply to "Button" and "Transport" controls and "Pedal1":
  Unlatch = 0
  Latch = 1
  Increase = 2
  
  # The following apply to "Rotary" and "Slider":
  NoCenterClick = 0
  CenterClick = 4
  
  
class Velocity:
  Touch = 0
  # Numbers 1-127 have usual meaning

class AftMode:
  # Applies to "Note" events with "Button" and "Pad" controls
  Off = 0
  ChannelPressure = 1
  PolyphonicPressure = 2

class Port:
  One = 0
  Two = 1
  OneAndTwo = 2

class MidiChannels:
  Chn1 = 0
  Chn2 = 1
  Chn3 = 2
  Chn4 = 3
  Chn5 = 4
  Chn6 = 5
  Chn7 = 6
  Chn8 = 7
  Chn9 = 8
  Chn10 = 9
  Chn11 = 10
  Chn12 = 11
  Chn13 = 12
  Chn14 = 13
  Chn15 = 14
  Chn16 = 15
  
class Realtime:
  TuneRequest = 0xF6
  Start = 0xFA
  Continue = 0xFB
  Stop = 0xFC


def SendPayload(p):
  
  # Add header (Roland "write")
  b = b'\xf0\x41\x10\x00\x00\x44\x12'

  # Add checksum
  c = 0
  for i in range(len(p)):
    c += struct.unpack_from('B', p, i)[0]

  b += p
  b += struct.pack('BB', (-c)%128, 0xf7)
  
  # Send using the amidi system (Linux only). To make this work on Windows,
  # consider using python-rtmidi.
  s = 'amidi -p {0} --send-hex="'.format(DEVICE_NAME)
  
  # Create the hex string
  for i, bb in enumerate(b):
    if i > 0:
      s += " "
    s += "{0:02X}".format(bb)
    
  s += '"'
  
  # Display to the user
  print(s)
  
  # Send it!
  os.system(s)
  

  
def ReceivePayload(p):
  
  # Add header (Roland "read")
  b = b'\xf0\x41\x10\x00\x00\x44\x11'

  # Add checksum
  c = 0
  for i in range(len(p)):
    c += struct.unpack_from('B', p, i)[0]
  b += p
  b += struct.pack('BB', (-c)%128, 0xf7)

  # Send using the amidi system (Linux only). To make this work on Windows,
  # consider using python-rtmidi.
  s = 'amidi -p {0} --send-hex="'.format(DEVICE_NAME)

  # Create the hex string
  for i, bb in enumerate(b):
    if i > 0:
      s += " "
    s += "{0:02X}".format(bb)
    
  s += '"'
  
  # Display to the user
  print(s)
  
  # Send it!
  os.system(s)
  


def MakePayloadRead(CtrlMap=19):
  # Make a payload to read a control map. Use ReceivePayload() and look for response
  # on device hw:1,0,2.
  
  return struct.pack('BBHI', 0, CtrlMap, 0, 0)


def MakePayload(msg=Messages.ControlChange,
                  CtrlMap=19,
                  Ctrl=Controls.Rotary5,
                  Title="                ",
                  btnMode=ButtonMode.Unlatch,
                  port=Port.One,
                  midiChn=MidiChannels.Chn1,
                  noteNumber = 60,  # only used for "note" event
                  velocity=Velocity.Touch,
                  aft = AftMode.Off,
                  controller=0x01,   # used for "ControllerChange" and "EncoderSimulate" events
                  minVal = 0,
                  maxVal = 127,
                  realtime = Realtime.Start
                  ):
  
  # Make a payload to write a single control. No response is expected.
  
  if msg==Messages.MapTitle:
    # A different format is used for this message
    b = struct.pack('BB', 0, CtrlMap)
    b += struct.pack('BB', msg, 0)
    
    # Can add up to 16 characters in 4+4 format
    for ch in Title[:16].encode('ascii'):
      b += struct.pack('BB', ch//16, ch%16)
    
    
    needed = 132 - len(b)
    b += b'\x00' * needed
    
    return b
  
  
  
  b = struct.pack('BB', 0, CtrlMap)
  b += struct.pack('BB', Ctrl, 0)
  
  msgVal = int(msg)
  
  b += struct.pack('BB', msgVal//16, msgVal%16)

  for ch in Title[:16].encode('ascii'):
    b += struct.pack('BB', ch//16, ch%16)

  while len(b) < 0x26:
    b += b'\x00\x00'


  encoderModeVal = 0
  if msg==Messages.EncoderSimulate:
      encoderModeVal = 1
  b += struct.pack('BB', encoderModeVal//16, encoderModeVal%16)


  buttonModeVal = int(btnMode)
  b += struct.pack('BB', buttonModeVal//16, buttonModeVal%16)

  portVal = int(port)
  b += struct.pack('BB', portVal//16, portVal%16)
  
  midiChannelVal = int(midiChn)
  b += struct.pack('BB', midiChannelVal//16, midiChannelVal%16)
  
  if msg==Messages.Note:
    b += struct.pack('BB', noteNumber//16, noteNumber%16)
    b += struct.pack('BB', velocity//16, velocity%16)
    aftVal = int(aft)
    b += struct.pack('BB', aftVal//16, aftVal%16)
  elif msg==Messages.ControlChange:

    b += struct.pack('BB', controller//16, controller%16)
    b += struct.pack('BB', minVal//16, minVal%16)
    b += struct.pack('BB', maxVal//16, maxVal%16)
  elif msg==Messages.EncoderSimulate:
    b += struct.pack('BB', controller//16, controller%16)
    minValEnc = 0 # ??
    b += struct.pack('BB', minValEnc//16, minValEnc%16)
    maxValEnc = 127 # ??
    b += struct.pack('BB', maxValEnc//16, maxValEnc%16)
  elif msg==Messages.RealTime:
    realtimeVal = int(realtime)
    b += struct.pack('BB', realtimeVal//16, realtimeVal%16)
  elif msg==Mesasges.PolyphonicPressure:
    b += struct.pack('BB', noteNumber//16, noteNumber%16)
    b += struct.pack('BB', minVal//16, minVal%16)
    b += struct.pack('BB', maxVal//16, maxVal%16)
  elif msg==Mesasges.ChannelPressure:
    b += struct.pack('BB', minVal//16, minVal%16)
    b += struct.pack('BB', maxVal//16, maxVal%16)

  needed = 132 - len(b)
  
  
  
  b += b'\x00' * needed
  
  return b









if __name__=="__main__":

  SendPayload(MakePayload(Ctrl=0,  controller = 0x01, Title="Rotary 1"))
  SendPayload(MakePayload(Ctrl=1,  controller = 0x02, Title="Rotary 2"))
  SendPayload(MakePayload(Ctrl=2,  controller = 0x03, Title="Rotary 3"))
  SendPayload(MakePayload(Ctrl=3,  controller = 0x04, Title="Rotary 4"))
  SendPayload(MakePayload(Ctrl=4,  controller = 0x05, Title="Rotary 5"))
  SendPayload(MakePayload(Ctrl=5,  controller = 0x06, Title="Rotary 6"))
  SendPayload(MakePayload(Ctrl=6,  controller = 0x07, Title="Rotary 7"))
  SendPayload(MakePayload(Ctrl=7,  controller = 0x08, Title="Rotary 8"))
  SendPayload(MakePayload(Ctrl=8,  controller = 0x09, Title="Rotary 9"))
  SendPayload(MakePayload(Ctrl=9,  controller = 0x0A, Title="Slider 1"))
  SendPayload(MakePayload(Ctrl=10, controller = 0x0B, Title="Slider 2"))
  SendPayload(MakePayload(Ctrl=11, controller = 0x0C, Title="Slider 3"))
  SendPayload(MakePayload(Ctrl=12, controller = 0x0D, Title="Slider 4"))
  SendPayload(MakePayload(Ctrl=13, controller = 0x0E, Title="Slider 5"))
  SendPayload(MakePayload(Ctrl=14, controller = 0x0F, Title="Slider 6"))
  SendPayload(MakePayload(Ctrl=15, controller = 0x10, Title="Slider 7"))
  SendPayload(MakePayload(Ctrl=16, controller = 0x11, Title="Slider 8"))
  SendPayload(MakePayload(Ctrl=17, controller = 0x12, Title="Slider 9"))
  SendPayload(MakePayload(Ctrl=18, controller = 0x13, Title="Pad 1"))
  SendPayload(MakePayload(Ctrl=19, controller = 0x14, Title="Pad 2"))
  SendPayload(MakePayload(Ctrl=20, controller = 0x15, Title="Pad 3"))
  SendPayload(MakePayload(Ctrl=21, controller = 0x16, Title="Pad 4"))
  SendPayload(MakePayload(Ctrl=22, controller = 0x17, Title="Pad 5"))
  SendPayload(MakePayload(Ctrl=23, controller = 0x18, Title="Pad 6"))
  SendPayload(MakePayload(Ctrl=24, controller = 0x19, Title="Pad 7"))
  SendPayload(MakePayload(Ctrl=25, controller = 0x1A, Title="Pad 8"))
  SendPayload(MakePayload(Ctrl=26, controller = 0x1B, Title="Button 1", btnMode=ButtonMode.Latch))
  SendPayload(MakePayload(Ctrl=27, controller = 0x1C, Title="Button 2", btnMode=ButtonMode.Latch))
  SendPayload(MakePayload(Ctrl=28, controller = 0x1D, Title="Button 3", btnMode=ButtonMode.Latch))
  SendPayload(MakePayload(Ctrl=29, controller = 0x1E, Title="Button 4", btnMode=ButtonMode.Latch))
  SendPayload(MakePayload(Ctrl=30, controller = 0x1F, Title="Transport 1"))
  SendPayload(MakePayload(Ctrl=31, controller = 0x20, Title="Transport 2"))
  SendPayload(MakePayload(Ctrl=32, controller = 0x21, Title="Transport 3"))
  SendPayload(MakePayload(Ctrl=33, controller = 0x22, Title="Transport 4"))
  SendPayload(MakePayload(Ctrl=34, controller = 0x23, Title="Transport 5"))
  SendPayload(MakePayload(Ctrl=35, controller = 0x24, Title="Transport 6"))
  SendPayload(MakePayload(Ctrl=36, controller = 0x25, Title="Transport 7"))
  SendPayload(MakePayload(Ctrl=37, controller = 0x26, Title="Transport 8"))
  SendPayload(MakePayload(Ctrl=38, controller = 0x27, Title="Transport 9"))
  SendPayload(MakePayload(Ctrl=39, controller = 0x28, Title="Pedal 1"))
  SendPayload(MakePayload(Ctrl=40, controller = 0x29, Title="Pedal 2"))
  SendPayload(MakePayload(Ctrl=41, controller = 0x2A, Title="Bend"))
  SendPayload(MakePayload(Ctrl=42, controller = 0x2B, Title="Modulation"))
  SendPayload(MakePayload(Ctrl=43, controller = 0x2C, Title="Aftertouch"))
  SendPayload(MakePayload(msg=Messages.MapTitle, Title="CT-X Map"))
