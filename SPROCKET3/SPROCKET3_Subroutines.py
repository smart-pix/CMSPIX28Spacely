import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *
#from Spacely_Utils import int_to_vec


DEBUG_SPI = True

## Memory Map Dictionary
## Keys: Reg names
## Values: [register byte address, bit offset, bit length]
mem_dict = {'comp_rise_calc': [131, 0, 14],
            'comp_fall_calc': [133, 0, 14],
            'comp_rise_read': [135, 0, 14],
            'comp_fall_read': [137, 0, 14],
            'comp_rise_Rst': [139, 0, 14],
            'comp_fall_Rst': [141, 0, 14],
            'comp_rise_bufsel': [143, 0, 14],
            'comp_fall_bufsel': [145, 0, 14],
            'DACclr_pattern_delay': [147, 0, 4],
            'Qequal_pattern_delay': [147, 4, 4],
            'global_counter_period': [148, 0, 14],
            'DACclr_pattern': [150, 0, 192],
            'Qequal_pattern': [174, 0, 192],
            'fullReadout': [198, 0, 1],
            'global_shutter': [198, 1, 1],
            'cis_ctrl_clk_div': [199, 0, 10],
            'cis_ctrl_skip_samples': [201, 0, 16],
            'pattern_ccd_reset': [203, 0, 108],
            'pattern_integration': [217, 0, 108],
            'pattern_skipping': [231, 0, 108],
            'DTP0_Select': [245, 0, 6],
            'DTP1_Select': [246, 0, 6],
            'DTP2_Select': [247, 0, 6],
            'gpio': [248, 0, 8]}



def spi_write_reg(name, data):
    byte_address = mem_dict[name][0]
    bit_offs = mem_dict[name][1]
    bit_length = mem_dict[name][2]

    if bit_offs > 0:
        # Read the lower bits and write them back
        lower_bits = spi_cmd(byte_address,bit_offs,0)
        return spi_cmd(byte_address,bit_length+bit_offs,1,(data << bit_offs) + lower_bits)
    else:
        return spi_cmd(byte_address,bit_length,1,data)


def spi_read_reg(name):
    byte_address = mem_dict[name][0]
    bit_offs = mem_dict[name][1]
    bit_length = mem_dict[name][2]

    if bit_offs > 0:
        read_data = spi_cmd(byte_address,bit_length+bit_offs,0) >> bit_offs
    else:
        read_data = spi_cmd(byte_address,bit_length,0)

    return read_data
    
    
def genpattern_spi_cmd(address, length, WnR, data=0):
    """Generate a Glue pattern dict that produces a given SPI command"""

    waves = {"cs_b":     [1],
             "reset_b" : [1],
             "pico"    : [0],
             "trig"    : [0]}

    address_bits = int_to_vec(address, 10)
    address_bits.reverse() # Big endian address
    data_bits    = int_to_vec(data, length)

    cmd_bits = [WnR] + address_bits + data_bits

    if DEBUG_SPI:
        print(f"spi_cmd: {cmd_bits}")

    for i in range(len(cmd_bits)):
        waves["pico"]    += [cmd_bits[i]]
        waves["cs_b"]    += [0]

    waves["pico"]    += [0,0]
    waves["cs_b"]    += [1,1]

    return waves


def spi_cmd(address, length, WnR, data=0):

    MAGIC_DATA_SHIFT_READ = 14
    
    waves = genpattern_spi_cmd(address,length,WnR,data)
    glue_wave_obj = sg.gc.dict2Glue(waves)

    if DEBUG_SPI:
        sg.gc.write_glue(glue_wave_obj,"spi_cmd_ascii.txt")

    result = sg.pr.run_pattern(glue_wave_obj, return_mode = 1)
        
    poci_data = sg.gc.get_bitstream(result,"poci")

    poci_bits = poci_data[MAGIC_DATA_SHIFT_READ:-2]

    poci_bin = vec_to_int(poci_bits)

    if DEBUG_SPI:
        print(f"poci_data: {poci_data}")
        print(f"poci_bits: {poci_bits}")
        print(f"poci_bin:  {poci_bin}")


    return poci_bin
    
        
