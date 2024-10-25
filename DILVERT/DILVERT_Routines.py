#ExampleASIC Routines File
#
# This file contains any custom code that you want to write for your ASIC,
# for example routines to read or write to registers, or to run tests.


#Import Spacely functions (this is necessary for almost every chip)
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *



DEFAULT_SC = None

def onstartup():
    global DEFAULT_SC
    DEFAULT_SC = DILVERT_SC([0]*25)
    
    DEFAULT_SC.set_field("DOUT1_Select",1)
    DEFAULT_SC.set_field("DOUT2_Select",1)
    DEFAULT_SC.set_field("CAL1",1)
    DEFAULT_SC.set_field("DRV",3)

    DEFAULT_SC.print_fields()




#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
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
   

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_get_avg_core_power():
    """Returns the average power consumed by VDDC over 100 queries."""
    
    power_results = []
    
    for _ in range(100):
        power_results.append(V_PORT["VDDC"].get_current()*0.8)
        
    print(f"Minimum power: {min(power_results)}")
    print(f"Maximum power: {max(power_results)}")
    print(f"\nAVERAGE POWER: {sum(power_results)/100}")


#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_tuning_sensitivity_analysis():
    """Analyze the sensitivity of resolution to tuning voltage."""
    
    # Because setting the three pulse intervals requires human intervention,
    # we are going to collect all the necessary tuning voltage points for 
    # each power rail at a time.
    
    PULSE_TIME_STEPS = [0,100,1000]
    
    V_SLOW_CHAIN_NOM = 0.55
    V_SLOW_CHAIN_RANGE = [x/100 for x in range(0,200)]
    
    V_RO_NOM = 1
    V_RO_RANGE = [x/100 for x in range(0,200)]
    
    TEST_V_RO = [V_RO_NOM]*len(V_SLOW_CHAIN_RANGE) + V_RO_RANGE
    TEST_V_SLOW_CHAIN = V_SLOW_CHAIN_RANGE + [V_SLOW_CHAIN_NOM]*len(V_RO_RANGE)
    
    TEST_N = len(TEST_V_RO)
    assert(TEST_N == len(TEST_V_SLOW_CHAIN))
    
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
            
            time.sleep(0.001)
            
            (Qc, Qf) = get_TDC_result(N_avg=100)
        
            QCOARSE[pulse_time].append(Qc)
            QFINE[pulse_time].append(Qf)
    
    
    ## STAGE 2: Analysis
    
    print("TBD!!! Implement system of equation solving")
        
def get_TDC_result(N_avg = 1):
    """Gets 1 or more TDC results and averages them together"""
    
    Qc = []
    Qf = []
    
    for i in range(N_avg):
        # (1) Wait for the rising edge of START/STOP (TRIGGER)
    
        print("ERROR! NEED TO IMPLEMENT WAIT FOR TRIGGER")
    
        # (2) Grab data from the TDC internal registers.
        sc_contents = serial_read()
    
        pulse_reset()
        
        Qc.append(sc_contents.get_field("QCOARSE"))
        Qf.append(sc_contents.get_field("QFINE"))
        
    return (sum(Qc)/N_avg, sum(Qf)/N_avg)