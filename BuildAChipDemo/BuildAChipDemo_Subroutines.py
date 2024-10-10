# Build-A-Chip Demo Subroutines File
#
# This file contains helper functions for BuildAChipDemo_Routines.py

#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

# From 7seg datasheet:
#       6
#    1     5
#       0
#    2     4
#       3
SEVEN_SEG_PATTERNS = {0: [0,1,1,1,1,1,1],
                      1: [0,0,0,0,1,1,0],
                      2: [1,0,1,1,0,1,1],
                      3: [1,0,0,1,1,1,1],
                      4: [1,1,0,0,1,1,0],
                      5: [1,1,0,1,1,0,1],
                      6: [1,1,1,1,1,0,1],
                      7: [0,0,0,0,1,1,1],
                      8: [1,1,1,1,1,1,1],
                      9: [1,1,0,0,1,1,1],
                      " ":[0,0,0,0,0,0,0],
                      "H":[1,1,1,0,1,1,0],
                      "A":[1,1,1,0,1,1,1]
                      }


def genpattern_7seg(display_val):
    """Generates a wave pattern which allows writing a given number to a two-digit 7seg display"""
    
    if type(display_val) == int:
        #Split the number into a 10's place and a 1's place, and 
        #find the 7-seg patterns that correspond to each digit.
        sdi1_pattern = SEVEN_SEG_PATTERNS[int(display_val/10)] 
        sdi2_pattern = SEVEN_SEG_PATTERNS[display_val % 10]
    else:
        sdi1_pattern = SEVEN_SEG_PATTERNS[display_val[0]] 
        sdi2_pattern = SEVEN_SEG_PATTERNS[display_val[1]]
    
    waves = {"CLK": [],
             "SDI1": [],
             "SDI2": [],
             "LE" : []}
      
    #Create a serial waveform to write the appropriate pattern to the chip.
    for i in range(len(sdi1_pattern)):
        waves["CLK"] = waves["CLK"] + [0,1]
        waves["SDI1"] = waves["SDI1"] + [sdi1_pattern[i]]*2
        waves["SDI2"] = waves["SDI2"] + [sdi2_pattern[i]]*2
        waves["LE"]  = waves["LE"]  + [0,0]
        
    #At the end of the serial pattern, assert LE for one cycle to 
    #pass data from shift registers into the chip.
    waves["LE"] = waves["LE"] + [1]
    
    return waves


def print_result(actual_result, expected_result):
    """Helper function. Prints the actual result, and adds a '*' if it differs from the expected result."""
    
    if actual_result == expected_result:
        print_string = str(actual_result)
    else:
        print_string = str(actual_result)+"*"
    
    print(f"{print_string:<5}",end='')
       