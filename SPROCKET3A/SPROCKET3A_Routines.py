import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

import itertools


def onstartup():

    # GLOBAL CONFIG VARIABLES
    assume_defaults = False
    
    sg.INSTR["car"].axi_registers = {"apg": ["apg_run", "apg_write_channel", "apg_read_channel",
                     "apg_sample_count","apg_n_samples","apg_write_buffer_len",
                     "apg_next_read_sample","apg_wave_ptr","apg_status", "apg_control",
                     "apg_dbg_error",
                             "apg_clear"],
                     "spi_apg": ["spi_apg_run", "spi_apg_write_channel", "spi_apg_read_channel",
                     "spi_apg_sample_count","spi_apg_n_samples","spi_apg_write_buffer_len",
                                 "spi_apg_next_read_sample","spi_apg_wave_ptr","spi_apg_status", "spi_apg_control",
                                 "spi_apg_dbg_error", "spi_apg_clear"],
                     "lpgbt_fpga":  ["uplinkRst", "mgt_rxpolarity", "lpgbtfpga_status"]}

    print("====================================")
    print("=== Starting SP3A Default Setup ===")

    if not assume_defaults:
        do_setup = input("Press enter to begin or 'n' to skip >")
        if 'n' in do_setup:
            print("Skipping all setup!")
            return

    sg.INSTR["car"].debug_memory = False
        
    print("Step 1: Initializing ZCU102")

    sg.INSTR["car"].set_memory("gpio_direction",0)
    print(">  Set all AXI GPIOs as outputs")

    sg.INSTR["car"].setUsrclkFreq(int(320e6))
    print(">  Initialized Usrclk to 320 MHz")
    
    init_car =  input("Step 2: Initializing CaR Board ('n' to skip)>>>")

    if 'n' in init_car:
        print("Skipped!")
    else:

        #Basic initialization of CaR board
        sg.INSTR["car"].init_car()

        #Init CMOS I/O voltages
        print(">  Setting CMOS In/Out Voltage = 1.2V",end='')
        if not assume_defaults: 
            set_cmos_voltage = input("('n' to skip)")
        if assume_defaults or not 'n' in set_cmos_voltage:
            sg.INSTR["car"].set_input_cmos_level(1.2)
            sg.INSTR["car"].set_output_cmos_level(1.2)

       

    init_asic = input("Step 3: Initializing ASIC ('n' to skip)>>>")

    if 'n' in init_asic:
        print("Skipped!")
    else:

        #Config Si5345
        print(">  Configuring SI5345 w/ config option 1 (disable refclk)")
        #if not assume_defaults:
        #    config_si5345 = input("('n' to skip)")
        #if assume_defaults or not 'n' in config_si5345:
        sg.INSTR["car"].configureSI5345(1)
        #input("?")
        
        assert_reset()
        #input("?")
        time.sleep(0.1)
        deassert_reset()
        #input("?")
        print(">  Pulsed digital Reset")
        
        spi_write_tx_config(TX_REG_DEFAULTS)
        #input("?")
        print(">  Wrote default transmitter configuration")

      
        print(">  Configuring SI5345 w/ config option 2 (enable refclk)")
        #if not assume_defaults:
        #    config_si5345 = input("('n' to skip)")
        #if assume_defaults or not 'n' in config_si5345:
        sg.INSTR["car"].configureSI5345(2)
        #input("?")
        
    print("Step 4: Uplink Reset")
    sg.INSTR["car"].set_memory("uplinkRst",1)
    time.sleep(0.1)
    sg.INSTR["car"].set_memory("uplinkRst",0)
    print(">  Pulsed uplink reset")
        
    print("=== Finished SP3A Default Setup ===")
    print("===================================")


            


#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_bit_bang_test():
    """Test how fast data can be bitbanged out using the AXI GPIO IP."""

    #0 = output, 1 = input
    sg.INSTR["car"].set_memory("gpio_direction",0x0)

    METHOD = int(input("Bitbang method?"))

    sg.log.info("Begin Bit Banging")
    try:
        while True:
            if METHOD == 1:
                sg.INSTR["car"].set_memory("gpio_data",0x2)
                sg.INSTR["car"].set_memory("gpio_data",0x0)
            elif METHOD == 2:
                x = sg.INSTR["car"].get_memory("gpio_data")
                sg.INSTR["car"].set_memory("gpio_data", 0x2 ^ x)
    except KeyboardInterrupt:
        sg.log.debug("Interrupted")

    sg.log.info("End Bit Banging")
        
    

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_check_spi_loopback():
    """Write a register over SPI and read back its value to confirm the SPI interface is working."""

    for test_val in [49, 102, 1]:
        spi_write_reg("comp_fall_bufsel",test_val)
    
        val = spi_read_reg("comp_fall_bufsel")

        if val == 0:
            sg.log.warning("Read back 0. Retrying...")
            val = spi_read_reg("comp_fall_bufsel")

        if val == test_val:
            sg.log.info("SPI Loopback Passed!")
        else:
            sg.log.error(f"SPI Loopback Failed: Wrote {test_val} (bin:{bin(test_val)}), Read {val} (bin:{bin(val)})")
            return



def ns_to_cycles(num_ns):
    return int(num_ns/1.5625) 

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_basic_signals():
    """Program some basic patterns in the pattern generator and observe outputs"""


    #Try to replicate the commands sent in slides 23, 24, and 25
    #First, observe the results with oscilloscope
    #We can also add some basic firmware that will grab these signals as digital values.

    #Make sure you exercise all the potential options of the PG.

    #EXAMPLE:
    #50 cycles = 78.125 ns
    # spi_write(COMP_RISE_CALC, 0)
    # spi_write(COMP_FALL_CALC, 50)

    #input("CHECK: Is PW of 78.125 ns observed on calc? (Press enter to continue)")

    #Global Counter Period = 15 us
    spi_write_reg("global_counter_period",ns_to_cycles(15000))

    #(1) Phase Control Signals
    spi_write_reg("comp_rise_calc",ns_to_cycles(0))
    time.sleep(0.1)
    spi_write_reg("comp_fall_calc",ns_to_cycles(500))
    spi_write_reg("comp_rise_read",ns_to_cycles(0))
    spi_write_reg("comp_fall_read",ns_to_cycles(1000))
    spi_write_reg("comp_rise_Rst",ns_to_cycles(1000))
    spi_write_reg("comp_fall_Rst",ns_to_cycles(5000))
    spi_write_reg("comp_rise_bufsel",ns_to_cycles(5000))
    spi_write_reg("comp_fall_bufsel",ns_to_cycles(15000))

    print("CHECK 1 Expected Values")
    print("calc:   0~500ns")
    print("read:   0~1us")
    print("Rst:    1~5us")
    print("bufsel: 5~15us")

    #At default logic_clk_div settings, APG is driven at 40 MHz
    # 1000 * 25 ns = 25 us
    get_glue_wave(1000)
    
    input("")

    #(2) Full Readout
    spi_write_reg("FULL_READOUT",1)

    print("CHECK 2 -- is full readout asserted?")

    get_glue_wave(1000)

    input("")

    #(3) Qequal / DACclr Patterns

    test_pattern = 0
    for i in range(5):
        test_pattern = (test_pattern << 20) + 0b11001100110011001100

    spi_write_reg("Qequal_pattern",test_pattern)
    spi_write_reg("DACclr_pattern",test_pattern)
        
    #spi_write_reg("Qequal_pattern",0b0101010101001100110011)
    #spi_write_reg("DACclr_pattern",0b01010101010011001100110011)
    
    spi_write_reg("Qequal_pattern_delay",3)
    spi_write_reg("DACclr_pattern_delay",4)

    print("CHECK 3 -- Qequal and DACclr patterns?")

    get_glue_wave(1000)
    input("")






#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_spi_shell():
    """Microshell to interact with the AXI registers and debug the design."""

    
    SPI_REGISTERS = list(SPI_REG.keys())

    while True:

        # Print register contents
        i = 0
        for reg in SPI_REGISTERS:
            #reg_contents = sg.INSTR["car"].get_memory(reg)

            #if reg == "spi_status":
            #    reg_contents = SPI_Status(reg_contents)
            
            print(f"{i}. {reg : <16} ")
            i = i+1

        write_reg_num = input("which reg?").strip()

        if write_reg_num == "":
            continue

        if write_reg_num == "q":
            return

        try:
            this_reg = SPI_REGISTERS[int(write_reg_num)]
        except ValueError:
            print("ERROR")
            continue

        operation = input("op (r/w)?").strip()

        if operation == "w":

            try:
                write_val = int(input("val?"))
            except ValueError:
                print("ERROR")
                continue

            spi_write_reg(this_reg,write_val)

        else:
            print(spi_read_reg(this_reg))


#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_get_glue_wave():

    N = input("How many samples do you want to take?")
    N = int(N)

    get_glue_wave(N)


#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_write_tx_config():
    """Write ALL fields of the tx config to their default values."""
    spi_write_tx_config(TX_REG_DEFAULTS)


#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_Update_tx_config():
    """Update a single field of the tx config, which is specified interactively."""

    key_list = list(TX_REG_DEFAULTS.keys())

    for i in range(len(key_list)):
        print(f"{i}. {key_list[i]}")

    user_choice = int(input("which # cfg to modify? >>>"))
    user_val = int(input("New value >>>"))

    spi_update_tx_reg(key_list[user_choice], user_val)
    
    #TX_REG_DEFAULTS[key_list[user_choice]] = user_val

    #spi_write_tx_config(TX_REG_DEFAULTS)


#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_get_rx_status():
    """Check the status of the lpgbt-fpga receiver."""

    rx_status_bin = sg.INSTR["car"].get_memory("lpgbtfpga_status")

    uplinkrdy = rx_status_bin & 0x1
    uplinkFEC = (rx_status_bin & 0x2) >> 1
    uplinkEcData = (rx_status_bin & 0xC) >> 2
    uplinkIcData = (rx_status_bin & 0x30) >> 4
    uplinkPhase = (rx_status_bin & 0x1C0) >> 6
    mgt_rx_rdy  = (rx_status_bin & 0x200) >> 9
    # more debug signals 2024.09.10
    bitslip_counter  = (rx_status_bin & 0x00FFC00) >> 10
    sta_headerLocked = (rx_status_bin & 0x0100000) >> 20
    sta_gbRdy        = (rx_status_bin & 0x0200000) >> 21
    datapath_rst_s   = (rx_status_bin & 0x0400000) >> 22
    rst_pattsearch   = (rx_status_bin & 0x0800000) >> 23
    rst_gearbox      = (rx_status_bin & 0x1000000) >> 24
    sta_headerFlag   = (rx_status_bin & 0x2000000) >> 25
    uplinkReady      = (rx_status_bin & 0x4000000) >> 26

    #print(rx_status_bin)
    #print(rx_status_bin & 0x100)
    #print(0x200)

    print("~ ~ ~ Rx Status ~ ~ ~")
    print(f"(binary: {bin(rx_status_bin)})")
    print(f"Uplink Ready:   {uplinkrdy}")
    print(f"Uplink FEC Err: {uplinkFEC}")
    print(f"Uplink EC Data: {bin(uplinkEcData)}")
    print(f"Uplink IC Data: {bin(uplinkIcData)}")
    print(f"Uplink Phase:   {uplinkPhase}")
    print(f"Mgt Rx Ready:   {mgt_rx_rdy}")
    # more debug signals 2024.09.10
    print(f"frame_aligner                 bitslip_counter  : {bitslip_counter}")
    print(f"frame_aligner                 sta_headerLocked : {sta_headerLocked}")
    print(f"RX Gearbox Ready              sta_gbRdy        : {sta_gbRdy}")
    print(f"not(RX Gearbox Ready)         datapath_rst_s   : {datapath_rst_s}")
    print(f"Rx ready from the transceiver rst_pattsearch   : {rst_pattsearch}")
    print(f"not(sta_headerLocked)         rst_gearbox      : {rst_gearbox}")
    print(f"frame_aligner(one pulse)      sta_headerFlag   : {sta_headerFlag}")
    print(f"uplink decoder ready          uplinkReady      : {uplinkReady}")

#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_pulse_uplinkRst():

    sg.INSTR["car"].set_memory("uplinkRst",1)

    time.sleep(0.1)

    sg.INSTR["car"].set_memory("uplinkRst",0)



    
    
    

#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_run_array_serial_pattern():

    user_pattern_str = input("Enter a binary pattern>>>")

    #Split the user's pattern by characters:
    user_pattern = []
    for c in user_pattern_str:
        if c == "1":
            user_pattern.append(1)
        elif c == "0":
            user_pattern.append(0)


    pattern_glue = sg.gc.dict2Glue({"array_serial_0":user_pattern})

    sg.pr.run_pattern(sg.gc.read_glue(pattern_glue), True)
    

#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_run_APG_test_pattern():

    test_pattern = [0,1,2,3,4,5,6,7]

    pattern_glue = GlueWave(test_pattern,None,"Caribou/Caribou/apg")

    sg.pr.run_pattern(pattern_glue,True)



#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_posedge_count():
    """Estimate the activity on certain internal FPGA clocks by counting posedges"""

    counts = ["count_0", "count_1", "count_2", "count_3", "count_4"]
    clks   = ["axi_clk", "uplinkMgtWordParity", "clk40_o", "wave_clk", "not conn"]
    count_s1 = []
    count_s2 = []
    freq = []

    for count in counts:
        count_s1.append(sg.INSTR["car"].get_memory(count))

    time.sleep(1)

    for count in counts:
        count_s2.append(sg.INSTR["car"].get_memory(count))

    for i in range(len(counts)):
        freq_estimate = (count_s2[i] - count_s1[i])/(count_s2[0] - count_s1[0]) * 100e6
        print(f"{clks[i]} Est Freq = {freq_estimate}  (Samples: {count_s2[i]}, {count_s1[i]})")
        


#<<Registered w/ Spacely as ROUTINE 12, call as ~r12>>
def ROUTINE_dataframe_read():
    """Reads current value of err counter + 1 sample from data FIFO"""


    lpgbt_rd_en = sg.INSTR["car"].get_memory("lpgbt_rd_en")

    if lpgbt_rd_en == 0:
        sg.log.warning("lpgbt_rd_en was not previously set; setting now...")
        sg.INSTR["car"].set_memory("lpgbt_rd_en",1)
        time.sleep(1)

    try:
        while True:
            input("Press enter to take sample>")

            # (1) Read lpgbt data frame
            dataframe = 0

            for i in range(8):
                dataframe_reg = sg.INSTR["car"].get_memory(f"data_frame[{i}]")
                sg.log.debug(f"Frame reg[{i}] = {dataframe_reg}")
                dataframe = dataframe + (dataframe_reg << (32*i))

            #Print Dataframe, padded to 234b (+ "0b")
            print(f"Dataframe: {dataframe:#0236b}")
                

            # (2) Read Err Count
            err_count = sg.INSTR["car"].get_memory("err_counter")
            print(f"Error Count: {err_count}")

    except KeyboardInterrupt:
        print("Finished")

    

#<<Registered w/ Spacely as ROUTINE 13, call as ~r13>>
def ROUTINE_FEC_Error_Rate_Eval():
    """Evaluate the FEC Error Rate vs Tx parameters."""
    
    par = {"tolineDrv_modDAC": [],
           "tolineDrv_empDAC": [],
           "tolineDrv_enEmp" : [],
           "tolineDrv_empDurReduce":[]}
    
    for test_condition in [1,2,3]:
        
        for i in range(1,127,4):
            for j in range(1,127,4):
                
                par["tolineDrv_modDAC"] += [127-i]
                par["tolineDrv_empDAC"] += [127-j]
                
                if test_condition == 1:
                    par["tolineDrv_enEmp"] += [0]
                    par["tolineDrv_empDurReduce"] += [0]
                elif test_condition == 2:
                    par["tolineDrv_enEmp"] += [1]
                    par["tolineDrv_empDurReduce"] += [0]
                elif test_condition == 3:
                    par["tolineDrv_enEmp"] += [1]
                    par["tolineDrv_empDurReduce"] += [1]    
                
    
    
    ####################################################
    
    key_list = list(par.keys())
    
    for k in par.keys():
        print(f"Parameter {k}: {len(par[k])} values")
        N = len(par[k])
    print(f"Expected duration for {N} values is {N/6/60} hours")
    
    tx_params = ",".join(key_list)
    print(f"n,{tx_params},Errors_in_10sec,Estimated_BER")
    
    for k in range(N):
        
 
        for key in key_list:
            spi_update_tx_reg(key, par[key][k])
            
        ROUTINE_pulse_uplinkRst()
        time.sleep(1)
        
        err_count1 = sg.INSTR["car"].get_memory("err_counter")
        time.sleep(10)
        err_count2 = sg.INSTR["car"].get_memory("err_counter")
        
        error_diff = err_count2 - err_count1
        est_ber = error_diff / (10*10.24e9)
        
        vals = ",".join([str(par[x][k]) for x in key_list])
        
        print(f"{k},{vals},{error_diff},{est_ber}")
    
    
    