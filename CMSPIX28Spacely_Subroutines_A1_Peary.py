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
    # convert each hex list to a packed 32-bit value, then write them all to
    # sw_write32_0 in a single round trip (pearyd loops the write locally),
    # in the same order they'd otherwise be written one at a time
    values = [gen_sw_write32_0(hex_list) for hex_list in hex_lists]
    sg.INSTR["car"].burst_write_sw0(values)

def sw_pollStatusDone(
        bit_index = 14, # status_index_test1_done: sm_test1_o_status_done (ip1 CONFIG-SHIFT-REG-programmed flag)
        timeout_us = 20000,
):
    # poll sw_read32_1 in a single round trip (pearyd spins locally) until
    # the given status-done bit goes high, or timeout_us elapses
    return sg.INSTR["car"].burst_poll_status_done(bit_index, timeout_us)

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
        N = 1, #default to reading 1 word
        opcode = 0xD, # op code for the memory being read (DATA_ARRAY_1 by default)
        base_addr = 0 # first word address to read; words are read at base_addr, base_addr+1, ..., base_addr+N-1
):

    # read N words in a single round trip: pearyd loops the write(address)+read
    # sequence locally and returns all N words at once, in increasing address order
    sw_read32_0_stream = sg.INSTR["car"].burst_read_data_array_1(opcode, base_addr, N)
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