#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.

# python
import time

# spacely
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

# short custom scripts

# Function to convert each hex value to a binary string with proper bit width
def hex_to_bin(hex_str):
    bit_width, hex_value = hex_str.split("'h") # get the bit length and hex value
    bit_width = int(bit_width) # convert bit length to an int
    decimal_value = int(hex_value, 16) # Convert the hexadecimal number to an integer
    binary_str = bin(decimal_value)[2:].zfill(bit_width) # Convert the hexadecimal number to an integer
    return binary_str

def gen_sw_write32_0(hex_list):
    # Convert the list of hex values to a single binary string
    binary_str = ''.join(hex_to_bin(hex_str) for hex_str in hex_list)
    # Convert the binary string to an integer
    resulting_int = int(binary_str, 2)
    # return
    # print(binary_str, resulting_int)
    return resulting_int

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_sw_write32_0(
        hex_lists = [ ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"] ], 
        cleanup = False
):

    # check if hex_lists is none. if so then put a default value in
    #if hex_lists == None:
    #    hex_lists = [ ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"] ]

    # check register initial value and store it
    sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
    print(f"Starting register value sw_write32_0 = {sw_write32_0}")
    sw_write32_0_init = sw_write32_0

    # loop over the write values
    for hex_list in hex_lists:
        
        # convert hex list to input to set memory
        temp = gen_sw_write32_0(hex_list)

        # do write
        sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0", temp)

        # read back
        sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")

        # verify
        successful = (sw_write32_0 == temp)
        print(f"Write to sw_write32_0: {successful}. Wrote {temp} and register reads {sw_write32_0}. hex_list = {hex_list}")

        # sleep between consecutive writes
        time.sleep(1)
    
    if cleanup:
        print(f"Returning register to how it started sw_write32_0 = {sw_write32_0_init}")
        sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0", sw_write32_0_init)
        sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
        print(f"Register returned to initial value: {sw_write32_0_init == sw_write32_0}")


#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_clk_divide():

    # create hex lists
    hex_lists = []

    # 1st parameter of the hex code (right to left)
    # this number divides the original 400 MHz down for the BxCLK_ana and BxCLK
    # 400 MHz / clk_divide
    clk_divides = range(10, 41)

    # loop over clk_divides from 10 to 40
    for divide in clk_divides:
        # get clk_divide value
        clk_divide = "6'h" + hex(divide)[2:] # removes the 0x prefix, ex. 0x28 -> 28
        # create hex list
        hex_list = ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", clk_divide]
        hex_lists.append(hex_list)

    print(f"Writing {len(hex_lists)} hex lists to register sw_write32_0")

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)


#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_clk_delay():
    
    # create hex lists
    hex_lists = []

    # 2nd parameter of hex code (right to left)
    # change the amount of the delay
    delays = range(0,6)
    
    # 3rd parameter of hex code (right to left)
    # change the sign of the delay
    # 1'h0 = positive offset of analog clock w.r.t digital clock = rising edge of analog clock and the rising egde of the digital clock
    # 1'h1 = negative offset of analog clock w.r.t digital clock = rising edge of analog clock and the falling edge of the digital clock
    signs = ["1'h0", "1'h1"]

    # create hex list to be easy to see on the scope
    for sign in signs:

        for delay in delays:

            # get clk_divide value
            clk_delay = "5'h" + hex(delay)[2:] # removes the 0x prefix, ex. 0x28 -> 28

            # create hex list
            hex_list = ["4'h2", "4'h2", "11'h0", "1'h0", sign, clk_delay, "6'h28"]
            hex_lists.append(hex_list)
        
    print(f"Writing {len(hex_lists)} hex lists to register sw_write32_0")

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_test_loopback_CFG_STATIC():
    
    # send a FW reset
    hex_lists = [
        ["4'h2", "4'h1", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op 1 (firmware reset)
        ["4'h2", "4'hC", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 6 (status clear)
    ]
    ROUTINE_sw_write32_0(hex_lists)

    # op codes
    OP_CODES = [
        ["4'h2", "4'h3"], # [OP_CODE_W_CFG_STATIC_0, OP_CODE_R_CFG_STATIC_0]
        ["4'h4", "4'h5"] # [OP_CODE_W_CFG_STATIC_1, OP_CODE_R_CFG_STATIC_1]
    ]
    
    for write, read in OP_CODES:

        print(f"Sending OP_CODES: {write}, {read}")

        # hex lists 
        hex_lists = [
            ["4'h2", write, "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"], # write op code 2 (write)
            ["4'h2", read, "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"], # write op code 3 (read)
        ]
        ROUTINE_sw_write32_0(hex_lists)

        # print value of read register
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        print(f"sw_read32_0 = {sw_read32_0}")
        print(f"sw_read32_1 = {sw_read32_1}")    
        print(f"Expected in sw_read32_0", hex_lists[0][2:], gen_sw_write32_0(hex_lists[0][2:]))
        
        # send status clear
        hex_lists = [
            ["4'h2", "4'hC", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 6 (status clear)
        ]
        ROUTINE_sw_write32_0(hex_lists)
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        print(f"sw_read32_0 = {sw_read32_0}")
        print(f"sw_read32_1 = {sw_read32_1}")
        

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_scanChain_counter():

    # hex lists                                                                                                                    
    hex_lists = [
        ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"], # write op code 2 (write)                                       
        ["4'h2", "4'h6", "8'h0", "16'h1"], # write op code 6 (array 0) writing to address 0 (8'h0) value 1 (16'h1)
        ["4'h2", "4'h6", "8'h1", "16'h3"], # write op code 6 (array 0) writing to address 1 (8'h1) value 3 (16'h3)
        ["4'h2", "4'h6", "8'h2", "16'h7"], # write op code 6 (array 0) writing to address 2 (8'h7) value 7 (16'h7)
        ["4'h2", "4'h6", "8'h3", "16'hf"], # write op code 6 (array 0) writing to address 3 (8'hf) value 2 (16'hf)
        ["4'h2", "4'h6", "8'h5", "16'hff"], # write op code 6 (array 0) writing to address 5 (8'hf) value 2 (16'hff)
        # ["4'h2", "4'hd", "7'h0", "1'h1", "4'h1", "6'h3", "6'h8"], # execute with op code d with test number 2 enabled  # Commented out
        ["4'h2", "4'hd", "1'h0", "6'h00", "1'h0", "4'h1", "6'h04", "6'h08"] # execute with op code d
    ]

    ROUTINE_sw_write32_0(hex_lists)

# IMPORTANT! If you want to be able to run a routine easily from
# spacely, put its name in the "ROUTINES" list:
# ROUTINES = [ROUTINE_basicLoopback, ROUTINE_clk_divide] # NOTE. Anthony commented this out on 06/19/24 because it seemed to have no impact.
