# ExampleASIC Config File
#
# This file contains all the static configuration info that describes how
# your ASIC test stand is set up, for example power supply voltages.
import os

USE_NI = True

DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot6":"NI7976_NI6583_40MHz"}


# We almost always want to default to the iospec present in the same directory.
DEFAULT_IOSPEC = os.path.join("spacely-asic-config","DILVERT","DILVERT_iospec.txt")


# # # # # # # # # # # # # # # # # # # 
#  Setting up INSTRUMENT Dictionary #
# # # # # # # # # # # # # # # # # # #

# Almost all of the test instruments controlled by Spacely are accessed through
# the INSTR dictionary. 
# After initialization, an instrument handle can be accessed as, for example:
#    sg.INSTR["SMU_A"]
# (sg = Spacely Globals)

INSTR = {"SMU_A" : {"type" : "NIDCPower", 
                    "slot" : "PXI1Slot3"},
         "SMU_B" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot4"},
         "PSU_A" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot8"},
         "PSU_B" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot9"}
        }


# # # # # # # # # # # # # # # # # # # # # # #
#  Setting up Voltage and Current Channels  #
# # # # # # # # # # # # # # # # # # # # # # #

# 1) Define the sequence in which your current and voltage rails will be
#    initialized.

# Example: We have two voltage rails, VDD and Vref. VDD will be initialized
#          first. We have one current rail, Ibias.
V_SEQUENCE = ["LS_3V3","VDDIO", "VDDC", "VTUNE_N_FAST", "VTUNE_P_FAST", "VTUNE_N_SLOW", "VTUNE_P_SLOW", 
               "VTUNE_N_RO", "VTUNE_P_RO", "NMOS_BG_BIAS", "PMOS_BG_BIAS"]
I_SEQUENCE = []

REVERSE_FLANGE = False

# 2) Define the instrument + channel that will be used for each rail:

# Example: VDD is on myPSU channel 0, etc.
V_INSTR = {"LS_3V3":"PSU_A",
           "VDDIO": "PSU_A",
           "VDDC": "PSU_B",
           "VTUNE_N_FAST":"SMU_A",
           "VTUNE_P_FAST":"SMU_A",
           "VTUNE_N_SLOW":"SMU_B",
           "VTUNE_P_SLOW":"SMU_B",
           "VTUNE_N_RO"  :"SMU_B",
           "VTUNE_P_RO"  :"SMU_A",
           "NMOS_BG_BIAS":"SMU_B",
           "PMOS_BG_BIAS":"SMU_A"}
V_CHAN  = {"LS_3V3":0,
           "VDDIO": 1,
           "VDDC": 0,
           "VTUNE_N_FAST":3,
           "VTUNE_P_FAST":2,
           "VTUNE_N_SLOW":1,
           "VTUNE_P_SLOW":0,
           "VTUNE_N_RO"  :2,
           "VTUNE_P_RO"  :1,
           "NMOS_BG_BIAS":3,
           "PMOS_BG_BIAS":0}
I_INSTR = {}
I_CHAN  = {}


# 3) Define the nominal output level. V_PORTs are in volts, I_PORTs are in amps.

V_LEVEL = {"LS_3V3":3.3,
           "VDDIO": 1.8,
           "VDDC": 0.8,
           "VTUNE_N_FAST": 1.9,
           "VTUNE_P_FAST": 0.1,
           "VTUNE_N_SLOW": 0.55,
           "VTUNE_P_SLOW":1.45,
           "VTUNE_N_RO"  :  1,
           "VTUNE_P_RO"  :1,
           "NMOS_BG_BIAS":1,
           "PMOS_BG_BIAS":-1}     
I_LEVEL = {} #100 uA


# 4) Define limit values. For V_PORTs we set a maximum current. For I_PORTs
#    we set a maximum voltage.
V_CURR_LIMIT = {
            "LS_3V3":0.5,
            "VDDIO": 0.1,
           "VDDC": 0.1,
           "VTUNE_N_FAST":0.0001,
           "VTUNE_P_FAST":0.0001,
           "VTUNE_N_SLOW":0.0001,
           "VTUNE_P_SLOW":0.0001,
           "VTUNE_N_RO"  :0.0001,
           "VTUNE_P_RO"  :0.0001,
           "NMOS_BG_BIAS":0.0001,
           "PMOS_BG_BIAS":0.0001} #100 uA 

I_VOLT_LIMIT = {} #2.5 V

           
# 5) Create V_PORT and I_PORT dictionaries. When Spacely initializes these rails,
#    you will be able to access them with these dictionaries.
V_PORT = {"LS_3V3":None,
            "VDDIO": None,
           "VDDC": None,
           "VTUNE_N_FAST":None,
           "VTUNE_P_FAST":None,
           "VTUNE_N_SLOW":None,
           "VTUNE_P_SLOW":None,
           "VTUNE_N_RO"  :None,
           "VTUNE_P_RO"  :None,
           "NMOS_BG_BIAS":None,
           "PMOS_BG_BIAS":None}
I_PORT = {}

# 6) (Optional) for each rail, define a warning voltage range in the
#    form [Vhigh, Vlow]. Spacely will warn you if the voltage ever falls
#    outside of this range.
V_WARN_VOLTAGE = {
            "LS_3V3":[3.2,3.4],
            "VDDIO": [1.7,1.9],
           "VDDC": [0.7,0.9],
           "VTUNE_N_FAST":[0,2.0],
           "VTUNE_P_FAST":[0,2.0],
           "VTUNE_N_SLOW":[0,2.0],
           "VTUNE_P_SLOW":[0,2.0],
           "VTUNE_N_RO"  :[0,2.0],
           "VTUNE_P_RO"  :[0,2.0],
           "NMOS_BG_BIAS":[0,2.0],
           "PMOS_BG_BIAS":[-2.0,0]}
I_WARN_VOLTAGE = {}


if REVERSE_FLANGE:
    print("!!! WARNING -- Config file is written to use a CRYO_ISOk63_FLANGE_ANALOG Board with REVERSED connectors!!!")
    
    for rail in V_SEQUENCE:
        if "SMU" in V_INSTR[rail]:
            #Swap channels 0~3
            V_CHAN[rail] = 3 - V_CHAN[rail]

            #Swap polarities of warn and set voltages:
            V_LEVEL[rail] = -1*V_LEVEL[rail]
            V_WARN_VOLTAGE[rail][0] = -1*V_WARN_VOLTAGE[rail][0]
            V_WARN_VOLTAGE[rail][1] = -1*V_WARN_VOLTAGE[rail][1]