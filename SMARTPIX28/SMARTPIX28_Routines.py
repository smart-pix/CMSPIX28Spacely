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
def ROUTINE_basicLoopback():
    """This routine tests basic loopback from data_in to data_out"""    
    #Define the routine's purpose in a docstring like above, this will appear
    #when you call the routine in Spacely.

    '''
    1. Reset AXI interface (~S_AXI_ARESETN)
    '''
    sg.INSTR["car"].set_memory("S_AXI_ARESETN", 0)


    '''
    2. Initiate below writes in-order
    0x00000011 <--- sets superpixsel and opcode for reset
    0x00000022 <--- sets opcode for configin with data
    0x00000003 <--- sets opcode for wait
    0x00000004 <--- sets opcode for configout
    '''


    '''
    3. Snoop on reg_rddin[0] [3:0] for status
    if(4'b0001) IDLE_STATUS      <--- FSM is in IDLE state
    if(4'b0010) RESET_STATUS     <-- Superpixsel is programmed and reset is de-asserted, asserted back at following edge of ConfigClk
    if(4'b0011) CONFIGIN_STATUS  <-- bit 1 is inserted into shift register i.e asserted and de-asserted back at following edge of ConfigClk
    if(4'b0100) WAIT_STATUS      <-- FW has waited for 5164 cycles
    if(4'b1000) CONFIGOUT_STATUS <-- FW sends final value for ConfigOut
    '''
    snoop = True
    statuses = {
        "4'b0001" : "IDLE_STATUS",
        "4'b0010" : "RESET_STATUS",
        "4'b0011" : "CONFIGIN_STATUS",
        "4'b0100" : "WAIT_STATUS",
        "4'b1000" : "CONFIGOUT_STATUS",
    }
    while snoop:

        reg_rddin = sg.INSTR["car"].get_memory("reg_rddin")
        time.sleep(0.5)
        print(reg_rddin)
        
        # check status
        for key, val in statuses.items():
            if reg_rddin == key:
                print(val)
        

    '''
    4. As soon as SW sees CONFIGIN status, it can snoop upon reg_rddin[1][0] for ConfigOut 
    '''
    
    # reg_wrdout = sg.INSTR["car"].get_memory("reg_wrdout")
    # reg_wrdout = int(reg_wrdout)

    # time.sleep(0.5)
    
    # # write something
    # temp = int(not (reg_wrdout == 1))
    # write = sg.INSTR["car"].set_memory("reg_wrdout", temp)
    # time.sleep(0.5)
    
    # reg_wrdout = int(sg.INSTR["car"].get_memory("reg_wrdout"))
    # print(temp, write, reg_wrdout)
    
    pass


# #<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
# def ROUTINE_clk_divide():
    
#     # check register initial value and store it
#     sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
#     print(f"Starting register value sw_write32_0 = {sw_write32_0}")
#     sw_write32_0_init = sw_write32_0
    
#     # loop over clk_divides from 10 to 40
#     for divide in range(10, 41):
      
#         # get clk_divide value
#         clk_divide = "6'h" + hex(divide).strip("0x")

#         # create hex list
#         hex_list = ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", clk_divide]

#         # convert hex list to input to set memory
#         temp = gen_sw_write32_0(hex_list)

#         # do write
#         sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0", temp)

#         # read back
#         sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
#         print(f"Wrote {temp} and register reads {sw_write32_0}. clk_divide = {divide} ({clk_divide})")

#         # sleep between consecutive writes
#         time.sleep(1)  

#     print(f"Returning register to how it started sw_write32_0 = {sw_write32_0_init}")
#     sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0", sw_write32_0_init)
#     sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
#     print(f"Register returned to initial value: {sw_write32_0_init == sw_write32_0}")


#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_sw_write32_0(hex_lists = None):

    # check if hex_lists is none. if so then put a default value in
    if hex_lists == None:
        hex_lists = [ ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"] ]

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
        print(f"Wrote {temp} and register reads {sw_write32_0}. hex_list = {hex_list}")

        # sleep between consecutive writes
        time.sleep(1)

    print(f"Returning register to how it started sw_write32_0 = {sw_write32_0_init}")
    sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0", sw_write32_0_init)
    sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
    print(f"Register returned to initial value: {sw_write32_0_init == sw_write32_0}")


#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_clk_divide():

    # create hex lists
    hex_lists = []

    # 1st parameter of the hex code (right to left)
    # this number divides the original 400 MHz down for the bclk and bclk_ana
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


#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
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

# IMPORTANT! If you want to be able to run a routine easily from
# spacely, put its name in the "ROUTINES" list:
# ROUTINES = [ROUTINE_basicLoopback, ROUTINE_clk_divide] # NOTE. Anthony commented this out on 06/19/24 because it seemed to have no impact.
