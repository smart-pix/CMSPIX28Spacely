#from .XROCKET2_Routines import *


USE_ARDUINO = False
USE_NI = True
USE_AWG = True



DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot11":"NI7976_NI6583_40MHz"}

# DEFAULT_PROLOGIX_IPADDR = "192.168.1.15"
# DEFAULT_AWG_GPIBADDR = 10

#CDAC Trimming
DEFAULT_CDAC_TRIMSTRING = "100000"

DEFAULT_IOSPEC = ".\\spacely-asic-config\\XROCKET2\\xrocket2_iospec.txt"


# #Voltage Channels
# #SMU A and B designations are from Scott's PCB.
# SMU_A = "PXI1Slot2"
# SMU_B = "PXI1Slot3"
# PSU_A = "PXI1Slot7" # PXI-4110 or 4111; CH0=0-6VDC, CH1=0-20V, CH2=-20V-0V
# PSU_B = "PXI1Slot8" # PXI-4110 or 4111; CH0=0-6VDC, CH1=0-20V, CH2=-20V-0V



#On the FLORA Motherboard,
# SMU_A -> J2   SMU_B -> J3
# PSU_A -> J8   PSU_B -> J24

# INSTR_INIT_SEQUENCE = [SMU_A, SMU_B, PSU_A, PSU_B]
INSTR = {"SMU_A" : {"type" : "NIDCPower", 
                    "slot" : "PXI1Slot2"},
         "SMU_B" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot3"},
         "PSU_A" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot7"},
         "PSU_B" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot8"},
<<<<<<< Updated upstream
         #"Scope" : {"type" : "Oscilloscope",
         #           "io"   : "VISA",
         #           "resource" : "USB0::0x0957::0x1745::MY48080042::INSTR",
         #           "alias": "scope"},
        #  "AWG"   : {"type" : "AWG",
        #             "io"   : "VISA",
        #             "resource" : "GPIB1::10::INSTR"
                    }
        








=======
        #  "Scope" : {"type" : "Oscilloscope",
        #             "io"   : "VISA",
        #             "resource" : "USB0::0x0957::0x1745::MY48080042::INSTR",
        #             "alias": "scope"},
         "AWG"   : {"type" : "AWG",
                     "io"   : "VISA",
                     "resource" : "GPIB1::10::INSTR"
                    }
}
        
>>>>>>> Stashed changes

# Power distribtion
# //Note: names here are 1:1 as on the board (including upper/lowercase)
#   PSU-A => slot 7 as in cfg above; supplied level translators (VDDIO_LT@ch0, VCC_LT@ch1); P1 on flange
#   PSU-B => slot 8 as in cfg above; supplies ASIC (VDD_ASIC@ch0, VCC_ASIC@ch1); P2 on flange
#   SMU-A => slot 13 as in cfg above; provides vdda, vref, vdd12, ib2; J6 on flange
#   SMU-B => slot 14 as in cfg above; provides iterm_ts, ife, icharge, icomp; J7 on flange

V_SEQUENCE = [ "VCC_LT", "Vref", "Vdd12", "Ib2",  "vdda", "VDD_LVDS", "VDD_ASIC"] #"VddA"]

V_INSTR= {"vdda"      :   "SMU_A",
          #"Vref_adc" :   "SMU_A",
          "Vdd12"     :   "SMU_A",
          "Vref"      :   "SMU_A",
          "Ib2"       :   "SMU_A",
          "VDD_LVDS"  :   "PSU_B",
          #"VddA"      :   "PSU_B",          
          "VCC_LT"    :   "PSU_A",    
          "VDD_ASIC"  :   "PSU_A",
}

# V_INSTR = {"vdda" : SMU_A,
#            "VDD_LVDS" : PSU_B,
#            "VCC_LT" : PSU_A,   #On FLORA MB, called "VCC"
#            "VDD_ASIC" : PSU_A,      #On FLORA MB, called "Vd1"
#            "Vref" : SMU_A,
#            "Vdd12": SMU_A,
#            "Ib2"  : SMU_A}
#            #"Iterm":   SMU_B} NOTE: There is no Iterm needed for XR2 because all pixels are P1-flavor
           
V_CHAN = {
          #"Iterm":   3,
          "VCC_LT"  : 0,
          "VDD_ASIC": 1,
          "vdda"    : 2,
          "VDD_LVDS": 1,
          #"VddA"    : 0,
          "Ib2"     : 0,
          "Vref"    : 1,
          "Vdd12"   : 3
          #"VDDIO_LT":
          }

V_LEVEL = {
             "vdda"       :   2.5,
             "VDD_LVDS"   :   2.5,
             #"VddA"       :   1.2,
             "Vref"       :   1.0,
             "Vdd12"      :   1.2,
             "Ib2"        :   1.35,
             #"Iterm"     :   1.415,
             "VCC_LT"     :   2.5,
             "VDD_ASIC"   :   1.2            
           }

#Spacely will warn if the voltage falls outside this range.
V_WARN_VOLTAGE = {
             "vdda"     : [2.4, 2.6],
             "VDD_LVDS" : [2.4, 2.6],
             "Vref"     : [0.9, 1.1],
             "Vdd12"    : [1.1, 1.3],
             "Ib2"      : [1.25, 1.45],
             #"Iterm"   : 1.415,
             "VCC_LT"   : [2.4, 2.6],
             "VDD_ASIC" : [1.1, 1.3],
             #"VddA"     : [1.1, 1.3]           
           }

# Rough current guidelines
# TODO: TEST IF THESE VALUES IN DOCS BELOW ARE CORRECT OR WE'RE OFF IN UNITS IN THE DICT BELOW
#  - 100mA for vdda 
#  - 1mA for all other ASIC power rails
#  - 100mA for level translators (LT) power rails
#  - 10uA for others     
V_CURR_LIMIT = {
                  "vdda"      : 0.1,
                  "Vref"      : 0.00001,
                  "Vdd12"     : 0.00001,
                  #"Iterm"    : 0.00001,
                  "Ib2"       : 0.00001,
                  #"VDDIO_LT" : 0.1,                  
                  "VCC_LT"    : 0.3, #Changed from 0.1
                  "VDD_LVDS"  : 0.3,
                  "VCC_ASIC"  : 0.01,
                  "VDD_ASIC"  : 0.15, # this is correct: fixes latchup by giving the ASIC 100mA
                  #"VddA"      : 0.01 #for initial testing
                  }

#Global dict to hold the port objects created for each of these.
V_PORT = {"vdda"        : None, 
          "Vref"        : None, 
          "Vdd12"       : None, 
          "Ib2"         : None,
          #"Iterm"      : None,
          #"VDDIO_LT"   : None,   
          "VDD_ASIC"    : None,  
          "VDD_LVDS"    : None,
          #"VddA"        : None
<<<<<<< Updated upstream
=======
          "VCC_LT"      : None
>>>>>>> Stashed changes
         }

#Current Channels
I_SEQUENCE = ["Icomp", "Ife", "Icharge"]

# I_INSTR = {
#           "Iterm" :     "SMU_B",
#           "Ib1"   :     "SMU_B",
#           "Ibuf"  :     "SMU_B",
#           "Ib2"   :     "SMU_A",
#           "Icomp" :     "SMU_B"
#           }

I_INSTR = {
          #"Ib2"     :     "SMU_A",          
          "Ife"     :     "SMU_B",
          "Icharge" :     "SMU_B",
          "Icomp"   :     "SMU_B"
          }
<<<<<<< Updated upstream
I_CHAN  = {
          
=======

I_CHAN  = {      
>>>>>>> Stashed changes
          "Ife"     :   2,
          "Icharge" :   1,
          "Icomp"   :   0,
          #"Ib2"     :   0,
          }

I_LEVEL  = {
            #"Iterm":     80e-6,
            "Ife":      -35e-6,
            "Icharge":  -120e-6,
            "Icomp":    -20e-6
           }

I_WARN_VOLTAGE = {
            "Ife":      [0,2],
            "Icharge":  [0,2],
            "Icomp":    [0,2]
           }
            
I_PORT  = {
           "Ife":     None,
           "Icharge": None,
           "Icomp":   None
          }

I_VOLT_LIMIT = 2.5