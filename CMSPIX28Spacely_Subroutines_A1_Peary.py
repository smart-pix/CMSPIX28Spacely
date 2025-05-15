# spacely
from Master_Config import *

# python modules
import sys
try:
    pass 
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately


def sw_write32_0(
        hex_lists = [ ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"] ], 
):
    # loop over the write values
    for hex_list in hex_lists:
        # convert hex list to input to set memory
        temp = gen_sw_write32_0(hex_list)
        # do write
        sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0", temp)

def sw_read32(
        sw_read32_0_expected = None, 
        sw_read32_1_expected = None,
        sw_read32_1_nbitsToCheck = 32, # number of bits to check. for some cases it is better to leave out the testX_o_status_done bits
        print_code = "",
        do_sw_read32_1 = True
):
    
    # read value of register
    sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
    sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1") if do_sw_read32_1 else 0   # default is True so we need to be careful?

    # store pass/fail
    sw_read32_0_pass = (sw_read32_0_expected == sw_read32_0)
    sw_read32_1_pass = (sw_read32_1_expected == sw_read32_1)
    
    # print result
    if sw_read32_0_expected != None and sw_read32_1_expected != None:
        print(f"Expected value and actual read from sw_read32_0: {sw_read32_0_expected} and {sw_read32_0} -> {'Pass' if sw_read32_0_pass else 'Fail'}")
        print(f"Expected value and actual read from sw_read32_1: {sw_read32_1_expected} and {sw_read32_1} -> {'Pass' if sw_read32_1_pass else 'Fail'}")
        if sw_read32_1_nbitsToCheck != 32:
            temp = bin(sw_read32_1)[2:]
            temp = int(temp[len(temp) - sw_read32_1_nbitsToCheck:], 2)
            sw_read32_1_pass = (sw_read32_1_expected == temp)
            print(f"  UPDATE: User asked to only check {sw_read32_1_nbitsToCheck} bits of sw_read32_1: {sw_read32_1_expected} and {temp} -> {'Pass' if sw_read32_1_pass else 'Fail'}")

    # check print codes
    if print_code == "ihb":
        print("Read sw_read32_0 (int, hex, binary): ", sw_read32_0, int_to_32bit_hex(sw_read32_0), int_to_32bit(sw_read32_0))
        print("Read sw_read32_1 (int, hex, binary): ", sw_read32_1, int_to_32bit_hex(sw_read32_1), int_to_32bit(sw_read32_1))

    # Suggestion - but this could break a lot of things
    # check for firmware error
    if any(x=='1' for x in int_to_32bit(sw_read32_1)[0:5]):
        fw_error = 1
    return sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass #, fw_error

def sw_readStream(
        sw_read32_0_expected = None, 
        sw_read32_1_expected = None,
        sw_read32_1_nbitsToCheck = 32, # number of bits to check. for some cases it is better to leave out the testX_o_status_done bits
        print_code = "",
        do_sw_read32_1 = True,
        N = 1 #default to reading 1 word 
):
    
    # read value of register
    sw_read32_0_stream = sg.INSTR["car"].stream_memory("sw_read32_0", N)
    # sw_read32_0_get = sg.INSTR["car"].get_memory("sw_read32_0")
    sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1") if do_sw_read32_1 else None

    # store pass/fail
    sw_read32_0_pass = (sw_read32_0_expected == sw_read32_0_stream)
    sw_read32_1_pass = (sw_read32_1_expected == sw_read32_1)
    
    # print result
    if sw_read32_0_expected != None and sw_read32_1_expected != None:
        print(f"Expected value and actual read from sw_read32_0: {sw_read32_0_expected} and {sw_read32_0} -> {'Pass' if sw_read32_0_pass else 'Fail'}")
        print(f"Expected value and actual read from sw_read32_1: {sw_read32_1_expected} and {sw_read32_1} -> {'Pass' if sw_read32_1_pass else 'Fail'}")
        if sw_read32_1_nbitsToCheck != 32:
            temp = bin(sw_read32_1)[2:]
            temp = int(temp[len(temp) - sw_read32_1_nbitsToCheck:], 2)
            sw_read32_1_pass = (sw_read32_1_expected == temp)
            print(f"  UPDATE: User asked to only check {sw_read32_1_nbitsToCheck} bits of sw_read32_1: {sw_read32_1_expected} and {temp} -> {'Pass' if sw_read32_1_pass else 'Fail'}")

    # check print codes
    if print_code == "ihb":
        print("Read sw_read32_0 (int, hex, binary): ", sw_read32_0, int_to_32bit_hex(sw_read32_0), int_to_32bit(sw_read32_0))
        print("Read sw_read32_1 (int, hex, binary): ", sw_read32_1, int_to_32bit_hex(sw_read32_1), int_to_32bit(sw_read32_1))

    return sw_read32_0_stream, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass