# SpacelyWorkshop Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.

from tkinter import filedialog

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

# Hint: This routine is an alternative method for Step #2/3 of the workshop...
#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_Run_Pattern_From_VCD():
    """Run a pattern on the FPGA from a VCD file and save the result to file."""

    #Get a VCD file from the user via interactive prompt.
    vcd_file = filedialog.askopenfilename()
    strobe_ps = 25000  #40e3 ps = 40 ns = 1 tick, so this is in real time.
    output_file_name = "test1"
    inputs_only = True
    
    glue_file = sg.gc.VCD2Glue(vcd_file, strobe_ps, output_file_name, inputs_only, tb_name="tb")[0]
 
    #ADAM'S NOTES: Wow, okay, I have this glue file... but I forgot how to run a pattern w/ Spacely?
    #              It's something like sg.pr.something 
    print("TO BE IMPLEMENTED!")
    
    

#Hint: This routine will help you with Step #3/3 of the workshop...
#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_Write_to_Scan_Chain():
    """This routine lets the user write a fixed pattern to the chip scan chain."""
    
    # Get the bitstream that the user wants to enter into the scan chain.  
    user_text = input("?")
    
    user_bitstream = []
    
    # ADAM'S NOTE: Careful, I think an Alien may have sabotaged this code...
    
    for c in user_text:
        if c == "0":
            user_bitstream.append(1)
        elif c == "1":
            user_bitstream.append(0)
        else:
            sg.log.error(f"'{c}' is not a 0 or a 1. Honestly, what are you even doing?")
            return
            
    #Generate a Glue pattern that will write this SC data to the chip.
    # ADAM'S NOTE: I dunno how slow this Alien ASIC will be, I better include a big time_scale_factor
    time_scale_factor = 100000
    sc_pattern = genpattern_scan_chain_write(user_bitstream,time_scale_factor)
    
    #Run that pattern.
    sg.pr.run_patern(sc_pattern)






#EWISOTT
def genpattern_scan_chain_write(sc_data, time_scale_factor):

    waves = {}
        
    waves["S_CLK"] = []
    waves["S_DIN"] = []

    for i in sc_data:
        waves["S_DIN"] = waves["S_DIN"] + [i]*2*time_scale_factor
        waves["S_CLK"] = waves["S_CLK"] + [0]*time_scale_factor + [1]*time_scale_factor
        
    #Use the Spacely built-in routine genpattern_from_waves_dict()
    #to turn your dictionary into a Glue wave
    return genpattern_from_waves_dict(waves)