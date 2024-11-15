'''
Author: Anthony Badea, Benjamin Parpillon
Date: June, 2024
'''

# python
import time
import tqdm
import h5py
from datetime import datetime
import csv

# spacely
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

superpixel = 0
# note that all functions in CMSPIX28_Subroutines.py will automatically be imported by Master_Config.py

def onstartup():

    # GLOBAL CONFIG VARIABLES
    assume_defaults = False
    
    # sg.INSTR["car"].axi_registers = {"apg": ["apg_run", "apg_write_channel", "apg_read_channel",
    #                  "apg_sample_count","apg_n_samples","apg_write_buffer_len",
    #                  "apg_next_read_sample","apg_wave_ptr","apg_status", "apg_control",
    #                  "apg_dbg_error",
    #                          "apg_clear"],
    #                  "spi_apg": ["spi_apg_run", "spi_apg_write_channel", "spi_apg_read_channel",
    #                  "spi_apg_sample_count","spi_apg_n_samples","spi_apg_write_buffer_len",
    #                              "spi_apg_next_read_sample","spi_apg_wave_ptr","spi_apg_status", "spi_apg_control",
    #                              "spi_apg_dbg_error", "spi_apg_clear"],
    #                  "lpgbt_fpga":  ["uplinkRst", "mgt_rxpolarity", "lpgbtfpga_status"]}

    print("====================================")
    print("=== Starting CMSPIX28 Default Setup ===")

    if not assume_defaults:
        do_setup = input("Press enter to begin or 'n' to skip >")
        if 'n' in do_setup:
            print("Skipping all setup!")
            return

    #sg.INSTR["car"].debug_memory = False
        
    # print("Step 1: Initializing ZCU102")

    # sg.INSTR["car"].set_memory("gpio_direction",0)
    # print(">  Set all AXI GPIOs as outputs")

    # sg.INSTR["car"].setUsrclkFreq(int(320e6))
    # print(">  Initialized Usrclk to 320 MHz")
    
    init_car =  input("Step 2: Initializing CaR Board ('n' to skip)>>>")

    if 'n' in init_car:
        print("Skipped!")
    else:

        #Basic initialization of CaR board
        sg.INSTR["car"].init_car()

        #Init CMOS I/O voltages
        print(">  Setting CMOS In/Out Voltage = 0.9 V",end='')
        if not assume_defaults: 
            set_cmos_voltage = input("('n' to skip)")
        if assume_defaults or not 'n' in set_cmos_voltage:
            sg.INSTR["car"].set_input_cmos_level(0.9)
            sg.INSTR["car"].set_output_cmos_level(0.9)
        print("finished setting CMOS")
       

    init_asic = input("Step 3: Initializing ASIC ('n' to skip)>>>")

    if 'n' in init_asic:
        print("Skipped!")
    else:
        iDVDD = V_PORT["vddd"].get_current()
        iAVDD = V_PORT["vdda"].get_current()
        print(f"DVDD current is {iDVDD}")
        print(f"AVDD current is {iAVDD}")
        print("Programming of the ASIC shift register")
        ROUTINE_IP1_test1()
        print("shift register Programmed")
        iDVDD = V_PORT["vddd"].get_current()
        iAVDD = V_PORT["vdda"].get_current()
        print(f"DVDD current is {iDVDD}")
        print(f"AVDD current is {iAVDD}")
        # #Config Si5345
        # print(">  Configuring SI5345 w/ config option 1 (disable refclk)")
        # #if not assume_defaults:
        # #    config_si5345 = input("('n' to skip)")
        # #if assume_defaults or not 'n' in config_si5345:
        # sg.INSTR["car"].configureSI5345(1)
        # #input("?")
        
        # assert_reset()
        # #input("?")
        # time.sleep(0.1)
        # deassert_reset()
        # #input("?")
        # print(">  Pulsed digital Reset")
        
        # spi_write_tx_config(TX_REG_DEFAULTS)
        # #input("?")
        # print(">  Wrote default transmitter configuration")

      
        # print(">  Configuring SI5345 w/ config option 2 (enable refclk)")
        # #if not assume_defaults:
        # #    config_si5345 = input("('n' to skip)")
        # #if assume_defaults or not 'n' in config_si5345:
        # sg.INSTR["car"].configureSI5345(2)
        # #input("?")
        
    # print("Step 4: Uplink Reset")
    # sg.INSTR["car"].set_memory("uplinkRst",1)
    # time.sleep(0.1)
    # sg.INSTR["car"].set_memory("uplinkRst",0)
    # print(">  Pulsed uplink reset")
        
    # print("=== Finished SP3A Default Setup ===")
    # print("===================================")


#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_sw_write32_0(
        hex_lists = [ ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", "6'ha"] ], 
        cleanup = False,
        doPrint = False
):

    # check register initial value and store it
    sw_write32_0 = sg.INSTR["car"].get_memory("sw_write32_0")
    if doPrint: 
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
        if doPrint:
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
        do_sw_read32_1 = True
):
    
    # read value of register
 #   start =time.time()
    sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
    sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1") if do_sw_read32_1 else None

 #   read_time = time.time() - start
 #   print(f"readtime={read_time}")
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
    
    #general_function(superpixel=sup)
    print(superpixel)
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
    #hex_list = [["4'h1", "4'hA", "8'h" + hex(i)[2:], "16'hAAAA"] for i in range(256)]
    hex_list = [["4'h1", "4'hA", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]

    # testing programming 4 pixels
    #hex_list[120] = ["4'h1", "4'hA", "8'h78", "16'h0100"]
    hex_list[112] = ["4'h1", "4'hA", "8'h70", "16'h0002"] 
    hex_list[128] = ["4'h1", "4'hA", "8'h80", "16'h0000"]
    #hex_list[115] = ["4'h1", "4'hA", "8'h73", "16'h0020"]
    #hex_list[136] = ["4'h1", "4'hA", "8'h88", "16'h2000"]   
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
        #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"],#BSDG7102A and CARBOARD and long cable
        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
          
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
    nwrites = 240 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    hex_lists = [["4'h2", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(nwrites)]
    sw_read32_0_expected_list = [int_to_32bit_hex(0)]*len(hex_lists)

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")

    # send an execute for test 1 and loopback enabled
    # https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L251-L260
    # hex_lists = [
    #     [
    #         "4'h2",  # firmware id
    #         "4'hF",  # op code for execute
    #         "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
    #         "6'h1C", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
    #         "1'h0",  # 1 bit for w_execute_cfg_test_loopback
    #         "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
    #         "6'h1A", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
    #         "6'h18"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
    #     ]
    # ]
    # SDG7102A SETTINGS
    hex_lists = [
        [
            "4'h2",  # firmware id
            "4'hF",  # op code for execute
            "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            "6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            "6'h08", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
        ]
    ]           

    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code="ihb")
   
    # boolean to store overall test pass or fail
    PASS = True

    # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
    # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
    wordList =   list(range(24)) #[23]
    words = []

    start_readback = time.process_time()
    for iW in wordList: #range(nwords):

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
        sw_read32_0, sw_read32_1, _, _ = ROUTINE_sw_read32(print_code = "ihb")
        
        # update
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # store data
        words.append(int_to_32bit(sw_read32_0)[::-1])
    
    s = ''.join(words)
    #s = split_bits_to_numpy(s[22:-10],3)
    
    print(len(words), s)
    # start = 0
    # npix = []
    # deadpix = []
    # deadbit = []
    # while True:
    #     index = s.find("111", start)
    #     if index == -1:
    #         break
    #     npix.append(index/3)
    #     start = index +1

    # start = 0
    # while True:
    #     index_deadbit = s.find("1", start)
    #     if index_deadbit == -1:
    #         break
    #     deadpix.append(int((index_deadbit+1)/3))
    #     deadbit.append(round(((((index_deadbit+1)/3)-int((index_deadbit+1)/3))*3)))
    #     start = index_deadbit +1
    # print(f"pixel number {npix} is programmed")
    # {print(f"pixel number {deadpix[ind]}, bit {deadbit[ind]} is dead") for ind in range(len(deadbit))}
    return None



#<<Registered w/ Spacely as ROUTINE 13, call as ~r13>>
def ROUTINE_scanChain_CDF():

    # Note we do not yet have a smoke test. verify this on scope as desired.
    
    # hex lists                                                                                                                    
    hex_lists = [
        #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h05", "1'h1", "1'h0", "5'h09", "6'h28"],  #BK4600HLEV
        #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h09", "6'h28"],  #BSDG7102A
        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
        # ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h14", "1'h1", "1'h0", "5'h0B", "6'h28"],#BSDG7102A and CARBOARD new setup
          
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # w_cfg_static_0_reg_pack_data_array_0_IP2
         # SPARE bits:  "3'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2"

  

    ]

    ROUTINE_sw_write32_0(hex_lists,doPrint=False)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32()
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 24 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    VHLEV = 0.1

    #voltage step increment in the ASIC
    #The Pulse generator voltage is divided by 2 at the ASIC input vin_test due to the 50ohm divider
    #each voltage step is then set with 2.vstep
    #1mV equals 25e- (TBD!!!!!)
    #vstep_asic = 0.001
    #vstep_asic = 0.01

    S = 40e-6           #Charge Sensitivity in V/e-
    #npulse_step = 450    #number of charge settings 
    #npulse_step = 20

    # define range of asic voltages
    v_min = 0.025
    v_max = 0.1
    v_step = 0.0005
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # number of samples to run for each charge setting
    nsample = 1000
    
         #number of sample for each charge settings

    outDir = datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.3f}_nSample{nsample:.3f}"
    outDir = os.path.join("data", outDir)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)

    # for i in tqdm.tqdm(range(1,npulse_step+1), desc="Voltage Step"):
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0 
            return 
        #BK4600HLEV_SWEEP(v_asic*2)
        SDG7102A_SWEEP(v_asic*2)
        #SDG7102A_SWEEP(v_asic)  # we used 50 ohm output load settings in the pulse generator

        save_data = []
        
        for j in tqdm.tqdm(range(nsample), desc="Number of Samples", leave=False):
            #start = time.time()
            #hex_lists = [["4'h2", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(nwrites)]
            #sw_read32_0_expected_list = [int_to_32bit_hex(0)]*len(hex_lists)

            # call ROUTINE_sw_write32_0
            #ROUTINE_sw_write32_0(hex_lists,doPrint=False)
            #print(f"time to do the for first part of the loop is {time.time()-start} second")
            #sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code = "ihb")
  
            # send an execute for test 1 and loopback enabled
            # https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L251-L260
            #start_exec = time.process_time()

            # BK4600HLEV SETTINGS
            # hex_lists = [
            #     [
            #         "4'h2",  # firmware id
            #         "4'hF",  # op code for execute
            #         "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            #         "6'h0A", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            #         "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            #         "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            #         "6'h08", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            #         "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
            #     ]
            # ]

            # SDG7102A SETTINGS
            hex_lists = [
                [
                    "4'h2",  # firmware id
                    "4'hF",  # op code for execute
                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                    "6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                    "1'h0",  # 1 bit for w_execute_cfg_test_loopback
                    "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                    "6'h08", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                    "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                ]
            ]           
            #   SDG7102A SETTINGS, CARBOARD and NEW SETUP
            # hex_lists = [
            #     [
            #         "4'h2",  # firmware id
            #         "4'hF",  # op code for execute
            #         "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            #         "6'h1C", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            #         "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            #         "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            #         "6'h08", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            #         "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
            #     ]
            # ]
            ROUTINE_sw_write32_0(hex_lists, doPrint=False)
            #read_exec=time.process_time()-start_exec
            #print(f"exec_time={read_exec}")

            #sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code="ihb")
        
            # boolean to store overall test pass or fail
            #PASS = True

            # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
            # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
            

            # nwords = 24 # 24 words * 32 bits/word = 768 bits - I added one in case
            wordList = [0] # list(range(24))
            words = ["0"*32] * 24
            #words = []

            #start_readback = time.process_time()
            for iW in wordList: #range(nwords):

                # send read
                address = "8'h" + hex(iW)[2:]
                hex_lists = [
                    ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                ]
                ROUTINE_sw_write32_0(hex_lists,doPrint=False)
                
                # read back data
                sw_read32_0, sw_read32_1, _, _ = ROUTINE_sw_read32(do_sw_read32_1=False)
     

                # store data
                # words.append(int_to_32bit(sw_read32_0)[::-1])
                words[iW] = int_to_32bit(sw_read32_0)[::-1]
            
            #read_time=time.process_time()-start_readback

            #print(f"readback_time={read_time}")
            
            s = [int(i) for i in "".join(words)]
            save_data.append(s)

        # save the data to a file
        save_data = np.stack(save_data, 0)
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npz")
        np.savez(outFileName, **{"data": save_data})


    return None



#<<Registered w/ Spacely as ROUTINE 14, call as ~r14>>
def ROUTINE_DNN_readout(loopbackBit=0):
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    ]

    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")


    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")


    #prepare list of pixels
    pixelListToProgram =  [82, 78, 74,80, 76,72] # [74, 75, 72, 73, 77, 76, 81, 138, 139, 142, 143, 146, 137, 136, 141] #  #list(range(0,256))
    pixelSettingsToProgram = [3,3,2,3,3,2] #[3, 2] + [3] * 12 + [1] #   # #[3]*256
    pixelConfig = genPixelProgramList(pixelListToProgram, pixelSettingsToProgram)

    # Programming the NN weights and biases
    hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig)
    # print(hex_list)
    # print("Printing DNN config")
    ROUTINE_sw_write32_0(hex_lists, doPrint=False)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

    hex_lists = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h1",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "4'h0", # 3 bits for spare_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for test number
            "7'h4", # 6 bits test sample
            "7'h3F"  # 6 bits for test delay
        ]
	
    ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

    # NEED SLEEP TIME BECAUSE FW TAKES 53ms (5162 shift register at 100KHz speed) which is slower than python in this case
    time.sleep(0.5)

    # # hex lists                                                                                                                    
    hex_lists = [
        #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h05", "1'h1", "1'h0", "5'h09", "6'h28"],
       # ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h14", "1'h1", "1'h0", "5'h0B", "6'h28"], #Setting with carboard and new pulse generator
        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
        #["4'h2", "4'h2", "4'h0", "1'h0","6'h0A", "1'h1", "1'h0", "5'h04", "6'h28"],
          
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 1 is selected: "1'h1"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay  disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"

         # SPARE bits:  "4'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2"

    ]

    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ibh")
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    
    # DODO SETTINGS
    hex_lists = [
        [
            "4'h2",  # firmware id
            "4'hF",  # op code for execute
            "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            "6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            "6'h06", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            "6'h05"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
        ]
    ]       
    # hex_lists = [
    #     [
    #         "4'h2",  # firmware id
    #         "4'hF",  # op code for execute
    #         "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
    #         "6'h1C", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
    #         f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
    #         "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
    #         "6'h09", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
    #         "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
    #     ]
    # ]

    #CRISTIAN SETTINGS = WORKING
    
    # hex_lists = [
    #     [
    #         "4'h2",  # firmware id
    #         "4'hF",  # op code for execute
    #         "1'h0",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
    #         "6'h03", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
    #         f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
    #         "4'h4",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
    #         "6'h06", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
    #         "6'h05"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
    #     ]
    # ]

    #CRISTIAN + DODO SETTINGS = WORKING
    
    # hex_lists = [
    #     [
    #         "4'h2",  # firmware id
    #         "4'hF",  # op code for execute
    #         "1'h0",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
    #         "6'h03", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
    #         f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
    #         "4'h4",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
    #         "6'h09", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min # VERY IMPORTANT, must be tuned properly to sample the data at the right time
    #         "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min # VERY IMPORTANT
    #     ]
    # ]

    print("HEX LIST CONTENT: ", gen_sw_write32_0(hex_lists[0]))
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code="ihb")
    # time.sleep(1)
    # boolean to store overall test pass or fail
    # PASS = True

    # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
    # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
    nwords = 24 # 24 words * 32 bits/word = 768 bits - I added one in case
    words = []
    
    for iW in range(nwords):

        # send read
        address = "8'h" + hex(iW)[2:]
        hex_lists = [
            ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
        ]
        ROUTINE_sw_write32_0(hex_lists)
        
        # read back data
        #sw_read32_0_expected = int(sw_read32_0_expected_list[iW], 16)
        #sw_read32_1_expected = int("10100000100010",2) # from running op codes. see here for the mapping https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L179-L196
        #sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, sw_read32_1_nbitsToCheck = 14, print_code = "ihb")
        sw_read32_0, sw_read32_1, _, _ = ROUTINE_sw_read32() #print_code = "ihb")
        
        # update
        #PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # store data
        words.append(int_to_32bit(sw_read32_0)[::-1])
    
    s = ''.join(words)
    #s = split_bits_to_numpy(s[22:-10],3)
    # dnn_0=hex(int(s[:48][::-1],2))
    # dnn_1=hex(int(s[48:96][::-1],2))
    # print(f"dnn_0 ={dnn_0} and dnn_1 ={dnn_1} ")
    # print(len(words), s)
    # print(s.find("1"))

    temp = np.array([int(i) for i in s]).reshape(256,3)
    superpixel_array = np.zeros((8,32))
    for iP, val in enumerate(temp):
        if 1 in val:
            print(iP, val)
            result_string = ''.join(val.astype(str))
            row = 7-find_grid_cell_superpix(iP)[0]
            col = find_grid_cell_superpix(iP)[1]
            superpixel_array[row][col]=int(thermometric_to_integer(result_string))
            even_columns = superpixel_array[:,::2]
            odd_columns = superpixel_array[:,1::2]
            row_sums = np.concatenate((even_columns.sum(axis=1),odd_columns.sum(axis=1)))
    print(f"the input vector to the DNN is {row_sums}")       
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ibh")
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    
    # DODO SETTINGS
    hex_lists = [
        [
            "4'h2",  # firmware id
            "4'hF",  # op code for execute
            "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            "6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h4",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            "6'h06", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            "6'h05"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
        ]
    ]       


    print("HEX LIST CONTENT: ", gen_sw_write32_0(hex_lists[0]))
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(print_code="ihb")
    # time.sleep(1)
    # boolean to store overall test pass or fail
    # PASS = True

    # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
    # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
    nwords = 24 # 24 words * 32 bits/word = 768 bits - I added one in case
    words = []
    
    for iW in range(nwords):

        # send read
        address = "8'h" + hex(iW)[2:]
        hex_lists = [
            ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
        ]
        ROUTINE_sw_write32_0(hex_lists)
        
        # read back data
        #sw_read32_0_expected = int(sw_read32_0_expected_list[iW], 16)
        #sw_read32_1_expected = int("10100000100010",2) # from running op codes. see here for the mapping https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L179-L196
        #sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, sw_read32_1_nbitsToCheck = 14, print_code = "ihb")
        sw_read32_0, sw_read32_1, _, _ = ROUTINE_sw_read32() #print_code = "ihb")
        
        # update
        #PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # store data
        words.append(int_to_32bit(sw_read32_0)[::-1])
    
    s = ''.join(words)
    #s = split_bits_to_numpy(s[22:-10],3)
    dnn_0=hex(int(s[:48][::-1],2))
    dnn_1=hex(int(s[48:96][::-1],2))
    print(f"dnn_0 ={dnn_0} and dnn_1 ={dnn_1} ")
    print(len(words), s)
    print(s.find("1"))


    return None




def pixelProg_scanChain_CDF(pixelList=[0], pixelSettings=[2], scan_address=[0], vmin=0.025, vmax = 0.2, vstep = 0.0005, nsample =100):
    # STEP 1: WE PROGRAM THE PIXELS
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    ]
    
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")


    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
    ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")


    #prepare list of pixels
    pixelListToProgram =  pixelList
    pixelSettingsToProgram = pixelSettings
    pixelConfig = genPixelProgramList(pixelListToProgram, pixelSettingsToProgram)

    # Programming the NN weights and biases
    hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig)
    # print(hex_list)
    # print("Printing DNN config")
    ROUTINE_sw_write32_0(hex_lists, doPrint=False)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

    hex_lists = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h1",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "4'h0", # 3 bits for spare_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for test number
            "7'h4", # 6 bits test sample
            "7'h3F"  # 6 bits for test delay
        ]
	
    ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

    # NEED SLEEP TIME BECAUSE FW TAKES 53ms (5162 shift register at 100KHz speed) which is slower than python in this case
    time.sleep(1)



    #STEP 2 - WE EXTRACT THE S-CURVE

    # hex lists                                                                                                                    
    hex_lists = [

        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
          
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # w_cfg_static_0_reg_pack_data_array_0_IP2
         # SPARE bits:  "3'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2

    ]

    ROUTINE_sw_write32_0(hex_lists,doPrint=False)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32()
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 24 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    VHLEV = 0.1


    S = 40e-6           #Charge Sensitivity in V/e-
    #npulse_step = 450    #number of charge settings 
    #npulse_step = 20

    # define range of asic voltages
    v_min = vmin #0.025
    v_max = vmax #0.1
    v_step = vstep # 0.0005
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # number of samples to run for each charge setting
    nsample = nsample #1000
    
         #number of sample for each charge settings
    pixNumber = pixelList[0]
    configBit= pixelSettings[0]
    scanAddress=scan_address[0]
    # test_path = "/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea/CMSPIX28_DAQ/spacely/PySpacely/data/2024-10-25_MATRIX"
    test_path = "/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea/CMSPIX28_DAQ/spacely/PySpacely/data/test"
    now = datetime.now()

    #folder_name = now.strftime("%Y-%m-%d_%H-%M-%S") + f"_scanAddress{scanAddress}" # Format: YYYY-MM-DD_HH-MM-SS
    #folder_name = now.strftime("%Y-%m-%d") + f"_scanAddress{scanAddress}" # Format: YYYY-MM-DD_HH-MM-SS
    #full_folder_path = os.path.join(test_path, folder_name)

    # Create the new directory
    #os.makedirs(full_folder_path, exist_ok=True)  # Create the folder


    outDir =  f"pixel{pixNumber}_config{configBit}_scanAddress{scanAddress}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.3f}_nSample{nsample:.3f}"
    outDir = os.path.join(test_path, outDir)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)

    # for i in tqdm.tqdm(range(1,npulse_step+1), desc="Voltage Step"):
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0 
            return 
        #BK4600HLEV_SWEEP(v_asic*2)
        SDG7102A_SWEEP(v_asic*2)
        #SDG7102A_SWEEP(v_asic)  # we used 50 ohm output load settings in the pulse generator

        save_data = []
        
        for j in tqdm.tqdm(range(nsample), desc="Number of Samples", leave=False):

            # SDG7102A SETTINGS
            hex_lists = [
                [
                    "4'h2",  # firmware id
                    "4'hF",  # op code for execute
                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                    "6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                    "1'h0",  # 1 bit for w_execute_cfg_test_loopback
                    "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                    "6'h08", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                    "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                ]
            ]           
  
            ROUTINE_sw_write32_0(hex_lists, doPrint=False)
 
            wordList = scan_address #[0] # list(range(24))
            words = ["0"*32] * 24
            #words = []

            #start_readback = time.process_time()
            for iW in wordList: #range(nwords):

                # send read
                address = "8'h" + hex(iW)[2:]
                hex_lists = [
                    ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                ]
                ROUTINE_sw_write32_0(hex_lists,doPrint=False)
                
                # read back data
                sw_read32_0, sw_read32_1, _, _ = ROUTINE_sw_read32(do_sw_read32_1=False)
     

                # store data
                # words.append(int_to_32bit(sw_read32_0)[::-1])
                words[iW] = int_to_32bit(sw_read32_0)[::-1]
            
            #read_time=time.process_time()-start_readback

            #print(f"readback_time={read_time}")
            
            s = [int(i) for i in "".join(words)]
            save_data.append(s)

        # save the data to a file
        save_data = np.stack(save_data, 0)
        # outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npz")
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.h5")
        # np.savez(outFileName, **{"data": save_data})
        with h5py.File(outFileName, 'w') as hf:
            hf.create_dataset("data", data=save_data)

    return None


#<<Registered w/ Spacely as ROUTINE 15, call as ~r15>>
def ROUTINE_pixelProg_scanChain_CDF():
    nsample = 10
    vstep = 0.001
    scanList = [0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 20]   # we scanonly the right side of the matrix
    # scanList = [ 20]   # we scanonly the right side of the matrix
    for i in scanList:
        for j in range(int(i*32/3)+((i*32/3)>int(i*32/3)),round((i+1)*32/3)):   #we only test the pixels which have the 3 bits in a single DATA_ARRAY_) address
            pixelProg_scanChain_CDF(pixelList=[j], pixelSettings=[1], scan_address=[i], vmin=0.02, vmax = 0.1, vstep = vstep, nsample =nsample)

    pixelProg_scanChain_CDF(pixelList=[7], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[8], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[9], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[10], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    # #pixelProg_scanChain_CDF(pixelList=[11], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.001, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[12], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[13], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[14], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[15], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[16], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[17], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[18], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[19], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[20], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    pixelProg_scanChain_CDF(pixelList=[21], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[22], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[23], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[24], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[25], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[26], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[27], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[28], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[29], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[30], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[31], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    # pixelProg_scanChain_CDF(pixelList=[64], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[65], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[66], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[67], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[68], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[69], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[70], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[71], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[72], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[73], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # #pixelProg_scanChain_CDF(pixelList=[74], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    # pixelProg_scanChain_CDF(pixelList=[75], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[76], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[77], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[78], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[79], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[80], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[81], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[82], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[83], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[84], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # #pixelProg_scanChain_CDF(pixelList=[85], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)    

    # pixelProg_scanChain_CDF(pixelList=[128], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[129], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[130], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[80], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[81], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[82], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[83], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[84], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    #<<Registered w/ Spacely as ROUTINE 14, call as ~r164>
#<<Registered w/ Spacely as ROUTINE 16, call as ~r16>>
def ROUTINE_DNN_FINAL(loopbackBit=0, patternIndexes = [0], verbose=False):
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    ]

    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")


    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    ROUTINE_sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")


    #Manual programming for debugging
    # pixels = [
    #     [list(range(0,256)), [3]*256],
    #     #[[74, 75, 72, 73, 77, 76, 81, 138, 139, 142, 143, 146, 137, 136, 141], [3, 2] + [3] * 12 + [1]],
    #     [[16, 12, 21, 17, 13, 9, 5, 83, 79, 75, 71, 67,82, 78, 74], [3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2]],
    #     [[82, 78, 74,80, 76,72], [3,3,2,3,3,2]],                                                                                        # RTL should see low momentum 1
    #     [[206, 202, 211, 207, 203, 199, 195, 145, 141, 137, 133, 129, 144, 140, 136], [3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2]],  # RTL should see low momentum 2
    #     [[86,82,78,74,70, 83,67, 80,76,72], [3,3,3,3,3,  3,2, 3,3,3]],                                                                     # RTL should see low momentum 1
    #     [[148,144,140,136,132, 149,145, 150,146,142], [3,3,3,3,3,  3,2, 3,3,3]],    # RTL should see low momentum 0
    # ]  
    #pixelLists = [i[0] for i in pixels]
    #pixelValues = [i[1] for i in pixels]

    # load all of the configs
    filename = "/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_D/tb/dnn/csv/l6/compouts.csv"
    pixelLists, pixelValues = genPixelConfigFromInputCSV(filename)

    # loop over test cases
    patternIndexes = range(len(pixelLists)) if patternIndexes == None else patternIndexes
    
    # list to save to
    yprofiles = []
    readouts = []

    for iP in tqdm.tqdm(patternIndexes):

        # pick up pixel config for the given pattern
        pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])

        # Programming the NN weights and biases
        hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig)
        ROUTINE_sw_write32_0(hex_lists, doPrint=False)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() 

        hex_lists = [
            [
                "4'h1",  # firmware id
                "4'hf",  # op code d for execute
                "1'h1",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
                "4'h0", # 3 bits for spare_index_max
                "1'h0",  # 1 bit for w_execute_cfg_test_loopback
                "4'h1",  # 4 bits for test number
                "7'h4", # 6 bits test sample
                "7'h3F"  # 6 bits for test delay
            ]
        
        ]
        ROUTINE_sw_write32_0(hex_lists)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ihb")

        # NEED SLEEP TIME BECAUSE FW TAKES 53ms (5162 shift register at 100KHz speed) which is slower than python in this case
        time.sleep(0.5)

        # # hex lists                                                                                                                    
        hex_lists = [
            ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
            #["4'h2", "4'h2", "3'h0", "1'h0", "1'h1","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
            
            # BxCLK is set to 10MHz : "6'h28"
            # BxCLK starts with a delay: "5'hB"
            # BxCLK starts LOW: "1'h0"
            # Superpixel 1 is selected: "1'h1"
            # scan load delay is set : "6'h0A"                 
            # scan_load delay  disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"

            # SPARE bits:  "4'h0"
            # Register Static 0 is programmed : "4'h2"
            # IP 2 is selected: "4'h2"

        ]

        ROUTINE_sw_write32_0(hex_lists)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() #print_code = "ibh")
        
        # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
        
        # # DODO SETTINGS
        hex_lists = [
            [
                "4'h2",  # firmware id
                "4'hF",  # op code for execute
                "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                "6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                #"4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST          
                "6'h08", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
            ]
        ]       

        ROUTINE_sw_write32_0(hex_lists)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = ROUTINE_sw_read32() 

        # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
        # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
        nwords = 24 # 24 words * 32 bits/word = 768 bits - I added one in case
        words = []
        
        for iW in range(nwords):

            # send read
            address = "8'h" + hex(iW)[2:]
            hex_lists = [
                ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
            ]
            ROUTINE_sw_write32_0(hex_lists)
            
            sw_read32_0, sw_read32_1, _, _ = ROUTINE_sw_read32() 

            # store data
            words.append(int_to_32bit(sw_read32_0)[::-1])
        
        s = ''.join(words)
        row_sums = [0]*16
        if s.find("1") != -1:
            #Y-projection
            temp = np.array([int(i) for i in s]).reshape(256,3)
            superpixel_array = np.zeros((8,32))
            for iP, val in enumerate(temp):
                if 1 in val:
                    result_string = ''.join(val.astype(str))
                    row = 7-find_grid_cell_superpix(iP)[0]
                    col = find_grid_cell_superpix(iP)[1]
                    superpixel_array[row][col]=int(thermometric_to_integer(result_string[::-1]))
                    even_columns = superpixel_array[:,::2].sum(axis=1)
                    odd_columns = superpixel_array[:,1::2].sum(axis=1)
                    row_sums = []
                    for i, j in zip(even_columns, odd_columns):
                        row_sums.append(int(i))
                        row_sums.append(int(j))
                    # row_sums = np.array(row_sums) 
            row_sums = row_sums[::-1]
                 

        dnn_nwords = 8
        dnn_words = []
        for iW in range(dnn_nwords):
            # send read
            address = "8'h" + hex(iW)[2:]
            hex_lists = [
                ["4'h2", "4'hD", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_1
            ]
            ROUTINE_sw_write32_0(hex_lists)
            sw_read32_0, sw_read32_1, _, _ = ROUTINE_sw_read32() 

            # store data
            dnn_words.insert(0, int_to_32bit(sw_read32_0))

        dnn_s = ''.join(dnn_words)

        if verbose:
            print(f"the input vector to the DNN is {row_sums}")
            # Printout of data seen in FW
            dnn_0=dnn_s[-48:] 
            dnn_1=dnn_s[-96:-48] 
            bxclk_ana=dnn_s[-144:-96] 
            bxclk=dnn_s[-192:-144] 
            print(f"reversed dnn_0     = {dnn_0}", len(dnn_0), hex(int(dnn_0, 2)))
            print(f"reversed dnn_1     = {dnn_1}", len(dnn_1), hex(int(dnn_1, 2))) 
            print(f"reversed bxclk_ana = {bxclk_ana}", len(bxclk_ana), hex(int(bxclk_ana, 2)))
            print(f"reversed bxclk     = {bxclk}", len(bxclk), hex(int(bxclk, 2)))   
            get_power()

        # append to y profile list and dnn output list
        yprofiles.append(row_sums)
        readouts.append(dnn_s)

    # save to csv file
    yprofileOutputFile = "yprofiles.csv"
    with open(yprofileOutputFile, 'w', newline="") as file:
        writer = csv.writer(file)
        writer.writerows(yprofiles)
    
    # save readouts to csv
    readoutOutputFile = "readout.csv"
    with open(readoutOutputFile, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(readouts)
    
    return None

