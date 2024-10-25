

#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

SC_DEBUG = False

class DILVERT_SC():
    
    def __init__(self, data_array):
        self.arr = data_array
        # Remember that the Scan Chain is MSB first.
        self.field_map = {"QCOARSE": [0,10],
                        "QFINE":[10,17],
                        "DOUT1_Select": [17,19], #Actually DOUT2 by Rev1 PCB silk
                        "DOUT2_Select":[19,21], #Actually DOUT1 by Rev1 PCB silk
                        "CAL1": [21,22],
                        "CAL0":[22,23],
                        "DRV": [23,25],
                         }      
        
    def get_field(self,field_name):
        """Returns the integer corresponding to the named field."""
        field_lo, field_hi = self.field_map[field_name]
        
        return vec_to_int(self.arr[field_lo:field_hi])

    def set_field(self,field_name,data):
        """Sets the named field to the given integer."""
        field_lo, field_hi = self.field_map[field_name]
        
        self.arr[field_lo:field_hi] = int_to_vec(data, field_hi-field_lo)

    def print_fields(self):
        for field_name in self.field_map.keys():
            print(f"{field_name:10} : {self.get_field(field_name)}")

    def __eq__(self,other_sc):
        return type(other_sc) == DILVERT_SC and self.arr == other_sc.arr

def pulse_reset():
    
    waves = {"RESET":[0,1,0]}
    
    sg.pr.run_pattern(sg.gc.dict2Glue(waves))

def serial_write(input_sc, tsf=1, s_pass=True):
    """Write SC data to the DILVERT ASIC"""
    
    waves = {"S_DIN":[0,0,0],
             "S_PASS":[0,0,0],
             "S_CLK":[0,0,0]}
    
    if SC_DEBUG:
        print(f"Writing SC: {input_sc.arr}")
    
    for i in range(len(input_sc.arr)):
        dat = input_sc.arr[i]
        waves["S_DIN"] += [dat,dat]
        waves["S_CLK"] += [0,1]
        waves["S_PASS"]+= [0,0]
    
    if s_pass:
        #Send data to internal registers.    
        waves["S_CLK"] +=[0,0,1,0]
        waves["S_PASS"]+=[0,1,1,0]
    
    write_glue = sg.gc.read_glue(sg.pr.run_pattern(sg.gc.dict2Glue(waves,output_mode=3),outfile_tag="sc_write", time_scale_factor=10)[0])
    
    if SC_DEBUG:
        sg.gc.plot_glue(write_glue)
    
def serial_read(tsf=1, s_load=True):
    """Read SC data from the DILVERT ASIC"""
    
    if s_load:
        waves = {"S_CLK":[0,0,1,0],
                "S_LOAD":[0,1,1,0]}
    else:
        waves = {"S_CLK":[0,0,0,0]}
    for i in range(25):
        waves["S_CLK"]+=[0,1]
        
        
    read_glue = sg.gc.read_glue(sg.pr.run_pattern(sg.gc.dict2Glue(waves),outfile_tag="sc_read", time_scale_factor=10)[0])
    
    if SC_DEBUG:
        sg.gc.plot_glue(read_glue)
    
    data_out = sg.gc.get_clocked_bitstream(read_glue,"S_CLK","S_DOUT")
    
    #Trim off the first data bit which comes from the S_LOAD clock.
    if s_load:
        data_out = data_out[1:]
    
    if SC_DEBUG:
        print(f"Clocked_bitstream: {data_out}")
    
    return DILVERT_SC(data_out)