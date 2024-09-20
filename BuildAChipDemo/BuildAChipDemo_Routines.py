#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.
import time

#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *



def onstartup():
    pass

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_demo1_Temperature_Sensor():
    """Demo "Chip1", a digital temperature sensor"""
    
    try:
        while True:
            LMT87_voltage = sg.INSTR["car"].get_voltage("VOL_IN_X")
            
            #Approximate transfer function from https://www.ti.com/lit/ds/symlink/lmt87.pdf?ts=1726810597654
            T_degC = (LMT87_voltage - 2.637)/(-0.0136)
            
            T_degF = round((T_degC * 1.8) + 32)
            
            #Write to 7seg display
            run_pattern_caribou(genpattern_from_waves_dict(genpattern_7seg(T_degF)))
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        sg.log.warning("(Ctrl-C) Detected, finishing routine!")
    

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_demo2_Binary_Calculator():
    """Demo "Chip2", a Binary Calculator"""
    
    # We generate a pattern that will exercise all possible states of the chip.
    waves = {"RESET": [],
             "CP1"  : [],
             "CP2"  : []}
             
    # (1) Pulse reset signal
    waves["RESET"] = waves["RESET"] + [1,0]
    waves["CP1"]   = waves["CP1"]   + [0,0]
    waves["CP2"]   = waves["CP2"]   + [0,0]
    
    # (2) Iterate through 256 possible values by incrementing CP1 and CP2:
    golden_results = []
    
    for i in range(16):
        for j in range(16):
            waves["CP1"]   = waves["CP1"]   + [0,1]
            waves["CP2"]   = waves["CP2"]   + [0,0]
            golden_results.append(i+j)
        
        waves["CP1"]   = waves["CP1"]   + [0,0]
        waves["CP2"]   = waves["CP2"]   + [0,1]
    
    
    # Run pattern on the hardware
    input_wave = sg.gc.read_glue(genpattern_from_waves_dict(waves))
    output_wave = sg.gc.read_glue(run_pattern_caribou(glue_wave))
    
    
    # Check correctness of results.
    # (1) Extract binary results from output_wave for each step.
    result_bin = [sg.gc.get_bitstream(output_wave,f"R{i}") for i in range(4)]
    
    
    cp1_sig = [1 if x & (1 << sg.gc.IO_pos["CP1"]) else 0 for x in input_wave.vector]
    result_num = []
        
    for i in range(1,len(wave.vector)):
        if cp1_sig[i] == 0 and cp1_sig[i-1] == 1:
            bitstream.append(data_sig[i-1])   
            result_num.append(result_bin[3][i] << 3 + result_bin[2][i] << 2 + result_bin[1][i] << 1 + result_bin[0][i])
        
    print(result_num)
    print(golden_results)
    
    
    


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


