import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

DEBUG_SPI = True
EMULATE_SPI = False


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



TX_REG_MAP = {
    "txDataRate" : [0,0],
    "fecMode"    : [1,1],
    "txRxMode"   : [2,3],
    "txEnable"   : [4,4],
    "rxEnable"   : [5,5],
    "enableDes"  : [6,6],
    "enableSer"  : [7,7],
    "enablePhaseShifter":[8,8],
    "rxLockMode" : [9,9],
    "frameAlignerReady": [10,10],
    "pllCdrMode" : [11,11],
    "fecBypass"  : [12,12],
    "interleaverBypass" : [13,13],
    "scramblerBypass" : [14,14],
    "skipCycle" :[15,15],
    "txEC" : [16,17],
    "txIC" : [18,19],
    "disSER" : [24,24],
    "disCLK" : [25,25],
    "disEXT" : [26,26],
    "disVCO" : [27,27],
    "disDES" : [28,28],
    "disEOM" : [29,29],
    "refClk_enableRx" : [32,32],
    "refClk_enableTermination" : [33,33],
    "refClk_setCommonMode" : [34,34],
    "toser_rxLoopbackSel" :[40,40],
    "LJCDR_dataMuxCfg" : [41,42],
    "toLineDrv_enLineDrv" : [43,43],
    "eclk640MEnable" : [44,44],
    "clkTreeADisable" :[45,45],
    "clkTreeBDisable" :[46,46],
    "clkTreeCDisable" :[47,47],
    "tolineDrv_modDAC":[48,54],
    "tolineDrv_enEmp" :[55,55],
    "tolineDrv_empDAC":[56,62],
    "tolineDrv_empDurReduce":[63,63],
    "CLKGBiasGenConfig":[64,67],
    "CLKGCDRFeedForwardPropCur":[68,71],
    "CLKGCDRFeedForwardPropCurWhenLocked":[72,75],
    "CLKGCDRIntCur":[76,79],
    "CLKGCDRIntCurWhenLocked":[80,83],
    "CLKGCDRPropCur":[84,87],
    "CLKGCDRPropCurWhenLocked":[88,91],
    "CLKGCalibrationEndOfCount":[92,95],
    "CLKGCapBankSelect":[96,104],
    "CLKGFeedForwardCap":[105,107],
    "CLKGFeedForwardCapWhenLocked":[108,110],
    "CLKGFLLIntCur":[112,115],
    "CLKGFLLIntCurWhenLocked":[116,119],
    "CLKGLockFilterLockThrCounter":[120,123],
    "CLKGLockFilterReLockThrCounter":[124,127],
    "CLKGLockFilterUnLockThrCounter":[128,131],
    "CLKGPLLIntCur":[132,135],
    "CLKGPLLIntCurWhenLocked":[136,139],
    "CLKGPLLPropCur":[140,143],
    "CLKGPLLPropCurWhenLocked":[144,147],
    "CLKGPLLRes":[148,151],
    "CLKGPLLResWhenLocked":[152,155],
    "CLKGVcoDAC":[156,159],
    "CLKG_BIASGEN_CONFIG":[160,163],
    "CLKGwaitCDRTime":[164,167],
    "CLKGwaitPLLTime":[168,171],
    "CLKGVcoRailMode":[172,172],
    "CLKGLockFilterEnable":[173,173],
    "CLKGCDRRes":[174,174],
    "CLKGCOoverrideVc":[175,175],
    "CLKGCapBankOverrideEnable":[176,176],
    "CLKGDisableFrameAlignerLockControl":[177,177],
    "CLKGCOConnectCDR":[184,184],
    "CDRCOConnectPLL":[185,185],
    "CDRCODisDESvbiasGen":[186,186],
    "CDRCODisDataCounterRef":[187,187],
    "CDRCOEnableCDR":[188,188],
    "CDRCOEnableFD":[189,189],
    "CDRCOEnablePLL":[190,190],
    "CDRCORefClkSel":[191,191],
    "CDRControlOverrideEnable":[192,192]
}

TX_REG_DEFAULTS = {
    "txDataRate" : 1,   #10.24 GB/s 
    "fecMode"    : 1,
    "txRxMode"   : 3,
    "txEnable"   : 1,
    "rxEnable"   : 0, #There's no receiver.
    "enableDes"  : 1,
    "enableSer"  : 1,
    "enablePhaseShifter": 0,
    "rxLockMode" : 0,
    "frameAlignerReady": 0,
    "pllCdrMode" : 0,  #Use PLL
    "fecBypass"  : 1, #Bypass everything complicated by default.
    "interleaverBypass" : 1,
    "scramblerBypass" : 1,
    "skipCycle" :0,
    "txEC" : 3,
    "txIC" : 3,
    "disSER" : 0,
    "disCLK" : 0,
    "disEXT" : 1,
    "disVCO" : 0,
    "disDES" : 0,
    "disEOM" : 0,
    "refClk_enableRx" : 1,
    "refClk_enableTermination" : 1,
    "refClk_setCommonMode" : 1,
    "toser_rxLoopbackSel" : 0,
    "LJCDR_dataMuxCfg" : 3, # ?? Maybe this is CLKG_dataMuxCfg which is a test feature.
    "toLineDrv_enLineDrv" : 1, #Enable line driver
    "eclk640MEnable" : 1,  #Enable 640 MHz clock output
    "clkTreeADisable" : 0, #Primarily for TMR testing
    "clkTreeBDisable" : 0,
    "clkTreeCDisable" : 0,
    "tolineDrv_modDAC": 127,
    "tolineDrv_enEmp" : 0,
    "tolineDrv_empDAC": 0,
    "tolineDrv_empDurReduce": 0,
    "CLKGBiasGenConfig": 8 , #bias current for charge pumps LSB=8uA
    "CLKGCDRFeedForwardPropCur": 6,
    "CLKGCDRFeedForwardPropCurWhenLocked": 6,
    "CLKGCDRIntCur": 5,
    "CLKGCDRIntCurWhenLocked": 5,
    "CLKGCDRPropCur": 5,
    "CLKGCDRPropCurWhenLocked": 5,
    "CLKGCalibrationEndOfCount": 14, #cycles at end of VCO cal race
    "CLKGCapBankSelect": 0,
    "CLKGFeedForwardCap": 3,
    "CLKGFeedForwardCapWhenLocked": 3,
    "CLKGFLLIntCur": 5,
    "CLKGFLLIntCurWhenLocked": 5,
    "CLKGLockFilterLockThrCounter": 15,
    "CLKGLockFilterReLockThrCounter": 15,
    "CLKGLockFilterUnLockThrCounter": 15,
    "CLKGPLLIntCur": 9,
    "CLKGPLLIntCurWhenLocked": 9,
    "CLKGPLLPropCur": 9,
    "CLKGPLLPropCurWhenLocked": 9,
    "CLKGPLLRes": 2,
    "CLKGPLLResWhenLocked": 2,
    "CLKGVcoDAC": 8, #VCO current DAC, LSB=8mA
    "CLKG_BIASGEN_CONFIG":8,
    "CLKGwaitCDRTime": 8,
    "CLKGwaitPLLTime": 8,
    "CLKGVcoRailMode": 1, #current mode, select w/ CLKGVcoDAC
    "CLKGLockFilterEnable": 1,
    "CLKGCDRRes": 1, #Enable filter resistor
    "CLKGCOoverrideVc": 0,
    "CLKGCapBankOverrideEnable": 0, #Overrides cap search during VCO cal
    "CLKGDisableFrameAlignerLockControl": 0,
    "CLKGCOConnectCDR": 0,
    "CDRCOConnectPLL": 0,
    "CDRCODisDESvbiasGen": 0,
    "CDRCODisDataCounterRef": 0,
    "CDRCOEnableCDR": 0,
    "CDRCOEnableFD": 0,
    "CDRCOEnablePLL": 0,
    "CDRCORefClkSel": 0,
    "CDRControlOverrideEnable": 0 #CDRCO* options only take effect when CDRControlOverrideEnable=1
}



#This dictionary will emulate the contents of the SPI registers on the ASIC when EMULATE_SPI is set true.
SPI_REGS_EMU = {}


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


def spi_update_tx_reg(reg_name, field_val):

    start_bit = TX_REG_MAP[reg_name][0]
    end_bit = TX_REG_MAP[reg_name][1]
    byte = int((start_bit)/8)
    offset = start_bit - 8*byte
    offset_end = end_bit - 8*byte

    old_val = spi_read_tx_reg(byte)
    sg.log.debug(f"Updating Byte {byte}...")
    sg.log.debug(f"Old Value: {bin(old_val)}")

    for i in range(offset, offset_end+1):
        old_val = old_val & (~(1 << i))
        print(old_val)

    old_val = old_val | (field_val << offset)

    sg.log.debug(f"New Value: {bin(old_val)}")
    spi_write_tx_reg(byte, old_val)
    



#Generate Transmitter Config values from a dictionary of register values,
#and write it to the chip.
def spi_write_tx_config(reg_values):

    CFG_LINT = True

    #Initialize cfg to 24 bytes of all zeroes.
    tx_config = [0]*25

    sg.log.debug("Compiling Tx Configuration...")
    
    for field in TX_REG_MAP.keys():
        start_bit = TX_REG_MAP[field][0]
        end_bit = TX_REG_MAP[field][1]
        val = reg_values[field]
        
        for i in range(end_bit-start_bit+1):
            byte = int((start_bit+i)/8)
            offset = start_bit+i - 8*byte

            if CFG_LINT:
                #If there is already a 1 written where we are about to write
                if tx_config[byte] & (1 << offset) > 0:
                    sg.log.error(f"Tx Cfg Type 1 Error: {field} Overwrites at byte {byte} bit {offset} (raw_bit={start_bit+i})")
                    return -1

            #Grab the val from index [0], shift it by "offset" and OR it to the appropriate byte.
            tx_config[byte] = tx_config[byte] | ((val & 1) << offset)

            #Shift down val to put the next bit in index [0].
            val = val >> 1

        if CFG_LINT:

            if val > 0:
                sg.log.error(f"Tx Cfg Type 2 Error: {field} value {reg_values[field]} has a greater binary length than {end_bit-start_bit+1}")
                return -1
            

    #if CFG_LINT:
    #    for byte in tx_config:
    #        print(bin(byte))
            
    sg.log.debug("Writing Tx Config to ASIC...")

    for i in range(len(tx_config)):
        spi_write_tx_reg(i, tx_config[i])

    if CFG_LINT:
        sg.log.debug("Reading back config to check for errors...")
        for i in range(len(tx_config)):
            read_byte = spi_read_tx_reg(i)
            if read_byte != tx_config[i]:
                sg.log.error(f"Tx Cfg Readback failed for byte {i}: Wrote {tx_conifg[i]} and read {read_byte}")
                return -1

    sg.log.info("Writing Tx Config Successful!")
    

def spi_write_tx_reg(byte_num, data):
    return spi_cmd(opcode_grp=3, address=byte_num, length=8, WnR=1, data=data)

def spi_read_tx_reg(byte_num):
    return spi_cmd(opcode_grp=3, address=byte_num, length=8, WnR=0)

def spi_write_reg(reg_name, data):
    return spi_cmd(opcode_grp=SPI_REG[reg_name][0], address=SPI_REG[reg_name][1], length=SPI_REG[reg_name][2], WnR=1, data=data)

def spi_read_reg(reg_name):
    return spi_cmd(opcode_grp=SPI_REG[reg_name][0], address=SPI_REG[reg_name][1], length=SPI_REG[reg_name][2], WnR=0)

#Emulate SPI read and write operations in software.
def spi_cmd_emu(opcode_grp, address, length, WnR, data=0):
    sg.log.warning("Writing to EMULATED SPI registers (not the ASIC)!")

    key = str(opcode_grp)+str(address)

    #Write
    if WnR == 1:
        SPI_REGS_EMU[key] = data

    else:
        if key in SPI_REGS_EMU.keys():
            return SPI_REGS_EMU[key]
        else:
            return 0
    

def spi_cmd(opcode_grp, address, length, WnR, data=0):

    if EMULATE_SPI:
        return spi_cmd_emu(opcode_grp, address, length, WnR, data)
    
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
