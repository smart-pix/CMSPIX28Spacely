#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.

import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *
from pattern_runner import *


#This dictionary defines all the possible SPI commands. Based on Austin's powerpoint.
#              "Name of Command"               : [ config bit (1b), opcode (3b), W/nR(1b)]
SPI_CMD_DEF = {"Memory Select"                 : [ 1              , [0,0,0]    ,1        ],
               "Start Chan Read Address Lower" : [ 1              , [0,0,1]    ,1        ],
               "Start Chan Read Address Upper" : [ 1              , [0,1,0]    ,1        ],
               "End Chan Read Address Lower"   : [ 1              , [0,1,1]    ,1        ],
               "End Chan Read Address Upper"   : [ 1              , [1,0,0]    ,1        ],
               "Write Mode"                    : [ 1              , [1,0,1]    ,[]       ],
               "Read Mode"                     : [ 1              , [1,1,0]    ,[]       ],
               "Idle Mode"                     : [ 1              , [1,1,1]    ,[]       ],
               "Block Write"                   : [ 0              , []         ,[]       ],
               "Block Read"                    : [ 0              , []         ,[]       ]}



def ROUTINE_FPGATest():
    """Basic Test of our ability to write bits using the FPGA"""
    #Define the routine's purpose in a docstring like above, this will appear
    #when you call the routine in Spacely.
    
    #Create a basic pattern
    test_pattern = sg.pr.genpattern_from_waves_dict({"mclk":[0,1]*20, "data_in":[0,0,0,0,0,0,1,1,1,1,1,1,1]}, time_scale_factor=3)
    
    #Run that pattern
    sg.pr.run_pattern( test_pattern, outfile_tag ="testpattern")


def ROUTINE_SPICommandTest():
    """Send some SPI commands"""
    
    
    cmd = SPI_cmd("Start Chan Read Address Lower", [0,0,0,0,0,1,0,1])
    
    sg.pr.run_pattern(cmd, outfile_tag="SPI_cmd_result")
    

def tolist(arg):
    if type(arg) == int:
        return [arg]
    else:
        return arg
    
# Generates a wave dict corresponding to a SPI command.
# command_type - Name of command to send. See the table above.
# data_bits    - Array containing the user data bits that need to be added to the command. 
#                If there are not enough user data bits to fill the command, zeros will be added.
def SPI_cmd(command_type, data_bits=[], time_scale_factor=1):


    if command_type not in SPI_CMD_DEF.keys():
        print(f"ERROR: {command_type} is not a valid SPI command type.")
        print("Valid command types are:",end='')
        print(SPI_CMD_DEF.keys())

    config_bit = tolist(SPI_CMD_DEF[command_type][0])
    opcode     = tolist(SPI_CMD_DEF[command_type][1])
    WnR        = tolist(SPI_CMD_DEF[command_type][2])

    command = [config_bit] + opcode + [WnR] + data_bits
    
    #Fill w/ zeroes if necessary
    command = command + [0]*(17-len(command))
   
    w = {}
    
    #Start out w/ a few zeros, then 2 clk cycles while ss is high.
    w["spi_clk"] = [0,0,0,0,1,0,1,0]
    w["ss"]      = [1,1,1,1,1,1,1,1]
    w["mosi"]    = [0,0,0,0,0,0,0,0]
    
    
    for i in range(len(command)):
        w["spi_clk"] = w["spi_clk"] + [1,0]
        w["ss"]      = w["ss"]      + [0,0]
        w["mosi"]    = w["mosi"]    + [command[i]]*2
    
    #Finish with 2 clk cycles while ss is high, just to be sure.
    w["spi_clk"] = w["spi_clk"] + [1,0,1,0]
    w["ss"]      = w["ss"]      + [1,1,1,1]
    w["mosi"]    = w["mosi"]    + [0,0,0,0]

    return sg.pr.genpattern_from_waves_dict(w, time_scale_factor=time_scale_factor)


# IMPORTANT! If you want to be able to run a routine easily from
# spacely, put its name in the "ROUTINES" list:
ROUTINES = [ROUTINE_FPGATest,ROUTINE_SPICommandTest]
