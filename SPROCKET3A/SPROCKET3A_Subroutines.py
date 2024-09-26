import random
import time
import shutil

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

DEBUG_SPI = False
EMULATE_SPI = False
# Set to "apg" or "simple_serial"
SPI_FIRMWARE = "apg"

#Config Lint Checking
# 0 = No checking
# 1 = Check lengths of the input fields
# 2 = Readback from the chip after writing
# 3 = Readback from the chip after writing, and on failure, take multiple reads for debugging.
CFG_LINT_LEVEL = 2


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
    "fecMode"    : 0,   #FEC5
    "txRxMode"   : 3,
    "txEnable"   : 1,
    "rxEnable"   : 0, #There's no receiver.
    "enableDes"  : 1,
    "enableSer"  : 1,
    "enablePhaseShifter": 0,
    "rxLockMode" : 0,
    "frameAlignerReady": 0,
    "pllCdrMode" : 0,  #Use PLL
    "fecBypass"  : 0, #Enable SIF mode by default.
    "interleaverBypass" : 0,
    "scramblerBypass" : 0,
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
    "CLKGLockFilterEnable": 0, #MODIFIED! Disabling the lf allows us to lock immediately.
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

    global CFG_LINT_LEVEL

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

            if CFG_LINT_LEVEL >= 1:
                #If there is already a 1 written where we are about to write
                if tx_config[byte] & (1 << offset) > 0:
                    sg.log.error(f"Tx Cfg Type 1 Error: {field} Overwrites at byte {byte} bit {offset} (raw_bit={start_bit+i})")
                    return -1

            #Grab the val from index [0], shift it by "offset" and OR it to the appropriate byte.
            tx_config[byte] = tx_config[byte] | ((val & 1) << offset)

            #Shift down val to put the next bit in index [0].
            val = val >> 1

        if CFG_LINT_LEVEL >= 1:

            if val > 0:
                sg.log.error(f"Tx Cfg Type 2 Error: {field} value {reg_values[field]} has a greater binary length than {end_bit-start_bit+1}")
                return -1
            

    #if CFG_LINT:
    #    for byte in tx_config:
    #        print(bin(byte))
            
    print("Writing Tx Config to ASIC",end='',flush=True)

    #Single Write Mode WiP
    SINGLE_WRITE_MODE = False

    if SINGLE_WRITE_MODE:

        waves_combined = {"cs_b": [], "pico": []}

        for i in range(len(tx_config)):
            waves = genpattern_spi_cmd(opcode_grp=3, address=i, length=8, WnR=1, data=tx_config[i])
            waves_combined["cs_b"] = waves_combined["cs_b"] + waves["cs_b"]
            waves_combined["pico"] = waves_combined["pico"] + waves["pico"]

        glue_wave_obj = genpattern_from_waves_dict_fast(waves, "spi_apg")
        run_pattern_caribou(glue_wave_obj, "spi_apg")
        
        
        print("...",end='')
    else:
    
        for i in range(len(tx_config)):
            print(".",end='',flush=True)
            spi_write_tx_reg(i, tx_config[i])

    print("done!")

    if CFG_LINT_LEVEL >= 2:
        print("Reading back config to check for errors",end='')
        for i in range(len(tx_config)):
            print(".",end='',flush=True)
            read_byte = spi_read_tx_reg(i)
            if read_byte != tx_config[i]:
                sg.log.error(f"Tx Cfg Readback failed for byte {i}: Wrote {tx_config[i]} (bin: {bin(tx_config[i])}) and read {read_byte} (bin:{bin(read_byte)})")

                if CFG_LINT_LEVEL >= 3:
                    ## Loop and try to analyze why this byte failed.
                    shutil.copyfile("apg_samples.glue",f"apg_samples_dbg_{0}.glue")
                    for k in range(1,5):

                        for reg in ["spi_apg_run", "spi_apg_write_channel", "spi_apg_read_channel",
                     "spi_apg_sample_count","spi_apg_n_samples","spi_apg_write_buffer_len",
                     "spi_apg_next_read_sample","spi_apg_wave_ptr","spi_apg_status", "spi_apg_control"]:
                            val = sg.INSTR["car"].get_memory(reg)

                            print(f"{reg} -- {val}")
                        
                        input("")
                        read_byte = spi_read_tx_reg(i)
                        shutil.copyfile("apg_samples.glue",f"apg_samples_dbg_{k}.glue")
                        print(f"Retry {k}: Read {read_byte}")

                    #Go into gcshell for further debug
                    sg.gc.gcshell()
                else:
                    ## Simple retry
                    sg.log.warning(f"Error detected, retrying write for byte {i}")
                    while tx_config[i] != read_byte:
                        spi_write_tx_reg(i, tx_config[i])
                        read_byte = spi_read_tx_reg(i)
                        sg.log.debug(f"(wrote: {tx_config[i]} read: {read_byte})")

        dbg_error_val = sg.INSTR["car"].get_memory("spi_apg_dbg_error")
        sg.log.debug(f"spi_apg_dbg_error val: {dbg_error_val}")
                    

                
    print("done!")
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
    else:
        if SPI_FIRMWARE == "apg":
            return spi_cmd_apg(opcode_grp, address, length, WnR, data)
        elif SPI_FIRMWARE == "simple_serial":
            return spi_cmd_simple_serial(opcode_grp, address, length, WnR, data)
        else:
            print(f"spi_cmd error: didn't recognize SPI_FIRMWARE={SPI_FIRMWARE}")



# Directly convert a waves dict to a Glue Wave, without going through
# the step of writing ASCII files.
def genpattern_from_waves_dict_fast(waves_dict, apg_name):

    max_pattern_len = max([len(x) for x in waves_dict.values()])
    
    vector = [0 for _ in range(max_pattern_len)]

    for key in waves_dict.keys():
        io_pos = sg.gc.IO_pos[key]

        vector = [vector[i] | (waves_dict[key][i] << io_pos) for i in range(min(len(vector),len(waves_dict[key])))]

    if DEBUG_SPI:
        sg.log.debug(f"Vector: {vector}")

    APG_CLOCK_FREQUENCY = 10e6
    strobe_ps = 1/APG_CLOCK_FREQUENCY * 1e12
        
    return GlueWave(vector,strobe_ps,f"Caribou/Caribou/{apg_name}")


#Generate a dict-format wave for an individual SPI command, and just return that dict.
def genpattern_spi_cmd(opcode_grp, address, length, WnR, data=0):

    #Magic numbers to align inputs & outputs
    MAGIC_DATA_SHIFT_WRITE = 14 #14
    MAGIC_DATA_SHIFT_READ = 14  #15

    if length+14 > 512:
        sg.log.warning("WARNING: Attempting SPI write > 512 bits, check FW compatibility.")
    
    #First, build the SPI command which consists of:
    #{0} {WE (1b)} {opcode (2b)} {Address (8b)}
    cmd = 0
    cmd = cmd | WnR << 10 # WE
    cmd = cmd | opcode_grp << 8
    cmd = cmd | address
                     
    # Add 2 delay cycles
    cmd = cmd << 2

    spi_bitstring = cmd | (data) << MAGIC_DATA_SHIFT_WRITE


    # Convert bitstring to a waves dict
    pre_pattern_len = 5
    
    waves = {"cs_b": [1 for _ in range(pre_pattern_len)],
             "pico": [0 for _ in range(pre_pattern_len)]}

    for i in range(MAGIC_DATA_SHIFT_READ+length):
        if spi_bitstring & (1 << i) > 0:
            waves["pico"] = waves["pico"] + [1]
        else:
            waves["pico"] = waves["pico"] + [0]
        waves["cs_b"] = waves["cs_b"] + [0]

    waves["cs_b"] = waves["cs_b"] + [1 for _ in range(pre_pattern_len)]
    waves["pico"] = waves["pico"] + [0 for _ in range(pre_pattern_len)]

    return waves


def spi_cmd_apg(opcode_grp, address, length, WnR, data=0):

    #Magic numbers to align inputs & outputs
    MAGIC_DATA_SHIFT_WRITE = 14 #14
    MAGIC_DATA_SHIFT_READ = 14  #15

    if length+14 > 512:
        sg.log.warning("WARNING: Attempting SPI write > 512 bits, check FW compatibility.")
    
    #First, build the SPI command which consists of:
    #{0} {WE (1b)} {opcode (2b)} {Address (8b)}
    cmd = 0
    cmd = cmd | WnR << 10 # WE
    cmd = cmd | opcode_grp << 8
    cmd = cmd | address
                     
    # Add 2 delay cycles
    cmd = cmd << 2

    spi_bitstring = cmd | (data) << MAGIC_DATA_SHIFT_WRITE


    # Convert bitstring to a waves dict
    pre_pattern_len = 5
    
    waves = {"cs_b": [1 for _ in range(pre_pattern_len)],
             "pico": [0 for _ in range(pre_pattern_len)]}

    for i in range(MAGIC_DATA_SHIFT_READ+length):
        if spi_bitstring & (1 << i) > 0:
            waves["pico"] = waves["pico"] + [1]
        else:
            waves["pico"] = waves["pico"] + [0]
        waves["cs_b"] = waves["cs_b"] + [0]

    waves["cs_b"] = waves["cs_b"] + [1 for _ in range(pre_pattern_len)]
    waves["pico"] = waves["pico"] + [0 for _ in range(pre_pattern_len)]

    
    glue_wave_obj = genpattern_from_waves_dict_fast(waves, "spi_apg")

    result = sg.gc.read_glue(run_pattern_caribou(glue_wave_obj, "spi_apg"))


    poci_data = sg.gc.get_bitstream(result, "poci")
    
   

    poci_bin = 0
   
    for i in range(length):
        if poci_data[i+MAGIC_DATA_SHIFT_READ + pre_pattern_len] > 0:
            poci_bin = poci_bin | (1 << i)

            
    if DEBUG_SPI and not WnR:
        sg.log.debug(f"Return: {poci_data}")
        sg.log.debug(f"Return bits: {poci_bin} (bin: {bin(poci_bin)})")
        
    
    #sg.gc.plot_glue(result)
    return poci_bin
    

def spi_cmd_simple_serial(opcode_grp, address, length, WnR, data=0):
    
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
        if SPI_FIRMWARE == "simple_serial":
            status = sg.INSTR["car"].get_memory("spi_status")
        elif SPI_FIRMWARE == "apg":
            status = sg.INSTR["car"].get_memory("spi_apg_status")

        if DEBUG_SPI:
            sg.log.debug(f"spi_status - {SPI_Status(status)}")

        if status == 0:
            break

        time.sleep(0.01)


def apg_wait_for_idle(apg_name):
    while True:
        status = sg.INSTR["car"].get_memory(f"{apg_name}_status")

        if status == 0:
            break

        time.sleep(0.1)

#Caribou version of sg.pr.run_pattern()
# Right now, apg_name = "apg" or "spi_apg"
def run_pattern_caribou(glue_wave,apg_name):

    ## (0) Wait for idle, then clear the write buffer.
    apg_wait_for_idle(apg_name)
    sg.INSTR["car"].set_memory(f"{apg_name}_clear",1)
    
    #Parse glue file names OR python objects
    if type(glue_wave) == str:
        glue_wave = sg.gc.read_glue(glue_wave)


    ## (1) SET NUMBER OF SAMPLES
    N = glue_wave.len

    sg.INSTR["car"].set_memory(f"{apg_name}_n_samples", N)

    ## (2) WRITE PATTERN TO APG
    for n in range(N):
        sg.INSTR["car"].set_memory(f"{apg_name}_write_channel",glue_wave.vector[n])


    ## (3) RUN AND WAIT FOR IDLE
    sg.INSTR["car"].set_memory(f"{apg_name}_run", 1)

    time.sleep(0.1)
    apg_wait_for_idle(apg_name)

    ## (4) READ BACK SAMPLES
    samples = []

    for n in range(N):
        #dbg_error_val = sg.INSTR["car"].get_memory("spi_apg_next_read_sample")
        #sg.log.debug(f"nrs: {dbg_error_val}")
        samples.append(sg.INSTR["car"].get_memory(f"{apg_name}_read_channel"))


    APG_CLOCK_FREQUENCY = 10e6
    strobe_ps = 1/APG_CLOCK_FREQUENCY * 1e12
        
    glue = GlueWave(samples,strobe_ps,f"Caribou/Caribou/{apg_name}")

    sg.gc.write_glue(glue,"apg_samples.glue")

    return "apg_samples.glue"



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


    APG_CLOCK_FREQUENCY = 40e6
    strobe_ps = 1/APG_CLOCK_FREQUENCY * 1e12
        
    glue = GlueWave(samples,strobe_ps,"Caribou/Caribou/apg")

    sg.gc.write_glue(glue,"apg_samples.glue")
    sg.gc.plot_glue(glue)
