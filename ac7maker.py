#! /bin/usr/python3


# Import some standard modules
import json
import struct
import os
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

# Table of values for the 0x40 atom related to CT-X3000 names for the reverb
# setting. Note that values aren't all unique -- there's more we can do to specify
# the precise reverb effect, but this is a good first attempt.
# May be expanded later to cover all CT-X5000 names
reverb_def = {
  "Off"         : -1,
  "Room 1"      : 0x00,
  "Room 2"      : 0x01,
  "Room 3"      : 0x01,
  "Room 4"      : 0x10,
  "Room 5"      : 0x11,
  "Large Room1" : 0x0A,
  "Large Room2" : 0x0B,
  "Hall 1"      : 0x03,
  "Hall 2"      : 0x04,
  "Hall 3"      : 0x17,
  "Hall 4"      : 0x18,
  "Hall 5"      : 0x19,
  "Hall 6"      : 0x1A,
  "Stadium 1"   : 0x0C,
  "Stadium 2"   : 0x0D,
  "Stadium 3"   : 0x1F,
  "Plate 1"     : 0x05,
  "Plate 2"     : 0x08,
  "Delay"       : 0x06,
  "Pan Delay"   : 0x07,
  "Long Delay 1" : 0x0E,
  "Long Delay 2" : 0x0F,
  "Church"      : 0x16,
  "Cathedral"   : 0x1E
}

# Table of values for the 0x41 atom related to CT-X3000 names for the chorus
# setting. Note that values aren't all unique -- there's more we can do to specify
# the precise chorus effect, but this is a good first attempt.
# May be expanded later to cover all CT-X5000 names
chorus_def = {
  "Tone"        : 0x02,
  "Chorus 1"    : 0x00,
  "Chorus 2"    : 0x01,
  "Chorus 3"    : 0x01,
  "Chorus 4"    : 0x03,
  "FB Chorus"   : 0x04,
  "Deep Chorus" : 0x0F,
  "Flanger 1"   : 0x05,
  "Flanger 2"   : 0x06,
  "Flanger 3"   : 0x07,
  "Flanger 4"   : 0x08,
  "Short Delay 1" : 0x09,
  "Short Delay 2" : 0x0A
}

# Table of values for the 0x42 atom related to CT-X3000 names for the delay
# setting.
delay_def = {
  "Tone"              : -1,  # not possible? May just need to set all send values to 0
  "Short 1"           : 0,
  "Short 2"           : 1,
  "Echo"              : 2,
  "Tempo Sync Short"  : 3,
  "Tempo Sync Middle" : 4,
  "Tempo Sync Long"   : 5,
  "Ambience"          : 6,
  "Mid 1"             : 7,
  "Mid 2"             : 8,
  "Long 1"            : 9,
  "Long 2"            : 10,
  "Mid Pan"           : 16,
  "Long Pan 1"        : 17,
  "Long Pan 2"        : 18,
  "Long Pan 3"        : 19
}

def ac7make_delay_send_vector(el, b):
  # Returns a vector of 8 bytes with the delay send values for all the parts. The
  # file format gives us the capability to change all settings for each element also,
  # but here just give the elements the same values (element number "el" is ignored)
  
  g = b''
  for pt in range(1,9):
    g += struct.pack('B', b['rhythm']['parts'][pt-1].get('delay_send', 0))
  return g


def ac7make_mixer_element(pt, b):
  # Set up a mixer table element for given part number. The file format
  # gives us the capability to change all settings for each element also,
  # but here just give the elements the same values.
  
  g = b''
  pt_patch = b['rhythm']['parts'][pt-1].get('patch', -1)
  pt_bank = b['rhythm']['parts'][pt-1].get('bank_msb', -1)
  if pt_patch < 0 or pt_bank < 0:
    # Not specified correctly - use defaults for that part
    pt_patch = instruments[pt-1]['patch']
    pt_bank = instruments[pt-1]['bank_msb']
  g += struct.pack('B', pt_patch)
  g += struct.pack('B', pt_bank)
  g += struct.pack('B', b['rhythm']['parts'][pt-1].get('volume', 127))  # volume
  g += struct.pack('B', 64 + b['rhythm']['parts'][pt-1].get('pan', 0))   # pan
  g += struct.pack('B', b['rhythm']['parts'][pt-1].get('reverb_send', 40))   # reverb send
  g += struct.pack('B', b['rhythm']['parts'][pt-1].get('chorus_send', 0))   # chorus send
  return(g)

def ac7make_mixer(mixers, addr):
  # Make a "MIXR" block from a vector of data strings
  
  g1 = b'MIXR'
  g2 = b''
  g3 = b''
  number_of_parts = len(mixers)
  if number_of_parts != 96:
    raise Exception("Expected 96 mixer parts, got {0}".format(number_of_parts))
  addr = addr + 10 + 4*number_of_parts
  for mm in mixers:
    g3 = g3 + mm
    g2 = g2 + struct.pack('<I', addr)
    addr = addr + len(mm)
  g1 = g1 + struct.pack('<I', 10 + len(g2) + len(g3))
  g1 = g1 + struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)

# Determine if the element should be omitted in total from the rhythm. Typically
# this is done for elements 7, 8, 9 & 10 and is possibly for compatibility
# with keyboards with only 2 variations.
def ac7make_element_has_drum(b, el):
  return (b['rhythm']['elements'][el].get('omit', 0) != 1)

def ac7make_element_has_other(b, el):
  return (b['rhythm']['elements'][el].get('omit', 0) != 1)



def ac7make_midi_to_ac7(trk, end_time):
  # Change the digested midi data into AC7 track data
  latest_time = 0
  b = b''
  for evt in trk:
    if evt['event'] == 'note_on':
      v = evt['velocity']
      if v == 0:
        v = 1  # AC7 doesn't allow on velocity of 0
      time_d = round(4.0*(evt['absolute_time'] - latest_time))
      if time_d > 255:
        b += ac7make_time_jump(time_d)
        time_d = 0
      b += struct.pack('<3B', time_d, evt['note'], v)
      latest_time = evt['absolute_time']
    elif evt['event'] == 'note_off':
      time_d = round(4.0*(evt['absolute_time'] - latest_time))
      if time_d > 255:
        b += ac7make_time_jump(time_d)
        time_d = 0
      b += struct.pack('<3B', time_d, evt['note'], 0x00)
      latest_time = evt['absolute_time']
    else:
      d = ac7make_track_event(evt)
      if len(d)==2:
        time_d = round(4.0*(evt['absolute_time'] - latest_time))
        if time_d > 255:
          b += ac7make_time_jump(time_d)
          b += b'\x00' + d
        else:
          b += struct.pack('<B', time_d) + d
        latest_time = evt['absolute_time']
      
  time_d = end_time - round(4.0*latest_time)
  if time_d > 255:
    b += ac7make_time_jump(time_d)
    time_d = 0
  b += struct.pack('<3B', time_d, 0xFC, 0x00) # End-of-track indicator
  return b

def ac7make_get_track(tracks, ch):
  # Select a track from an array of tracks by matching the MIDI channel number.
  # This is appropriate for Type I MIDI files where each MIDI channel has its
  # own track. It's not explicitly checked that the MIDI is structured in that
  # way, if not then behaviour will be undefined.
  #
  
  for trk in tracks:
    for evt in trk:
      if evt['event']=='note_on' and evt['channel']==ch:
        # Have found the track!
        return trk
  # If get here, have not found any track
  return None

def ac7make_drum_element(pt, el, total_midi_clks, midi_trks, trk_ch = -1):
  # Create a single track to go into the "DRUM" section of the AC7 file
  #
  
  g1 = b''
  if midi_trks != None:
    midi_trk = ac7make_get_track(midi_trks, trk_ch)
  else:
    midi_trk = None
  if midi_trk != None:  
    g1 += b'\x00\xe5\x00'  # Optional. This makes the track editable, probably a good thing..
    # Translate total time from midi clocks (24 per crotchet) to AC7 clocks (96 per crotchet)
    g1 += ac7make_midi_to_ac7(midi_trk, round(4.0*total_midi_clks))
  else:
    # A default value that means "skip to track end time" (a skip of 0x0480 is for some reason
    # interpreted in that way) followed by "end of track".
    g1 += b'\x80\xff\x04\x00\xfc\x00'
  return g1


def ac7make_drum(drums, start_addr):
  # Create the "DRUM" section from an array of drum tracks
  #
  
  g1 = b'DRUM'
  g2 = b''
  g3 = b''
  
  number_of_parts = len(drums)
  addr = start_addr + 10 + 4*number_of_parts
  for dd in drums:
    g2 += struct.pack('<I', addr)
    addr += len(dd)
    g3 += dd
  g1 += struct.pack('<I', 10 + len(g2) + len(g3))
  g1 += struct.pack('<H', number_of_parts)
  return (g1 + g2 + g3)


def ac7make_chord_conversion(tk):
  # Return a chord conversion (numerical value 0-15) to use for a track. If a
  # valid conversion is explicitly specified then use that, otherwise choose an
  # appropriate default for the part and element.
  #
  # See above for a list of possible specification values (they are strings)
  #
  
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
  # Return a chord inversion (numerical value 0-7) to use for a track. If a
  # valid inversion is explicitly specified then use that, otherwise choose an
  # appropriate default for the part and element.
  #
  # See above for a list of possible specification values (they are strings)
  #
  
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
  # Return a chord break point (numerical value 0-11) to use for a track. If a
  # valid break point is explicitly specified then use that, otherwise choose an
  # appropriate default for the part and element.
  #
  # The break point is simply a number. I think 0 corresponds to "C", 1 to "C#",
  # etc.
  #
  
  bkp = tk.get("break_point", -1)
  
  # If a break point has been specified, return it.
  if bkp >= 0 and bkp < 12:
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
  # Make up the "starter" (first 3 bytes) of a Other track.
  #
  
  if tk["part"] <= 2:
    # This is a drum part. No starter.
    return b''
    
  x1 = ac7make_chord_conversion(tk)
  x2 = (ac7make_break_point(tk) << 4)                   \
                + (ac7make_chord_inversion(tk) << 1)    \
                + 0x1&tk.get("retrigger", 0)
  
  x3 = 0x7F&tk.get("lowest_note", 0) + (tk.get("f-root", 0)<<7)
  return struct.pack("<3B", x1, x2, x3)


def ac7make_time_jump(t):
  # Make a "time-jump" rhythm event. Input is in units of AC7 ticks (96 per crotchet)
  #
  
  return struct.pack('<3B', t%256, 0xFF, t//256)


def ac7make_track_event(e):
  # Make a rhythm event from a digested MIDI event (excluding note-on/note-off)
  #
  
  if e['event'] == 'pitch_bend':
    if e['bend'] >= 0:
      return struct.pack('<2B', 0x8E, e['bend']//64)
    else:
      return struct.pack('<2B', 0x8E, e['bend']//64+256)
  elif e['event'] == 'control_change':
    if e['controller'] == 0x01:  # Modulation
      return struct.pack('<2B', 0xB0, e['value'])
    elif e['controller'] == 0x0B:  # Expression
      return struct.pack('<2B', 0xB5, e['value'])
    elif e['controller'] == 0x4A:  # Filter control
      return struct.pack('<2B', 0xBA, e['value'])
    elif e['controller'] == 0x47:  # Filter control
      return struct.pack('<2B', 0xBB, e['value'])
    elif e['controller'] == 0x49:  # Attack time
      return struct.pack('<2B', 0xBC, e['value'])
    elif e['controller'] == 0x48:  # Release time
      return struct.pack('<2B', 0xBD, e['value'])
    # There are some other event types that are seen in AC7 tracks which
    # have not been fully identified. May add later. Also, there are tempo
    # changes which are quite tricky
  elif e['event'] == 'registered_param':
    if e['parameter'] == 0x0000:   # Pitch bend range
      return struct.pack('<2B', 0xB9, e['value']//128)

  # If we get here, no recognised events. Return an empty string
  return b''


def ac7make_other_element(pt, el, trk, total_midi_clks, midi_trks, trk_ch=-1):
  # Create a Casio-style track for Other (i.e. non-Drum). That will start with a
  # 3-byte "starter" followed by track events
  #
  
  if trk != None:
    g1 = ac7make_starter(trk)
  else:
    g1 = ac7make_starter({"part": pt, "element": el})
  if midi_trks != None:
    midi_trk = ac7make_get_track(midi_trks, trk_ch)
  else:
    midi_trk = None
  if midi_trk != None:
    g1 += b'\x00\xe5\x00'  # Optional. This makes the track editable, probably a good thing..
    # Translate total time from midi clocks (24 per crotchet) to AC7 clocks (96 per crotchet)
    g1 += ac7make_midi_to_ac7(midi_trk, round(4.0*total_midi_clks))
  else:
    g1 += b'\x80\xff\x04\x00\xfc\x00'
  return g1


def ac7make_other(others, start_addr):
  # Make an "OTHR" block given a vector of data strings
  #
  
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
  # Make an "atom" (i.e. type byte, length byte, then a string of data bytes)
  
  return struct.pack('B', in_val) + struct.pack('B', len(in_str)) + in_str


def ac7make_time_signature(s):
  # Takes a string as input. The following is a complete list of possible
  # inputs:
  #   2/4 3/4 4/4 5/4 6/4 7/4 8/4
  #   2/8 3/8 4/8 5/8 6/8 7/8 8/8 9/8 10/8 11/8 12/8 13/8 14/8 15/8 16/8
  # 
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
  # Take a vector of "ELMT" block and combine them as they will be in the AC7 file
  
  number_of_parts = len(elements)
  if number_of_parts != 12:
    raise Exception("Expected 12 elements, got {0}".format(number_of_parts))
  addr = start_addr + 7 + 4*number_of_parts
  
  # Magic number for "elements"
  g0 = struct.pack('<I', 0x07ffffff)
  
  g2 = b''
  g2 += b'\x00\x0c'   # Name length (12 bytes)
  # Ensure the name is exactly 8 bytes long, with the final character
  # being a space.
  g2 += b['rhythm'].get('name', "No Name")[:7].ljust(8, ' ').encode('ascii')
  # Now pad with 4 more bytes to get to 12 bytes. We can probably have
  # longer names, but they won't be displayed on the CT-X anyway.
  #
  # The first byte here must be 0x00 (null terminator), others don't seem to matter.
  g2 += b'\x00\x01\x00\x00'
  g2 += ac7make_element_atom(1, struct.pack('B', ac7make_time_signature(b['rhythm'].get('time_signature', '4/4')))) # Time signature. This probably
  # isn't used for anything
  g2 += ac7make_element_atom(2, struct.pack('B', 120)) # Tempo bpm. Ignored by the keyboard
  # Volume
  v = b['rhythm'].get('volume', -1)
  if v >= 0:
    g2 += ac7make_element_atom(9, struct.pack('B', v))   # Overall volume
  # Reverb
  v = reverb_def.get(b['rhythm'].get('reverb_type', ''), -1)
  if v >= 0:
    g2 += ac7make_element_atom(64, struct.pack('B', v)) # Reverb type
  # Chorus
  v = chorus_def.get(b['rhythm'].get('chorus_type', ''), -1)
  if v >= 0:
    g2 += ac7make_element_atom(65, struct.pack('B', v)) # Chorus type
  # Delay
  v = delay_def.get(b['rhythm'].get('delay_type', ''), -1)
  if v >= 0:
    g2 += ac7make_element_atom(66, struct.pack('B', v)) # Delay type
  
  # The following stuff is optional. I don't know what it is...
  if True:
    g2 += ac7make_element_atom(17, b'\x06\x01') # ??
    g2 += ac7make_element_atom(17, b'\x07\x12') # ??
    g2 += ac7make_element_atom(17, b'\x08\x13') # ??
    g2 += ac7make_element_atom(17, b'\x09\x22') # ??
    g2 += ac7make_element_atom(17, b'\x0A\x23') # ??
    g2 += ac7make_element_atom(17, b'\x0B\x31') # ??

  g2 += ac7make_element_atom(255, b'') # End

  addr = addr + len(g2)

  # Now add the individual element definitions

  g1 = b''
  g3 = b''
  for ee in elements:
    g3 += b'ELMT' + struct.pack('<H', 6 + len(ee)) + ee
    g1 += struct.pack('<I', addr)
    addr = addr + 6 + len(ee)
  g0 += struct.pack('<H', 7 + len(g1) + len(g2) + len(g3))
  g0 += struct.pack('B', number_of_parts)
  return (g0 + g1 + g2 + g3)


def ac7make_is_drum_part(pt):
  # Returns True if the part number indicates a drum part
  
  return pt<=2

def ac7make_dsp_effect_parameter_count(ef):
  # Returns the number of effect parameters given the effect number
  # 13 is the maximum so for now are just returning that
  #

  return 13

def ac7make_track_element(pt):
  # Returns the track number nibble (bottom 4 bits of the track byte)
  #
  
  if pt <= 1:
    return 0x0f  # 0x0F = negative 1
  else:
    return pt-2

def ac7make_track_flag(trk):
  # Returns the flag nibble (top 4 bits of the track byte)
  #
  
  pt = trk.get("part", -1)
  flag = 0x00  # Default : both major and minor
  major = trk.get("with_major", 1)
  minor = trk.get("with_minor", 1)
  if major and not minor:
    flag = 0x80
  elif not major and minor:
    flag = 0xA0
  elif not major and not minor:
    raise Exception("Both with_major and with_minor set to 0 in track for part {0}. At least one must be 1!".format(pt))
  if not (pt >= 1 and pt <= 2):
    # A melody part. "chord_sync" defaults to 1
    if trk.get("chord_sync", -1) == 0:
      flag |= 0x10
  else:
    # For drum parts, "chord_sync" operates the other way round. I'm not yet sure if this has
    # any effect on drum parts or not.
    if trk.get("chord_sync", -1) == 1:
      flag |= 0x10
  return flag

def ac7maker(b):
  # The main routine. Create the different parts of the AC7 file (header, ELMT,
  # MIXR, DRUM, OTHER) and return them concatenated together.
  
  elements = []
  mixers = []
  drums = []
  others = []
  
  for el in range(1,13):
    # First pass: find a time signature, tempo and measure count for the element
    tempo = 120
    max_absolute_time = 0
    time_sig = {"numerator": 0, "log_denominator": 0}
    for trk in b["rhythm"]["tracks"]:
      if trk.get("element", -1)==el:
        with open(os.path.join(b.get("input_dir", ""), trk["source_file"]), "rb") as f3:
          mdata = internal.midifiles.midifile_read(f3.read())
        for mtrk in mdata:
          for evt in mtrk:
            if evt["absolute_time"] > max_absolute_time:
              max_absolute_time = evt["absolute_time"]
            
            if time_sig["numerator"] == 0 and evt["event"] == "time_signature":
              time_sig["numerator"] = evt["numerator"]
              time_sig["log_denominator"] = evt["log_denominator"]
    if max_absolute_time == 0:  # (if not, probably have no tracks associated)
      # Use some default values
      max_absolute_time = 24.0*4.0
      time_sig["numerator"] = 4
      time_sig["log_denominator"] = 2
    else:
      if time_sig["numerator"] == 0 or time_sig["log_denominator"] == 0:
        raise Exception("Time signature not detected in non-empty element {0}. Make sure that a MIDI file associated with this element contains a time signature specifier".format(el))

    # Second pass: change requested tracks to Casio format (from MIDI)
    num_trk_el = 0
    e_20 = b''
    e_21 = b''
    e_22 = b''
    for pt in range(1,9):
      num_trk = 0
      for trk in b["rhythm"]["tracks"]:
        if trk.get("element", -1)==el and trk.get("part", -1)==pt:
          with open(os.path.join(b.get("input_dir", ""), trk["source_file"]), "rb") as f3:
            mdata = internal.midifiles.midifile_read(f3.read())
          
          # Found a non-empty track to add. Add it
          e_22 += struct.pack('<B', ac7make_track_element(pt) + ac7make_track_flag(trk))
    
          if ac7make_is_drum_part(pt):
            e_20 += struct.pack('<H', len(drums) + 0x8000)
            drums.append(ac7make_drum_element(pt, el, max_absolute_time, mdata, trk["source_channel"]))
          else:
            e_20 += struct.pack('<H', len(others) + 0x8000)
            others.append(ac7make_other_element(pt, el, trk, max_absolute_time, mdata, trk["source_channel"]))
          
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
        e_22 += struct.pack('<B', ac7make_track_element(pt))
  
        if ac7make_is_drum_part(pt):
          e_20 += struct.pack('<H', len(drums) + 0x8000)
          drums.append(ac7make_drum_element(pt, el, max_absolute_time, None))
        else:
          e_20 += struct.pack('<H', len(others) + 0x8000)
          others.append(ac7make_other_element(pt, el, None, max_absolute_time, None))
          
        e_21 += struct.pack('<H', len(mixers) + 0x8000)
        mixers.append(ac7make_mixer_element(pt, b))
        
        num_trk += 1
        
      num_trk_el += num_trk
    # Have now processed all the parts & tracks for this element. Complete
    # the element bytestring
    el_00 = b''
    el_00 += ac7make_element_atom(1, struct.pack('<B', (time_sig["numerator"] << 3) | time_sig["log_denominator"])) # Time signature
    num_measures = 1
    if time_sig["log_denominator"] == 2:  # crotchet time
      num_measures = round( max_absolute_time / (24.0*float(time_sig["numerator"] )))
    elif time_sig["log_denominator"] == 3:  # quaver time
      num_measures = round( max_absolute_time / (12.0*float(time_sig["numerator"] )))
    else:
      raise Exception("Invalid time signature in element {0}: specified {1}/2^{2}, should be 2/4 to 4/4 or 2/8 to 16/8 only".format(el, time_sig["numerator"], time_sig["log_denominator"]))
    el_00 += ac7make_element_atom(6, struct.pack('<B', num_measures))  # Number of measures
    el_00 += ac7make_element_atom(7, struct.pack('<B', num_trk_el))  # Total number of tracks
    el_00 += ac7make_element_atom(0x20, e_20)
    el_00 += ac7make_element_atom(0x21, e_21)
    el_00 += ac7make_element_atom(0x22, e_22)
    el_00 += ac7make_element_atom(0x30, ac7make_delay_send_vector(el, b))  # Delay send values
    el_00 += ac7make_element_atom(253, b'')  # Start of AiX-specific data
    # Add any 36 atoms (DSP)
    for pp in b["rhythm"]["parts"]:
      tf = pp.get("tone_file", "")
      pn = pp["part"]
      if tf != "":
        tn = b''
        with open(os.path.join(b.get("input_dir", ""), tf), "rb") as f11:
          tn = f11.read()
        if len(tn) >= 456:
          # First add a "clear DSP chain" instruction
          el_00 += ac7make_element_atom(0x36, struct.pack('<4B', 0, pn - 1 + 8, 0, 0))
          for j in range(4):  # Number of effects to include
            dsp_ef = tn[0x156 + j*0x12]
            if dsp_ef != 0 and dsp_ef <= 0x1f:
              # Next define the DSP effect
              el_00 += ac7make_element_atom(0x36, struct.pack('<4B', 0, pn - 1 + 8, j, dsp_ef))
              # Now add all the parameters
              for i in range(ac7make_dsp_effect_parameter_count(dsp_ef)):
                el_00 += ac7make_element_atom(0x36, struct.pack('<6B', 1, pn - 1 + 8, j, dsp_ef, i, tn[0x156 + j*0x12 + 2 +i]))
    el_00 += ac7make_element_atom(254, b'')  # Start of CTX-specific data
    # Add "3x"-style atoms. This is very rudimentary so far, and only allows one "33" and one "35" atom per
    # element.
    # Add any 33 atoms
    h = b["rhythm"]["elements"][el-1].get("var_33", [])
    if len(h) == 7:
      el_00 += ac7make_element_atom(0x33, struct.pack('<7B', h[0], h[1], h[2], h[3], h[4], h[5], h[6]))  # ?? What does this do?
    # Add any 35 atoms
    h = b["rhythm"]["elements"][el-1].get("var_35", [])
    if len(h) == 6:
      el_00 += ac7make_element_atom(0x35, struct.pack('<6B', h[0], h[1], h[2], h[3], h[4], h[5]))  # Tone control parameters
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

  return (g1 + g5 + g2 + g3 + g4)



#
# USAGE:
#  python3 ac7maker.py <input .json file>
#  python3 ac7maker.py   <   <pipe>
#


if __name__=="__main__":
  if sys.version_info[0] < 3:
    raise Exception("Only for use with Python 3! (Found {0}.{1})".format(sys.version_info[0], sys.version_info[1]))
  if len(sys.argv) < 2:
    if not sys.stdin.isatty():
      # sysin has some data being piped in. In this case, we don't know where the
      # JSON is stored so MIDI files are just searched for in the current directory.
      # If they're not there, then this won't work - use the named file method instead
      # in that case
      sys.stdout.buffer.write(ac7maker(sys.stdin.read()))
    else:
      sys.stderr.write("Returning : no input\n")
      # No input, nothing to do
      sys.exit(0)
  elif len(sys.argv) == 2:
    # write to standard out
    with open(sys.argv[1], "r") as f1:
      b = json.load(f1)
    b["input_dir"] = os.path.dirname(sys.argv[1])
    sys.stdout.buffer.write(ac7maker(b))

