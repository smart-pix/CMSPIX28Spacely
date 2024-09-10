import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *


def onstartup():

   

    # GLOBAL CONFIG VARIABLES
    assume_defaults = False

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

        #Config Si5345
        print(">  Configuring SI5345 w/ config option 2",end='')
        if not assume_defaults:
            config_si5345 = input("('n' to skip)")
        if assume_defaults or not 'n' in config_si5345:
            sg.INSTR["car"].configureSI5345(2)


    init_asic = input("Step 3: Initializing ASIC ('n' to skip)>>>")

    if 'n' in init_asic:
        print("Skipped!")
    else:
        assert_reset()
        time.sleep(0.1)
        deassert_reset()
        print(">  Pulsed digital Reset")
        
        spi_write_tx_config(TX_REG_DEFAULTS)
        print(">  Wrote default transmitter configuration")

        
    print("Step 4: Uplink Reset")
    sg.INSTR["car"].set_memory("uplinkRst",1)
    time.sleep(0.1)
    sg.INSTR["car"].set_memory("uplinkRst",0)
    print(">  Pulsed uplink reset")
        
    print("=== Finished SP3A Default Setup ===")
    print("===================================")

def random_coords():
    return [random.randint(0,9),random.randint(0,9)]

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_ZCU102_Demo_Game():

    USE_ZCU_INPUT = True
    
    player_coords = random_coords()
    candy_coords = [random_coords(), random_coords(), random_coords()]

    print(player_coords)
    print(candy_coords)

    while True:

        ate_candy_this_tick = False
        
        time.sleep(0.5)

        if USE_ZCU_INPUT:
            pushbutton_state = int(sg.INSTR["car"].get_memory("gpio_0_data"))
        else:
            pushbutton_state = int(input("pb state?"))
        print(f"Pushbutton State: {pushbutton_state}")

        if pushbutton_state == 2 and player_coords[0] < 9:
            player_coords[0] = player_coords[0]+1
        elif pushbutton_state == 4 and player_coords[1] < 9:
            player_coords[1] = player_coords[1]+1
        elif pushbutton_state == 8 and player_coords[0] > 0:
            player_coords[0] = player_coords[0]-1
        elif pushbutton_state == 16 and player_coords[1] > 0:
            player_coords[1] = player_coords[1]-1

        ## Game Ends if You Eat All Candy
        if len(candy_coords) == 0:
            break

        ## Print the Game Map
        print("Try to eat all the candy :) ")
        for i in range(10):
            print("")
            for j in range(10):

                if [i,j] == player_coords:
                    print("A",end='')

                    if [i,j] in candy_coords:
                        ate_candy_this_tick = True
                        for x in range(len(candy_coords)):
                            if candy_coords[x] == player_coords:
                                candy_coords.pop(x)
                                break

                elif [i,j] in candy_coords:
                    print("c",end='')
                else:
                    print(".",end='')

        if ate_candy_this_tick:
            print("You ate a piece of candy!")
        else:
            print("")
            


#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_bit_bang_test():

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
        
    

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_i2c_debug():

    bus = 1
    component_addr = 0x40


    for i in range(7):
        print(sg.INSTR["car"].car_i2c_read(bus, component_addr, i, 2))




def _ROUTINE_check_fw():
    """Write + readback a single value to FW to make sure the firmware is flashed."""

    #Short alias for Caribou system
    car = sg.INSTR["car"]

    TEST_VAL = 0b1010101010

    car.set_memory("spi_write_data",TEST_VAL)

    val = car.get_memory("spi_write_data")

    if val == TEST_VAL:
        sg.log.info("FW check passed!")
    else:
        sg.log.error(f"FW check failed: TEST_VAL={TEST_VAL}, read back {val}")




#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
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

def _ROUTINE_spi_address_mapping():
    """Sweep through possible SPI commands"""

    pattern_1 = 0b101010101
    pattern_2 = 0b101010001

    for offset in range(4,12,1):
        write_pattern = pattern_1 << offset
        read_pattern = pattern_2 << offset
        print(f"Write Bitstring: {bin(write_pattern)} ")

        sg.INSTR["car"].set_memory("spi_write_data", write_pattern)
        sg.INSTR["car"].set_memory("spi_data_len", 32)
        sg.INSTR["car"].set_memory("spi_trigger",1)

        time.sleep(0.1)
        print("Return Data:",bin(sg.INSTR["car"].get_memory("spi_read_data")))

        print(f"Read Bitstring: {bin(read_pattern)} ")

        sg.INSTR["car"].set_memory("spi_write_data", read_pattern)
        sg.INSTR["car"].set_memory("spi_data_len", 32)
        sg.INSTR["car"].set_memory("spi_trigger",1)

        time.sleep(0.1)
        print("Return Data:",bin(sg.INSTR["car"].get_memory("spi_read_data")))
    

def _ROUTINE_scan_chain_loopback():
    """Write 10b of data into the scan chain and read it back (slide 16)"""
    pass

def _ROUTINE_config_chain_loopback():
    """Write 29b of data into the scan chain and read it back (slide 18)"""
    pass


#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
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
    

    spi_write_reg("global_counter_period",9600)
    spi_write_reg("comp_rise_calc",1)
    spi_write_reg("comp_fall_calc",3200)
    spi_write_reg("FULL_READOUT",1)


#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_axi_shell():
    """Microshell to interact with the AXI registers and debug the design."""

    register_list = {"apg": ["apg_run", "apg_write_channel", "apg_read_channel",
                     "apg_sample_count","apg_n_samples","apg_write_buffer_len",
                     "apg_next_read_sample","apg_wave_ptr","apg_status", "apg_control",
                     "apg_dbg_error",
                             "apg_clear"],
                     "spi_apg": ["spi_apg_run", "spi_apg_write_channel", "spi_apg_read_channel",
                     "spi_apg_sample_count","spi_apg_n_samples","spi_apg_write_buffer_len",
                                 "spi_apg_next_read_sample","spi_apg_wave_ptr","spi_apg_status", "spi_apg_control",
                                 "spi_apg_dbg_error", "spi_apg_clear"],
                     "lpgbt_fpga":  ["uplinkRst", "mgt_rxpolarity", "lpgbtfpga_status"]}
    
   # spi_registers = ["spi_write_data", "spi_read_data", "spi_data_len","spi_trigger",
    #                 "spi_transaction_count", "spi_status"]

    for x in register_list.keys():
        print(x)
        
    fw_choice = input("Which fw module would you like to interact with?")
    
    AXI_REGISTERS = register_list[fw_choice]

    while True:

        # Print register contents
        i = 0
        for reg in AXI_REGISTERS:
            reg_contents = sg.INSTR["car"].get_memory(reg)

            if reg == "spi_status":
                reg_contents = SPI_Status(reg_contents)
            
            print(f"{i}. {reg : <16} -- {reg_contents}")
            i = i+1

        write_reg_num = input("write which?").strip()

        if write_reg_num == "":
            continue

        if write_reg_num == "q":
            return

        write_reg = AXI_REGISTERS[int(write_reg_num)]

        write_val = int(input("val?"))

        sg.INSTR["car"].set_memory(write_reg, write_val)



#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
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


#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_get_glue_wave():

    N = input("How many samples do you want to take?")
    N = int(N)

    get_glue_wave(N)


#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_write_tx_config():
    spi_write_tx_config(TX_REG_DEFAULTS)


#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_Update_tx_config():

    key_list = list(TX_REG_DEFAULTS.keys())

    for i in range(len(key_list)):
        print(f"{i}. {key_list[i]}")

    user_choice = int(input("which # cfg to modify? >>>"))
    user_val = int(input("New value >>>"))

    spi_update_tx_reg(key_list[user_choice], user_val)
    
    #TX_REG_DEFAULTS[key_list[user_choice]] = user_val

    #spi_write_tx_config(TX_REG_DEFAULTS)


#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_get_rx_status():

    rx_status_bin = sg.INSTR["car"].get_memory("lpgbtfpga_status")

    uplinkrdy = rx_status_bin & 0x1
    uplinkFEC = (rx_status_bin & 0x2) >> 1
    uplinkEcData = (rx_status_bin & 0xC) >> 2
    uplinkIcData = (rx_status_bin & 0x30) >> 4
    uplinkPhase = (rx_status_bin & 0x1C0) >> 6
    mgt_rx_rdy  = (rx_status_bin & 0x200) >> 9
    # more debug signals 2024.09.10
    bitslip_counter  = (rx_status_bin & 0x00FF300) >> 10
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
    print(f"not(RX Gearbox Ready)         datapath_rst     : {datapath_rst}")
    print(f"Rx ready from the transceiver rst_pattsearch   : {rst_pattsearch}")
    print(f"not(sta_headerLocked)         rst_gearbox      : {rst_gearbox}")
    print(f"frame_aligner(one pulse)      sta_headerFlag   : {sta_headerFlag}")
    print(f"uplink decoder ready          uplinkReady      : {uplinkReady}")

#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_pulse_uplinkRst():

    sg.INSTR["car"].set_memory("uplinkRst",1)

    time.sleep(0.1)

    sg.INSTR["car"].set_memory("uplinkRst",0)



def run_pattern_apg(pattern_glue, loop=False):

    #First, stop looping and wait for the pattern to end if necessary.
    sg.INSTR["car"].set_memory("apg_control",0)

    while True:
        apg_status = sg.INSTR["car"].get_memory("apg_status")
        if apg_status == 0:
            break
        else:
            sg.log.debug(f"Waiting for APG idle (status={apg_status})...")

    sg.INSTR["car"].set_memory("apg_n_samples",len(pattern_glue.vector))

    #Write the pattern glue into memory.
    for c in pattern_glue.vector:
        sg.INSTR["car"].set_memory("apg_write_channel",c)


    #Set up looping if requested
    if loop:
        sg.INSTR["car"].set_memory("apg_control",1)

    #Run
    sg.INSTR["car"].set_memory("apg_run",1)

    sg.log.info("APG Now Running!")
    
    
    

#<<Registered w/ Spacely as ROUTINE 12, call as ~r12>>
def ROUTINE_run_array_serial_pattern():

    user_pattern_str = input("Enter a binary pattern>>>")

    #Split the user's pattern by characters:
    user_pattern = []
    for c in user_pattern_str:
        if c == "1":
            user_pattern.append(1)
        elif c == "0":
            user_pattern.append(0)


    pattern_glue = genpattern_from_waves_dict({"array_serial_0":user_pattern})

    run_pattern_apg(sg.gc.read_glue(pattern_glue), True)
    

#<<Registered w/ Spacely as ROUTINE 13, call as ~r13>>
def ROUTINE_run_APG_test_pattern():

    test_pattern = [0,1,2,3,4,5,6,7]

    pattern_glue = GlueWave(test_pattern,None,"Caribou/Caribou/apg")

    run_pattern_apg(pattern_glue,True)



#<<Registered w/ Spacely as ROUTINE 14, call as ~r14>>
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
        


