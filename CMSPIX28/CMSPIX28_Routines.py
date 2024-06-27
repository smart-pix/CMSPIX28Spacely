'''
Author: Anthony Badea
Date: June, 2024
'''

# python
import time

# spacely
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

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
def ROUTINE_startup_tests():
    
    # boolean to store overall test pass or fail
    tests = [
        ["ROUTINE_test_OP_CODE_NOOP", ROUTINE_test_OP_CODE_NOOP()],
        ["ROUTINE_test_OP_CODE_RST_FW", ROUTINE_test_OP_CODE_RST_FW()],
        ["ROUTINE_test_OP_CODE_CFG_STATIC", ROUTINE_test_OP_CODE_CFG_STATIC()],
        ["ROUTINE_test_OP_CODE_CFG_ARRAY", ROUTINE_test_OP_CODE_CFG_ARRAY()],
        ["ROUTINE_test_OP_CODE_R_DATA_ARRAY", ROUTINE_test_OP_CODE_R_DATA_ARRAY()]
    ]
    
    # print out results
    for test, result in tests:
        print(f"{test} : {'Pass' if result else 'Fail'}")
    
    # print overall startup test 
    startup_test_result = all([i[1] for i in tests])

    print(f"Full startup test: {'Pass' if startup_test_result else 'Fail'}")


#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_test_OP_CODE_NOOP():
    '''
    test case for:
    - OP_CODE_NOOP
    '''
    
    # boolean to store overall test pass or fail
    PASS = True
    
    print("Executing test routine for OP_CODE_NOOP")
    print("*******************************************")

    # send a FW reset
    hex_lists = [
        ["4'h2", "4'h0", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 0 (no operation)
    ]
    ROUTINE_sw_write32_0(hex_lists)
    
    print("Pass" if PASS else "Fail")
    print("*******************************************")
    print("\n\n")

    return PASS

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_test_OP_CODE_RST_FW():
    ''' 
    test case for:
    - OP_CODE_W_RST_FW
    '''
    
    PASS = True

    print("Executing test routine for OP_CODE_W_RST_FW")
    print("*******************************************")

    # send a FW reset
    hex_lists = [
        ["4'h2", "4'h1", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 1 (firmware reset)
    ]
    ROUTINE_sw_write32_0(hex_lists)

    # store expected values
    sw_read32_0_expected = gen_sw_write32_0(hex_lists[0][2:])
    sw_read32_1_expected = 1 # 1 from https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/main/src/fw_ip2.sv#L179
    
    # print value of read register
    sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
    sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")

    # store pass/fail
    sw_read32_0_pass = (sw_read32_0_expected == sw_read32_0)
    sw_read32_1_pass = (sw_read32_1_expected == sw_read32_1)

    # print result
    print(f"Expected value and actual read from sw_read32_0: {sw_read32_0_expected} and {sw_read32_0} -> {'Pass' if sw_read32_0_pass else 'Fail'}")
    print(f"Expected value and actual read from sw_read32_1: {sw_read32_1_expected} and {sw_read32_1} -> {'Pass' if sw_read32_1_pass else 'Fail'}")
    
    # add to PASS
    PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

    print("Pass" if PASS else "Fail")
    print("*******************************************")
    print("\n\n")

    return PASS

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_test_OP_CODE_CFG_STATIC():
    '''
    test case for:
    - OP_CODE_W_CFG_STATIC_0 and OP_CODE_R_CFG_STATIC_0
    - OP_CODE_W_CFG_STATIC_1 and OP_CODE_R_CFG_STATIC_1
    '''
    
    # boolean to store overall test pass or fail
    PASS = True

    print("Executing test routine for OP_CODE_W_CFG_STATIC_0, OP_CODE_R_CFG_STATIC_0, OP_CODE_W_CFG_STATIC_1, and OP_CODE_R_CFG_STATIC_1")
    print("*****************************************************************************************************************************")

    # send a FW reset
    hex_lists = [
        ["4'h2", "4'h1", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 1 (firmware reset)
        ["4'h2", "4'hC", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 6 (status clear)
    ]
    ROUTINE_sw_write32_0(hex_lists)
    print("\n\n")

    # op codes
    OP_CODES = [
        [["OP_CODE_W_CFG_STATIC_0", "4'h2"], ["OP_CODE_R_CFG_STATIC_0", "4'h3"]],
        [["OP_CODE_W_CFG_STATIC_1", "4'h4"], ["OP_CODE_R_CFG_STATIC_1", "4'h5"]]
    ]
    
    for [write_name, write_code], [read_name, read_code] in OP_CODES:

        print("-------------------------------------------------------------------------------")
        print(f"Executing test routine for {write_name} and {read_name}")

        # hex lists 
        hex_lists = [
            ["4'h2", write_code, "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"], # write op code (write)
            ["4'h2", read_code, "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"],  # write op code (read)
        ]
        ROUTINE_sw_write32_0(hex_lists)
        
        # store expected values
        sw_read32_0_expected = gen_sw_write32_0(hex_lists[0][2:])
        if read_name == "OP_CODE_R_CFG_STATIC_0":
            sw_read32_1_expected = 6 # 110 from https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/main/src/fw_ip2.sv#L180-L181
        else:
            sw_read32_1_expected = 24 # 11000 from https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/main/src/fw_ip2.sv#L182-L183
        
        # print value of read register
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")

        # store pass/fail
        sw_read32_0_pass = (sw_read32_0_expected == sw_read32_0)
        sw_read32_1_pass = (sw_read32_1_expected == sw_read32_1)

        # print result
        print(f"Expected value and actual read from sw_read32_0: {sw_read32_0_expected} and {sw_read32_0} -> {'Pass' if sw_read32_0_pass else 'Fail'}")
        print(f"Expected value and actual read from sw_read32_1: {sw_read32_1_expected} and {sw_read32_1} -> {'Pass' if sw_read32_1_pass else 'Fail'}")
        
        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # print status clear
        print("Sending OP_CODE_W_STATUS_FW_CLEAR to clean up.")

        # send status clear
        hex_lists = [
            ["4'h2", "4'hC", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code C (status clear)
        ]
        ROUTINE_sw_write32_0(hex_lists)

        # store expected values
        sw_read32_0_expected = 0
        sw_read32_1_expected = 0

        # read value of register
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        
        # store pass/fail
        sw_read32_0_pass = (sw_read32_0_expected == sw_read32_0)
        sw_read32_1_pass = (sw_read32_1_expected == sw_read32_1)

        # print result
        print(f"Expected value and actual read from sw_read32_0: {sw_read32_0_expected} and {sw_read32_0} -> {'Pass' if sw_read32_0_pass else 'Fail'}")
        print(f"Expected value and actual read from sw_read32_1: {sw_read32_1_expected} and {sw_read32_1} -> {'Pass' if sw_read32_1_pass else 'Fail'}")
        print("-------------------------------------------------------------------------------")
        print("\n\n")

        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

    
    print("Pass" if PASS else "Fail")
    print("*****************************************************************************************************************************")
    print("\n\n")
    
    return PASS

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_test_OP_CODE_CFG_ARRAY():
    '''
    test case for:
    - OP_CODE_W_CFG_ARRAY_0 and OP_CODE_R_CFG_ARRAY_0
    - OP_CODE_W_CFG_ARRAY_1 and OP_CODE_R_CFG_ARRAY_1
    '''
    
    # boolean to store overall test pass or fail
    PASS = True

    print("Executing test routine for OP_CODE_W_CFG_ARRAY_0, OP_CODE_R_CFG_ARRAY_0, OP_CODE_W_CFG_ARRAY_1, and OP_CODE_R_CFG_ARRAY_1")
    print("*****************************************************************************************************************************")

    # send a FW reset
    hex_lists = [
        ["4'h2", "4'h1", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 1 (firmware reset)
        ["4'h2", "4'hC", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 6 (status clear)
    ]
    ROUTINE_sw_write32_0(hex_lists)
    print("\n\n")

    # op codes
    OP_CODES = [
        [["OP_CODE_W_CFG_ARRAY_0", "4'h6"], ["OP_CODE_R_CFG_ARRAY_0", "4'h7"]],
        [["OP_CODE_W_CFG_ARRAY_1", "4'h8"], ["OP_CODE_R_CFG_ARRAY_1", "4'h9"]]
    ]
    
    for [write_name, write_code], [read_name, read_code] in OP_CODES:

        print("-------------------------------------------------------------------------------")
        print(f"Executing test routine for {write_name} and {read_name}")

        # hex lists 
        hex_lists = [
            ["4'h2", write_code, "8'h0", "16'h1"], # write op code (write)
            ["4'h2", read_code, "8'h0", "16'h1"],  # write op code (read)
        ]
        ROUTINE_sw_write32_0(hex_lists)
        
        # store expected values
        sw_read32_0_expected = gen_sw_write32_0(hex_lists[0][2:])
        if read_name == "OP_CODE_R_CFG_ARRAY_0":
            sw_read32_1_expected = 96 # 1100000 from https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/main/src/fw_ip2.sv#L184-L185
        else:
            sw_read32_1_expected = 384 # 110000000 from https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/main/src/fw_ip2.sv#L186-L187

        # print value of read register
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")

        # store pass/fail
        sw_read32_0_pass = (sw_read32_0_expected == sw_read32_0)
        sw_read32_1_pass = (sw_read32_1_expected == sw_read32_1)

        # print result
        print(f"Expected value and actual read from sw_read32_0: {sw_read32_0_expected} and {sw_read32_0} -> {'Pass' if sw_read32_0_pass else 'Fail'}")
        print(f"Expected value and actual read from sw_read32_1: {sw_read32_1_expected} and {sw_read32_1} -> {'Pass' if sw_read32_1_pass else 'Fail'}")
        
        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # print status clear
        print("Sending OP_CODE_W_STATUS_FW_CLEAR to clean up.")

        # send status clear
        hex_lists = [
            ["4'h2", "4'hC", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code C (status clear)
        ]
        ROUTINE_sw_write32_0(hex_lists)

        # store expected values
        sw_read32_0_expected = 0
        sw_read32_1_expected = 0

        # read value of register
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        
        # store pass/fail
        sw_read32_0_pass = (sw_read32_0_expected == sw_read32_0)
        sw_read32_1_pass = (sw_read32_1_expected == sw_read32_1)

        # print result
        print(f"Expected value and actual read from sw_read32_0: {sw_read32_0_expected} and {sw_read32_0} -> {'Pass' if sw_read32_0_pass else 'Fail'}")
        print(f"Expected value and actual read from sw_read32_1: {sw_read32_1_expected} and {sw_read32_1} -> {'Pass' if sw_read32_1_pass else 'Fail'}")
        print("-------------------------------------------------------------------------------")
        print("\n\n")

        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

    
    print("Pass" if PASS else "Fail")
    print("*****************************************************************************************************************************")
    print("\n\n")
    
    return PASS

#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_test_OP_CODE_R_DATA_ARRAY():

    '''
    test case for:
    - OP_CODE_R_DATA_ARRAY_0
    - OP_CODE_R_DATA_ARRAY_1
    '''
    
    # boolean to store overall test pass or fail
    PASS = True

    print("Executing test routine for OP_CODE_R_DATA_ARRAY_0 and OP_CODE_R_DATA_ARRAY_1")
    print("*****************************************************************************************************************************")


    print("Pass" if PASS else "Fail")
    print("*****************************************************************************************************************************")
    print("\n\n")
    return PASS


#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
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
