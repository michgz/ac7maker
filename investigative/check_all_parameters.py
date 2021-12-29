
# pip install python-rtmidi
import rtmidi


import sys
import logging
import datetime
import random
import struct
import time



# Define the device ID. Constructed as follows:
#    0x44       Manufacturer ID ( = Casio)
#    0x19 0x01  Model ID ( = CT-X3000 or CT-X5000)
#    0x7F       Device. This is a "don't care" value
#
DEVICE_ID = b"\x44\x19\x01\x7F"


have_got_resp = False

def main():
  
    global have_got_resp

    #rtmidi_version = "Unknown"

    #if sys.version_info[0]>=3 and sys.version_info[1]>=8:
    #    # https://stackoverflow.com/a/32965521/4708963
    #    from importlib.metadata import version
    #    rtmidi_version = version("rtmidi_python")
    
    rtmidi_version = rtmidi.__version__
    

    # Set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('log_{0:07d}_{1}.txt'.format( random.randint(0, 9999999), datetime.datetime.now().strftime("%Y%m%d%H%M%S") ))
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    
    
    # Start the program
    logger.info("Python version:\n" + sys.version + "\n")
    logger.info("RtMidi-Python version:\n" + rtmidi_version + "\n")
    logger.info("RtMidi version: \n" + rtmidi.get_rtmidi_version() + "\n")
    logger.info("Platform:\n" + sys.platform + "\n")
    
    logger.info("Started " + datetime.datetime.now().isoformat() + "\n")
    
    midiout = rtmidi.MidiOut()
    
    port_num_out = -1
    for i, name in enumerate(midiout.get_ports()):
        if 'casio' in name.lower():
            # Found a casio Midi port. Assume this is it.
            port_num_out = i
            logger.info("Found output MIDI port. Number: {0}, Name: {1}\n".format(i, name))
            break
    
    midiin = rtmidi.MidiIn()
    
    port_num_in = -1
    for i, name in enumerate(midiin.get_ports()):
        if 'casio' in name.lower():
            # Found a casio Midi port. Assume this is it.
            port_num_in = i
            logger.info("Found input MIDI port. Number: {0}, Name: {1}\n".format(i, name))
            break
    
    midiout.open_port(port_num_out)
    midiin.open_port(port_num_in)
    midiin.ignore_types(sysex=False) # Make sure we can receive sysex!
    midiin.set_callback(mycallback, 0)
    
    # Read from Category 0 (the keyboard identifiers). All the values are strings, but
    # we don't know how long they are so need to try different lengths.
    
    logger.info(" ....  Doing Category 0 .... \n")
    print("Category 0:")
    
    lens = [-1] * 12
    is_still_going = [True] * 12
    
    for l in range(1, 31):
        for p in range(17):
            if is_still_going[p]:
                q = get_single_parameter(p, category=0, memory=3, length=l)
                logging.info("> " + bytes(q).hex(" ").upper() + "\n")
                have_got_resp = False
                midiout.send_message(q)
                time.sleep(0.1)
                
                if have_got_resp:
                    # Record success
                    lens[p] = l
                else:
                    # Stop trying any larger values
                    is_still_going[p] = False
            
    for i, y in enumerate(lens):
        s = "Parameter {0}, max length {1}".format(i, y)
        logger.info(s + "\n")
        print("  " + s)
    
    
    # Read from Category 3 (Tones). Assume they're all numbers (no strings), so
    # length of 0.
    # Scan through block0 values
    
    logger.info(" ....  Doing Category 3 .... \n")
    print("Category 3:")
    
    uses_blocks = [True] * 230
    max_block = [-1] * 230
    has_at_all = [False] * 230
    is_still_going = [True] * 230
    
    for b in range(-1, 10):
        for p in range(230):
            if is_still_going[p]:
                block = b
                if b < 0:
                    block = 99  # Some ridiculous value. If it works, we know blocks are not used
                if b < 0 or (uses_blocks[p] and is_still_going[p]):
                    q = get_single_parameter(p, category=3, memory=3, length=0, block0=block)
                    logging.info("> " + bytes(q).hex(" ").upper() + "\n")
                    have_got_resp = False
                    midiout.send_message(q)
                    time.sleep(0.05)
                    
                    if have_got_resp:
                        if b < 0:
                            uses_blocks[p] = False
                        has_at_all[p] = True
                        if b >= 0:
                            max_block[p] = b
                    else:
                        # Stop trying any larger block values
                        if b >= 0:
                            is_still_going[p] = False
    
    
    s = "Maximum parameter number = {0}".format(  max([p for p in range(230) if has_at_all[p]]))
    print(s)
    logger.info(s + "\n")
    
      
    for i, y in enumerate(max_block):
        if has_at_all[i]:
            if y < 0:
                s = "Parameter {0}, Any".format(i)
            else:
                s = "Parameter {0}, Blocks 0..{1}".format(i, y)
            logger.info(s + "\n")
        
    
    
    midiin.close_port()
    midiout.close_port()
    
    
    logger.info("Finished " + datetime.datetime.now().isoformat() + "\n")
    
    



def mycallback(msg, data):
    global have_got_resp
    
    have_got_resp = True
    logger = logging.getLogger()
    logger.info("<  " + bytes(msg[0]).hex(" ").upper() + "\n")
    

  

def make_packet(tx=False,
                category=30,
                memory=1,
                parameter_set=0,
                block=[0,0,0,0],
                parameter=0,
                index=0,
                length=1,
                command=-1,
                sub_command=3,
                data=b''):


  w = b'\xf0' + DEVICE_ID
  if command < 0:
    if (tx):
      command = 1
    else:
      command = 0
  w += struct.pack('<B', command)

  if command == 0x8:
    return w + struct.pack('<B', sub_command) + b'\xf7'

  w += struct.pack('<2B', category, memory)
  w += struct.pack('<2B', parameter_set%128, parameter_set//128)

  if command == 0xA:
    return w + b'\xf7'
  
  elif command == 5:
    w += struct.pack('<2B', length%128, length//128)
    w += midi_8bit_to_7bit(data)
    crc_val = binascii.crc32(w[1:])
    w += midi_8bit_to_7bit(struct.pack('<I', crc_val))
    w += b'\xf7'
    return w

  elif (command >= 2 and command < 8) or command == 0xD or command == 0xE: # OBR/HBR doesn't have the following stuff

    pass

    
  else:
    if len(block) != 4:
      print("Length of block should be 4, was {0}; setting to all zeros".format(len(block)))
      block = [0,0,0,0]
    for blk_x in block:
      w += struct.pack('<BB', blk_x%128, blk_x//128)
    w += struct.pack('<BBHH', parameter%128, parameter//128, index, length-1)
  if (tx):
    w += data
  w += b'\xf7'
  return w


def get_single_parameter(parameter, category=3, memory=3, parameter_set=0, block0=0, block1=0, length=0):

    if length>0:
        l = length
    else:
        l = 1

    pkt = make_packet(parameter_set=parameter_set, category=category, memory=memory, parameter=parameter, block=[0,0,block1,block0], length=l)
    return bytearray( pkt )






if __name__=="__main__":
    main()

