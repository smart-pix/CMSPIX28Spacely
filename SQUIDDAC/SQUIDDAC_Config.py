#from .XROCKET2_Routines import *


USE_ARDUINO = False
USE_NI = True
USE_AWG = False



DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot16":"NI7972_NI6583_40MHz"}


DEFAULT_IOSPEC = ".\\asic_config\\SQUIDDAC\\squiddac_iospec.txt"


#Voltage Channels
SMU_A = "PXI1Slot13"

INSTR_INIT_SEQUENCE = [SMU_A]
INSTR = {SMU_A:None}

V_SEQUENCE = [ "Vout"]

# Set up "Vout on SMU_A channel 1, w/ a nominal voltage of 0
V_INSTR = {"Vout" : SMU_A}           
V_CHAN = {"Vout"   : 1}
V_LEVEL = {"Vout": 0}

#Spacely will warn if the voltage falls outside this range.
V_WARN_VOLTAGE = {"Vout": [-0.1,0.1]}
     
V_CURR_LIMIT = {"Vout": 0.1}

#Global dict to hold the port objects created for each of these.
V_PORT = {"Vout": None}

