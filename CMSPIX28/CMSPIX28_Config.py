# ExampleASIC Config File
#
# This file contains all the static configuration info that describes how
# your ASIC test stand is set up, for example PSU and SMU voltages.


#These global variables define whether we will initialize specific pieces of
#equipment that can be controlled by Spacely.
USE_ARDUINO = False  #(Arduino Portenta)
USE_NI      = False   #(NI Chassis)
USE_AWG     = False  #(Arbitrary Wave Gen)
USE_SCOPE   = False  #(Oscilloscope)



# This dict gives a default FPGA bitfile for each slot that you are using.
# "NI7972_NI6583_40MHz" is a bitfile that has been generated for the NI7972
# FPGA running at a clock speed of 40 MHz with the I/O card NI6583.
# If you need to generate a new bitfile, contact aquinn@fnal.gov
DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot4":"NI7972_NI6583_40MHz"}



DEFAULT_IOSPEC = ".\\asic_config\\ExampleASIC\\ExampleASIC_iospec.txt"


# # # # # # # # # # # # # 
#  Setting up SMU/PSUs  #
# # # # # # # # # # # # #

#First, define which NI slot an SMU or PSU sits in.
mySMU = "PXI1Slot2"
myPSU = "PXI1Slot7"

#Define what order these instruments should be powered on in:
INSTR_INIT_SEQUENCE = [mySMU, myPSU]

#Create a dictionary called "INSTR". When Spacely initializes the instruments,
#it will put them into this dictionary for easy referencing.
INSTR = { "car" : { "type" : "Caribou",
                    "host" : "192.168.7.63",
                    "port" : 12345,
                    "device" : "ExampleCaribou"}}

# # # # # # # # # # # # # # # # # # # # # # #
#  Setting up Voltage and Current Channels  #
# # # # # # # # # # # # # # # # # # # # # # #

# 1) Define the sequence in which your current and voltage rails will be
#    initialized.

# Example: We have two voltage rails, VDD and Vref. VDD will be initialized
#          first. We have one current rail, Ibias.
V_SEQUENCE = ["VDD","Vref"]
I_SEQUENCE = ["Ibias"]


# 2) Define the instrument + channel that will be used for each rail:

# Example: VDD is on myPSU channel 0, etc.
V_INSTR = {"VDD": myPSU,
           "Vref":mySMU}
V_CHAN  = {"VDD": 0,
           "Vref":1}
I_INSTR = {"Ibias":mySMU}
I_CHAN  = {"Ibias":0}


# 3) Define the nominal output level. V_PORTs are in volts, I_PORTs are in amps.

V_LEVEL = {"VDD":1.2,      #1.2 V
           "Vref":1.0}     #1.0 V
I_LEVEL = {"Ibias": 100e-6} #100 uA


# 4) Define limit values. For V_PORTs we set a maximum current. For I_PORTs
#    we set a maximum voltage.
V_CURR_LIMIT = {"VDD": 0.1,  #100 mA
                "Vref": 10e-6} #10 uA 

I_VOLT_LIMIT = {"Ibias": 2.5} #2.5 V

           
# 5) Create V_PORT and I_PORT dictionaries. When Spacely initializes these rails,
#    you will be able to access them with these dictionaries.
V_PORT = {"VDD": None,
          "Vref": None}
I_PORT = {"Ibias": None}

# 6) (Optional) for each rail, define a warning voltage range in the
#    form [Vhigh, Vlow]. Spacely will warn you if the voltage ever falls
#    outside of this range.
V_WARN_VOLTAGE = {"VDD": [1.1,1.3],
                  "Vref": [0.9,1.1]}
I_WARN_VOLTAGE = {"Ibias": [0,2.5]}



