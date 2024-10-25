#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.


#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_congrats():
    """If you can run this routine from the Spacely command line ('~r0'), you've installed everything correctly!"""
    
    sg.log.notice(" `*%*` CONGRATS! `*%*` (Spacely is installed correctly.) ")


#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_basicLoopback():
    """This routine tests basic loopback from data_in to data_out"""

    #Define the routine's purpose in a docstring like above, this will appear
    #when you call the routine in Spacely.

    pass


