import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *


# [lucahhot]: Sets the clock divide factor (which should be set once so it doesn't need to be set everytime we read/write to SPI)
def set_clock_divide_factor(clock_divide_factor):

    #Set clock_divide_factor (not sure if this new firmware has been flashed on the ZCU yet)
    sg.INSTR["car"].set_memory("clock_divide_factor",clock_divide_factor)

    # Check to see if the correct value has been set in memory
    memory_value = sg.INSTR["car"].get_memory("clock_divide_factor")

    if memory_value == clock_divide_factor:
        return 0
    else:
        return -1



# Returns: 0 on success, negative number on failure.
def spi_write(opcode_grp, address, data, length):

    """Write data to a SPI Register on the ASIC"""

    # Set spi_read_write
    sg.INSTR["car"].set_memory("spi_read_write",1) # "1" to write

    # Set spi_address
    sg.INSTR["car"].set_memory("spi_address",address)

    # Set spi_opcode
    sg.INSTR["car"].set_memory("spi_opcode",opcode_grp)

    # Set spi_write_data 
    # Will need a bit of extra logic here depending on how much data we need to write. Since this is a generic subroutine,
    # we can't just hardcode it and it will look similar to spi_controller_SP3A_tb in the spacely-caribou-common-blocks repo:
    # spacely-caribou-common-blocks/spi_controller_interface/testbench/ folder
    sg.INSTR["car"].set_memory("spi_write_data",data)

    # Set spi_data_len (this will trigger the SPI transaction)
    sg.INSTR["car"].set_memory("spi_data_len",length)

    # Read in spi_done to see if the SPI transaction was successful (might need to read this in a loop
    # until it is set to 1, and timeout and return -1 if we loop through it too many times)
    # This timeout time would technically be the longest number of SPI cycles it would take to send a SPI write command.
    done = sg.INSTR["car"].get_memory("spi_done")

    if done == 1:
        return 0
    else:
        return -1



# Returns: Unsigned int representing the value read on success, negative number on failure.
def spi_read(opcode_grp, address, length):

    """Read data from a SPI Register on the ASIC"""

    # Set spi_read_write
    sg.INSTR["car"].set_memory("spi_read_write",0) # "0" to read

    # Set spi_address
    sg.INSTR["car"].set_memory("spi_address",address)

    # Set spi_opcode
    sg.INSTR["car"].set_memory("spi_opcode",opcode_grp)

    # Set spi_data_len (this will trigger the SPI transaction)
    sg.INSTR["car"].set_memory("spi_data_len",length)

    done = sg.INSTR["car"].get_memory("spi_done")

    # We can only read from spi_read_data if the SPI transaction is done
    if (done == 1):

        # Read from spi_read_data
        # Will need a bit of extra logic here depending on how much data we need to read. Since this is a generic subroutine,
        # we can't just hardcode it and we will need to read the spi_read_data register multiple times and concatenate the data
        # into the single "data" variable that we can return
        data = sg.INSTR["car"].get_memory("spi_read_data")
        return data

    else:
        return -1

    

    
