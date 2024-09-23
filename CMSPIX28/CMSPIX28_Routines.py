'''
Author: Anthony Badea, Benjamin Parpillon
Date: June, 2024
'''

# python
import time

# spacely
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

# note that all functions in CMSPIX28_Subroutines.py will automatically be imported by Master_Config.py

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
    
    if cleanup:
        print(f"Returning register to how it started sw_write32_0 = {sw_write32_0_init}")
        sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0", sw_write32_0_init)
        sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
        print(f"Register returned to initial value: {sw_write32_0_init == sw_write32_0}")

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_sw_read32(
        sw_read32_0_expected = None, 
        sw_read32_1_expected = None,
        sw_read32_1_nbitsToCheck = 32, # number of bits to check. for some cases it is better to leave out the testX_o_status_done bits
        print_code = "",
):
    
    # read value of register
    sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
    sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        
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

    return sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_startup_tests():
    
    # boolean to store overall test pass or fail
    tests = [
        ["ROUTINE_startup_test_OP_CODE_NOOP", ROUTINE_startup_test_OP_CODE_NOOP()],
        ["ROUTINE_startup_test_OP_CODE_RST_FW", ROUTINE_startup_test_OP_CODE_RST_FW()],
        ["ROUTINE_startup_test_OP_CODE_CFG_STATIC", ROUTINE_startup_test_OP_CODE_CFG_STATIC()],
        ["ROUTINE_startup_test_OP_CODE_CFG_ARRAY", ROUTINE_startup_test_OP_CODE_CFG_ARRAY()],
        ["ROUTINE_startup_test_OP_CODE_R_DATA_ARRAY", ROUTINE_startup_test_OP_CODE_R_DATA_ARRAY()]
    ]
    
    # print out results
    for test, result in tests:
        print(f"{test} : {result}")
    
#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_startup_test_OP_CODE_NOOP():
    '''
    test case for:
    - OP_CODE_NOOP
    '''

    # setup test
    print_test_header("Executing test routine for OP_CODE_NOOP")
    PASS = True # boolean to store overall test pass or fail

    # send a FW reset
    hex_lists = [["4'h2", "4'h0", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"]] # write op code 0 (no operation)
    ROUTINE_sw_write32_0(hex_lists)
    
    # print and return PASS
    print_test_footer(PASS)
    return PASS

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_startup_test_OP_CODE_RST_FW():
    ''' 
    test case for:
    - OP_CODE_W_RST_FW
    '''

    # setup test
    print_test_header("Executing test routine for OP_CODE_W_RST_FW")
    PASS = True # boolean to store overall test pass or fail

    # send a FW reset
    # op code list https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/cd_ip1_test2/vrf/fw_ipx_wrap_tb.sv#L92-L109
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code E (status clear)
        ["4'h2", "4'h1", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code 1 (firmware reset)
    ]
    ROUTINE_sw_write32_0(hex_lists)

    # store expected values
    sw_read32_0_expected = 0 # reset should set this to zero
    sw_read32_1_expected = 1 # 1 from https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/main/src/fw_ip2.sv#L179
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, sw_read32_1_nbitsToCheck = 14, print_code = "ihb")

    # print and return pass
    PASS = PASS and sw_read32_0_pass and sw_read32_1_pass
    print_test_footer(PASS)
    return PASS

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_startup_test_OP_CODE_CFG_STATIC():
    '''
    test case for:
    - OP_CODE_W_CFG_STATIC_0 and OP_CODE_R_CFG_STATIC_0
    - OP_CODE_W_CFG_STATIC_1 and OP_CODE_R_CFG_STATIC_1
    '''

    # setup test
    print_test_header("Executing test routine for OP_CODE_W_CFG_STATIC_0, OP_CODE_R_CFG_STATIC_0, OP_CODE_W_CFG_STATIC_1, and OP_CODE_R_CFG_STATIC_1")
    PASS = True # boolean to store overall test pass or fail

    # print("Executing test routine for OP_CODE_W_CFG_STATIC_0, OP_CODE_R_CFG_STATIC_0, OP_CODE_W_CFG_STATIC_1, and OP_CODE_R_CFG_STATIC_1")
    # print("*****************************************************************************************************************************")

    # send a FW reset
    hex_lists = [
        ["4'h2", "4'h1", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code firmware reset
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code fw status clear
    ]
    ROUTINE_sw_write32_0(hex_lists)

    # op codes
    OP_CODES = [
        [["OP_CODE_W_CFG_STATIC_0", "4'h2"], ["OP_CODE_R_CFG_STATIC_0", "4'h3"]],
        [["OP_CODE_W_CFG_STATIC_1", "4'h4"], ["OP_CODE_R_CFG_STATIC_1", "4'h5"]]
    ]
    
    for [write_name, write_code], [read_name, read_code] in OP_CODES:

        print_test_header(f"Executing test routine for {write_name} and {read_name}", div="-")

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
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, sw_read32_1_nbitsToCheck = 12, print_code = "ihb")
        
        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # print status clear
        print("Sending OP_CODE_W_STATUS_FW_CLEAR to clean up.")

        # send status clear
        hex_lists = [
            ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code fw status clear
        ]
        ROUTINE_sw_write32_0(hex_lists)

        # store expected values
        sw_read32_0_expected = 0
        sw_read32_1_expected = 0
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, print_code = "ihb")

        print("----")

        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

    # print and return pass
    print_test_footer(PASS)
    return PASS

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_startup_test_OP_CODE_CFG_ARRAY():
    '''
    test case for:
    - OP_CODE_W_CFG_ARRAY_0 and OP_CODE_R_CFG_ARRAY_0
    - OP_CODE_W_CFG_ARRAY_1 and OP_CODE_R_CFG_ARRAY_1
    - OP_CODE_W_CFG_ARRAY_2 and OP_CODE_R_CFG_ARRAY_2
    '''
    
    # setup test
    print_test_header("Executing test routine for OP_CODE_W_CFG_ARRAY_0, OP_CODE_R_CFG_ARRAY_0, OP_CODE_W_CFG_ARRAY_1, OP_CODE_R_CFG_ARRAY_1, OP_CODE_W_CFG_ARRAY_2, OP_CODE_R_CFG_ARRAY_2")
    PASS = True # boolean to store overall test pass or fail

    # send a FW reset
    hex_lists = [
        ["4'h2", "4'h1", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code firmware reset
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code fw status clear
    ]
    ROUTINE_sw_write32_0(hex_lists)

    # op codes
    OP_CODES = [
        [["OP_CODE_W_CFG_ARRAY_0", "4'h6"], ["OP_CODE_R_CFG_ARRAY_0", "4'h7"]],
        [["OP_CODE_W_CFG_ARRAY_1", "4'h8"], ["OP_CODE_R_CFG_ARRAY_1", "4'h9"]],
        [["OP_CODE_W_CFG_ARRAY_2", "4'hA"], ["OP_CODE_R_CFG_ARRAY_2", "4'hB"]],
    ]
    
    for [write_name, write_code], [read_name, read_code] in OP_CODES:

        print_test_header(f"Executing test routine for {write_name} and {read_name}", div="-")

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
        elif read_name == "OP_CODE_R_CFG_ARRAY_1":
            sw_read32_1_expected = 384 # 110000000 from https://github.com/Fermilab-Microelectronics/cms_pix_28_test_firmware/blob/main/src/fw_ip2.sv#L186-L187
        elif read_name == "OP_CODE_R_CFG_ARRAY_2":
            sw_read32_1_expected = 1536
        else:
            sw_read32_1_expected = -1

        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, sw_read32_1_nbitsToCheck = 12, print_code = "ihb")

        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # print status clear
        print("Sending OP_CODE_W_STATUS_FW_CLEAR to clean up.")

        # send status clear
        hex_lists = [
            ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code fw status clear
        ]
        ROUTINE_sw_write32_0(hex_lists)

        # store expected values
        sw_read32_0_expected = 0
        sw_read32_1_expected = 0
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, print_code = "ihb")

        print("----")

        # add to PASS
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

    # print and return pass
    print_test_footer(PASS)
    return PASS

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_startup_test_OP_CODE_R_DATA_ARRAY():

    '''
    test case for:
    - OP_CODE_R_DATA_ARRAY_0
    - OP_CODE_R_DATA_ARRAY_1
    '''
    
    print_test_header("Executing test routine for OP_CODE_R_DATA_ARRAY_0 and OP_CODE_R_DATA_ARRAY_1")

    # boolean to store overall test pass or fail
    PASS = True

    # send op code to set up bxclk to 40 MHz
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"], # write op code fw status clear
        ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h2", "6'h28"], # write op code write
    ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ibh")
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 96 # updated from 48

    # hex lists to write
    hex_lists = [["4'h2", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(nwrites)]
    hex_lists[47] = ["4'h2", "4'h6", "8'h2f", "16'he007"]
    hex_lists[46] = ["4'h2", "4'h6", "8'h2e", "16'hffff"]    
    hex_lists[3] = ["4'h2", "4'h6", "8'h3", "16'hffff"]
    hex_lists[2] = ["4'h2", "4'h6", "8'h2", "16'hffff"]
    hex_lists[1] = ["4'h2", "4'h6", "8'h1", "16'hffff"]
    hex_lists[0] = ["4'h2", "4'h6", "8'h0", "16'h8001"]
    sw_read32_0_expected_list = [int_to_32bit_hex(0)]*len(hex_lists)

    # write and read
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ibh")

    # send an execute for test 1 and loopback enabled
    # https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L251-L260
    hex_lists = [
        [
            "4'h2",  # firmware id
            "4'hF",  # op code for execute
            "1'h0",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            "6'h00", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            "1'h1",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            "6'h04", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
        ]
    ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code="ihb")    
    
    # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
    # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
    nwords = 24 # 24 words * 32 bits/word = 768 bits
    words = []
    for iW in range(nwords):

        # send read
        address = "8'h" + hex(iW)[2:]
        hex_lists = [
            ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
        ]
        ROUTINE_sw_write32_0(hex_lists)
        
        # read back data
        sw_read32_0_expected = int(sw_read32_0_expected_list[iW], 16)
        sw_read32_1_expected = int("10100000100010",2) # from running op codes. see here for the mapping https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L179-L196
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, sw_read32_1_nbitsToCheck = 14, print_code = "ihb")
        
        # update
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # store data
        words.append(sw_read32_0)

    print(len(words), words)

    return None

#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
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

#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
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

#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_scanChain_counter():

    # Note we do not yet have a smoke test. verify this on scope as desired.

    # hex lists                                                                                                                    
    hex_lists = [
        ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"], # write op code 2 (write)                                       
        ["4'h2", "4'h6", "8'h0", "16'h1"], # write op code 6 (array 0) writing to address 0 (8'h0) value 1 (16'h1)
        ["4'h2", "4'h6", "8'h1", "16'h3"], # write op code 6 (array 0) writing to address 1 (8'h1) value 3 (16'h3)
        ["4'h2", "4'h6", "8'h2", "16'h7"], # write op code 6 (array 0) writing to address 2 (8'h7) value 7 (16'h7)
        ["4'h2", "4'h6", "8'h3", "16'hf"], # write op code 6 (array 0) writing to address 3 (8'hf) value 2 (16'hf)
        ["4'h2", "4'h6", "8'h5", "16'hff"], # write op code 6 (array 0) writing to address 5 (8'hf) value 2 (16'hff)
        # ["4'h2", "4'hd", "7'h0", "1'h1", "4'h1", "6'h3", "6'h8"], # execute with op code d with test number 2 enabled  # Commented out
        ["4'h2", "4'hF", "1'h0", "6'h00", "1'h0", "4'h1", "6'h04", "6'h08"] # execute with OP_CODE_W_EXECUTE
    ]

    ROUTINE_sw_write32_0(hex_lists)

    # 1st parameter of the hex code (right to left)
    # this number divides the original 400 MHz down for the BxCLK_ana and BxCLK
    # 400 MHz / clk_divide
    clk_divides = [50, 127]

    # loop over clk_divides from 10 to 40
    for divide in clk_divides:
        # get clk_divide value
        clk_divide = "7'h" + hex(divide)[2:] # removes the 0x prefix, ex. 0x28 -> 28
        # create hex list
        hex_list = [["4'h1", "4'h2", "16'h0", "1'h0", clk_divide], # send a write
                    ["4'h1", "4'h3", "16'h0", "1'h0", clk_divide]] # send a read
    	# call ROUTINE_sw_write32_0
        ROUTINE_sw_write32_0(hex_list)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")

        # send an execute for test 1 and loopback enabled
        # https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L251-L260
        hex_lists = [
        	[
            	"4'h1",  # firmware id
            	"4'hF",  # op code execute
            	"1'h0",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            	"4'h0", # 3 bits for spare_index_max
            	"1'h1",  # 1 bit for w_execute_cfg_test_loopback
            	"4'h4",  # 3 bits for test number
                "7'h04", # 6 bits test sample
                "7'h12"  # 6 bits for test delay
        	]
    	]
        ROUTINE_sw_write32_0(hex_lists)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code="ihb")
 
#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_IP1_test1():
    
    #FW reset followed with Status reset
    ROUTINE_startup_test_OP_CODE_RST_FW()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    ROUTINE_sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")
 

    hex_list = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")

    hex_list = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    ROUTINE_sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")

    hex_list = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code execute
            "1'h0",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            "4'h0", # 3 bits for spare_index_max
            "1'h1",  # 1 bit for w_execute_cfg_test_loopback
            "4'h4",  # 3 bits for test number
            "7'h04", # 6 bits test sample
            "7'h12"  # 6 bits for test delay
        ]
    ]
    nwrites = 511
    ROUTINE_sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")

     # write on array0    
    hex_list = [["4'h1", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]
   #hex_list[255] = ["4'h1", "4'h6", "8'hFF", "16'hFF0F"]
    #hex_list[2] = ["4'h1", "4'h6", "8'h02", "16'h0F0F"] 
    #hex_list[1] = ["4'h1", "4'h6", "8'h01", "16'hF0F0"]       
    hex_list[0] = ["4'h1", "4'h6", "8'h00", "16'hFF00"]

    # write on array1
    # pixels are programmed between addresses [68] and [99] (see figure 6 from report)    
    array0 = hex_list
    hex_list = [["4'h1", "4'h8", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]
    #hex_list[69] = ["4'h1", "4'h8", "8'h45", "16'h0000"]    
    #hex_list[68] = ["4'h1", "4'h8", "8'h44", "16'h003F"]
    #hex_list[67] = ["4'h1", "4'h8", "8'h43", "16'hFFFF"]  
    #hex_list[0] = ["4'h1", "4'h8", "8'h00", "16'hFF00"]
    array1 = hex_list

   # write on array2
    hex_list = [["4'h1", "4'hA", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]

    hex_list[104] = ["4'h1", "4'hA", "8'h68", "16'hFFFF"]

    hex_list[112] = ["4'h1", "4'hA", "8'h70", "16'hF00F"]

    hex_list[115] = ["4'h1", "4'hA", "8'h73", "16'hFFFF"]
    hex_list[136] = ["4'h1", "4'hA", "8'h88", "16'h00FF"]   
    array2 = hex_list

    hex_list =  array2+array1+array0   
    
    ROUTINE_sw_write32_0(hex_list)

    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")
    hex_list = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h0",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "4'h0", # 3 bits for spare_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 3 bits for test number
            "7'h4", # 6 bits test sample
            "7'h3F"  # 6 bits for test delay
        ]
	
    ]
    ROUTINE_sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")
    time.sleep(1)

# IMPORTANT! If you want to be able to run a routine easily from
# spacely, put its name in the "ROUTINES" list:
# ROUTINES = [ROUTINE_basicLoopback, ROUTINE_clk_divide] # NOTE. Anthony commented this out on 06/19/24 because it seemed to have no impact.



#<<Registered w/ Spacely as ROUTINE 12, call as ~r12>>
def ROUTINE_scanChain_readout():

    # Note we do not yet have a smoke test. verify this on scope as desired.

    # hex lists                                                                                                                    
    hex_lists = [
        ["4'h2", "4'h2", "4'h0", "1'h0","6'h05", "1'h1", "1'h0", "5'h09", "6'h28"],
          
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # SPARE bits:  "4'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2"

  

    ]

    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ibh")
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 96 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    hex_lists = [["4'h2", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(nwrites)]
    sw_read32_0_expected_list = [int_to_32bit_hex(0)]*len(hex_lists)

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")

    # send an execute for test 1 and loopback enabled
    # https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L251-L260
    hex_lists = [
        [
            "4'h2",  # firmware id
            "4'hF",  # op code for execute
            "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            "6'h0A", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            "6'h04", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
        ]
    ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code="ihb")


