#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.


#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

import serial
import time
import numpy as np

DEFAULT_SC = None
SERIAL_PORT = 'COM5'
BAUD = 230400

PORT = None

#Calibration points for 3-point cal.
PULSE_TIME_STEPS_GLOBAL = [0,100,10000]

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_open_port():
    global DEFAULT_SC
    global PORT
    
    sg.log.debug("Opening Port to Arduino...")
    
    PORT = open_port()
    
    
    while True:
    
        sg.log.debug("Checking Serial...")
        null_count = 0
        
        while True:
            #if null_count > 50:
            #    sg.log.error("Didn't receive anything over serial for > 5 seconds. :/")
                
            char = PORT.read()
            x = char.decode('utf-8')
            if len(x)>0:
                print(x,end='',flush=True)
            else:
                null_count += 1
           
            if char == b'*':
                mode = "IDLE"
                sg.log.debug("Arduino is idling.")
                break
            elif char == b'?':
                mode = "SELECT"
                sg.log.debug("Arduino is waiting for mode selection.")
                break
            elif null_count > 50:
                mode = "SELECT"
                sg.log.debug("Haven't received any bytes in > 5 secs, maybe Arduino is waiting for mode selection.")
                break
            elif char == b'~':
                mode = "STREAM"
                sg.log.debug("Arduino is streaming.")
                break
        
        if mode == "STREAM":
            break
            
        if mode == "IDLE":
            sg.log.debug("Attempting SC check...")
            PORT.write(b'\n')
            
        if mode == "SELECT":
            sg.log.debug("Selecting mode '2' (streaming)")
            PORT.write(b'2')
    
    sg.log.debug("Done!")

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_close_port():
    global PORT
    PORT.__del__()
    


#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_check_sc_loopback():
   
   pulse_reset()
   
   print("Testing loopback w/o pass/load")
   
   serial_write(DEFAULT_SC, s_pass=False)
   return_sc = serial_read(s_load = False)
   
   return_sc.print_fields()
   
   if DEFAULT_SC == return_sc:
       print("PASS!")
   else:
       print("FAIL!")
   
   print("Testing loopback w/ pass/load")
   
   serial_write(DEFAULT_SC, s_pass=True)
   return_sc = serial_read(s_load = True)
   
   return_sc.print_fields()
   
   SC2 = DILVERT_SC([0]*25)
    
   SC2.set_field("DOUT1_Select",1)
   SC2.set_field("DOUT2_Select",1)
   SC2.set_field("CAL1",1)
   SC2.set_field("DRV",3)
   SC2.set_field("QFINE",99)
   
   if SC2 == return_sc:
       print("PASS!")
   else:
       print("FAIL!")
   

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_get_avg_core_power():
    """Returns the average power consumed by VDDC over 100 queries."""
    
    power_results = []
    
    for _ in range(100):
        power_results.append(V_PORT["VDDC"].get_current()*0.8)
        
    print(f"Minimum power: {min(power_results)}")
    print(f"Maximum power: {max(power_results)}")
    print(f"\nAVERAGE POWER: {sum(power_results)/100}")


#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_tuning_sensitivity_data_collection(PULSE_TIME_STEPS = PULSE_TIME_STEPS_GLOBAL, do_V_RO=True, do_V_SLOW_CHAIN=True):
    """Analyze the sensitivity of resolution to tuning voltage."""
    
    # Because setting the three pulse intervals requires human intervention,
    # we are going to collect all the necessary tuning voltage points for 
    # each power rail at a time.
    
    sg.log.debug(f"PULSE_TIME_STEPS = {PULSE_TIME_STEPS}")
    
    V_SLOW_CHAIN_NOM = 0.55
    if do_V_SLOW_CHAIN:
        V_SLOW_CHAIN_RANGE = [x/10 for x in range(0,20)]
    else:
        V_SLOW_CHAIN_RANGE = []
    
    V_RO_NOM = 1
    if do_V_RO:
        V_RO_RANGE = [x/10 for x in range(0,20)]
    else:
        V_RO_RANGE = []
    
    TEST_V_RO = [V_RO_NOM]*len(V_SLOW_CHAIN_RANGE) + V_RO_RANGE
    TEST_V_SLOW_CHAIN = V_SLOW_CHAIN_RANGE + [V_SLOW_CHAIN_NOM]*len(V_RO_RANGE)
    
    TEST_N = len(TEST_V_RO)
    assert(TEST_N == len(TEST_V_SLOW_CHAIN))
    
    
    e = Experiment("DILVERT Back-Gate Tuning Sensitivity")
    df = e.new_data_file("Qc_Qf_vs_BackGate")
    
    sg.log.debug(f"Beginning tuning sensitivity analysis. Will gather {TEST_N} voltage points.")
    
    ## STAGE 1: Data Collection
    
    #Each key of the QCOARSE/QFINE dictionaries is a pulse time. 
    #Each value is a list of the Qc/Qf values for each voltage condition under that pulse time.
    QCOARSE = {}
    QFINE   = {}
    
    
    
    for pulse_time in PULSE_TIME_STEPS:
        
        QCOARSE[pulse_time] = []
        QFINE[pulse_time] = []
        
        input(f"Please configure the pulse generator for delT={pulse_time} picoseconds and press 'Enter' when ready.")
        
        for i in range(TEST_N):
            sg.log.debug(f"Test Condition {i}: V_RO={TEST_V_RO[i]} V_SLOW_CHAIN={TEST_V_SLOW_CHAIN[i]}")
            
            V_PORT["VTUNE_N_RO"].set_voltage(TEST_V_RO[i])
            V_PORT["VTUNE_P_RO"].set_voltage(2-TEST_V_RO[i])
            V_PORT["VTUNE_N_SLOW"].set_voltage(TEST_V_SLOW_CHAIN[i])
            V_PORT["VTUNE_P_SLOW"].set_voltage(2-TEST_V_SLOW_CHAIN[i])
            
            sg.log.debug("Flushing buffer...")
            PORT.reset_input_buffer()
            time.sleep(0.2)
            #Intentionally flush the buffer twice to get rid of any stragglers.
            PORT.reset_input_buffer()
            
            (Qc, Qf) = get_TDC_result_arduino(N_avg=500)
        
            QCOARSE[pulse_time].append(Qc)
            QFINE[pulse_time].append(Qf)
    
    #Write results before analysis. 
    df.write("V_RO,V_SLOW_CHAIN")
    for pulse_time in PULSE_TIME_STEPS:
        df.write(f",{pulse_time}ps_Qc,{pulse_time}ps_Qf")
    df.write("\n")
    
    for i in range(TEST_N):
        df.write(f"{TEST_V_RO[i]},{TEST_V_SLOW_CHAIN[i]}")
        for pulse_time in PULSE_TIME_STEPS:
            df.write(f",{QCOARSE[pulse_time][i]},{QFINE[pulse_time][i]}")
        df.write("\n")
    
    df.close()
    
    ## STAGE 2: Analysis

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_tuning_sensitivity_analysis(PULSE_TIME_STEPS = PULSE_TIME_STEPS_GLOBAL):
    
    sg.log.debug(f"PULSE_TIME_STEPS = {PULSE_TIME_STEPS}")
    
    a = Analysis()
    
    a.load_df(os.path.join("output","DILVERT Back-Gate Tuning Sensitivity","Qc_Qf_vs_BackGate.csv"))
    
    data = a.data[a.data_sources[0]]
    
    tOffset = []
    tR_fine = []
    tR_coarse = []
    
    TEST_N = len(data["V_RO"])
    
    t0 = PULSE_TIME_STEPS[0]
    t1 = PULSE_TIME_STEPS[1]
    t2 = PULSE_TIME_STEPS[2]
    
    # Solve System of Linear Equations for each row...
    for n in range(TEST_N):
        
        # tOffset + Qc * tR_coarse - Qf * tR_fine = Tin
        
        a = np.array([[1,data[f"{t0}ps_Qc"][n],-1*data[f"{t0}ps_Qf"][n]],
                      [1,data[f"{t1}ps_Qc"][n],-1*data[f"{t1}ps_Qf"][n]],
                      [1,data[f"{t2}ps_Qc"][n],-1*data[f"{t2}ps_Qf"][n]]])
        b = np.array(PULSE_TIME_STEPS)
        
        try:
            x = np.linalg.solve(a,b)
        except np.linalg.LinAlgError:
            print("ERR: Singular Matrix")
            print(f"a = {a}")
            print(f"Determinant: {np.linalg.det(a)}")
            x = [0,0,0]
        
        tOffset.append(x[0])
        tR_coarse.append(x[1])
        tR_fine.append(x[2])
     
    e = Experiment("DILVERT Back-Gate Tuning Sensitivity")
    df = e.new_data_file("tR_vs_BackGate")
        
    #Write results before analysis. 
    df.write("V_RO,V_SLOW_CHAIN,")
    df.write("tOffset,tR_coarse,tR_fine")
    df.write("\n")
    
    for i in range(TEST_N):
        v_ro = data["V_RO"][i]
        v_slow_chain = data["V_SLOW_CHAIN"][i]
        df.write(f"{v_ro},{v_slow_chain}")
        df.write(f",{tOffset[i]},{tR_coarse[i]},{tR_fine[i]}\n")
    
    df.close()
    
def run_x(str_cmd):
    global PORT
        
    eval(str_cmd)


#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_get_TDC_result():
    
    how_many = int(input("How many TDC results do you want to average? "))
    
    sg.log.debug("Flushing buffer...")
    PORT.reset_input_buffer()
    time.sleep(0.2)
    #Intentionally flush the buffer twice to get rid of any stragglers.
    PORT.reset_input_buffer()
    
    get_TDC_result_arduino(how_many, verbose=True)
    
    #port.close()
    
def get_TDC_result_arduino(N_avg=1, verbose=False):
    global PORT
    if PORT == None:
        print("ERROR! Need a port to be provided to get TDC result.")
        return -1
    n = 0
    Qc_list = []
    Qf_list = []
    
    skip_next_line = False
    
    while n < N_avg:
        line = ""
        while True:
            char = PORT.read().decode('utf-8')
            if len(char) > 0:
                line= line + char
                if verbose:
                    print(char,end='',flush=True)
                if char == '\n':
                    break
        
        #line = PORT.readline().strip() #Blocks forever until new line is available.
        line = line.strip()

        if len(line) == 0:
            if verbose:
                print("(Skipped empty line.)")
        elif '~~~' in line:
            skip_next_line = True
            if verbose:
                print("(Skipping first line of batch.)")
        else:
            #If the skip_next_line flag is set, then this line should be skipped.
            if skip_next_line:
                skip_next_line = False
                continue
            try:
                Qc, Qf = line.split(',')
            except ValueError:
                sg.log.error(f"{line} has too many/few commas.")
                continue
            Qc_list.append(int(Qc))
            Qf_list.append(int(Qf))
            n = n + 1
            
    Qc_avg = sum(Qc_list)/N_avg
    Qf_avg = sum(Qf_list)/N_avg
    
    if verbose:
        print(f"Counted {N_avg} results, average is: ({Qc_avg},{Qf_avg})")
    
    return (Qc_avg, Qf_avg)
    
    
    
def open_port():
    port = serial.Serial(SERIAL_PORT, BAUD, timeout=0.1)

    try:
            port.open()
    except serial.serialutil.SerialException:
        print("Port is already open...")
    print("Serial port opened!")   

    return port
    
#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_poll_io():
    
    
    counter = 0
    attempts = 0
    
    samples = int(input("How many FPGA Samples?>>>"))
    
    start = time.time()
    
    while time.time() - start < 1:
        if samples == 0:
            x = sg.pr._interface['PXI1Slot6/NI6583'].interact("r","SE_IO_Data_In")
        else:
            out_wave = sg.gc.read_glue(sg.pr.run_pattern(sg.gc.dict2Glue({"S_DIN":[0]*samples}),outfile_tag="poll")[0])
            trig_signal = sg.gc.get_bitstream(out_wave,"TRIGGER")
            x = any([x > 0 for x in trig_signal])
        if x > 0:
            counter += 1
        attempts += 1
            
    print(f"Counter: {counter}/{attempts}")
    