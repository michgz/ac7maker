#! /bin/usr/python3


# Import some standard modules
import json
import struct
#import operator
import sys

import internal.midifiles

# Import one non-standard module. Can be installed by:
#
#   pip3 install mido
#
#import mido


# Default instrument allocations. Ordered by part number
instruments = [
  {'patch': 0,  'bank_msb': 120},
  {'patch': 0,  'bank_msb': 120},
  {'patch': 33, 'bank_msb': 0},
  {'patch': 0,  'bank_msb': 0},
  {'patch': 25, 'bank_msb': 0},
  {'patch': 27, 'bank_msb': 0},
  {'patch': 49, 'bank_msb': 0},
  {'patch': 61, 'bank_msb': 0}
]


# Table of possible specifications for "conversion_table". 16 possibilities
# are given, corresponding to encodings 0-15. In fact, integers up to
# 255 are accepted by the keyboard, but most of them give glitchy results
# and are probably of no use.
conversions = [
  "Bass Basic",
  "Bass 7th",
  "Basic",
  "Var2",
  "Var3",
  "Var4",
  "7th",
  "Minor",
  "Phrase",
  "Bass Minor",
  "Penta",
  "Intro n-minor",
  "Intro m-minor",
  "Intro h-minor",
  "Intro no Change",
  "Intro dorian"
]

# Table of possible specifications for "inversion". 8 possibilities are
# given, corresponding to encodings 0-7. Only 3 are documented, the 5 
# other integer values are accepted by the keyboard and give potentially
# interesting results.
# TODO: add a way to select the undocumented values.
inversions = [
  "Off",
  "",
  "On",
  "",
  "7th",
  "",
  "",
  ""
]



# Set up a mixer table element for given part number. The file format
# gives us the capability to change all settings for each element also,
# but here just give the elements the same values.
def ac7make_mixer_element(pt, b):
  g = b''
  pt_patch = b['rhythm']['parts'][pt-1].get('patch', -1)
  pt_bank = b['rhythm']['parts'][pt-1].get('bank_msb', -1)
  if pt_patch < 0 or pt_bank < 0:
    # Not specified correctly - use defaults for that part
    pt_patch = instruments[pt-1]['patch']
    pt_bank = instruments[pt-1]['bank_msb']
  g = g + struct.pack('B', pt_patch)
  g = g + struct.pack('B', pt_bank)
  g = g + struct.pack('B', b['rhythm']['parts'][pt-1].get('volume', 100))  # volume
  g = g + struct.pack('B', 64 + b['rhythm']['parts'][pt-1].get('pan', 0))   # pan
  g = g + struct.pack('B', b['rhythm']['parts'][pt-1].get('reverb_send', 40))   # reverb send
  g = g + struct.pack('B', b['rhythm']['parts'][pt-1].get('chorus_send', 0))   # chorus send
  return(g)

def ac7make_mixer(mixers, addr):
  g1 = b'MIXR'
  g2 = b''
  g3 = b''
  number_of_parts = len(mixers)
  if number_of_parts != 96:
    print("Expected 96 mixer parts, got {0}".format(number_of_parts))
    raise Exception
  addr = addr + 10 + 4*number_of_parts
  for mm in mixers:
    g3 = g3 + mm
    g2 = g2 + struct.pack('<I', addr)
    addr = addr + len(mm)
  g1 = g1 + struct.pack('<I', 10 + len(g2) + len(g3))
  g1 = g1 + struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)


# MIDI event to Casio event converter
def ac7make_mid2casio(msg):
  if msg.type == "note_on":
    vel = msg.velocity
    if vel == 0:  # velocity of 0 not allowed in Casio
      vel = 1
    return struct.pack('3B', round(24*msg.time), msg.note, vel)
  elif msg.type == 'note_off':
    return struct.pack('3B', round(24*msg.time), msg.note, 0)
  else:
    return b''

# Determine if the element should be omitted in total from the rhythm. Typically
# this is done for elements 7, 8, 9 & 10 and is possibly for compatibility
# with keyboards with only 2 variations.
def ac7make_element_has_drum(b, el):
  return (b['rhythm']['elements'][el].get('omit', 0) != 1)

def ac7make_element_has_other(b, el):
  return (b['rhythm']['elements'][el].get('omit', 0) != 1)



def ac7make_drum_element(pt, el, b, midi_trks):
  for track in b["rhythm"]["tracks"]:
    if track["part"]==1 or track["part"]==2:
      if track["part"]==(pt+1) and track["element"]==(el+1):
        #midi_file = mido.MidiFile(track["source_file"])
        g = b'\x00\xe5\x00'  # "Start user data" indicator
        #for msg in midi_file:
        #  if msg.type == 'note_on' or msg.type == 'note_off':
        #    if msg.channel == track["source_channel"]:
        #      g += ac7make_mid2casio(msg)
        g += b'\x00\x24\x4b\x0b\x24\x00\x57\x28\x3c\x0f\x28\x00\x53\x24\x48\x15\x24\x00\x44\x28\x40\x0c\x28\x00\x57\xfc\x00'
        #return  g + b'\x00\xfc\x00'
        return g
        
  #if el == 6 or el == 11:
  #  # For some reason, these tracks take an extra E5
  #  return b'\x00\xe5\x00\x80\xff\x04\x00\xfc\x00'
  
  # If we get down to here, no matching input has been found. Just return
  # an empty track that has only two elements:
  # 80 FF 04   -- wait whole length
  # 00 FC 00   -- end of track  
  return b'\x80\xff\x04\x00\xfc\x00'

def ac7make_drum(drums, start_addr):
  g1 = b'DRUM'
  g2 = b''
  g3 = b''
  
  number_of_parts = len(drums)
  addr = start_addr + 10 + 4*number_of_parts
  for dd in drums:
    g3 += dd
    g2 = g2 + struct.pack('<I', addr)
    addr += len(dd)
  g1 = g1 + struct.pack('<I', 10 + len(g2) + len(g3))
  g1 = g1 + struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)


def ac7make_chord_conversion(tk):
  cconv = tk.get("conversion_table", "")
  x = -1
  if cconv != "":
    try:
      x = conversions.index(cconv)
    except ValueError:
      x = -1
  
  # If a conversion has been specified, return it.
  if x >= 0:
    return x

  # No conversion has been specified. Choose a default based on
  # part and element.
  pt_1 = tk["part"]
  el_1 = tk["element"]
  if (el_1 == 1 or el_1 == 6 or el_1 == 7 or el_1 == 12):
    # An intro or outro element
    if (pt_1 == 3):
      # Bass
      return conversions.index("Intro n-minor")
    else:
      # Chords
      return conversions.index("Intro n-minor")
  else:
    # An ordinary variation/fill
    if (pt_1 == 3):
      # Bass
      return conversions.index("Bass Basic")
    else:
      # Chords
      return conversions.index("Basic")


def ac7make_chord_inversion(tk):
  cinv = tk.get("inversion", "")
  x = -1
  if cinv != "":
    try:
      x = inversions.index(cinv)
    except ValueError:
      x = -1
  
  # If an inversion has been specified, return it.
  if x >= 0:
    return x

  # No inversion has been specified. Choose a default value
  return inversions.index("Off")

def ac7make_break_point(tk):
  bkp = tk.get("break_point", -1)
  
  # If a break point has been specified, return it.
  if bkp >= 0 and bkp <= 12:
    return bkp

  # No break point has been specified. Choose a default value
  pt_1 = tk["part"]
  if (pt_1 == 3):
    # Bass
    return 4
  else:
    # Chords
    return 7


def ac7make_starter(tk):
  # Make up the "starter" (first 3 bytes) of a track.
  
  if tk["part"] <= 2:
    # This is a drum part. No starter.
    return b''
    
  x1 = ac7make_chord_conversion(tk)
  x2 = (ac7make_break_point(tk) << 4)                   \
                + (ac7make_chord_inversion(tk) << 1)    \
                + 0x1&tk.get("retrigger", 0)
  
  x3 = 0x7F&tk.get("lowest_note", 0) + (tk.get("f-root", 0)<<7)
  return struct.pack("<3B", x1, x2, x3)


def ac7make_track_data(tk):
  # TODO: read MIDI data for the track
  return b''



def ac7make_time_jump(t):
  return struct.pack('<3B', t%256, 0xFF, t//256)

def ac7make_midi_to_ac7(trk):
  # Changes digested midi data into AC7 track data
  print("Got track of length {0}".format(len(trk)))
  print(trk)
  latest_time = 0
  b = b''
  for evt in trk:
    if evt['event'] == 'note_on':
      v = evt['velocity']
      if v == 0:
        v = 1  # AC7 doesn't allow on velocity of 0
      time_d = round(evt['absolute_time'] - latest_time)
      if time_d > 255:
        b += ac7make_time_jump(time_d)
        time_d = 0
      b += struct.pack('<3B', time_d, evt['note'], v)
      latest_time = evt['absolute_time']
    elif evt['event'] == 'note_off':
      time_d = round(evt['absolute_time'] - latest_time)
      if time_d > 255:
        b += ac7make_time_jump(time_d)
        time_d = 0
      b += struct.pack('<3B', time_d, evt['note'], 0x00)
      latest_time = evt['absolute_time']
  return b






def ac7make_other_element(pt, el, b, midi_trks):
  # A default track that has three elements:
  # 02 70 00   -- something to do with break points, split tables, etc.
  # 80 FF 04   -- wait whole length
  # 00 FC 00   -- end of track
  if (el == 0 or el == 5 or el == 6 or el == 11):
    # An intro or outro element
    if (pt == 0):
      # Bass
      g1 = b'\x0b\x40\x00'
    else:
      # Chords
      g1 = b'\x0b\x70\x00'
    #if el == 6 or el == 11:
    #  g1 += b'\x00\xe5\x00'
  else:
    # An ordinary variation/fill
    if (pt == 0):
      # Bass
      g1 = b'\x00\x40\x00'
    else:
      # Chords
      g1 = b'\x02\x70\x00'
    if midi_trks != None:
      g1 += ac7make_midi_to_ac7(midi_trks[1])  # First non-system track in the array
    #if pt == 2 and el == 1:
      #return b'\x02\x70\x00\x00\xe5\x00\x00\x24\x42\x00\x2b\x53\x00\x30\x47\x00\x34\x3e\x00\x37\x49\x00\x3c\x3a\x00\x34\x3e\x00\x30\x47\x00\x2b\x53\x8a\x37\x00\x01\x2b\x00\x00\x30\x00\x00\x3c\x00\x00\x30\x00\x00\x2b\x00\x02\x34\x00\x00\x34\x00\x01\x24\x00\x2f\x2b\x4f\x01\x37\x44\x01\x30\x4a\x00\x24\x47\x00\x3c\x3d\x00\x34\x3f\x1f\x30\x00\x01\x2b\x00\x01\x37\x00\x01\x24\x00\x00\x3c\x00\x02\x34\x00\x35\x24\x36\x00\x2b\x4c\x01\x37\x44\x00\x34\x3f\x00\x3c\x35\x00\x30\x50\x38\x2b\x00\x00\x37\x00\x00\x30\x00\x01\x34\x00\x01\x3c\x00\x01\x24\x00\x2c\xfc\x00'
  return g1 + b'\x80\xff\x04\x00\xfc\x00'


def ac7make_other(others, start_addr):
  g1 = b'OTHR'
  g2 = b''
  g3 = b''
  
  number_of_parts = len(others)
  addr = start_addr + 10 + 4*number_of_parts
  for oo in others:
    g3 = g3 + oo
    g2 = g2 + struct.pack('<I', addr)
    addr = addr + len(oo)
  g1 = g1 + struct.pack('<I', 10 + len(g2) + len(g3))
  g1 = g1 + struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)


def ac7make_element_atom(in_val, in_str):
  return struct.pack('B', in_val) + struct.pack('B', len(in_str)) + in_str


def ac7make_time_signature(s):
  # Takes a string as input. The following is a complete list of possible
  # inputs:
  #   2/4 3/4 4/4 5/4 6/4 7/4 8/4
  #   2/8 3/8 4/8 5/8 6/8 7/8 8/8 9/8 10/8 11/8 12/8 13/8 14/8 15/8 16/8
  # 
  # TODO: could make a bit more robust
  num = int(s.split('/')[0])
  den = int(s.split('/')[1])
  if num < 2 or num > 16:
    raise Exception
  x = 0x00
  if den == 4:
    if num > 8:
      raise Exception
    x = 0x02
  elif den == 8:
    x = 0x03
  else:
    # Only allowed denominators are 4 or 8
    raise Exception
  return x + 8*num


def ac7make_element(b, elements, start_addr):
  number_of_parts = len(elements)
  if number_of_parts != 12:
    print("Expected 12 elements, got {0}".format(number_of_parts))
    raise Exception
  addr = start_addr + 7 + 4*number_of_parts
  
  # Magic number for "elements"
  g0 = struct.pack('<I', 0x07ffffff)
  
  g2 = b''
  g2 = g2 + b'\x00\x0c'   # Name length (12 bytes)
  # Ensure the name is exactly 8 bytes long, with the final character
  # being a space.
  g2 += b['rhythm'].get('name', "No Name")[:7].ljust(8, ' ').encode('ascii')
  # Now pad with 4 more bytes to get to 12 bytes. We can probably have
  # longer names, but they won't be displayed on the CT-X anyway.
  #
  # The first byte here must be 0x00 (null terminator), others don't seem to matter.
  g2 += b'\x00\x01\x00\x00'
  g2 = g2 + ac7make_element_atom(1, struct.pack('B', ac7make_time_signature(b['rhythm'].get('time_signature', '4/4')))) # Time signature.
  g2 = g2 + ac7make_element_atom(2, struct.pack('B', 120)) # Tempo bpm
  g2 = g2 + ac7make_element_atom(9, struct.pack('B', b['rhythm'].get('volume', 127)))   # Overall volume
  g2 = g2 + ac7make_element_atom(64, struct.pack('B', 23)) # Reverb type. TODO: how does this relate to CT-X numbering?
  g2 = g2 + ac7make_element_atom(65, struct.pack('B', 2)) # Chorus type. TODO: how does this relate to CT-X numbering?
  g2 = g2 + ac7make_element_atom(66, struct.pack('B', 4)) # Delay type. TODO: how does this relate to CT-X numbering?
  
  # The following stuff is optional. I don't know what it is...
  if True:
    g2 = g2 + ac7make_element_atom(17, b'\x06\x01') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x07\x12') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x08\x13') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x09\x22') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x0A\x23') # ??
    g2 = g2 + ac7make_element_atom(17, b'\x0B\x31') # ??

  g2 = g2 + ac7make_element_atom(255, b'') # End

  addr = addr + len(g2)

  # Now add the individual element definitions

  g1 = b''
  g3 = b''
  for ee in elements:
    g3 += ee
    g1 += struct.pack('<I', addr)
    addr = addr + len(ee)
  g0 += struct.pack('<H', 7 + len(g1) + len(g2) + len(g3))
  g0 += struct.pack('B', number_of_parts)
  return g0 + g1 + g2 + g3


def ac7make_track_element(pt):
  if pt <= 1:
    return b'\x0f'  # 0x0F = negative 1
  else:
    return struct.pack('<B', pt-2)

def ac7make_is_drum_part(pt):
  return pt<=2


def ac7maker(b):
  
  elements = []
  mixers = []
  drums = []
  others = []
  
  for el in range(1,13):
    num_trk_el = 0
    e_20 = b''
    e_21 = b''
    e_22 = b''
    for pt in range(1,9):
      num_trk = 0
      for trk in b["rhythm"]["tracks"]:
        if trk.get("element", -1)==el and trk.get("part", -1)==pt:
          print("Got non-empty track at element={0} part={1}".format(el, pt))
          print("File name = ")
          print(trk["source_file"])
          with open(trk["source_file"], "rb") as f3:
            bm = internal.midifiles.midifile_read(f3.read())
          print(bm)
          
          # Found a non-empty track to add. Add it
          e_22 += ac7make_track_element(pt)
    
          if ac7make_is_drum_part(pt):
            e_20 += struct.pack('<H', len(drums) + 0x8000)
            drums.append(ac7make_drum_element(pt, el, b, bm))
          else:
            e_20 += struct.pack('<H', len(others) + 0x8000)
            others.append(ac7make_other_element(pt, el, b, bm))
          
          if num_trk == 0:
            # This is the first track for this element/part combo
            e_21 += struct.pack('<H', len(mixers) + 0x8000)
            mixers.append(ac7make_mixer_element(pt, b))
          else:
            # There's already a mixer for this combo. Just add a filler
            # value
            e_21 += struct.pack('<H', 0xFFFF)

          num_trk += 1
      if num_trk == 0:
        # No tracks for this element/part combination. Add an empty one
        e_22 += ac7make_track_element(pt)
  
        if ac7make_is_drum_part(pt):
          e_20 += struct.pack('<H', len(drums) + 0x8000)
          drums.append(ac7make_drum_element(pt, el, b, None))
        else:
          e_20 += struct.pack('<H', len(others) + 0x8000)
          others.append(ac7make_other_element(pt, el, b, None))
          
        e_21 += struct.pack('<H', len(mixers) + 0x8000)
        mixers.append(ac7make_mixer_element(pt, b))
        
        num_trk += 1
        
      num_trk_el += num_trk
    # Have now processed all the parts & tracks for this element. Complete
    # the element bytestring
    el_00 = b''
    el_00 += ac7make_element_atom(1, b'\x22')  # Time signature
    el_00 += ac7make_element_atom(6, b'\x01')  # Number of measures
    el_00 += ac7make_element_atom(7, struct.pack('<B', num_trk_el))  # Total number of tracks
    el_00 += ac7make_element_atom(0x20, e_20)
    el_00 += ac7make_element_atom(0x21, e_21)
    el_00 += ac7make_element_atom(0x22, e_22)
    el_00 += ac7make_element_atom(0x30, struct.pack('<8B', 0, 0, 0, 0, 0, 0, 0, 0))  # Delay send values
    el_00 += ac7make_element_atom(253, b'')  # Start of AiX-specific data (currently none)
    el_00 += ac7make_element_atom(254, b'')  # Start of CTX-specific data (currently none)
    el_00 += ac7make_element_atom(255, b'')  # End
    elements.append(el_00)


  # Size of the header. 'AC07' plus start address of each block (4 bytes),
  # plus end address (4 bytes)
  addr = 0x1C
  
  g1 = b''
  
  g1 += struct.pack('<I', addr)
  g5 = ac7make_element(b, elements, 0)
  addr += len(g5)
  
  g1 += struct.pack('<I', addr)

  g2 = ac7make_mixer(mixers, addr)

  addr += len(g2)

  g1 += struct.pack('<I', addr)
  g3 = ac7make_drum(drums, addr)
  addr += len(g3)

  g1 += struct.pack('<I', addr)
  g4 = ac7make_other(others, addr)
  addr += len(g4)

  # End-of-list indicator
  g1 += struct.pack('<I', 0xffffffff)

  g1 = b'AC07' + struct.pack('<I', addr) + g1

  return g1 + g5 + g2 + g3 + g4
  
  
# Following https://github.com/shimpe/ac7parser/Ac7CasioEventAnalyzer.py
# Note that '-' as a synonym for flat has been retained, but it leads to
# ambiguity if octave is 1 or -1. Consider removing.

chromatic_scale = [['c', 'b#', 'dbb', 'd--'],  # one row contains all synonyms (i.e. synonym for our purpose)
                   ['c#', 'bx', 'db', 'd-'],
                   ['d', 'cx', 'ebb', 'e--'],
                   ['d#', 'eb', 'e-', 'fbb', 'f--'],
                   ['e', 'dx', 'fb', 'f-'],
                   ['f', 'e#', 'gbb', 'g--'],
                   ['f#', 'ex', 'gb', 'g-'],
                   ['g', 'fx', 'abb', 'a--'],
                   ['g#', 'ab', 'a-'],
                   ['a', 'gx', 'bbb', 'b--'],
                   ['a#', 'bb', 'b-', 'cbb', 'c--'],
                   ['b', 'ax', 'cb', 'c-']]

corner_case_octave_lower = {"b#", "bx"}
corner_case_octave_higher = {"cb", "c-", "cbb", "c--"}


def read_music(f):
  dd = []
  while True:
    s = f.readline()
    if not s:
      break
    h1 = s.split()
    if len(h1) != 4:
      raise Exception
    d = dict()
    vel = int(h1[2])
    if vel == 0:
      # The Casio format doesn't allow 0 velocity (but MIDI does!)
      raise Exception
    d['velocity'] = vel

    u = h1[0].split('.')
    if len(u) == 2:
      d['time'] = 24*(4*(int(u[0]) -1) + int(u[1]) -1)
    elif len(u) == 3:
      d['time'] = 24*(4*(int(u[0]) -1) + int(u[1]) -1) + int(u[2])
    else:
      raise Exception
      
    u = h1[3].split('.')
    if len(u) == 1:
      d['duration'] = 24*int(u[0])
    elif len(u) == 2:
      d['duration'] = 24*int(u[0]) + int(u[1])
    else:
      raise Exception

    if h1[1].endswith("-1"):
      octave = -1
      s = h1[1][0:-2]
    else:
      octave = int(h1[1][-1:])
      s = h1[1][0:-1]
    
    n = 0
    note = -2
    for t in chromatic_scale:
      if s in t:
        note = n
      n = n + 1
    if note == -2:
      # Not found
      raise Exception
    
    if s in corner_case_octave_lower:
      octave += 1
    elif s in corner_case_octave_higher:
      octave -= 1
    d['pitch'] = note + (octave + 1)*12

    # Add the note-on event, making a deep copy
    dd.append(dict(d))
    # Now add the note-off event!
    d['velocity'] = 0
    d['duration'] = 0
    dd.append(d)
  return sorted(dd, key=operator.itemgetter('time'))





#
# USAGE:
#  python3 ac7maker.py <input .json file> [ <output .ac7 file> ]
#


if __name__=="__main__":
  if len(sys.argv) < 2:
    print("Returning : no input")
    # No input, nothing to do
  elif len(sys.argv) == 2:
    # No output filename; send to standard out
    with open(sys.argv[1], "r") as f1:
      b = json.load(f1)
    sys.stdout.write(str(ac7maker(b), sys.stdout.encoding))
  else:
    # Has an output filename. Write to it.
    with open(sys.argv[1], "r") as f1:
      b = json.load(f1)
    with open(sys.argv[2], "wb") as f2:
      f2.write(ac7maker(b))

