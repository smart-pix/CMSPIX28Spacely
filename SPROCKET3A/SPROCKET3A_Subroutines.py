import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

DEBUG_SPI = True


def SPI_Status(status_num):
    if status_num & 3 == 0:
        status = "IDLE"
    elif status_num & 3 == 1:
        status = "TRANSACTION"
    elif status_num & 3 == 2:
        status = "DONE"
    else:
        status = "ERROR"
    if status_num & (1 << 2) == 1:
        status = status + ", Triggered"
    else:
        status = status + ", No Trigger Pending"

    return status
        

#NOTE: Remember that reset_b is active-low, so setting the GPIO to 1 will deassert.
def deassert_reset():
    gpio_val = sg.INSTR["car"].get_memory("gpio_data")
    gpio_val = gpio_val | 1
    sg.INSTR["car"].set_memory("gpio_data",gpio_val)

def assert_reset():
    gpio_val = sg.INSTR["car"].get_memory("gpio_data")
    gpio_val = gpio_val & (~1)
    sg.INSTR["car"].set_memory("gpio_data",gpio_val) 

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

#SP3A SPI_REG Dictionary provided for convenience
# Format:
#[<opcode>, <address>, <bit width>]
#This gets compiled into the full SPI command which is:
# [0, <WnR(1bit)>, <opcode(2bit)>, <address(8bit)>]  (total length: 12 bits)

SPI_REG={}

SPI_REG["INVALID_OPCODE_FLAG"]            =[0,0,1]
SPI_REG["INTERRUPTED_OPCODE_STRM"]        =[0,1,1]
SPI_REG["INTERRUPTED_DATA_STRM"]          =[0,2,1]
SPI_REG["SPI_IS_IDLE"]                    =[0,3,1]
SPI_REG["SPI_WAITING_FOR_BITS"]           =[0,4,1]
SPI_REG["LPGBT_READY"]                    =[0,5,1]
SPI_REG["CLKG_lfLossOfLockCount"]         =[0,6,8]
SPI_REG["CLKG_lfState"]                   =[0,7,2]
SPI_REG["CLKG_smState"]                   =[0,8,4]
SPI_REG["FULL_READOUT"]                   =[0,15,1]
SPI_REG["comp_rise_calc"]                 =[1,0,14]
SPI_REG["comp_fall_calc"]                 =[1,1,14]
SPI_REG["comp_rise_read"]                 =[1,2,14]
SPI_REG["comp_fall_read"]                 =[1,3,14]
SPI_REG["comp_rise_Rst"]                  =[1,4,14]
SPI_REG["comp_fall_Rst"]                  =[1,5,14]
SPI_REG["comp_rise_bufsel"]               =[1,6,14]
SPI_REG["comp_fall_bufsel"]               =[1,7,14]
SPI_REG["DACclr_pattern_delay"]           =[1,8,14]
SPI_REG["Qequal_pattern_delay"]           =[1,9,14]
SPI_REG["global_counter_period"]          =[1,10,14]
SPI_REG["DACclr_pattern"]                 =[2,0,192]
SPI_REG["Qequal_pattern"]                 =[2,1,192]
SPI_REG["scanOut"]                        =[2,2,20] #10b data + 10b array addr
SPI_REG["configOut"]                      =[2,3,39] #29b data + 10b array addr
SPI_REG["done"]                           =[2,4,192]



def spi_cmd_to_string(opcode_grp, address, WnR, data, length):
    """Creates a string representation of the properly formatted SPI command w/ given params"""
    opcode_str = format(opcode_grp, '02b')
    address_str = format(address, '08b')
    WnR_str = '0' + format(WnR,'01b')

    if data is not None:
        data_str = format(data,f'0{length}b')
    else:
        data_str = 'd'*length

    return 'XX'+WnR_str+opcode_str+address_str+data_str

def spi_write_tx_reg(byte_num, data):
    return spi_write(3,byte_num,data,8)

def spi_read_tx_reg(byte_num):
    return spi_read(3,byte_num,8)

def spi_write_reg(reg_name, data):
    return spi_cmd(opcode_grp=SPI_REG[reg_name][0], address=SPI_REG[reg_name][1], length=SPI_REG[reg_name][2], WnR=1, data=data)

def spi_read_reg(reg_name):
    return spi_cmd(opcode_grp=SPI_REG[reg_name][0], address=SPI_REG[reg_name][1], length=SPI_REG[reg_name][2], WnR=0)




def spi_cmd(opcode_grp, address, length, WnR, data=0):

    MAGIC_DATA_SHIFT_WRITE = 14 #14
    MAGIC_DATA_SHIFT_READ = 15  #15

    if length+14 > 32:
        sg.log.warning("WARNING: Attempting SPI write > 32 bits, check FW compatibility.")
    
    #First, build the SPI command which consists of:
    #{0} {WE (1b)} {opcode (2b)} {Address (8b)}
    cmd = 0
    cmd = cmd | WnR << 10 # WE
    cmd = cmd | opcode_grp << 8
    cmd = cmd | address
                     
    # Add 2 delay cycles
    cmd = cmd << 2

    spi_bitstring = cmd | (data) << MAGIC_DATA_SHIFT_WRITE

    if DEBUG_SPI:
        sg.log.debug(f"SPI Cmd:        {bin(cmd)} (dec: {cmd})")
        sg.log.debug(f"SPI Data:       {bin(data)} (dec: {data})")
        sg.log.debug(f"Full Bitstring: {bin(spi_bitstring)} ")

        prev_count = sg.INSTR["car"].get_memory("spi_transaction_count")
        sg.log.debug(f"SPI Prev. Transaction Count: {prev_count}")

    spi_wait_for_idle()
    
    sg.INSTR["car"].set_memory("spi_write_data", spi_bitstring)
    sg.INSTR["car"].set_memory("spi_data_len", MAGIC_DATA_SHIFT_READ+length)
    sg.INSTR["car"].set_memory("spi_trigger",1)

    #Check that the SPI transaction is complete.
    spi_wait_for_idle()

    if DEBUG_SPI:
        count = sg.INSTR["car"].get_memory("spi_transaction_count")
        sg.log.debug(f"SPI New  Transaction Count: {count}")

    
    return_data = sg.INSTR["car"].get_memory("spi_read_data")

    if DEBUG_SPI:
        sg.log.debug(f"SPI Return Bits: {bin(return_data)}")

    # Right-shift by 15 bits to account for the cycles taken by the command word.
    return_data = return_data >> MAGIC_DATA_SHIFT_READ

    if DEBUG_SPI:
        sg.log.debug(f"Data:            {bin(return_data)} (dec: {return_data})")
    
    return  return_data


#Polls spi_status until the status is IDLE and not triggered.
def spi_wait_for_idle():
    while True:
        status = sg.INSTR["car"].get_memory("spi_status")

        if DEBUG_SPI:
            sg.log.debug(f"spi_status - {status}")

        if status == 0:
            break

        time.sleep(0.1)
        

#This function gets a set of samples from the FW Arbitrary_Pattern_Generator() and saves them as a GlueWave.
def get_glue_wave(n_samples):

    #Set the # of samples to collect and run the Arbitrary Pattern Gen
    sg.INSTR["car"].set_memory("apg_n_samples",n_samples)
    sg.INSTR["car"].set_memory("apg_run",1)

    #Wait for the APG to finish running.
    while True:
        status = sg.INSTR["car"].get_memory("apg_status")
        if status == 0:
            break
        else:
            sg.log.debug(f"APG Status: {status}")
            time.sleep(0.5)


    #Read back all the samples
    samples = []

    for n in range(n_samples):
        samples.append(sg.INSTR["car"].get_memory("apg_read_channel"))


    APG_CLOCK_FREQUENCY = 10e6
    strobe_ps = 1/APG_CLOCK_FREQUENCY * 1e12
        
    glue = GlueWave(samples,strobe_ps,"Caribou/Caribou/Caribou")

    sg.gc.write_glue(glue,"apg_samples.glue")
    sg.gc.plot_glue(glue)
