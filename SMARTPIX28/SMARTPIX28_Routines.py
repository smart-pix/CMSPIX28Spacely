#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.




def ROUTINE_basicLoopback():
    """This routine tests basic loopback from data_in to data_out"""

    #Define the routine's purpose in a docstring like above, this will appear
    #when you call the routine in Spacely.
    reg_wrdout = int(sg.INSTR["car"].get_memory("reg_wrdout"))
    print(reg_wrdout)
    
    pass




# IMPORTANT! If you want to be able to run a routine easily from
# spacely, put its name in the "ROUTINES" list:
ROUTINES = [ROUTINE_basicLoopback]
