# SpacelyWorkshop Config File
#
# This file contains all the static configuration info that describes how
# your ASIC test stand is set up, for example PSU and SMU voltages.

USE_NI = True

# This dict gives a default FPGA bitfile for each slot that you are using.
# "NI7972_NI6583_40MHz" is a bitfile that has been generated for the NI7972
# FPGA running at a clock speed of 40 MHz with the I/O card NI6583.
# If you need to generate a new bitfile, contact aquinn@fnal.gov
DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot4":"NI7972_NI6583_40MHz"}


# ADAM'S NOTES: I think I'll need an SMU for this...
INSTR = {"SMU_A" : {"type" : "NIDCPower", 
                    "slot" : "PXI1Slot20"}}


DEFAULT_IOSPEC = ".\\asic_config\\SpacelyWorkshop\\SpacelyWorkshop_iospec.txt"





# # # # # # # # # # # # # # # # # # # # # # #
#  Setting up Voltage and Current Channels  #
# # # # # # # # # # # # # # # # # # # # # # #

# 1) Define the sequence in which your current and voltage rails will be
#    initialized.

# ADAM'S NOTES: Wow, it was so much work to set up V_PWR1. I'm gonna go for a milkshake.
#               when I get back, I'll do V_PWR2.
V_SEQUENCE = ["V_PWR1"]

# 2) Define the instrument + channel that will be used for each rail:

V_INSTR = {"V_PWR1": "SMU_A"}
V_CHAN  = {"V_PWR1": 2}


# 3) Define the nominal output level. V_PORTs are in volts, I_PORTs are in amps.

V_LEVEL = {"V_PWR1":0}     # ADAM'S NOTES: Just gotta figure out what voltage this should be.....


# 4) Define limit values. For V_PORTs we set a maximum current. For I_PORTs
#    we set a maximum voltage.
V_CURR_LIMIT = {"V_PWR1": 0.1} #100 mA 


           
# 5) Create V_PORT and I_PORT dictionaries. When Spacely initializes these rails,
#    you will be able to access them with these dictionaries.
V_PORT = {"V_PWR1": None}


# 6) (Optional) for each rail, define a warning voltage range in the
#    form [Vhigh, Vlow]. Spacely will warn you if the voltage ever falls
#    outside of this range.
V_WARN_VOLTAGE = {"V_PWR1": [0,5]}




