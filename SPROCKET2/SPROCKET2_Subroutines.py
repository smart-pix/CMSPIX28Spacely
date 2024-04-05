# SQUIDDAC Routines


import numpy as np
import time

#Import utilities from py-libs-common
from hal_serial import * #todo: this shouldn't import all symbols but just the ArudinoHAL class
from pattern_runner import *

from fnal_libIO import *
from fnal_libinstrument import *
from fnal_ni_toolbox import * #todo: this should import specific class(es)
import fnal_log_wizard as liblog

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *




# # # # # # # # # # # # # # # # # # # # # # # # # # 
#            SUB-ROUTINES                         #
# # # # # # # # # # # # # # # # # # # # # # # # # # 
# These are mini functions that execute a small part of a routine.

def set_basic_gain_region_params(df, region):
    if region == 0:
        df.set("Range2",1)
        df.set("n_skip",10)
        
    elif region == 1:
        df.set("Range2",1)
        df.set("n_skip",1)
        
    elif region == 2:
        df.set("Range2",0)
        df.set("n_skip",10)

    elif region == 3:
        df.set("Range2",0)
        df.set("n_skip",1)
        

# Core function to set up the system to take full conversions. 
def setup_full_conversion(df):

    if not df.check(["tsf_sample_phase","Range2","CapTrim","n_skip","time_scale_factor"]):
        print("df metadata check for setup_full_conversion() failed!")
        return -1

    ## (1) UNSTICK VDD_ASIC IF LATCHED
    unstick_VDD_ASIC()
    
    ## (2) SET UP THE PULSE GENERATOR
    tsf_sample_phase = df.get("tsf_sample_phase")
    period_us = 0.25*tsf_sample_phase+0.05
    
    # When tsf=1, pulses are 250 nanoseconds (0.25 us) wide because mclk's frequency is 2 MHz (T=500ns).
    # Default amplitude for starting out = 5 mV. If you want to change this you have to do it yourself.
    sg.INSTR["AWG"].config_AWG_as_Pulse(5, pulse_width_us=0.25*df.get("tsf_sample_phase"), pulse_period_us=period_us)
    #time.sleep(3)

    ## (3) SETUP THE SCAN CHAIN
    #Set CapTrim value and ensure TestEn=0
    SC_PATTERN = SC_CFG(override=0,TestEn=0,Range2=df.get("Range2"), CapTrim=df.get("CapTrim"))
    sg.pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")


    ## (4) GENERATE GLUE WAVEFORM
    fc_glue = genpattern_Full_Conversion(df)

    return fc_glue


# Core function which performs a full-channel conversion by running a Glue wave and returns the result. 
def get_full_conversion_result(fc_glue, pulse_mag, df):

    if pulse_mag is not None:
        sg.INSTR["AWG"].set_pulse_mag(pulse_mag)
        time.sleep(0.1)

    check_halt_sample = df.get("check_halt_sample")
    if check_halt_sample == None:
        check_halt_sample = False

    #If we want to check halt_sample, we must use the Scope.
    if check_halt_sample:
        sg.INSTR["Scope"].setup_trigger(1,0.6)

    #Run the Glue wave on the ASIC
    fc_result = sg.pr.run_pattern(fc_glue,outfile_tag="fc_result")[0]
    
    #Analyze halt_sample if needed.
    if check_halt_sample:
        halt_sample_wave = sg.INSTR["Scope"].get_wave(2)
        
        if any([x > 0.6 for x in halt_sample_wave]):
            halt_sample = 1
        else:
            halt_sample = 0

    #Get DACclr and capLo
    result_glue = sg.gc.read_glue(fc_result)
    dacclr_wave = sg.gc.get_bitstream(result_glue,"DACclr")
    caplo_wave = sg.gc.get_bitstream(result_glue,"capLo_ext")

    result = interpret_CDAC_pattern_edges(caplo_wave, dacclr_wave)

    if check_halt_sample:
        return (result, halt_sample)
    else:
        return result




def falling_edge_idx(wave, number=1, thresh=0.6):

    falling_edge_count = 0

    for i in range(1,len(wave)):
        if wave[i] <= thresh and wave[i-1] > thresh:
            falling_edge_count = falling_edge_count + 1
            
            if falling_edge_count == number:
                return i
            

def rising_edge_idx(wave, number=1, thresh=0.6):

    rising_edge_count = 0

    for i in range(1,len(wave)):
        if wave[i] >= thresh and wave[i-1] < thresh:
            rising_edge_count = rising_edge_count + 1

            if rising_edge_count == number:
                return i
        #print(wave[i-1],wave[i],rising_edge_count)


def unstick_VDD_ASIC():
    
    while True:
        VDD_ASIC_Current = V_PORT["VDD_ASIC"].get_current()
        
        if VDD_ASIC_Current < 50e-6:
            break
        
        #rando = np.random.randint(0,350)
        #voltage = 1 + float(rando)/1000
        rando = np.random.randint(0,550)
        voltage = 0.8 + float(rando)/1000

        print(f"Setting VDD_ASIC={voltage}")
        V_PORT["VDD_ASIC"].set_voltage(voltage)
        
    #Restore VDD_ASIC to set voltage.
    V_PORT["VDD_ASIC"].set_voltage(V_LEVEL["VDD_ASIC"])
    print("DONE!")



# Helper function to write a CSV file.
# col_param_range = List containing all values of the column parameter.
# row_param_range = List containing all values of the row parameter.
# results = List of lists. Each sublist corresponds to a column parameter value and each item in the sublist corresponds to a row param value.
def write_parameter_sweep_to_csv(col_param_range, row_param_range, results, filename, col_param_name="Col_Param",row_param_name="Row_Param"):

    assert(len(results) == len(col_param_range))
    assert(len(results[0]) == len(row_param_range))

    write_file = open("output\\"+filename, "w")

    #First row: write out all the column headers.
    write_file.write(f"{row_param_name}")
    for col_param in col_param_range:
            write_file.write(f",{col_param}")

    write_file.write("\n")

    #For each row after that, start by writing vin...
    row_idx = 0
    for row_param in row_param_range:
        write_file.write(f"{row_param}")

        col_idx = 0

        #Then write down the results ...
        for col_param in col_param_range:
            write_file.write(f",{results[col_idx][row_idx]}")

            col_idx = col_idx + 1

        write_file.write("\n")

        row_idx = row_idx+1


    write_file.close()


# # # # # # # # # # # # # # # # # # # # # # # # # # 
#            ANALYSIS FUNCTIONS                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # 


#Calculates the slope of PGL in Volts per second, given captured waves from the oscilloscope.
def calculate_PGL_Slope(Rst_wave, out_stage_1_wave, scope_timebase_s):

    #Calculate the number of scope points per microsecond. 
    #Each wave represents a capture of the full screen (10 divisions) so:

    scope_points_per_division = len(Rst_wave)/10

    scope_points_per_us = scope_points_per_division / (scope_timebase_s * 1e6) 
    
    #Get the first falling edge of Rst:
    Rst_falling_edge = falling_edge_idx(Rst_wave, 1, 0.6)

    #Heuristically, measure the slope at about Rst + 0.5us to Rst + 1.5us
    
    x1 = Rst_falling_edge + int(0.5*scope_points_per_us)
    x2 = Rst_falling_edge + int(5.5*scope_points_per_us)
    
    y1 = out_stage_1_wave[x1]
    y2 = out_stage_1_wave[x2]

    sg.log.debug(f"Calculating PGL slope from: ({x1},{y1}), ({x2},{y2})")
    
    #y2 and y1 are in units of V, and x2-x1 = 5us
    slope_V_per_us = (y2-y1) / 5
    
    slope_V_per_s = slope_V_per_us * 1e6

    sg.log.debug(f"Slope:{slope_V_per_s}")
    
    return slope_V_per_s

#Get the implied value from a string of DACclr and capLo pulses only by counting posedges.
#This method makes no assumption about the bit period, and thus can be accurate w/ lower scope resolution.
def interpret_CDAC_pattern_edges(caplo_wave, dacclr_wave):

    gc = GlueConverter(DEFAULT_IOSPEC)

    
    THRESH = 0.6

    caplo_edges = []

    for idx in range(1,len(caplo_wave)):

        #If there is a dacclr edge, start a new bit approximation. 
        if (dacclr_wave[idx-1] < THRESH and dacclr_wave[idx] >= THRESH):
            caplo_edges.append(0)
            #print(f"(DBG) dacclr edge at {idx*25} ns")

        #Within each bit approximation, count the number of capLo edges.
        if (caplo_wave[idx-1] < THRESH and caplo_wave[idx] >= THRESH):
            caplo_edges[-1] = caplo_edges[-1] + 1
            #print(f"(DBG) caplo edge at {idx*25} ns")

    sg.log.debug(f"caplo_edges: {caplo_edges}")

    if len(caplo_edges) != 12 or caplo_edges[0] != 0:
        print(f"ERROR: Malformed caplo_edges {caplo_edges}")
        gc.plot_waves([caplo_wave,dacclr_wave],["caplo","dacclr"],1)
        return -99

    binary_approximation = []
    
    for bit in range(1, 11):

        if caplo_edges[bit] - caplo_edges[bit-1] == 0:
            binary_approximation.append(1)

        elif caplo_edges[bit] - caplo_edges[bit-1] == 1:
            binary_approximation.append(0)
        
        else:
            print(f"ERROR: Malformed caplo_edges {caplo_edges}")
            gc.plot_waves([caplo_wave,dacclr_wave],["caplo","dacclr"],1)
            return -99

    sg.log.debug(f"bin_approx: {binary_approximation}")

    #Notes:
    # - Reverse the binary approximation because it is naturally big-endian (MSB is decided first) whereas
    #   vec_to_int expects little-endian.
    binary_approximation.reverse()
    
    return vec_to_int(binary_approximation)



# # # # # # # # # # # # # # # # # # # # # # # # # # 
#            PATTERN GENERATORS                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # 



#Function to generate a SPROCKET2 test pixel scan chain vector (19 bits long)
#based on setting each individual field by name. 
def SC_CFG(override,TestEn,Range2,CapTrim=0):
    captrim_vec = int_to_vec(CapTrim,6)

    #SC is big-endian, but int_to_vec() is little-endian
    captrim_vec.reverse()
    
    return [0]*10 + captrim_vec + [override] + [TestEn] + [Range2]




# Generates the pattern necessary to run the ADC.
def genpattern_Vref_Loopback(time_scale_factor):
    
    waves = {}
    
    #Start off w/ some zeros to avoid extra pulse bug.
    waves["DACclr"] = [0]*10
    waves["Qequal"] = [0]*10
    waves["capClk"] = [0]*10
    waves["calc"]   = [0]*10
    waves["read_ext"]   = [0]*10
    
   
    # Assert Rst and read_b throughout the entire thing.
    #Except we'll pulse read at the beginning to make sure this is interpreted as True_Rst.
    waves["read_ext"] = [1]*time_scale_factor + [0]*999*time_scale_factor
    waves["Rst_ext"]      = [1]*1000*time_scale_factor
    
    
    #Put a rising edge of phi1_ext in the middle.
    waves["phi1_ext"] = [0]*500*time_scale_factor + [1]*500*time_scale_factor
    
   
    #2) Writing to an ASCII file.
    with open("output\\genpattern_vref_loopback.txt",'w') as write_file:
        for w in waves.keys():
            write_file.write(w+":"+"".join([str(x) for x in waves[w]])+"\n")
            
    #3) Convert ASCII file to Glue.
    gc = GlueConverter(DEFAULT_IOSPEC)

    gc.ascii2Glue("output\\genpattern_vref_loopback.txt", 1, "genpattern_vref_loopback")


    return "genpattern_vref_loopback_se_io.glue"

    
# Generates the pattern necessary to run the ADC.
def genpattern_ADC_Capture(time_scale_factor, apply_pulse_1_fix=False, tsf_qequal=1, tsf_pause=1, tsf_finalpause=0):
    
    waves = {}
    
    #Start off w/ some zeros to avoid extra pulse bug.
    waves["DACclr"] = [0]*10
    waves["Qequal"] = [0]*10
    waves["capClk"] = [0]*10
    waves["calc"]   = [0]*10
    waves["read_ext"]   = [0]*10
    
    
    for adc_bit in range(1,12):  #Updated 12/8/2023 to add an 11th bit for 10b readout :D
        
        for clk_cycle in range(adc_bit):

            if clk_cycle == 0:
                #Each bit starts off w/ a DACclr pulse.
                waves["DACclr"] = waves["DACclr"] + [1,1,1]*time_scale_factor
                waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
                waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor
                
                if apply_pulse_1_fix:
                    #Extend this pulse only to be 10x longer.
                    waves["DACclr"] = waves["DACclr"] + [1,1,1]*10*time_scale_factor
                    waves["capClk"] = waves["capClk"] + [1,1,1]*10*time_scale_factor
                    waves["Qequal"] = waves["Qequal"] + [0,0,0]*10*time_scale_factor

            else:
                #capClk pulse
                waves["DACclr"] = waves["DACclr"] + [0,0,0]*time_scale_factor
                waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
                waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor


            #Add a 0 for non-overlapping.    
            waves["DACclr"] = waves["DACclr"] + [0]*tsf_pause
            waves["capClk"] = waves["capClk"] + [0]*tsf_pause
            waves["Qequal"] = waves["Qequal"] + [0]*tsf_pause
            
            #Qequal pulse
            waves["DACclr"] = waves["DACclr"] + [0,0,0]*time_scale_factor*tsf_qequal
            waves["capClk"] = waves["capClk"] + [0,0,0]*time_scale_factor*tsf_qequal
            waves["Qequal"] = waves["Qequal"] + [1,1,1]*time_scale_factor*tsf_qequal
            
            
            #Add a 0 for non-overlapping.    
            waves["DACclr"] = waves["DACclr"] + [0]*tsf_pause
            waves["capClk"] = waves["capClk"] + [0]*tsf_pause
            waves["Qequal"] = waves["Qequal"] + [0]*tsf_pause
            
            
            
            
        waves["DACclr"] = waves["DACclr"] + [0]*tsf_finalpause
        waves["capClk"] = waves["capClk"] + [0]*tsf_finalpause
        waves["Qequal"] = waves["Qequal"] + [0]*tsf_finalpause
        
        
    #Final DACclr pulse.
    waves["DACclr"] = waves["DACclr"] + [1,1,1]*time_scale_factor
    waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
    waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor
        
    waves["calc"] = waves["calc"] + [1]*(len(waves["DACclr"])-len(waves["calc"]))
    waves["read_ext"] = waves["calc"]
    
    #2) Writing to an ASCII file.
    with open("output\\genpattern_adc_op.txt",'w') as write_file:
        for w in waves.keys():
            write_file.write(w+":"+"".join([str(x) for x in waves[w]])+"\n")
            
    #3) Convert ASCII file to Glue.
    gc = GlueConverter(DEFAULT_IOSPEC)

    gc.ascii2Glue("output\\genpattern_adc_op.txt", 1, "genpattern_adc_op")


    return "genpattern_adc_op_se_io.glue"


def genpattern_Full_Conversion(df):


    time_scale_factor = df.get("time_scale_factor",missing_ok=True, default=10)
    tsf_sample_phase = df.get("tsf_sample_phase",missing_ok=True, default=2)
    StoC_Delay = df.get("StoC_Delay",missing_ok=True, default=0)
    sample_phase_stretch = df.get("sample_phase_stretch",missing_ok=True, default=0)
    trig_delay = df.get("trig_delay",missing_ok=True, default=0)
    n_skip = df.get("n_skip",missing_ok=True, default=10)
    tsf_reset = df.get("tsf_reset",missing_ok=True, default=1)
    tflip1 = df.get("tflip1",missing_ok=True, default=2)
    Rst_early = df.get("Rst_early",missing_ok=True,default=0)

    #Initialize wave dictionary
    waves = {}

    #Everything starts out at 0 for at least 10 cycles.
    #Possibly up to 10*tsf_sample_phase if needed so that we can have an appropriately early phi1_ext firing.
    waves["mclk"] =       [0]*max(10,10*tsf_sample_phase)
    #waves["read_ext"] =   [0]*10  --> at the end we will just assign read_ext = calc
    waves["Rst_ext"] =    [0]*max(10,10*tsf_sample_phase) 
    waves["bufsel_ext"] = [0]*max(10,10*tsf_sample_phase)
    waves["capClk"] = [0]*max(10,10*tsf_sample_phase)    
    waves["Qequal"] = [0]*max(10,10*tsf_sample_phase)
    waves["DACclr"] = [0]*max(10,10*tsf_sample_phase)
    waves["calc"]   = [0]*max(10,10*tsf_sample_phase)
    

    ### RESET PHASE ###

    #mclk=0 and Rst=1. read/calc=0, but we pulse it at the beginning to make sure SAR logic is reset.
    waves["mclk"] =       waves["mclk"]+[0]*40 + [0]*40*(tsf_reset-1)
    #waves["read_ext"] =   waves["read_ext"] + [1]*5 + [0]*35
    waves["calc"] =   waves["calc"] + [1]*5 + [0]*35 + [0]*40*(tsf_reset-1)
    waves["Rst_ext"] =    waves["Rst_ext"] + [1]*40 + [1]*40*(tsf_reset-1)

    #Establish autorange comparison voltage of 0.75V, see user manual.
    waves["bufsel_ext"] = waves["bufsel_ext"] + [0]*20 + [1]*20 + [1]*40*(tsf_reset-1)
    waves["capClk"] = waves["capClk"] + [0,1,1,1,0,0,0,0,0,1,1,1,0] + [0]*27 + [0]*40*(tsf_reset-1)
    waves["Qequal"] = waves["Qequal"] + [0,0,0,0,0,1,1,1,0,0,0,0,0,1,1,1,0] + [0]*23 + [0]*40*(tsf_reset-1)

    #DACclr = 0
    waves["DACclr"] =       waves["DACclr"]+[0]*40 + [0]*40*(tsf_reset-1)

    
    ### SAMPLING PHASE ###

    #if one_shot:
    #    n_samples = 1
    #else:
    #    n_samples = 10
    
    n_samples = n_skip

    for i in range(n_samples):
        #w/ time_scale_factor = 1, the period of mclk is 20 ticks or 2 MHz
        waves["mclk"] = waves["mclk"] + [1]*(10*tsf_sample_phase+sample_phase_stretch) + [0]*(10*tsf_sample_phase + sample_phase_stretch)

        #In the sampling phase, read=Rst=0, bufse1=1 (Vref_fe), and all the ADC signals are zero.
        #waves["read_ext"] = waves["read_ext"] + [0]*20*tsf_sample_phase
        waves["calc"] = waves["calc"] + [0]*(20*tsf_sample_phase + 2*sample_phase_stretch)
        waves["capClk"] = waves["capClk"] + [0]*(20*tsf_sample_phase + 2*sample_phase_stretch)
        waves["Qequal"] = waves["Qequal"] + [0]*(20*tsf_sample_phase + 2*sample_phase_stretch)
        waves["DACclr"] = waves["DACclr"] + [0]*(20*tsf_sample_phase + 2*sample_phase_stretch)
        waves["Rst_ext"] = waves["Rst_ext"] + [0]*(20*tsf_sample_phase + 2*sample_phase_stretch)
        waves["bufsel_ext"] = waves["bufsel_ext"] + [1]*(20*tsf_sample_phase + 2*sample_phase_stretch)
        


    ### CONVERSION PHASE ###
        
    n1 = max(Rst_early,0) #Number of cycles Rst is earlier than everyone else, if it is.
    n2 = max(-1*Rst_early,0) #Number of cylces Rst is later than everyone else, if it is.

    ## PROOF
    # Either n1 or n2 is non-zero. If n1 is zero, then n2 + tflip1-n2 = tflip1. 
    # If n2 is zero, then, n1 + tflip1 = n1+tflip1

    #So far, read has been exactly equal to calc. 
    waves["read_ext"] = waves["calc"]

    #bufsel->0 and Rst->1. Two cycles later, read->1
    #waves["read_ext"] = waves["read_ext"] + [0,0,1]
    waves["read_ext"] = waves["read_ext"] +     [0]*n1 +     [0]*tflip1 + [1]
    waves["capClk"] = waves["capClk"] +      [0]*n1 + [0]*tflip1 + [0]
    waves["Qequal"] = waves["Qequal"] +     [0]*n1 +  [0]*tflip1 + [0]
    waves["DACclr"] = waves["DACclr"] +     [0]*n1 + [0]*tflip1 + [0]
    waves["Rst_ext"] = waves["Rst_ext"] +    [1]*n1 + [0]*n2 + [1]*(tflip1-n2) + [1]
    waves["bufsel_ext"] = waves["bufsel_ext"] +  [1]*n1 +[0]*tflip1 + [0]
    waves["mclk"] = waves["mclk"] +  [0]*n1 +[0]*tflip1 + [0]

    
    #StoC_Delay
    waves["mclk"] = waves["mclk"] + [0]*StoC_Delay
    waves["read_ext"] = waves["read_ext"] + [1]*StoC_Delay
    waves["calc"] = waves["calc"] + [0,0]+[0]*StoC_Delay + [1]
    waves["capClk"] = waves["capClk"] + [0]*StoC_Delay
    waves["Qequal"] = waves["Qequal"] + [0]*StoC_Delay
    waves["DACclr"] = waves["DACclr"] + [0]*StoC_Delay
    waves["Rst_ext"] = waves["Rst_ext"] + [1]*StoC_Delay
    waves["bufsel_ext"] = waves["bufsel_ext"] + [0]*StoC_Delay
    
    for adc_bit in range(1,12):
        
        for clk_cycle in range(adc_bit):

            if clk_cycle == 0:
                #Each bit starts off w/ a DACclr pulse.
                waves["DACclr"] = waves["DACclr"] + [1,1,1]*time_scale_factor
                waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
                waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor

            else:
                #capClk pulse
                waves["DACclr"] = waves["DACclr"] + [0,0,0]*time_scale_factor
                waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
                waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor


            #Add a 0 for non-overlapping.    
            waves["DACclr"] = waves["DACclr"] + [0]
            waves["capClk"] = waves["capClk"] + [0]
            waves["Qequal"] = waves["Qequal"] + [0]
            
            #Qequal pulse
            waves["DACclr"] = waves["DACclr"] + [0,0,0]*time_scale_factor
            waves["capClk"] = waves["capClk"] + [0,0,0]*time_scale_factor
            waves["Qequal"] = waves["Qequal"] + [1,1,1]*time_scale_factor
            
            
            #Add a 0 for non-overlapping.    
            waves["DACclr"] = waves["DACclr"] + [0]
            waves["capClk"] = waves["capClk"] + [0]
            waves["Qequal"] = waves["Qequal"] + [0]
            
        
        
    #Final DACclr pulse.
    waves["DACclr"] = waves["DACclr"] + [1,1,1]*time_scale_factor
    waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
    waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor

    #Fill in calc+Rst with all 1's, and mclk+bufsel with all 0's
    waves["calc"] = waves["calc"] + [1]*(len(waves["DACclr"])-len(waves["calc"]))
    waves["read_ext"] = waves["read_ext"] + [1]*(len(waves["DACclr"])-len(waves["calc"]))
    waves["Rst_ext"] = waves["Rst_ext"] + [1]*(len(waves["DACclr"])-len(waves["Rst_ext"]))
    waves["mclk"] = waves["mclk"] + [0]*(len(waves["DACclr"])-len(waves["mclk"]))
    waves["bufsel_ext"] = waves["bufsel_ext"] + [0]*(len(waves["DACclr"])-len(waves["bufsel_ext"]))


    ## PHI1_EXT SETUP.
    phi_phase_len = 10*tsf_sample_phase + sample_phase_stretch
    first_mclk_edge = waves["mclk"].index(1)

    #delay phi1_ext edges so they occur at the falling edge of mclk (rising edge of phi2)
    waves["phi1_ext"] = [0]*phi_phase_len + waves["mclk"]
    
    for i in range(first_mclk_edge-phi_phase_len,first_mclk_edge):
        waves["phi1_ext"][i] = 1
    
    #Option to delay phi1_ext relative to mclk. 
    if trig_delay > 0:
        waves["phi1_ext"] = [0]*(trig_delay) + waves["phi1_ext"]
    elif trig_delay < 0:
        for k in waves.keys():
            if k != "phi1_ext":
                waves[k] = [0]*abs(trig_delay) + waves[k]
    
    
    #TWEAKS TO HELP DEBUG 
    #waves["calc"] = waves["calc"][1:]

    return genpattern_from_waves_dict(waves)
    
def genpattern_Front_End_demo(time_scale_factor):

    waves = {}

    waves["mclk"] =       [0]*10
    waves["read_ext"] =   [0]*10 
    waves["Rst_ext"] =    [0]*10 
    waves["bufsel_ext"] = [0]*10 
    waves["capClk"] = [0]*10    #Note: capClk and Qequal are only needed for setting up the autorange threshold.
    waves["Qequal"] = [0]*10
    

    #Reset phase
    waves["mclk"] =       waves["mclk"]+[0]*40
    waves["read_ext"] =   waves["read_ext"] + [1]*5 + [0]*35
    waves["Rst_ext"] =    waves["Rst_ext"] + [1]*40
    waves["bufsel_ext"] = waves["bufsel_ext"] + [0]*20 + [1]*20
    waves["capClk"] = waves["capClk"] + [0,1,1,1,0,0,0,0,0,1,1,1,0] 
    waves["Qequal"] = waves["Qequal"] + [0,0,0,0,0,1,1,1,0,0,0,0,0,1,1,1,0]
    
    #Sampling Phase
    for i in range(10):
        #w/ time_scale_factor = 1, the period of mclk is 20 ticks or 2 MHz
        waves["mclk"] = waves["mclk"] + [1]*10*time_scale_factor + [0]*10*time_scale_factor

        waves["read_ext"] = waves["read_ext"] + [0]*20*time_scale_factor
        waves["Rst_ext"] = waves["Rst_ext"] + [0]*20*time_scale_factor
        waves["bufsel_ext"] = waves["bufsel_ext"] + [1]*20*time_scale_factor
        

    waves["mclk"] = waves["mclk"] + [0]*42
    waves["read_ext"] = waves["read_ext"] + [0,0] + [1]*40
    waves["bufsel_ext"] = waves["bufsel_ext"] + [0]*42
    waves["Rst_ext"] = waves["Rst_ext"] + [1]*42

    waves["phi1_ext"] = waves["mclk"][7:]  #phi1_ext will be used to trigger the AWG. It is a copy of mclk, shifted earlier by 175 ns (7 ticks)

    return genpattern_from_waves_dict(waves)


# Given a string of bits to write to the scan chain, generates a glue waveform that will write those bits.
def genpattern_SC_write(sc_bits, time_scale_factor=1):

    #1) Generating the waves based on sc_bits
    waves = {}

    waves["S_CLK"] = []
    waves["S_DIN"] = []
    waves["S_PASS"] = []

    for bit in sc_bits:
        waves["S_CLK"] = waves["S_CLK"] + [0]*time_scale_factor+[1]*time_scale_factor
        waves["S_PASS"] = waves["S_PASS"] + [0]*2*time_scale_factor
        if bit == 1:
            waves["S_DIN"] = waves["S_DIN"] + [1]*2*time_scale_factor
        else:
            waves["S_DIN"] = waves["S_DIN"] + [0]*2*time_scale_factor



    #Finally assert S_PASS and clock in the data.
    waves["S_CLK"] = waves["S_CLK"] + [0]*time_scale_factor+[1]*time_scale_factor
    waves["S_PASS"] = waves["S_PASS"] + [1]*2*time_scale_factor
    waves["S_DIN"] = waves["S_DIN"] + [0]*2*time_scale_factor

    #2) Writing to an ASCII file.
    with open("output\\genpattern_SC_write.txt",'w') as write_file:
        for w in waves.keys():
            write_file.write(w+":"+"".join([str(x) for x in waves[w]])+"\n")
            
    #3) Convert ASCII file to Glue.
    gc = GlueConverter(DEFAULT_IOSPEC)

    gc.ascii2Glue("output\\genpattern_SC_write.txt", 1, "genpattern_SC_write")


    return "genpattern_SC_write_se_io.glue"


####################################################

