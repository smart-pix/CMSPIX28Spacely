#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.

# python
import time

# spacely
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *


#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_basicLoopback():
    """This routine tests basic loopback from data_in to data_out"""
    
    #Define the routine's purpose in a docstring like above, this will appear
    #when you call the routine in Spacely.
    reg_wrdout = sg.INSTR["car"].get_memory("reg_wrdout")
    reg_wrdout = int(reg_wrdout)

    time.sleep(0.5)
    
    # write something
    temp = int(not (reg_wrdout == 1))
    write = sg.INSTR["car"].set_memory("reg_wrdout", temp)
    time.sleep(0.5)
    
    reg_wrdout = int(sg.INSTR["car"].get_memory("reg_wrdout"))
    print(temp, write, reg_wrdout)
    
    pass




# IMPORTANT! If you want to be able to run a routine easily from
# spacely, put its name in the "ROUTINES" list:
ROUTINES = [ROUTINE_basicLoopback]
