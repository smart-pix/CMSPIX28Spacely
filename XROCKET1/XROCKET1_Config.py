
USE_ARDUINO = False
USE_NI = True
USE_AWG = True


DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot16":"NI7972_NI6583_40MHz"}

DEFAULT_PROLOGIX_IPADDR = "192.168.1.15"
DEFAULT_AWG_GPIBADDR = 10

#CDAC Trimming
DEFAULT_CDAC_TRIMSTRING = "100000"

DEFAULT_IOSPEC = ".\\asic_config\\XROCKET1\\xrocket1_iospec.txt"


#Voltage Channels
#SMU A and B designations are from Scott's PCB.
SMU_A = "PXI1Slot13"
SMU_B = "PXI1Slot14"
PSU_A = "PXI1Slot7" # PXI-4110 or 4111; CH0=0-6VDC, CH1=0-20V, CH2=-20V-0V
PSU_B = "PXI1Slot8" # PXI-4110 or 4111; CH0=0-6VDC, CH1=0-20V, CH2=-20V-0V



#On the FLORA Motherboard,
# SMU_A -> J2   SMU_B -> J3
# PSU_A -> J8   PSU_B -> J24

INSTR_INIT_SEQUENCE = [SMU_A, SMU_B, PSU_A, PSU_B]
INSTR = {SMU_A:None,
         SMU_B:None,
         PSU_A:None,
         PSU_B:None}









# Power distribtion
# //Note: names here are 1:1 as on the board (including upper/lowercase)
#   PSU-A => slot 7 as in cfg above; supplied level translators (VDDIO_LT@ch0, VCC_LT@ch1); P1 on flange
#   PSU-B => slot 8 as in cfg above; supplies ASIC (VDD_ASIC@ch0, VCC_ASIC@ch1); P2 on flange
#   SMU-A => slot 13 as in cfg above; provides vdda, vref, vdd12, ib2; J6 on flange
#   SMU-B => slot 14 as in cfg above; provides iterm_ts, ife, icharge, icomp; J7 on flange

V_SEQUENCE = [ "VCC_LT", "Vref", "Vdd12", "VDD_ASIC",  "Ib2", "Iterm", "vdda", "VDD_LVDS"]


V_INSTR = {"vdda" : SMU_A,
           "VDD_LVDS" : PSU_B,
           "VCC_LT" : PSU_A,   #On FLORA MB, called "VCC"
           "VDD_ASIC" : PSU_A,      #On FLORA MB, called "Vd1"
           "Vref" : SMU_A,
           "Vdd12": SMU_A,
           "Ib2"  : SMU_A,
           "Iterm":   SMU_B}
            #NOTE: In this ASIC, unlike SPROCKET1-TestPixel, Iterm is a voltage source
                    #because Iterm_ts was not bonded out, so we are faking it w/ a Vsource.
           

V_CHAN = {
          "Iterm":   3,
          "VCC_LT"  : 0,
          "VDD_ASIC": 1,
          "vdda"    : 2,
          "VDD_LVDS": 1,
          "Ib2"     : 0,
          "Vref"    : 1,
          "Vdd12"   : 3,
          }


V_LEVEL = {
             "vdda": 2.5,
             "VDD_LVDS" : 2.5,
             "Vref":  1.0,
             "Vdd12": 1.2,
             "Ib2": 1.35,
             "Iterm":1.415,
             "VCC_LT":   2.5,
             "VDD_ASIC": 1.2            
           }

#Spacely will warn if the voltage falls outside this range.
V_WARN_VOLTAGE = {
             "vdda": [2.4,2.6],
             "VDD_LVDS" : [2.4,2.6],
             "Vref":  [0.9,1.1],
             "Vdd12": [1.1,1.3],
             "Ib2": [1.25,1.45],
             "Iterm": [1.35,1.45],
             "VCC_LT":   [3.2,3.4],
             "VDD_ASIC": [1.1,1.3]           
           }

# Rough current guidelines
# TODO: TEST IF THESE VALUES IN DOCS BELOW ARE CORRECT OR WE'RE OFF IN UNITS IN THE DICT BELOW
#  - 100mA for vdda 
#  - 1mA for all other ASIC power rails
#  - 100mA for level translators (LT) power rails
#  - 10uA for others     
V_CURR_LIMIT = {
                  "vdda": 0.1,
                  "Vref":  0.00001,
                  "Vdd12": 0.00001,
                  "Iterm": 0.00001,
                  "Ib2": 0.00001,
                  "VDDIO_LT": 0.1,                  
                  "VCC_LT":   0.3, #Changed from 0.1
                  "VDD_LVDS": 0.3,
                  "VCC_ASIC": 0.01,
                  "VDD_ASIC": 0.10 # this is correct: fixes latchup by giving the ASIC 100mA
                  }

#Global dict to hold the port objects created for each of these.
V_PORT = {"vdda": None, 
          "Vref":  None, 
          "Vdd12": None, 
          "Ib2": None,
          "Iterm":None,
          "VDDIO_LT": None,   
          "VDD_ASIC": None,  
          "VDD_LVDS" : None
         }


#Current Channels
I_SEQUENCE = ["Icomp", "Ife", "Icharge"]
I_INSTR = {
          
          "Ife":     SMU_B,
          "Icharge": SMU_B,
          "Icomp":   SMU_B
          }
I_CHAN  = {
          
          "Ife":     2,
          "Icharge": 1,
          "Icomp":   0
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

