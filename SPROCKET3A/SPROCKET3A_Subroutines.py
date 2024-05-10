import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *



# Returns: 0 on success, negative number on failure.
def spi_write(opcode_grp, address, data, length):
    """Write data to a SPI Register on the ASIC"""
    return NotImplementedError

    #Set opcode & address
    sg.INSTR["car"].set_memory("spi_address",address)

    #Set WnR bit
    sg.INSTR["car"].set_memory("opcode", opcode_grp | 1<<WnR_bit)

    #Set data to write
    sg.INSTR["car"].set_memory("write_data", data)

    #Initiate SPI transaction
    sg.INSTR["car"].spi_data_transaction()

    #Check SPI status register to see if write is successful
    status = sg.INSTR["car"].get_memory("spi_status_register")
    if status & success:
        return 0
    else:
        return -1

def spi_data_transaction():
    


# Returns: Unsigned int representing the value read on success, negative number on failure.
def spi_read(opcode_grp, address, length):
    """Read data from a SPI Register on the ASIC"""
    return NotImplementedError

     #Set opcode & address
    sg.INSTR["car"].set_memory("spi_address",address)

    #Set WnR bit
    
    #Initiate SPI transaction

    #Return read value
