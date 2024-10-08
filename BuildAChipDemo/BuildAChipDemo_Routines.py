#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.
import time

#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *


Chip_A_iospec = ".\\spacely-asic-config\\BuildAChipDemo\\BuildAChipDemo_ChipA_iospec.txt"
Chip_B_iospec = ".\\spacely-asic-config\\BuildAChipDemo\\BuildAChipDemo_ChipB_iospec.txt"


def onstartup():
    try:
        
        #Basic initialization of CaR board
        sg.INSTR["car"].init_car()

        #Init CMOS I/O voltages
        print(">  Setting CMOS In/Out Voltage = 3.3V")
        sg.INSTR["car"].set_input_cmos_level(3.3)
        sg.INSTR["car"].set_output_cmos_level(3.3)
    except KeyError:
        sg.log.error("Key error running onstartup() code -- maybe CaR wasn't initialized?")
        

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_demo1_Temperature_Sensor():
    """Demo "Chip1", a digital temperature sensor"""
    
    sg.gc.parse_iospec_file(Chip_A_iospec)
    
    try:
        while True:
            LMT87_voltage = sg.INSTR["car"].get_voltage("VOL_IN_X")
            
            #Approximate transfer function from https://www.ti.com/lit/ds/symlink/lmt87.pdf?ts=1726810597654
            T_degC = (LMT87_voltage - 2.637)/(-0.0136)
            
            T_degF = round((T_degC * 1.8) + 32)
            
            #Write to 7seg display
            sg.pr.run_pattern(genpattern_from_waves_dict(genpattern_7seg(T_degF)))
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        sg.log.warning("(Ctrl-C) Detected, finishing routine!")
    

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_demo2_Binary_Calculator():
    """Demo "Chip2", a Binary Calculator"""
    
    DETAIL_LOGGING = False
    
    # Set the correct iospec
    sg.gc.parse_iospec_file(Chip_B_iospec)
    
    # Set up the clock for the chip to run at 100 kHz
    sg.INSTR["car"].set_memory("divider_cycles",99)
    sg.INSTR["car"].set_memory("divider_rstn",1)
    
    
    # Pulse the reset pin.
    sg.INSTR["car"].set_memory("apg_write_defaults", 0x1)
    time.sleep(0.1)
    sg.INSTR["car"].set_memory("apg_write_defaults",0x0)
    
    TIME_SCALE_FACTOR = 1
    
    # We want to generate a pattern that will exercise all possible states of the chip.
    waves = {"RESET": [0],
             "CP1"  : [0],
             "CP2"  : [0]}
    
    # Pulse CP1 16 times followed by CP2 one time. 
    for j in range(16):
        waves["CP1"]   = waves["CP1"]   + [0,1]
        waves["CP2"]   = waves["CP2"]   + [0,0]
        
        
    waves["CP1"]   = waves["CP1"]   + [0,0]
    waves["CP2"]   = waves["CP2"]   + [0,1]
    
    
    # Run pattern on the hardware
    sg.log.debug("Generating test pattern")
    input_wave = sg.gc.dict2Glue(waves,"Caribou/apg/write",output_mode=3)
    
    actual_results = []
    expected_results = []
    
    for n2 in range(16):
        for n1 in range(16):
            expected_results.append((n1+n2)%16)
    
    
    print("                 N1 VALUES:\nN2 VALS | ",end='')
    for n1 in range(16):
        print(f"{n1:<5}",end='')
    print("\n---------",end='')
    for _ in range(16):
        print("-----",end='')
    print("")
    
    for n2 in range(16):
        
        print(f"{n2:<5}    | ",end='')
        
        n1 = 0
    
        # Run the pattern on the ASIC.
        output_wave = sg.gc.read_glue(sg.pr.run_pattern(input_wave,tsf=TIME_SCALE_FACTOR))
    
        # Check correctness of results.
    
        cp1_sig = [1 if x & (1 << sg.gc.IO_pos["CP1"]) else 0 for x in input_wave.vector]
        #print(cp1_sig)
        result_sig = output_wave.vector
        #bitstream = []
        
        
        # Get the first result from the first bit. 
        actual = result_sig[0]
        expected = (n1+n2) % 32
        print_result(actual, expected)
        actual_results.append(actual)
        n1 += 1
        
        for i in range(1,len(input_wave.vector)):
            #Every falling edge of cp1, capture the result vector value.
            if cp1_sig[i] == 0 and cp1_sig[i-1] == 1:
                #bitstream.append(data_sig[i-1])
                
                
                actual = result_sig[i]
                expected = (n1+n2) % 32
                print_result(actual, expected)
                actual_results.append(actual)
                n1 += 1
                
                
                if n1 >= 16: 
                    break
                    
        print("")
    print("Info: '*' represents results that are in error.")
    print("ACTUAL RESULTS:", actual_results)
    print("EXPECTED RESULTS:", expected_results)
    
 
def print_result(actual_result, expected_result):
    if actual_result == expected_result:
        print_string = str(actual_result)
    else:
        print_string = str(actual_result)+"*"
    
    print(f"{print_string:<5}",end='')


#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_congrats():
    """If you can run this routine from the Spacely command line ('~r0'), you've installed everything correctly!"""
    
    sg.log.notice(" `*%*` CONGRATS! `*%*` (Spacely is installed correctly.) ")


#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_basicLoopback():
    """This routine tests basic loopback from data_in to data_out"""

    #Define the routine's purpose in a docstring like above, this will appear
    #when you call the routine in Spacely.

    pass



#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_axi_shell():
    """Microshell to interact with the AXI registers and debug the design."""

    register_list = {"apg": ["apg_run", "apg_write_channel", "apg_read_channel", "apg_write_defaults",
                     "apg_sample_count","apg_n_samples","apg_write_buffer_len",
                     "apg_next_read_sample","apg_wave_ptr","apg_status", "apg_control",
                     "apg_dbg_error",
                             "apg_clear"],
                     "logic_clk_div": ["divider_cycles","divider_rstn"],
                     #"spi_apg": ["spi_apg_run", "spi_apg_write_channel", "spi_apg_read_channel",
                     #"spi_apg_sample_count","spi_apg_n_samples","spi_apg_write_buffer_len",
                     #            "spi_apg_next_read_sample","spi_apg_wave_ptr","spi_apg_status", "spi_apg_control",
                     #            "spi_apg_dbg_error", "spi_apg_clear"],
                     #"lpgbt_fpga":  ["uplinkRst", "mgt_rxpolarity", "lpgbtfpga_status"],
                     }
    
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
