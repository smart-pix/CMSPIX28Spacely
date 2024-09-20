# ExampleASIC Config File
#
# This file contains all the static configuration info that describes how
# your ASIC test stand is set up, for example power supply voltages.


# When using the NI-PXI system, we define a bitfile to use in the Config file.
# This dict gives a default FPGA bitfile for each slot that you are using.
# "NI7972_NI6583_40MHz" is a bitfile that has been generated for the NI7972
# FPGA running at a clock speed of 40 MHz with the I/O card NI6583.
# If you need to generate a new bitfile, contact aquinn@fnal.gov
DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot4":"NI7972_NI6583_40MHz"}


# We almost always want to default to the iospec present in the same directory.
DEFAULT_IOSPEC = ".\\spacely-asic-config\\ExampleASIC\\ExampleASIC_iospec.txt"


# # # # # # # # # # # # # # # # # # # 
#  Setting up INSTRUMENT Dictionary #
# # # # # # # # # # # # # # # # # # #

# Almost all of the test instruments controlled by Spacely are accessed through
# the INSTR dictionary. 
# After initialization, an instrument handle can be accessed as, for example:
#    sg.INSTR["SMU_A"]
# (sg = Spacely Globals)

INSTR = {"car" : {"type": "Caribou",
                  "host":"192.168.1.24",
                  "port":12345,
                  "device":"SpacelyCaribouBasic"}
        }


# # # # # # # # # # # # # # # # # # # # # # #
#  Setting up Voltage and Current Channels  #
# # # # # # # # # # # # # # # # # # # # # # #

# 1) Define the sequence in which your current and voltage rails will be
#    initialized.

# Example: We have two voltage rails, VDD and Vref. VDD will be initialized
#          first. We have one current rail, Ibias.
V_SEQUENCE = ["VDD3V3", "VDD_LED"]
I_SEQUENCE = []


# 2) Define the instrument + channel that will be used for each rail:

# Example: VDD is on myPSU channel 0, etc.
V_INSTR = {"VDD3V3": "car",
           "VDD_LED": "car"}
V_CHAN  = {"VDD3V3": "PWR_OUT_1",
           "VDD_LED": "PWR_OUT_2"}
I_INSTR = {}
I_CHAN  = {}


# 3) Define the nominal output level. V_PORTs are in volts, I_PORTs are in amps.

V_LEVEL = {"VDD3V3": 3.3,
           "VDD_LED": 2.0}     #1.0 V
I_LEVEL = {} #100 uA


# 4) Define limit values. For V_PORTs we set a maximum current. For I_PORTs
#    we set a maximum voltage.
V_CURR_LIMIT = {"VDD3V3": 0.1,
                "VDD_LED": 0.1}  

I_VOLT_LIMIT = {} 

           
# 5) Create V_PORT and I_PORT dictionaries. When Spacely initializes these rails,
#    you will be able to access them with these dictionaries.
V_PORT = {"VDD3V3": None,
          "VDD_LED": None}

# 6) (Optional) for each rail, define a warning voltage range in the
#    form [Vhigh, Vlow]. Spacely will warn you if the voltage ever falls
#    outside of this range.
V_WARN_VOLTAGE = {"VDD3V3": [3.1,3.4],
                  "VDD_LED": [1.9,2.1]}
I_WARN_VOLTAGE = {}



