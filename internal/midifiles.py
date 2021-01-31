# A library of functions for reading, parsing and writing MIDI files.

import struct



# Implement a "running status" variable. This is required for compatibility with
# MIDI files as rendered by Traktion Waveform. It's not clear from reading online
# whether this is part of the official MIDI spec *for files* (as opposed to
# streamed data, where it definitely is part of the official spec), and it seems
# to be inconsistently supported by other software. May as well support it here.
#
running_status = 0


def consume_midi_time(b, pos):
  p = pos
  v = 0
  while True:
    x = b[p]
    p += 1
    v = 0x80*v + (0x7F&x)
    if (x&0x80)==0x00:
      # End
      return (v, p)
  #print("Got to end!")

# Variables used for tracking RPNs
c100 = []
c101 = []
c6 = []
c38 = []

def clear_midi_events():
  global c100
  global c101
  global c6
  global c38

  c100 = [-1]*16
  c101 = [-1]*16
  c6 = [-1]*16
  c38 = [-1]*16

def consume_midi_event(b, pos):
  global c100
  global c101
  global c6
  global c38
  global running_status

  p = pos
  evt = b[p]
  
  if evt >= 0xF0:
      # Fx cancels running status
      running_status = 0
      p += 1
  elif evt <= 0x7F:
      if running_status >= 0x80:
          # Use the running status
          evt = running_status
      else:
          # This is an error condition! The exception at the end of this function
          # will be triggered.
          pass
  else:
      # Update the running status
      running_status = evt
      p += 1
  
  
  # Records of the "Registered parameters" entry
  if evt == 0xFF:
    # Meta-event
    n = b[p+1]
    if b[p+0]==0x51 and n==3:
      # Tempo
      x = 0x10000*b[p+2] + 0x100*b[p+3] + b[p+4]
      tempo = round(60000000.0 / float(x))
      # Note this is tempo per quarter note. Depending on the time signature,
      # may need to adjust to eighth notes.
      e = {'event':'tempo_change', 'absolute_time':0, 'value':tempo}
      return (e, p+2+n)
    elif b[p+0]==0x58 and n==4:
      e = {'event':'time_signature', 'absolute_time':0, 'numerator':b[p+2], 'log_denominator':b[p+3]}
      return (e, p+2+n)
    elif b[p+0]==0x2F and n==0:
      e = {'event':'track_end', 'absolute_time':0}
      return (e, p+2+n)
    else:
      e = {'event':'metadata', 'absolute_time':0, 'data': b''}
    return (e, p+2+n)
  elif evt == 0xF0:
    # System exclusive
    n = b[p+0]
    e = {'event':'sysex', 'absolute_time':0, 'data': b''}
    return (e, p+1+n)
  else:
    if evt&0xF0 == 0xB0:
      # Controller
      ch = evt&0x0F
      if b[p+0] == 100:
        c100[ch] = b[p+1]
      elif b[p+0] == 101:
        c101[ch] = b[p+1]
      elif b[p+0] == 6:
        c6[ch] = b[p+1]
      elif b[p+0] == 38:
        c38[ch] = b[p+1]
      else:
        e = {'event':'control_change', 'absolute_time':0, 'channel':ch+1, 'controller':b[p+0], 'value':b[p+1]}
        return (e, p+2)
      if c100[ch]>=0 and c101[ch]>=0 and c6[ch]>=0 and c38[ch]>=0: # TODO: is 38 optional?
        e = {'event':'registered_param', 'absolute_time':0, 'channel':ch+1, 'parameter':c100[ch]+128*c101[ch], 'value':c38[ch]+128*c6[ch]}
        c100[ch] = -1
        c101[ch] = -1
        c6[ch] = -1
        c38[ch] = -1
        return (e, p+2)
      return (None, p+2)
    elif evt&0xF0 == 0xC0:
      # Patch change
      e = {'event':'patch_change', 'absolute_time':0, 'channel':(evt&0x0F)+1, 'patch':b[p+0]}
      return (e, p+1)
    elif evt&0xF0 == 0x80:
      # Note off
      e = {'event':'note_off', 'absolute_time':0, 'channel':(evt&0x0F)+1, 'note':b[p+0], 'velocity':b[p+1]}
      return (e, p+2)
    elif evt&0xF0 == 0x90:
      # Note on
      e = {'event':'note_on', 'absolute_time':0, 'channel':(evt&0x0F)+1, 'note':b[p+0], 'velocity':b[p+1]}
      return (e, p+2)
    elif evt&0xF0 == 0xE0:
      # Pitch bend. Record it as a signed integer, values -0x2000 -- +0x1FFF
      e = {'event':'pitch_bend', 'absolute_time':0, 'channel':(evt&0x0F)+1, 'bend':128*b[p+0]+(127&b[p+1])-0x2000}
      return (e, p+2)
    elif evt&0xF0 == 0xD0:
      # Channel pressure. Not handled, but don't fail because of this.
      return (None, p+1)
    
  raise Exception("Unknown event {0:02X}".format(evt))


def process_track(b, division):
    global running_status
    
    clear_midi_events()
    
    pos = 0
    total_time = 0
    running_status = 0
    trk = []
    while pos < len(b):
    
      (c, pos) = consume_midi_time(b, pos)
      (d, pos) = consume_midi_event(b, pos)
      total_time += c
      if d != None:
        # Change time to MIDI clocks (24 per crotchet).
        d['absolute_time'] = (24.0 / float(division)) * float(total_time)
        trk.append(d)
    return trk




def midifile_read(b):
  pos = 0
  if b[pos+0:pos+4] != b'MThd':
    # Bad input
    raise Exception("Expected 'MThd' at position {0}, got '{1}'".format(pos, b[pos+0:pos+4]))
    return b''
  x = struct.unpack('>I', b[pos+4:pos+8])[0]  # Length of header
  num_trks = struct.unpack('>H', b[pos+10:pos+12])[0]  # Number of tracks in file
  division = struct.unpack('>H', b[pos+12:pos+14])[0]  # Number of ticks per quarter note (1 quarter note = 24 MIDI clocks)
  
  trks = []
  
  pos += 8 + x
  
  for t in range(num_trks):
    if b[pos+0:pos+4] != b'MTrk':
      # Bad input
      raise Exception("Expected 'MTrk' at position {0}, got '{1}'".format(pos, b[pos+0:pos+4]))
      return b''
    x = struct.unpack('>I', b[pos+4:pos+8])[0]  # Length of track
    trk = process_track(b[pos+8:pos+8+x], division)
    
    pos += 8 + x
    
    trks.append(trk)
    
  return trks
    





if __name__=="__main__":
  with open("MLTREC10.MID", "rb") as f1:
    b = f1.read()
  midifile_read(b)
