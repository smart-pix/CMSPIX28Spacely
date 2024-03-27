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

#from spacely-asic-config.SPROCKET2.SPROCKET2_Subroutines import *

def onstartup():
    #sg.INSTR["Scope"].enable_channels([1,2,3,4])
    #sg.INSTR["Scope"].set_timebase(1e-6)
    #sg.INSTR["Scope"].set_scale(0.5)
    #sg.INSTR["Scope"].set_offset(1.5)
    #sg.INSTR["Scope"].set_scale(1,chan_num=1)
    #sg.INSTR["Scope"].set_offset(3,chan_num=1)
    pass


def _ROUTINE_df_arithmetic_lint():
    """Check correctness of df_arithmetic functions"""
    

    # Instantiate the Analysis class
    analysis = Analysis()

    # Sample data
    data = {
        'X_values': [1, 2, 3, 4, 5],
        'Y_values': [2, 3, 5, 7, 11],
        'Values': [1,  2,  3,  4],
        'Frequencies': [1, 3, 2, 1]
    }

    # Load sample data into analysis object
    analysis.load_dict(data, name='Sample')

    # Test freq_avg
    print("Frequency Average:", analysis.freq_avg('Values', 'Frequencies', source='Sample'))
    print("Expected Value: 2.429 (hand calc)")

    # Test freq_stddev
    print("Frequency Standard Deviation:", analysis.freq_stddev('Values','Frequencies', source='Sample'))
    print("Expected Value: 0.9759 (calculator.net)")

    # Test plot_scatter
    try:
        analysis.plot_scatter('X_values', 'Y_values', source='Sample')
    except ValueError as e:
        print("Error:", e)

    # Test plot_histogram
    analysis.plot_histogram('Values', 'Frequencies', source='Sample')



# BASIC ROUTINE for a one-shot demo.
#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_Full_Conversion(pulse_mag = None):
    """Demo of a full conversion, all the way from preamplifier through the ADC."""

    #NOTES:
    # - Trigger must be supplied from NI, pre-level-shifters. 

    e = Experiment("Demo")

    df = e.new_data_file("Demo")

    print("NOTE: ENSURE THAT AWG TRIG IS CONNECTED to phi1_ext (silk as 'P1.0') on the NI side.")
    
    if pulse_mag is not None:
        pm = int(input("pulse magnitude (mV)?"))  

    df.set("time_scale_factor",10)
    df.set("tsf_sample_phase", 2)
    
    fc_glue = setup_full_conversion(df)

    if fc_glue == -1:
        return
   
    # When tsf=1, pulses are 250 nanoseconds (0.25 us) wide because mclk's frequency is 2 MHz (T=500ns).
    #sg.INSTR["AWG"].config_AWG_as_Pulse(pm, pulse_width_us=0.25*tsf_sample_phase, pulse_period_us=0.25*tsf_sample_phase+0.05)
    #time.sleep(3)

    #if use_scope:
    #    sg.INSTR["Scope"].setup_trigger(1,0.6)

    ##Set CapTrim value and ensure TestEn=0
    #SC_PATTERN = SC_CFG(override=0,TestEn=0,Range2=0, CapTrim=0)
    #sg.pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")

    #fc_glue = genpattern_Full_Conversion(time_scale_factor, tsf_sample_phase,n_samp=1, tsf_reset=2)

    #fc_result = sg.pr.run_pattern(fc_glue,outfile_tag="fc_result")[0]

    #"fc_result_PXI1Slot16_NI6583_se_io.glue"

    #Get DACclr and capLo
    #if use_scope:
    #    halt_sample_wave = sg.INSTR["Scope"].get_wave(2)
    #result_glue = gc.read_glue(fc_result)
    #dacclr_wave = gc.get_bitstream(result_glue,"DACclr")
    #caplo_wave = gc.get_bitstream(result_glue,"capLo_ext")

    result = get_full_conversion_result(fc_glue, pm, df)

    print(f"RESULT: {result}")

# BASIC ROUTINE for capturing Sweeps. 
#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_Full_Conversion_Sweep(experiment=None, data_file=None):
    """FULL SWEEP of full conversion, all the way from preamplifier through the ADC."""
    
    if experiment is None: #Interactive mode
    
        custom_name = input("Custom Exp name?")
    
        e = Experiment(custom_name)    
    
        e.set("VIN_STEP_uV",50000)
        e.set("VIN_STEP_MAX_mV",1000)
        e.set("VIN_STEP_MIN_mV",5)
    
        #NOTES:
        # - Trigger must be supplied from NI, pre-level-shifters. 

        input("""NOTE: PLEASE CONFIRM THAT
        1) AWG TRIG IS CONNECTED to phi1_ext (silk as 'P1.0') on the NI side.
        2) Scope Ch1 is also connected to P1.0
        3) Scope Ch2 is also connected to halt_sample (silk as 'Charge')""")
    
        #Set default values for the whole experiment.    
        e.set("time_scale_factor",10)
        e.set("tsf_sample_phase",2)
        
        e.set("Range2",0)       
        
        e.set("CapTrim",25)
        
        e.set("n_skip",1)
        e.set("SINGLE_PULSE_MODE",True)
        
    else:
        e = experiment
        
    if data_file is None:    
        df_name = f'FullConv_Sweep_on_'+time.strftime("%Y_%m_%d")
        
        df = e.new_data_file(df_name)
    else:
        df = data_file
        
           
    #############################################################################
    
    if not df.check(["SINGLE_PULSE_MODE","tsf_sample_phase","Range2","CapTrim","n_skip","VIN_STEP_uV","VIN_STEP_MAX_mV","VIN_STEP_MIN_mV"]):
        return -1
    
    df.set("check_halt_sample", False) 
    
    VIN_STEP_uV = df.get("VIN_STEP_uV")
    
    VIN_STEP_MAX_mV = df.get("VIN_STEP_MAX_mV")
    
    VIN_STEP_MIN_mV = df.get("VIN_STEP_MIN_mV") # Cannot be < 2 mV
    
    PULSE_MAG_RANGE = [i/1000 for i in range(1000*VIN_STEP_MIN_mV,1000*VIN_STEP_MAX_mV,VIN_STEP_uV)]
    
    fc_glue = setup_full_conversion(df)

    #write_file = open("output\\Full_Conversion_Sweep_on_"+time.strftime("%Y_%m_%d")+".csv","w")
    df.write("Vin,Result,halt_sample\n")
    
    for pulse_mag in PULSE_MAG_RANGE:
    
        if check_halt_sample:
            (result, halt_sample) = get_full_conversion_result(fc_glue, pulse_mag, df)
            print(f"RESULT: {result} (halt_sample={halt_sample})")
            df.write(f"{pulse_mag},{result},{halt_sample}\n")

        else:
            result = get_full_conversion_result(fc_glue, pulse_mag, df)
            print(f"RESULT: {result}")
            df.write(f"{pulse_mag},{result}\n")


    df.close()


# BASIC ROUTINE for capturing Histograms.
#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_Full_Conversion_Histogram(experiment = None, data_file=None):   
    """Create a histogram of the results from a Full Conversion """
    
    
    if experiment is None: #Interactive mode
    
        custom_name = input("Custom Exp name?")
    
        e = Experiment(custom_name)    
    
        e.set("VIN_mV",float(input("Vin_mV?")))
    
        #NOTES:
        # - Trigger must be supplied from NI, pre-level-shifters. 

        input("""NOTE: PLEASE CONFIRM THAT
        1) AWG TRIG IS CONNECTED to phi1_ext (silk as 'P1.0') on the NI side.
        2) Scope Ch1 is also connected to P1.0
        3) Scope Ch2 is also connected to halt_sample (silk as 'Charge')""")
    
        #Set default values for the whole experiment.    
        e.set("time_scale_factor",10)
        e.set("tsf_sample_phase",2)
        e.set("Range2",0)       
        e.set("NUM_SAMPLES",10000)
        
        e.set("CapTrim",25)
        
        e.set("n_skip",1)
        e.set("SINGLE_PULSE_MODE",True)
        
    else:
        e = experiment
        
    if data_file is None:    
        df_name = f'FullConv_Noise_Histogram_{e.get("VIN_mV")}mV_on_'+time.strftime("%Y_%m_%d")
        
        df = e.new_data_file(df_name)
    else:
        df = data_file
    
    # (1) CONFIGURE THE TEST SETUP ############################################################################
    
    df.set("check_halt_sample",False)
    
    if not df.check(["SINGLE_PULSE_MODE","tsf_sample_phase","Range2","CapTrim","n_skip","NUM_SAMPLES"]):
        return
    
    fc_glue = setup_full_conversion(df)

    #Set the input voltage:
    sg.INSTR["AWG"].set_pulse_mag(df.get("VIN_mV"))
    
    results = []
    
    for _ in range(df.get("NUM_SAMPLES")):
    
        (result, halt_sample) = get_full_conversion_result(fc_glue, None, df)

        results.append(result)

        if df.get("check_halt_sample"):
            print(f"RESULT: {result} (halt_sample={halt_sample})")
        else:
            print(f"RESULT: {result} (no_scope)")
    
    
    #Process results
    histo = liststring_histogram(" ".join([str(x) for x in results]))
    
    print(histo)
    
    df.write("Code,Count\n")
    
    for code in histo.keys():
        df.write(f"{code},{histo[code]}\n")      
            
    print(f'NOTE: NUM_SAMPLES={df.get("NUM_SAMPLES")} and len(results)={len(results)}, {df.get("NUM_SAMPLES")-len(results)} points were discarded b/c halt_sample=1')
    mean = np.mean(results)
    stddev = np.std(results)
    print(f"MEAN: {mean} STANDARD DEVIATION: {stddev} codes")
    
    return (mean, stddev)
    


# BASIC ROUTINE for capturing average transfer functions
#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_FC_Avg_XF(experiment=None, data_file=None):
    """Capture the Average FullConv Transfer function"""

    if experiment is None: #Interactive mode
    
        custom_name = input("Custom Exp name?")
    
        e = Experiment(custom_name)    
    
        e.set("VIN_STEP_uV",1000)
        e.set("VIN_STEP_MAX_mV",1000)
        e.set("VIN_STEP_MIN_mV",5)
        
        e.set("NUM_AVERAGES",20)
    
        #NOTES:
        # - Trigger must be supplied from NI, pre-level-shifters. 

        input("""NOTE: PLEASE CONFIRM THAT
        1) AWG TRIG IS CONNECTED to phi1_ext (silk as 'P1.0') on the NI side.
        2) Scope Ch1 is also connected to P1.0
        3) Scope Ch2 is also connected to halt_sample (silk as 'Charge')""")
    
        #Set default values for the whole experiment.    
        e.set("time_scale_factor",10)
        e.set("tsf_sample_phase",2)
        
        e.set("Range2",0)       
        
        e.set("CapTrim",25)
        
        e.set("n_skip",1)
        e.set("SINGLE_PULSE_MODE",True)
        
    else:
        e = experiment
        
    if data_file is None:    
        df_name = f'FullConv_Noise_Histogram_{e.get("VIN_mV")}mV_on_'+time.strftime("%Y_%m_%d")
        
        df = e.new_data_file(df_name)
    else:
        df = data_file
        
           
    #############################################################################
    
    if not df.check(["SINGLE_PULSE_MODE","tsf_sample_phase","Range2","CapTrim","n_skip","VIN_STEP_uV","VIN_STEP_MAX_mV","VIN_STEP_MIN_mV", "USE_SCOPE"]):
        return -1
    
    df.set("check_halt_sample",False)

    VIN_STEP_uV = df.get("VIN_STEP_uV")

    NUM_AVERAGES = df.get("NUM_AVERAGES")
    
    VIN_MIN_mV = df.get("VIN_STEP_MIN_mV")
    
    VIN_MAX_mV = df.get("VIN_STEP_MAX_mV")
    
    VIN_RANGE = [i/1000 for i in range(int(1000*VIN_MIN_mV),int(1000*VIN_MAX_mV),VIN_STEP_uV)]

    SINGLE_PULSE_MODE = df.get("SINGLE_PULSE_MODE")
    
    fc_glue = setup_full_conversion(df)
    

    if not SINGLE_PULSE_MODE:
        df.write("Vin,Avg Result,Std Dev,Avg Halt_Sample\n")
    else:
        df.write("Vin,Avg Result, Std Dev\n")


    for vin in VIN_RANGE:
                
        #Set the input voltage:
        sg.INSTR["AWG"].set_pulse_mag(vin)

        results_this_vin = []
        hs_this_vin = []

        for i in range(NUM_AVERAGES):
        
            
            #Pass 'None' for pulse_mag because we DON'T want to set it each time, only once at the beginning.
            result = get_full_conversion_result(fc_glue, None, df)


            if df.get("check_halt_sample"):
                hs_this_vin.append(halt_sample)

            results_this_vin.append(result)
            
        
        if df.get("check_halt_sample"):
            df.write(f"{vin},{np.mean(results_this_vin)},{np.std(results_this_vin)},{np.mean(hs_this_vin)}\n")
        else:
            df.write(f"{vin},{np.mean(results_this_vin)},{np.std(results_this_vin)}\n")

            
            
    df.close()



### CAUTION!!! This routine does not follow the new format, it may have legacy bugs.    
#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_Full_Conversion_vs_ArbParam():
    """Perform a single conversion while varying a parameter."""

    ARB_PARAM_NAME = ""
    
    VIN_mV = 75
    
    ARB_PARAM_RANGE = [i for i in range(0,10000000,100000)]
    
    #NOTES:
    # - Trigger must be supplied from NI, pre-level-shifters. 

    input("""NOTE: PLEASE CONFIRM THAT
    1) AWG TRIG IS CONNECTED to phi1_ext (silk as 'P1.0') on the NI side.
    2) Scope Ch1 is also connected to P1.0
    3) Scope Ch2 is also connected to halt_sample (silk as 'Charge')""")
    
    time_scale_factor = 10
    tsf_sample_phase = 2
    
    
    # When tsf=1, pulses are 250 nanoseconds (0.25 us) wide because mclk's frequency is 2 MHz (T=500ns).
    sg.INSTR["AWG"].config_AWG_as_Pulse(VIN_mV, pulse_width_us=0.25*tsf_sample_phase, pulse_period_us=0.25*tsf_sample_phase+0.05)
    #time.sleep(3)

    #Set CapTrim value and ensure TestEn=0
    SC_PATTERN = SC_CFG(override=0,TestEn=0,Range2=0, CapTrim=25)
    sg.pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")

    


    write_file = open(f"output\\Full_Conversion_Sweep_vs_{ARB_PARAM_NAME}_with_Vin_{VIN_mV}_mV_on_"+time.strftime("%Y_%m_%d")+".csv","w")
    write_file.write(f"{ARB_PARAM_NAME},Output Code,halt_sample\n")
    
    for param in ARB_PARAM_RANGE:
    
        fc_glue = genpattern_Full_Conversion(time_scale_factor=time_scale_factor,tsf_sample_phase=tsf_sample_phase, StoC_Delay=param)
    
        sg.INSTR["Scope"].setup_trigger(1,0.6)
    
        sg.INSTR["AWG"].set_pulse_mag(VIN_mV)

        fc_result = sg.pr.run_pattern(fc_glue,outfile_tag="fc_result")[0]
        
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

        print(f"RESULT: {result} (halt_sample={halt_sample})")
        write_file.write(f"{param},{result},{halt_sample}\n")


    write_file.close()
    
#Independent Routine, does not do full conversions.
#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_Vref_Loopback_Experiment():
    """Use the TPI as a buffer to loop back Vref_fe to the ADC for measurement."""
    
    
    input("Ensure that Scope-Ch1 is set to phi1_ext/P1.0, and Scope-Ch4 is set to TestEn")
    
    e = Experiment("Vreffe_Loopback_Experiment")
    
    e.set("time_scale_factor",10000)
    e.set("CapTrim",25)
    e.set("Range2",0)
    
    e.set("NUM_AVERAGES",1)
    e.set("VIN_STEP_uV",25000)
    e.set("VIN_STEP_MIN_mV",400)
    e.set("VIN_STEP_MAX_mV",1000)
    
    #Set TestEn=1, etcetera.
    SC_PATTERN = SC_CFG(override=0,TestEn=1,Range2=e.get("Range2"), CapTrim=e.get("CapTrim"))
    sg.pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")
    
    #Pre-generate a pattern which will output Vrefbuf, and do a rising edge of phi1_ext.
    op_glue = genpattern_Vref_Loopback(e.get("time_scale_factor"))
    
    VREF_RANGE = [i/1000 for i in range(1000*e.get("VIN_STEP_MIN_mV"),1000*e.get("VIN_STEP_MAX_mV"),e.get("VIN_STEP_uV"))]
    
    VREF_RANGE.reverse()
    
    df = e.new_data_file(f"Vref_fe_Loopback_XF")
    
    df.write("Vref,Mean,Stddev,Min,Max\n")
    
    sg.INSTR["Scope"].enable_channels([1,2,3,4])
    sg.INSTR["Scope"].set_scale(0.5,chan_num=4)
    sg.INSTR["Scope"].set_offset(1.5,chan_num=4)
    sg.INSTR["Scope"].set_timebase(1)
    sg.INSTR["Scope"].io.set_timeout(15000)
    
    for vref in VREF_RANGE:
        
        sg.log.notice(f"Setting Vref_fe to {vref}")
        V_PORT["Vref_fe"].set_voltage(vref/1000)
        
        
        results_this_vin = []

        for i in range(e.get("NUM_AVERAGES")):
            #Set up the scope to trigger on a rising edge of phi1_ext
            sg.INSTR["Scope"].setup_trigger(1,0.6)
            
            print("SLEEPING...")
            time.sleep(15)
            
            sg.pr.run_pattern(op_glue)
            
            print("SLEEPING...")
            time.sleep(10)

            Vrefbuf = sg.INSTR["Scope"].get_wave(4)
            print(np.mean(Vrefbuf),np.std(Vrefbuf))
            #Get DACclr and capLo
            #sg.INSTR["Scope"].onscreen()
            
            

        #df.write(f"{vref},{np.mean(results_this_vin)},{np.std(results_this_vin)},{min(results_this_vin)},{max(results_this_vin)}\n")
        
    #df.close()
    
# Calls ROUTINE_FC_Avg_XF
#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_Sweep_vs_Vreffe_Experiment():
    """Run a Full Conversion Sweep for different values of Vref_fe"""
    
    e = Experiment("Sweep_vs_Vreffe_Experiment_1_26_2024")
    
    #Defaults (same for all data files)
    e.set("time_scale_factor",10)
    e.set("tsf_sample_phase",2)
    e.set("CapTrim",25)
    e.set("SINGLE_PULSE_MODE",True)
    e.set("n_skip",1)
    
    e.set("NUM_AVERAGES",20)
    e.set("VIN_STEP_uV",5000)
    e.set("VIN_STEP_MIN_mV",5)
    e.set("VIN_STEP_MAX_mV",1000)
    
    Vref_fe_range = [x/1000 for x in range(400,1000,25)]
    
    for Range2 in [0,1]:
        for Vref_fe in Vref_fe_range:
            
            df = e.new_data_file(f'data,r2={Range2},Vref_fe={Vref_fe*1000}mV')
            df.set("Range2",Range2)
        
            if Range2 == 0:
                df.set("VIN_STEP_uV",5000)
                df.set("VIN_STEP_MIN_mV",5)
                df.set("VIN_STEP_MAX_mV",1000)
            else:
                df.set("VIN_STEP_uV",1000)
                df.set("VIN_STEP_MIN_mV",5)
                df.set("VIN_STEP_MAX_mV",100)
        
            #Set Vref_fe voltage to a different value for each data file.
            sg.log.notice(f"Setting Vref_fe={Vref_fe}")
            V_PORT["Vref_fe"].set_voltage(Vref_fe)
            time.sleep(0.1)

            #Run full conversion sweep
            result = ROUTINE_FC_Avg_XF(e,df)
            
            if result == -1: #Abort on abnormal return status
                return
        
 
# Calls ROUTINE_FC_Avg_XF
#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_Sweep_vs_trigdelay_Experiment():
    """Run a Full Conversion Sweep for different values of trig_delay"""
    
    e = Experiment("Sweep_vs_trigdelay_Experiment")
    
    #Defaults (same for all data files)
    e.set("time_scale_factor",10)
    e.set("tsf_sample_phase",2)
    e.set("CapTrim",25)
    e.set("SINGLE_PULSE_MODE",True)
    e.set("n_skip",1)
    
    e.set("NUM_AVERAGES",1)
    
    trig_delay_range = [x for x in range(0,10)]
    
    for Range2 in [0,1]:
        for trig_delay in trig_delay_range:
            
            df = e.new_data_file(f'data,r2={Range2},trig_delay={trig_delay*1000}mV')
            df.set("Range2",Range2)
            df.set("trig_delay",trig_delay)
        
            if Range2 == 0:
                df.set("VIN_STEP_uV",50000)
                df.set("VIN_STEP_MIN_mV",5)
                df.set("VIN_STEP_MAX_mV",1000)
            else:
                df.set("VIN_STEP_uV",10000)
                df.set("VIN_STEP_MIN_mV",5)
                df.set("VIN_STEP_MAX_mV",100)
        
            #Set Vref_fe voltage to a different value for each data file.
            #sg.log.notice(f"Setting Vref_fe={Vref_fe}")
            #V_PORT["Vref_fe"].set_voltage(Vref_fe)
            #time.sleep(0.1)

            #Run full conversion sweep
            result = ROUTINE_FC_Avg_XF(e,df)
            
            if result == -1: #Abort on abnormal return status
                return 
    
    
def _ROUTINE_Nskip_Noise_Experiment():
    """Evaluate noise variation vs Nskip and Range2"""
    
    e = Experiment("Nskip_Noise_Experiment")
    
    e.set("VIN_mV",40)
    
    e.set("time_scale_factor",10)
    e.set("tsf_sample_phase",2)      
    e.set("NUM_SAMPLES",1000)
    e.set("CapTrim",25)
    
    summary_file = e.new_data_file(f'Summary_VIN_mV={e.get("VIN_mV")}')
    summary_file.write("Range2,n_skip,mean,stddev\n")
    
    for Range2 in [0]:
        for n_skip in range(1,11):
                
            df = e.new_data_file(f'VIN_mV={e.get("VIN_mV")}Range2={Range2},n_skip={n_skip}')
        
            if n_skip == 1:
                df.set("SINGLE_PULSE_MODE",True)
            else:
                df.set("SINGLE_PULSE_MODE",False)
                
            df.set("Range2",Range2)
            df.set("n_skip",n_skip)
            
            (mean,stddev) = ROUTINE_Full_Conversion_Histogram(e,df)
            
            summary_file.write(f"{Range2},{n_skip},{mean},{stddev}\n")
            
            df.close()
            
    summary_file.close()
  
# Calls ROUTINE_Full_Conversion_Histogram
#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_FC_Histo_4quad():

    unstick_VDD_ASIC()

    e = Experiment("FullConv_Histogram_RT_Feb08")
    
    e.set("time_scale_factor",10)
    e.set("tsf_sample_phase",2)
    e.set("NUM_SAMPLES",10000)
    e.set("CapTrim",25)
    
    #Region0
    df0 = e.new_data_file("Region0_FC_Histo")
    df0.set("VIN_mV",4)
    df0.set("Range2",1)
    df0.set("n_skip",10)
    df0.set("SINGLE_PULSE_MODE",False)
    ROUTINE_Full_Conversion_Histogram(e,df0)
    
    #Region1
    df1 = e.new_data_file("Region1_FC_Histo")
    df1.set("VIN_mV",40)
    df1.set("Range2",1)
    df1.set("n_skip",1)
    df1.set("SINGLE_PULSE_MODE",True)
    ROUTINE_Full_Conversion_Histogram(e,df1)
    
    #Region2
    df2 = e.new_data_file("Region2_FC_Histo")
    df2.set("VIN_mV",40)
    df2.set("Range2",0)
    df2.set("n_skip",10)
    df2.set("SINGLE_PULSE_MODE",False)
    ROUTINE_Full_Conversion_Histogram(e,df2)
    
    #Region3
    df3 = e.new_data_file("Region3_FC_Histo")
    df3.set("VIN_mV",400)
    df3.set("Range2",0)
    df3.set("n_skip",1)
    df3.set("SINGLE_PULSE_MODE",True)
    ROUTINE_Full_Conversion_Histogram(e,df3)
    
 
# Calls ROUTINE_FC_Avg_XF
#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_FE_Bias_Sweep_Exp2():
    """Execute FC Avg XF while sweeping FE Bias Currents"""
    
    sweeps = {}
    sweeps["Ib1"] = [-30e-6,-40e-6,-50e-6,-60e-6,-100e-6]
    sweeps["Ib2"] = [-5e-6,-8e-6,-10e-6,-12e-6,-20e-6]
    sweeps["Ibuf"] = [-30e-6, -50e-6, -60e-6, -70e-6,-120e-6]
    sweeps["Icomp"] = [-10e-6,-18e-6, -20e-6,-22e-6,-40e-6]
    
    
    e = Experiment("Bias_Sweep_Experiment_3_27_2024")
    
    #This experiment in Region3 only.
    #e.set("VIN_mV",4)
    e.set("SINGLE_PULSE_MODE",True)
    e.set("Range2",0)
    e.set("n_skip",1)
    e.set("USE_SCOPE",False)
    
    e.set("VIN_STEP_uV",5000)
    e.set("VIN_STEP_MIN_mV",5)
    e.set("VIN_STEP_MAX_mV",1000)
    
    
    e.set("time_scale_factor",10)
    e.set("tsf_sample_phase",2)      
    e.set("NUM_AVERAGES",1)
    e.set("CapTrim",25)

    
    results_raw = []
    
    for swept_source in ["Ib1", "Ib2", "Ibuf", "Icomp"]:
        
        for i in range(len(sweeps[swept_source])):
        
            #Set all sources to their current value.
            for source in ["Ib1", "Ib2", "Ibuf", "Icomp"]:
                if source == swept_source:
                    I_PORT[source].set_current(sweeps[source][i])
                else:
                    #For not selected sources, get their level from the default. 
                    I_PORT[source].set_current(I_LEVEL[source])
                    
            sg.log.notice(f"Setting {swept_source} to {sweeps[swept_source][i]}...")
            
            prefix = f"{swept_source}({sweeps[swept_source][i]})"
            df = e.new_data_file(prefix)
        
            #Run full conversion sweep
            result = ROUTINE_FC_Avg_XF(e,df)
            
            if result == -1: #Abort on abnormal return status
                return 
            
            #summary_file.write(f"{swept_source},{sweeps[swept_source][i]},{mean},{stddev}\n")
            
    #summary_file.close()
    #print(results_raw)



def _ROUTINE_FE_Bias_Sweep_Exp():
    """Execute FC Histogram while sweeping some overall parameters."""
    
    sweeps = {}
    sweeps["Ib1"] = []# [-30e-6,-40e-6,-50e-6,-60e-6,-100e-6]
    sweeps["Ib2"] = [-20e-6] #[-5e-6,-8e-6,-10e-6,-12e-6]
    sweeps["Ibuf"] = [] #[-30e-6, -50e-6, -60e-6, -70e-6,-120e-6]
    sweeps["Icomp"] = []#[-10e-6,-18e-6, -20e-6,-22e-6,-40e-6]
    
    
    e = Experiment("Bias_Sweep_Experiment")
    
    #This experiment in Region0 only.
    e.set("VIN_mV",4)
    e.set("SINGLE_PULSE_MODE",False)
    e.set("Range2",1)
    e.set("n_skip",12)
    
    e.set("time_scale_factor",10)
    e.set("tsf_sample_phase",2)      
    e.set("NUM_SAMPLES",1000)
    e.set("CapTrim",25)
    
    
    
    
    summary_file = e.new_data_file("Summary")
    summary_file.write("Current_Bias,Setpt,mean,stddev\n")
    
    
    
    #summary_file = open("output\\Histogram_Param_Sweep_Summary.csv","w")
    
    #summary_file.write("Swept_Source,Condition,mean,stddev\n")
    
    results_raw = []
    
    for swept_source in ["Ib1", "Ib2", "Ibuf", "Icomp"]:
        
        for i in range(len(sweeps[swept_source])):
        
            #Set all sources to their current value.
            for source in ["Ib1", "Ib2", "Ibuf", "Icomp"]:
                if source == swept_source:
                    I_PORT[source].set_current(sweeps[source][i])
                else:
                    #For not selected sources, get their level from the default. 
                    I_PORT[source].set_current(I_LEVEL[source])
                    
            sg.log.notice(f"Setting {swept_source} to {sweeps[swept_source][i]}...")
            
            prefix = f"{swept_source}--{sweeps[swept_source][i]}"
            df = e.new_data_file(prefix)
        
            (mean, stddev) = ROUTINE_Full_Conversion_Histogram(e,df)
                
            
            results_raw.append((mean,stddev))
            
            summary_file.write(f"{swept_source},{sweeps[swept_source][i]},{mean},{stddev}\n")
            
    summary_file.close()
    print(results_raw)
            


# Calls ROUTINE_FC_Avg_XF (or it should)
#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_FC_Avg_XF_4quad():
    """Single experiment to collect FC Avg XF across all 4 gain regions"""
    
    unstick_VDD_ASIC()
    
    e = Experiment("FullConv_Sweep_RT_Feb07")
    
    e.set("NUM_AVERAGES",20)
    e.set("time_scale_factor",10)
    e.set("tsf_sample_phase",2)
    e.set("CapTrim",25)
    e.set("Temperature","RT")
    e.set("trig_delay",0)
    e.set("USE_SCOPE", False)
    
    #Region0
    df0 = e.new_data_file("Region0_FC_Avg_XF")
    df0.set("VIN_STEP_MIN_mV",2)
    df0.set("VIN_STEP_MAX_mV",20)
    df0.set("VIN_STEP_uV",100)
    df0.set("Range2",1)
    df0.set("n_skip",10)
    df0.set("SINGLE_PULSE_MODE",False)
    #ROUTINE_FC_Avg_XF(e,df0)
    ROUTINE_Full_Conversion_Sweep(e,df0)
    
    #Region1
    df1 = e.new_data_file("Region1_FC_Avg_XF")
    df1.set("VIN_STEP_MIN_mV",2)
    df1.set("VIN_STEP_MAX_mV",100)
    df1.set("VIN_STEP_uV",100)
    df1.set("Range2",1)
    df1.set("n_skip",1)
    df1.set("SINGLE_PULSE_MODE",True)
    #ROUTINE_FC_Avg_XF(e,df1)
    ROUTINE_Full_Conversion_Sweep(e,df1)
    
    #Region2
    df2 = e.new_data_file("Region2_FC_Avg_XF")
    df2.set("VIN_STEP_MIN_mV",2)
    df2.set("VIN_STEP_MAX_mV",100)
    df2.set("VIN_STEP_uV",100)
    df2.set("Range2",0)
    df2.set("n_skip",10)
    df2.set("SINGLE_PULSE_MODE",False)
    #ROUTINE_FC_Avg_XF(e,df2)
    ROUTINE_Full_Conversion_Sweep(e,df2)
    
    #Region3
    df3 = e.new_data_file("Region3_FC_Avg_XF")
    df3.set("VIN_STEP_MIN_mV",2)
    df3.set("VIN_STEP_MAX_mV",1000)
    df3.set("VIN_STEP_uV",1000)
    df3.set("Range2",0)
    df3.set("n_skip",1)
    df3.set("SINGLE_PULSE_MODE",True)
    #ROUTINE_FC_Avg_XF(e,df3)
    ROUTINE_Full_Conversion_Sweep(e,df3)


### CAUTION!!! This routine does not follow the new format, it may have legacy bugs.  
#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_FullConv_Transfer_Function_vs_ArbParam():
    """Capture the Full Conversion Transfer function for different values of ~Arb Param~, using Caplo->Spacely method"""

    VIN_STEP_mV = 10

    VIN_RANGE = [i for i in range(2,1000,VIN_STEP_mV)]


    PARAM_NAME = "tsf_sample_phase"

    PARAM_RANGE = [1,2,3,4,5]# [i for i in range(1,10,1)]
    
    SINGLE_PULSE_MODE = True



    input("""NOTE: PLEASE CONFIRM THAT
    1) AWG TRIG IS CONNECTED to phi1_ext (silk as 'P1.0') on the NI side.
    2) Scope Ch1 is also connected to P1.0
    3) Scope Ch2 is also connected to halt_sample (silk as 'Charge')""")
    
    time_scale_factor = 10
    #tsf_sample_phase = 2
    

    #Set CapTrim value and ensure TestEn=0
    SC_PATTERN = SC_CFG(override=0,TestEn=0,Range2=0, CapTrim=25)
    sg.pr.run_pattern( genpattern_SC_write(SC_PATTERN),outfile_tag="sc_cfg")

    
    result_values = []
    halt_sample_values = []

    for param in PARAM_RANGE:
    
        tsf_sample_phase = param
    
        if SINGLE_PULSE_MODE:
            period_us = 50
        else:
            period_us = 0.25*tsf_sample_phase+0.05
    
        # When tsf=1, pulses are 250 nanoseconds (0.25 us) wide because mclk's frequency is 2 MHz (T=500ns).
        sg.INSTR["AWG"].config_AWG_as_Pulse(VIN_RANGE[0], pulse_width_us=0.025*(10*tsf_sample_phase), pulse_period_us=period_us)
        time.sleep(1)
        
        #Pre-generate patterns to run the ADC (Full Channel)
        fc_glue = genpattern_Full_Conversion(time_scale_factor=time_scale_factor,tsf_sample_phase=tsf_sample_phase, n_samp=1)
        fc_wave = sg.gc.read_glue(fc_glue)       

        #Start a new list of result values for this ArbParam setting.
        result_values.append([])
        halt_sample_values.append([])

        for vin in VIN_RANGE:
        
            try:
                #sg.INSTR["Scope"].setup_trigger(1,0.6)
        
                sg.INSTR["AWG"].set_pulse_mag(vin)

                fc_result = sg.pr.run_pattern(fc_glue,outfile_tag="fc_result")[0]
            
                # FOR NOW: DON'T USE THE SCOPE BECAUSE IT'S BUGGY AND WE DON'T CARE ABOUT halt_sample IF n_samp=1
            
                #halt_sample_wave = sg.INSTR["Scope"].get_wave(2)
            
                #if any([x > 0.6 for x in halt_sample_wave]):
                #    halt_sample = 1
                #else:
                #    halt_sample = 0

                #Get DACclr and capLo
                result_glue = sg.gc.read_glue(fc_result)
                dacclr_wave = sg.gc.get_bitstream(result_glue,"DACclr")
                caplo_wave = sg.gc.get_bitstream(result_glue,"capLo_ext")

                result = interpret_CDAC_pattern_edges(caplo_wave, dacclr_wave)

                print(f"RESULT: {result}")# (halt_sample={halt_sample})")
                
                
                
            except Exception as e:
                print(e)
                sg.log.error("Bad data point! Proceeding with sentinel value -1 in data set. ")
                result = -1
                halt_sample = -1
                
            result_values[-1].append(result)
            #halt_sample_values[-1].append(halt_sample)
        


    print(result_values)
    print(halt_sample_values)


    write_parameter_sweep_to_csv(PARAM_RANGE,
                                 VIN_RANGE,
                                 result_values,
                                 f"FC_Transfer_Function_result_vs_Arb_Param_{PARAM_NAME}_Vin_step_by_{VIN_STEP_mV}_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")
    
    write_parameter_sweep_to_csv(PARAM_RANGE,
                                 VIN_RANGE,
                                 halt_sample_values,
                                 f"FC_Transfer_Function_hs_vs_Arb_Param_{PARAM_NAME}_Vin_step_by_{VIN_STEP_mV}_on_"+time.strftime("%Y_%m_%d")+".csv",
                                 row_param_name="Vin")

# Independent Routine
#<<Registered w/ Spacely as ROUTINE 12, call as ~r12>>
def ROUTINE_unstick_VDD_ASIC():
    unstick_VDD_ASIC()


# Independent Routine
#<<Registered w/ Spacely as ROUTINE 13, call as ~r13>>
def ROUTINE_PGL_Variation_Analysis():

    #unstick_VDD_ASIC()

    ## SETUP
    # Create a new Experiment
    e = Experiment("PGL Variation Analysis 3_27_2024")
    
    df1 = e.new_data_file("Results")
    df2 = e.new_data_file("Raw Data")
    
    df1.write("Vref_fe,Avg PGL Slope,RMS PGL Slope")
    df2.write("Vref_fe,Raw Data Samples")

    e.set("scope_timebase_s",2e-6)
    e.set("NUM_SAMP",100)

    sg.INSTR["Scope"].DEBUG_MODE = True
    sg.INSTR["Scope"].io.set_timeout(15000)
    sg.INSTR["Scope"].enable_channels([1,2])
    sg.INSTR["Scope"].set_timebase(e.get("scope_timebase_s"))
    sg.INSTR["Scope"].set_time_offset(8e-6)
    sg.INSTR["Scope"].set_scale(0.5,chan_num=2)
    sg.INSTR["Scope"].set_voltage_offset(1.5,chan_num=2)
    sg.INSTR["Scope"].set_scale(0.1,chan_num=1)
    sg.INSTR["Scope"].set_voltage_offset(3,chan_num=1)
    sg.INSTR["Scope"].set_bandwidth_limit(True,chan_num=1)
    
    #Range of vref_fe values we will check. 
    VREF_FE_RANGE_mV = [400, 450, 500, 550, 600, 650, 700, 750]
    
    #Number of times we will sample PGL slope for each value of vref_fe
    NUM_SAMP = e.get("NUM_SAMP")
    
    #This will become a 2D list where each sublist corresponds to one VREF_FE value.
    PGL_samples = []
    
    #Generate a Spacely pattern which will give a pulse on Rst
    waves = {}
    waves["Rst_ext"] = [0]*10 + [1]*40 + [0]*10
    Rst_pulse_pattern = genpattern_from_waves_dict(waves)

    input("""PLEASE ENSURE THAT:
          > Scope Channel 1 is connected to Out_stage_1
          > Scope Channel 2 is connected to Rst
          Press enter to continue... """)
    
    ## RUN EXPERIMENT
    for vref_fe in VREF_FE_RANGE_mV:
    
        #Start a new empty sub-list
        PGL_samples.append([])
    
        #Set Vref_fe to specified value
        V_PORT["Vref_fe"].set_voltage(1e-3*vref_fe)
        
        #Run N times
        for _ in range(NUM_SAMP):

            #input("Ready to run?")
        
            #Set up scope trigger
            sg.INSTR["Scope"].setup_trigger(2,0.6)
            
            #Pulse Rst
            sg.pr.run_pattern(Rst_pulse_pattern)
            
            #Get scope waveform
            
            out_stage_1_wave = sg.INSTR["Scope"].get_wave(1)
            Rst_wave = sg.INSTR["Scope"].get_wave(2)
            
            #Calculate PGL slope.
            PGL_slope = calculate_PGL_Slope(Rst_wave, out_stage_1_wave, e.get("scope_timebase_s"))

            #Save data
            PGL_samples[-1].append(PGL_slope)
    
    
        ## WRITE DATA TO FILE
        avg_slope = np.mean(PGL_samples[-1])
        rms_slope = np.std(PGL_samples[-1])
        
        #Summary statistics
        df1.write(f"{vref_fe},{avg_slope},{rms_slope}\n")
        
        #Raw data
        df2.write(str(vref_fe)+","+",".join([str(x) for x in PGL_samples[-1]])+"\n")

    df1.close()
    df2.close()

