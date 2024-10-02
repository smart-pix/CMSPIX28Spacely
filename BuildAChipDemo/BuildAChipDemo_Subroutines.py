
#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

SEVEN_SEG_PATTERNS = {0: [1,1,1,1,1,1,0],
                      1: [0,1,1,0,0,0,0],
                      2: [1,1,0,1,1,0,1],
                      3: [1,1,1,1,0,0,1],
                      4: [0,1,1,0,0,1,1],
                      5: [1,0,1,1,0,1,1],
                      6: [1,0,1,1,1,1,1],
                      7: [1,1,1,0,0,0,0],
                      8: [1,1,1,1,1,1,1],
                      9: [1,1,1,0,0,1,1]}


def genpattern_7seg(target_number):
    """Generates a wave pattern which allows writing a given number to a two-digit 7seg display"""
    
    sdi1_pattern = SEVEN_SEG_PATTERNS[int(target_number/10)] 
    sdi2_pattern = SEVEN_SEG_PATTERNS[target_number % 10]
    
    waves = {"CLK": [],
             "SDI1": [],
             "SDI2": [],
             "LE" : []}
             
    for i in range(len(sdi_pattern)):
        waves["CLK"] = waves["CLK"] + [0,1]
        waves["SDI1"] = waves["SDI1"] + [sdi1_pattern[i]]*2
        waves["SDI2"] = waves["SDI2"] + [sdi2_pattern[i]]*2
        waves["LE"]  = waves["LE"]  + [0,0]
        
        
    waves["LE"] = waves["LE"] + [1]
    
    return waves

def apg_wait_for_idle(apg_name):
    while True:
        status = sg.INSTR["car"].get_memory(f"{apg_name}_status")

        if status == 0:
            break

        time.sleep(0.1)
        
        
# Directly convert a waves dict to a Glue Wave, without going through
# the step of writing ASCII files.
def genpattern_from_waves_dict_fast(waves_dict, hw_name):

    max_pattern_len = max([len(x) for x in waves_dict.values()])
    
    vector = [0 for _ in range(max_pattern_len)]

    #For each signal under consideration:
    for key in waves_dict.keys():
        io_pos = sg.gc.IO_pos[key]
        signal_len = len(waves_dict[key])

        for i in range(len(vector)):
            if i < signal_len:   
                vector[i] = vector[i] | (waves_dict[key][i] << io_pos)
            else:
                #Pad out to the length of vector based on the last value of the signal.
                vector[i] = vector[i] | (waves_dict[key][signal_len-1] << io_pos)

    APG_CLOCK_FREQUENCY = 10e6
    strobe_ps = 1/APG_CLOCK_FREQUENCY * 1e12
        
    return GlueWave(vector,strobe_ps,f"Caribou/Caribou/{hw_name}")




#Caribou version of sg.pr.run_pattern()
# Right now, apg_name = "apg" or "spi_apg"
def run_pattern_caribou(glue_wave,apg_name="apg",tsf=1):

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
        #Implement time scaling.
        for _ in range(tsf):
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