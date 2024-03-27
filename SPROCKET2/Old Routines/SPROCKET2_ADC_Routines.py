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

from SPROCKET2_Subroutines import *

def onstartup():
    #sg.INSTR["Scope"].enable_channels([1,2,3,4])
    #sg.INSTR["Scope"].set_timebase(1e-6)
    #sg.INSTR["Scope"].set_scale(0.5)
    #sg.INSTR["Scope"].set_offset(1.5)
    #sg.INSTR["Scope"].set_scale(1,chan_num=1)
    #sg.INSTR["Scope"].set_offset(3,chan_num=1)
    pass



#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_Ramp_Histogram_vs_CapTrim():
    """Characterize ADC DNL using a ramp Histogram. Caplo->Spacely method"""

    VIN_STEP_uV = 10

    MIN_VIN_mV = 0
    
    MAX_VIN_mV = 1000

    VIN_RANGE = [i/1000 for i in range(1000*MIN_VIN_mV,1000*MAX_VIN_mV,VIN_STEP_uV)]
    
    VIN_RANGE.reverse() #Run reverse sweep.

    CAPTRIM_RANGE = [25,63] #[i for i in range(20,40,1)]

    CODE_RANGE = [i for i in range(0,1024)]
    
    sg.log.info(f"Commencing Ramp Histogram Characterization! Total # of points will be {(MAX_VIN_mV-MIN_VIN_mV)/VIN_STEP_uV*1000} x {len(CAPTRIM_RANGE)}...")

    #Set up AWG
    sg.INSTR["AWG"].config_AWG_as_DC(0)
    time.sleep(1)
    
    #Pre-generate patterns to run the ADC and to read from the scan chain.
    adc_op_glue = genpattern_ADC_Capture(10)

    result_values_by_captrim = []

    for captrim in CAPTRIM_RANGE:

        results = []
        
        #Set CapTrim value and ensure 
        SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=captrim)
        sg.pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
        
        time.sleep(1)

        for vin in VIN_RANGE:
                
            #Set the input voltage:
            sg.INSTR["AWG"].set_Vin_mV(vin)
                
            results.append(run_pattern_get_caplo_result(sg.pr, sg.gc, adc_op_glue))

            
        histo = liststring_histogram(" ".join([str(x) for x in results]))
    
        print(histo)
    
        with open(f"output\\SPROCKET2_Ramp_Histogram_CapTrim_{captrim}_Vin_{MIN_VIN_mV}_to_{MAX_VIN_mV}_mV_by_{VIN_STEP_uV}_on_"+time.strftime("%Y_%m_%d")+".csv","w") as write_file:
            write_file.write("Code,Count\n")

            for code in histo.keys():
                write_file.write(f"{code},{histo[code]}\n")

        result_values_by_captrim.append([])
        
        for i in CODE_RANGE:
            if i in histo.keys():
                result_values_by_captrim[-1].append(histo[i])
            else:
                result_values_by_captrim[-1].append(0)

    write_parameter_sweep_to_csv(CAPTRIM_RANGE,
                                 CODE_RANGE,
                                 result_values_by_captrim,
                                 f"Ramp_Histogram_vs_CapTrim_Vin_step_by_{VIN_STEP_uV}_uV_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")
    
def ROUTINE_Transfer_Function_vs_CapTrim():
    """Capture the ADC Transfer function vs CapTrim, using Caplo->Spacely method"""

    VIN_STEP_mV = 10

    VIN_RANGE = [i for i in range(0,1000,VIN_STEP_mV)]
    
    VIN_RANGE.reverse() #Try it backwards now y'all

    CAPTRIM_RANGE = [i for i in range(0,10,1)]

    #Set up pr, gc, and AWG
    pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)
    sg.INSTR["AWG"].config_AWG_as_DC(0)
    time.sleep(3)
    
    #Pre-generate patterns to run the ADC and to read from the scan chain.
    adc_op_glue = genpattern_ADC_Capture(10)

    result_values_by_captrim = []

    for captrim in CAPTRIM_RANGE:

        #Start a new list of result values for this captrim.
        result_values_by_captrim.append([])

        #Set CapTrim value and ensure 
        SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=captrim)
        pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
        time.sleep(0.5)

        for vin in VIN_RANGE:
                
            #Set the input voltage:
            sg.INSTR["AWG"].set_Vin_mV(vin)
                
            result = run_pattern_get_caplo_result(pr, gc, adc_op_glue)

            result_values_by_captrim[-1].append(result)


    print(result_values_by_captrim)

    write_parameter_sweep_to_csv(CAPTRIM_RANGE,
                                 VIN_RANGE,
                                 result_values_by_captrim,
                                 f"Transfer_Function_vs_CapTrim_Vin_step_by_{VIN_STEP_mV}_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")
    

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_Transfer_Function_vs_Vref():
    """Capture the ADC Transfer function for different Vref_adc voltages, using Caplo->Spacely method"""

    VIN_STEP_mV = 10

    VIN_RANGE = [i for i in range(0,1000,VIN_STEP_mV)]

    VREF_RANGE = [0.6, 0.8, 1.0, 1.2]

    #Set up pr, gc, and AWG
    pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)
    sg.INSTR["AWG"].config_AWG_as_DC(0)

    #Set CapTrim value = 0
    SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=0)
    pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
    
    time.sleep(3)
    
    #Pre-generate patterns to run the ADC and to read from the scan chain.
    adc_op_glue = genpattern_ADC_Capture(10)

    result_values_by_vref = []

    for vref in VREF_RANGE:

        #Start a new list of result values for this captrim.
        result_values_by_vref.append([])

        V_PORT["Vref_adc"].set_voltage(vref)

        for vin in VIN_RANGE:
                
            #Set the input voltage:
            sg.INSTR["AWG"].set_Vin_mV(vin)
                
            result = run_pattern_get_caplo_result(pr, gc, adc_op_glue)

            result_values_by_vref[-1].append(result)


    print(result_values_by_vref)

    write_parameter_sweep_to_csv(VREF_RANGE,
                                 VIN_RANGE,
                                 result_values_by_vref,
                                 f"Transfer_Function_vs_Vref_Vin_step_by_{VIN_STEP_mV}_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")


#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_Transfer_Function_vs_Timescale():
    """Capture the ADC Transfer function for different Time Scale Factors, using Caplo->Spacely method"""

    VIN_STEP_mV = 10

    VIN_RANGE = [i for i in range(0,1000,VIN_STEP_mV)]


    TIMESCALE_RANGE = [1,2,3,5,10] #,1,1,1,1,1,1,1,1,1,3,3,3,3,3,3,3,3,3,3]#[1,2,3,5,10,15,30,100]

    #Set up pr, gc, and AWG
    pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)
    sg.INSTR["AWG"].config_AWG_as_DC(0)

    #Set CapTrim value = 0
    SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=0)
    pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
    
    time.sleep(3)
    
    result_values = []

    for timescale in TIMESCALE_RANGE:

        #Pre-generate patterns to run the ADC and to read from the scan chain.
        adc_op_glue = genpattern_ADC_Capture(timescale, apply_pulse_1_fix=False, tsf_qequal = 1, tsf_pause=10)

        #Start a new list of result values for this captrim.
        result_values.append([])

        for vin in VIN_RANGE:
                
            #Set the input voltage:
            sg.INSTR["AWG"].set_Vin_mV(vin)
                
            result = run_pattern_get_caplo_result(pr, gc, adc_op_glue)

            result_values[-1].append(result)


    print(result_values)

    write_parameter_sweep_to_csv(TIMESCALE_RANGE,
                                 VIN_RANGE,
                                 result_values,
                                 f"Transfer_Function_vs_Timescale_Vin_step_by_{VIN_STEP_mV}_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")



#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_Transfer_Function_vs_ArbParam():
    """Capture the ADC Transfer function for different values of ~Arb Param~, using Caplo->Spacely method"""



    VIN_STEP_mV = 1

    VIN_RANGE = [i for i in range(0,15,VIN_STEP_mV)]


    PARAM_NAME = "post_SC_delay"

    PARAM_RANGE = [0.1,1,2,3]

    GET_MAX_INL = False

    INL_START_VIN = 0
    

    INL_END_VIN = 950
    

    #Set up pr, gc, and AWG
    pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)
    sg.INSTR["AWG"].config_AWG_as_DC(0)

    #Set CapTrim value = 0
    SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=15)
    pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
    
    time.sleep(3)
    
    result_values = []
    INL_values = []

    for param in PARAM_RANGE:

        #Pre-generate patterns to run the ADC and to read from the scadn chain.
        adc_op_glue = genpattern_ADC_Capture(10)

        adc_op_wave = gc.read_glue(adc_op_glue)

        #Start a new list of result values for this ArbParam setting.
        result_values.append([])
        INL_values.append([])

        #INL start and end code always start out as zero for each param.
        INL_START_CODE = 0
        INL_END_CODE =  0

        for vin in VIN_RANGE:
        
            #!!!! MODIFIED !!!! WRITE SCAN CHAIN BEFORE EVERY VIN. WORST CASE!
            #Set CapTrim value = 0
            SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=15)
            pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
            
            if param > 0:
                time.sleep(param)
                
            #Set the input voltage:
            sg.INSTR["AWG"].set_Vin_mV(vin)
                
            result = run_pattern_get_caplo_result(pr, gc, adc_op_wave)

            result_values[-1].append(result)

        if GET_MAX_INL == True:
            #Capture INL and maximum INL
            for i in range(len(VIN_RANGE)):
                if INL_START_CODE == 0 and VIN_RANGE[i] >= INL_START_VIN:
                    INL_START_CODE = result_values[-1][i]
                    INL_START_IDX = i

                if INL_END_CODE == 0 and VIN_RANGE[i] >= INL_END_VIN:
                    INL_END_CODE = result_values[-1][i]
                    INL_END_IDX = i

            for i in range(len(VIN_RANGE)):
                # y = mx + b
                nominal_value = ((INL_END_CODE-INL_START_CODE)/(INL_END_VIN-INL_START_VIN))*(VIN_RANGE[i]-INL_START_VIN) + INL_START_CODE
                INL_values[-1].append(result_values[-1][i]-nominal_value)


    print(result_values)

    if GET_MAX_INL == True:
        print("ParamVal,MaxINL")
        for i in range(len(INL_values)):
            maxinl = max([abs(n) for n in INL_values[i][INL_START_IDX:INL_END_IDX]])
            print(f"{PARAM_RANGE[i]},{maxinl}")

    write_parameter_sweep_to_csv(PARAM_RANGE,
                                 VIN_RANGE,
                                 result_values,
                                 f"Transfer_Function_vs_Arb_Param_{PARAM_NAME}_Vin_step_by_{VIN_STEP_mV}_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")
    if GET_MAX_INL == True:
        write_parameter_sweep_to_csv(PARAM_RANGE,
                                 VIN_RANGE,
                                 INL_values,
                                 f"Transfer_Function_INL_vs_Arb_Param_{PARAM_NAME}_Vin_step_by_{VIN_STEP_mV}_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")
                                 
                                 
                                 
#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_Transfer_Function_over_Time():
    """Sample the ADC Transfer Function over a period of time, using Caplo->Spacely method"""

    VIN_STEP_mV = 1

    VIN_RANGE = [i for i in range(0,1000,VIN_STEP_mV)]

    SAMPLE_INTERVAL_MINUTES = 10

    initial_date_string = time.strftime("%Y_%m_%d")

    #Set up pr, gc, and AWG
    pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)
    sg.INSTR["AWG"].config_AWG_as_DC(0)

    #Set CapTrim value = 0
    SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=0)
    pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
    
    #Pre-generate patterns to run the ADC and to read from the scan chain.
    adc_op_glue = genpattern_ADC_Capture(10)
    
    time.sleep(3)
    
    result_values = []
    time_samples  = []
    
    time_elapsed = 0

    while True:

        

        #Start a new list of result values for this sample.
        result_values.append([])
        time_samples.append(time_elapsed)

        for vin in VIN_RANGE:
                
            #Set the input voltage:
            sg.INSTR["AWG"].set_Vin_mV(vin)
                
            result = run_pattern_get_caplo_result(pr, gc, adc_op_glue)

            result_values[-1].append(result)


    

        write_parameter_sweep_to_csv(time_samples,
                                    VIN_RANGE,
                                    result_values,
                                    f"Transfer_Function_sampled_every_{SAMPLE_INTERVAL_MINUTES}_mins_Vin_step_by_{VIN_STEP_mV}_on_"+initial_date_string+".csv",
                                    row_param_name="Vin")
         
         
        print(f"SLEEPING for {SAMPLE_INTERVAL_MINUTES*60} seconds...")
        time.sleep(SAMPLE_INTERVAL_MINUTES*60)
        time_elapsed = time_elapsed + SAMPLE_INTERVAL_MINUTES


#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_average_transfer_function():
    """Capture the Average ADC Transfer function using Caplo->Spacely method"""

    VIN_STEP_uV = 100

    NUM_AVERAGES = 10
    
    VIN_RANGE = [i/1000 for i in range(0,1000000,VIN_STEP_uV)]
    
    VIN_RANGE.reverse()

    #Set up pr, gc, and AWG
    #pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    #gc = GlueConverter(DEFAULT_IOSPEC)
    sg.INSTR["AWG"].config_AWG_as_DC(0)
    
    #Set CapTrim value and ensure 
    SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=25)
    sg.pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
    
    time.sleep(3)
    
    #Pre-generate patterns to run the ADC and to read from the scan chain.
    adc_op_glue = genpattern_ADC_Capture(10)

    write_file = open(f"output\\Average_Transfer_Function_Vin_step_by_{VIN_STEP_uV}_uV_on_"+time.strftime("%Y_%m_%d")+".csv","w")

    write_file.write("Vin,Avg Result,Std Dev\n")


    for vin in VIN_RANGE:
                
        #Set the input voltage:
        sg.INSTR["AWG"].set_Vin_mV(vin)

        results_this_vin = []

        for i in range(NUM_AVERAGES):
            #Run the ADC to capture a reading.
            adc_op_result = sg.pr.run_pattern(adc_op_glue,outfile_tag="adc_op_result")[0]
            #"adc_op_result_PXI1Slot4_NI6583_se_io.glue"

            #Get DACclr and capLo
            dacclr_wave = sg.gc.get_bitstream(sg.gc.read_glue(adc_op_result),"DACclr")
            caplo_wave = sg.gc.get_bitstream(sg.gc.read_glue(adc_op_result),"capLo_ext")

            result = interpret_CDAC_pattern_edges(caplo_wave, dacclr_wave)

            results_this_vin.append(result)

        write_file.write(f"{vin},{np.mean(results_this_vin)},{np.std(results_this_vin)}\n")



#<<Registered w/ Spacely as ROUTINE 18, call as ~r18>>
def ROUTINE_Noise_Histogram():
    """Generate a noise histogram for the ADC"""

    VTEST_mV = 100

    HISTOGRAM_SAMPLES = 100000

    CENTER_CODE_SAMPLES = 2000

    #Set up pr, gc, and AWG
    pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)
    sg.INSTR["AWG"].config_AWG_as_DC(0)

    #Set CapTrim value = 0
    SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=0, CapTrim=0)
    pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
    
    time.sleep(3)
    
    #Pre-generate patterns to run the ADC and to read from the scan chain.
    pattern_glue = genpattern_ADC_Capture(10)
    
    histo = SP2_Vin_histogram(pr,gc,pattern_glue, SP2_center_code(pr,gc,pattern_glue,VTEST_mV, samples_per_val=CENTER_CODE_SAMPLES), HISTOGRAM_SAMPLES)


    print(histo)
    
    with open("output\\SPROCKET2_Noise_Histogram_100mV_on_"+time.strftime("%Y_%m_%d")+".csv","w") as write_file:
        write_file.write("Code,Count\n")

        for code in histo.keys():
            write_file.write(f"{code},{histo[code]}\n")




def SP2_Vin_histogram(pr, gc, pattern_glue, Vtest_mV: int, points: int) -> dict[int, int]:
    """
    Sets Vin and takes a specified number of points, returning a histogram of the resulting output codes.

    :param Vtest_mV: Voltage to test at in milli-volts
    :param points: Number of samples to take
    :return: See "liststring_histogram()" docblock
    """

    sg.INSTR["AWG"].set_Vin_mV(Vtest_mV)

    results = []

    for i in range(points):
        results.append(run_pattern_get_caplo_result(pr, gc, pattern_glue))

    return liststring_histogram(" ".join([str(x) for x in results]))


def SP2_center_code(pr, gc, pattern_glue, Vtest_init_mV: float, samples_per_val: int = 1000):


    Vtest = Vtest_init_mV
    Vtest_last = Vtest_init_mV

    count_outside = 1000

    sg.log.info(f"Running centering code from {Vtest_init_mV}mV...")

    while True:
        histogram = SP2_Vin_histogram(pr, gc, pattern_glue, Vtest, samples_per_val)
        mode = max(histogram, key=histogram.get) # primary bin count/statistical mode of all values in histogram
        #print(histogram)

        count_below = 0
        count_above = 0
        for bin_val, bin_count in histogram.items():
            if bin_val > mode:
                count_above += bin_count
            elif mode < bin_val:
                count_below += bin_count

        sg.log.debug(f"Vtest:{Vtest:.2f}mV, mode:{mode}, count_below_mode:{count_below}, count_above_mode:{count_above}")

        # That shouldn't be the case really... something is probably misconnected
        if mode == 0:
            sg.log.warning(f"Suspicious mode of 0 for Vtest={Vtest:.2f}mV")

        #If we are less centered than the previous guess, take the
        #last one and be done with it.
        #PROOF that this loop is non-infinite: count_outside is strictly decreasing and positive.
        if count_above + count_below >= count_outside:
            sg.log.notice(f"Centered at Vtest: {Vtest_last:.2f}mV")
            return Vtest_last

        #If not, that is if this was an improvement, try again.
        Vtest_last = Vtest
        count_outside = count_above + count_below

        #Tune by increments of 0.1 mV.
        if count_above > count_below:
            Vtest = Vtest - 0.1
        else:
            Vtest = Vtest + 0.1



#Run an ADC acquisition pattern w/ a given PatternRunner and use a GlueConverter to read/interpret the result.
def run_pattern_get_caplo_result(pattern_glue):
    #Run the ADC to capture a reading.
    adc_op_result = sg.pr.run_pattern(pattern_glue,outfile_tag="adc_op_result")[0]
    #"adc_op_result_PXI1Slot16_NI6583_se_io.glue"

    #Get DACclr and capLo
    result_wave = sg.gc.read_glue(adc_op_result)
    dacclr_wave = sg.gc.get_bitstream(result_wave,"DACclr")
    caplo_wave = sg.gc.get_bitstream(result_wave,"capLo_ext")

    result = interpret_CDAC_pattern_edges(caplo_wave, dacclr_wave)
    
    return result