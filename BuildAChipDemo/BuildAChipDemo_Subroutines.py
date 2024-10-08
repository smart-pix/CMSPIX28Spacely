
#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

SEVEN_SEG_PATTERNS = {0: [1,1,1,1,1,1,0],
                      1: [0,1,1,0,0,0,0],
                      2: [1,1,0,1,1,0,1],
                      3: [1,1,1,1,0,0,1],
                      4: [0,1,1,0,0,1,1],
                      5: [1,0,1,1,0,1,1],
                      6: [1,0,1,1,1,1,1],
                      7: [1,1,1,0,0,0,0],
                      8: [1,1,1,1,1,1,1],
                      9: [1,1,1,0,0,1,1]}


def genpattern_7seg(target_number):
    """Generates a wave pattern which allows writing a given number to a two-digit 7seg display"""
    
    sdi1_pattern = SEVEN_SEG_PATTERNS[int(target_number/10)] 
    sdi2_pattern = SEVEN_SEG_PATTERNS[target_number % 10]
    
    waves = {"CLK": [],
             "SDI1": [],
             "SDI2": [],
             "LE" : []}
             
    for i in range(len(sdi_pattern)):
        waves["CLK"] = waves["CLK"] + [0,1]
        waves["SDI1"] = waves["SDI1"] + [sdi1_pattern[i]]*2
        waves["SDI2"] = waves["SDI2"] + [sdi2_pattern[i]]*2
        waves["LE"]  = waves["LE"]  + [0,0]
        
        
    waves["LE"] = waves["LE"] + [1]
    
    return waves


       