# Build-A-Chip Demo Routines File
#
# This file contains software routines to interact with the two pre-built "chips".

import time

#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

Chip_A_iospec = ".\\spacely-asic-config\\BuildAChipDemo\\BuildAChipDemo_ChipA_iospec.txt"
Chip_B_iospec = ".\\spacely-asic-config\\BuildAChipDemo\\BuildAChipDemo_ChipB_iospec.txt"

#A list of AXI addressable registers in the firmware by module.
AXI_REGISTERS = {"apg": ["apg_run", "apg_write_channel", "apg_read_channel", "apg_write_defaults",
                        "apg_sample_count","apg_n_samples","apg_write_buffer_len",
                        "apg_next_read_sample","apg_wave_ptr","apg_status", "apg_control",
                        "apg_dbg_error",
                        "apg_clear"],
                     "logic_clk_div": ["divider_cycles","divider_rstn"],}


# onstartup() is a special function which runs automatically upon starting Spacely.
def onstartup():
    try:
        sg.INSTR["car"].axi_registers = AXI_REGISTERS
        
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
    """Demo "ChipA", a digital temperature sensor"""
    
    EMULATE_LMT87 = True
    
    sg.gc.parse_iospec_file(Chip_A_iospec)
    
    # Set up the arbitrary pattern generator clock to run at 100/(9+1) = 10 MHz
    sg.INSTR["car"].set_memory("divider_cycles",9)
    sg.INSTR["car"].set_memory("divider_rstn",1)
    
    try:
        while True:
            if EMULATE_LMT87 == True:
                LMT87_voltage = 2.33
            else:
                LMT87_voltage = sg.INSTR["car"].get_voltage("VOL_IN_1")
            
            #Approximate transfer function from https://www.ti.com/lit/ds/symlink/lmt87.pdf?ts=1726810597654
            T_degC = (LMT87_voltage - 2.637)/(-0.0136)
            
            T_degF = round((T_degC * 1.8) + 32)
            
            sg.log.debug(f"Measured Voltage = {LMT87_voltage} V     Temperature = {T_degF} deg F")
            
            #Write to 7seg display
            if T_degF > 100:
                sg.log.debug("Temperature too high, not writing to 7seg.")
            else:
                input_wave = sg.gc.dict2Glue(genpattern_7seg(T_degF),"Caribou/apg/write",output_mode=3)
                sg.pr.run_pattern(input_wave)
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        sg.log.warning("(Ctrl-C) Detected, finishing routine!")
    

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_demo2_Binary_Calculator(user_hz=None):
    """Demo "ChipB", a Binary Calculator"""
    
    #################
    ## Setup Phase ##
    #################
    
    # Set the correct iospec
    sg.gc.parse_iospec_file(Chip_B_iospec)
    
    # Ask the user how fast to run the test in Hz
    while True:
        if user_hz == None:
            user_hz = input("What rate should we test combinations at (Enter a number in Hz)?")
    
        try:
            user_hz = float(user_hz)
        except ValueError:
            print("Sorry, please enter a number!")
            user_hz = None
            continue
        
        #Each measurement takes 2 cycles, so divide user_hz by 2.
        divisor = round(100e6/(2*user_hz))
        
        if divisor >= 1:
            divider_cycles = divisor - 1
            sg.log.debug(f"Actual Clock Div Factor: {divisor}  Actual Freq: {100e6/divisor} Hz")
            break
        else:
            print("Sorry! Please enter a frequency < 100 MHz")
        
    # Set the divider_cycles value in Caribou firmware based on the user's choice.
    sg.INSTR["car"].set_memory("divider_cycles",divider_cycles)
    sg.INSTR["car"].set_memory("divider_rstn",1)
    
    
    ###################
    ## Test the Chip ##
    ###################
    
    ## (1) Pulse bit 1 (reset) to put the counters in a known state.
    sg.INSTR["car"].set_memory("apg_write_defaults", 0x1)
    time.sleep(2*(1/user_hz))
    sg.INSTR["car"].set_memory("apg_write_defaults",0x0)
    
    ## (2) Generate a test pattern that will exercise all possible states of the chip.
    waves = {"RESET": [0],
             "CP1"  : [0],
             "CP2"  : [0]}
    
    # Pulse CP1 16 times followed by CP2 one time to iterate through all possible 
    # combinations of 4-bit integers across the two counters.    
    for j in range(16):
        waves["CP1"]   = waves["CP1"]   + [0,1]
        waves["CP2"]   = waves["CP2"]   + [0,0]
        
    waves["CP1"]   = waves["CP1"]   + [0,0]
    waves["CP2"]   = waves["CP2"]   + [0,1]
    
    
    # Convert our test pattern into a Glue Wave
    sg.log.debug("Generating test pattern")
    input_wave = sg.gc.dict2Glue(waves,"Caribou/apg/write",output_mode=3)
    
    ## (3) Run the actual test
    # Create empty lists to hold the actual results from the chip, 
    # and theoretically expected results
    actual_results = []
    expected_results = []
    
    # Print out a formatted header 
    print("                 N1 VALUES:\nN2 VALS | ",end='')
    for n1 in range(16):
        print(f"{n1:<5}",end='')
    print("\n---------",end='')
    for _ in range(16):
        print("-----",end='')
    print("")
    
    #Each iteration of this loop represents one row in the results table.
    for n2 in range(16):
        
        #Print the value of n2 to the left of the row.
        print(f"{n2:<5}    | ",end='')
        
        n1 = 0
    
        # Run the test pattern we created on the ASIC & read the result.
        output_wave = sg.gc.read_glue(sg.pr.run_pattern(input_wave))
    
        #cp1_sig = string of clock pulses to chip 1. We use these to time the results.
        #result_sig = results read back from the adder.
        cp1_sig = [1 if x & (1 << sg.gc.IO_pos["CP1"]) else 0 for x in input_wave.vector]
        result_sig = output_wave.vector
        
        
        # Get the first result from the first tick of the GlueWave (before any CP1 pulses). 
        actual = result_sig[0]
        expected = (n1+n2) % 32
        print_result(actual, expected)
        actual_results.append(actual)
        expected_results.append(expected)
        n1 += 1
        
        for i in range(1,len(input_wave.vector)):
            #Every falling edge of cp1, capture another adder result.
            if cp1_sig[i] == 0 and cp1_sig[i-1] == 1:
                actual = result_sig[i]
                expected = (n1+n2) % 32
                print_result(actual, expected)
                actual_results.append(actual)
                expected_results.append(expected)
                n1 += 1
                
                # There are only 16 CP1 pulses, so we can exit the loop after 
                # finding all of them.
                if n1 >= 16: 
                    break
                    
        print("")
        
    #Print the full list of actual and expected results at the bottom.
    print("Info: '*' represents results that are in error.")
    print("ACTUAL RESULTS:", actual_results)
    print("EXPECTED RESULTS:", expected_results)
    
 
#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_demo3_countdown():
    """Use "ChipB" to display a numeric countdown from 50"""
    
    sg.gc.parse_iospec_file(Chip_A_iospec)
    
    # Set up the arbitrary pattern generator clock to run at 100/(9+1) = 10 MHz
    sg.INSTR["car"].set_memory("divider_cycles",9)
    sg.INSTR["car"].set_memory("divider_rstn",1)
    
    #Create a list of alphanumeric values to iterate through. 
    display_val_list = [x for x in range(50)]
    display_val_list.reverse()
    display_val_list += ["HA", "  ", "HA", "  ", "HA", "  ", "  ", "  "]
    
    #Loop through the list of values
    try:
        while True:
            
            for display_val in display_val_list:
            
                #For each value, use a glue wave to write it to the 7seg.
                input_wave = sg.gc.dict2Glue(genpattern_7seg(display_val),"Caribou/apg/write",output_mode=3)
                sg.pr.run_pattern(input_wave)
            
                #Wait for 100 ms after each number, and 500 ms after each "HA"
                if type(display_val) == int:
                    time.sleep(0.1)
                else:
                    time.sleep(0.5)
            
    except KeyboardInterrupt:
        sg.log.warning("(Ctrl-C) Detected, finishing routine!")
   
#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_loop_demo2():
    """Repeatedly run the demo2 routine (at 10 Hz), until we receive a Ctrl-C"""
    
    try:
        while True:
            ROUTINE_demo2_Binary_Calculator(10)
            
    except KeyboardInterrupt:
        sg.log.warning("(Ctrl-C) Detected, finishing routine!")

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_congrats():
    """If you can run this routine from the Spacely command line, you've installed everything correctly!"""
    
    sg.log.notice(" `*%*` CONGRATS! `*%*` (Spacely is installed correctly.) ")
