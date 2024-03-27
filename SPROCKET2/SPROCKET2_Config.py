
USE_ARDUINO = False
USE_NI = True
USE_AWG = True
USE_SCOPE = True



#INSTR_INIT_SEQUENCE = ["SMU_A", "SMU_B", "PSU_A", "PSU_B", "Scope", "AWG", "PSU_C"]



INSTR = {"SMU_A" : {"type" : "NIDCPower", 
                    "slot" : "PXI1Slot2"},
         "SMU_B" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot3"},
         "PSU_A" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot7"},
         "PSU_B" : {"type" : "NIDCPower",
                    "slot" : "PXI1Slot8"},
         "Scope" : {"type" : "Oscilloscope",
                    "io"   : "VISA",
                    "resource" : "USB0::0x0957::0x1745::MY48080042::INSTR"},
         "AWG"   : {"type" : "AWG",
                    "io"   : "VISA",
                    "resource" : "GPIB1::10::INSTR"
                    },
         "PSU_C" : {"type" : "Supply",
                    "io"   : "Prologix",
                    "ipaddr" : "192.168.1.15",
                    "gpibaddr" : 5}
        }
         
                    
                   



#SMU_A:None,
#         SMU_B:None,
#         PSU_A:None,
#         PSU_B:None}


#DEFAULT_OSCILLOSCOPE_RESOURCE = 

DEFAULT_FPGA_BITFILE_MAP = {"PXI1Slot4":"NI7972_NI6583_40MHz"}
DEFAULT_IOSPEC = ".\\spacely-asic-config\\SPROCKET2\\sprocket2_iospec.txt"

# AWG (Arbitrary Waverform Generator)
# 
# The AWG is controlled using an IP<>GPIB proxy (Prologix). It has an
# IP address (DEFAULT_PROLOGIX_IPADDR). The AWG has an address on the 
# GPIB bus itself (DEFAULT_AWG_GPIBADDR).
# When using Agilent gear, upon restarting, you should see an alert 
# saying "GPIB Interface Selected (Address 10)" - this is the GPIB
# address 
#DEFAULT_PROLOGIX_IPADDR = "192.168.1.15"
#DEFAULT_AWG_GPIBADDR = 10

#Emulation
EMULATE_ASIC = False

#CDAC Trimming
DEFAULT_CDAC_TRIMSTRING = "100000"

#Voltage Channels
#SMU A and B designations are from Scott's PCB.
#SMU_A = "PXI1Slot2"
#SMU_B = "PXI1Slot3"
#PSU_A = "PXI1Slot7" # PXI-4110 or 4111; CH0=0-6VDC, CH1=0-20V, CH2=-20V-0V
#PSU_B = "PXI1Slot8" # PXI-4110 or 4111; CH0=0-6VDC, CH1=0-20V, CH2=-20V-0V





#TO-DO:
# - Vref is supplied from an AWG, not an SMU.
# - Double-check whether currents should be positive or negative.


# Power distribtion
# //Note: names here are 1:1 as on the board (including upper/lowercase)
#   PSU-A => slot 7 as in cfg above; supplied level translators (VDDIO_LT@ch0, VCC_LT@ch1); P1 on flange
#   PSU-B => slot 8 as in cfg above; supplies ASIC (VDD_ASIC@ch0, VCC_ASIC@ch1); P2 on flange
#   SMU-A => slot 13 as in cfg above; provides vdda, vref, vdd12, ib2; J6 on flange
#   SMU-B => slot 14 as in cfg above; provides iterm_ts, ife, icharge, icomp; J7 on flange



#UPDATES FROM SPROCKET1:
# Vref_adc is taking the place of Vref (J3-10 to J6-5/J6-17), which corresponds to SMU_A, chan 1
# Vref_fe and Ibdig are supplied using an external power supply (so not on this list)
V_SEQUENCE = [ "VCC_LT", "VDDIO_LT", "Vref_adc", "Vdd12", "VDD_ASIC",    "vdda", "VCC_ASIC", "Vref_fe", "Ibdig"]
V_INSTR= {"vdda":   "SMU_A",
          "Vref_adc":   "SMU_A",
          "Vdd12":  "SMU_A",
          "VDDIO_LT": "PSU_A",          
          "VCC_LT":   "PSU_A",
          "VCC_ASIC": "PSU_B",            
          "VDD_ASIC": "PSU_B",
          "Vref_fe" : "PSU_C",
          "Ibdig"   : "PSU_C"}
V_CHAN = {# SMU_A
            "vdda": 0,            
            "Vref_adc":  1,
            "Vdd12": 2,
            
          # SMU_B => not used here; configured as current channels
          # PSU_A
            "VDDIO_LT": 0,
            "VCC_LT":   1,
          # PSU_B
            "VDD_ASIC": 0,
            "VCC_ASIC": 1,
          # PSU_C
            "Vref_fe" : "P6V",
            "Ibdig"   : "P25V"
         }

V_LEVEL = {# SMU_A
             "vdda": 2.5,
             "Vref_adc":  1.0,
             "Vdd12": 1.2,
             # PSU_A
             "VDDIO_LT": 1.2,                  
             "VCC_LT":   3.3,
             # PSU_B
             "VDD_ASIC": 1.35, #Boosted from 1.2V to account for PCB drop.
             "VCC_ASIC": 3.3 ,
             # PSU_C
             "Vref_fe" : 0.65,
             "Ibdig"   : 0.5
           }

           
V_WARN_VOLTAGE = {
             "vdda": [2.4,2.6],
             "Vref_adc" : [0.95,1.05],
             "Vref":  [0.9,1.1],
             "Vdd12": [1.1,1.3],
             #"Iterm":1.415,
             "VCC_LT":   [3.2,3.4],
             "VDD_ASIC": [1.3,1.4],
             "VCC_ASIC":   [3.2,3.4],
             "VDDIO_LT": [1.1,1.3]
             #"Vref_fe" : [0.6,0.7],
             #"Ibdig"   : [0.4,0.6]
           }


# Rough current guidelines
# TODO: TEST IF THESE VALUES IN DOCS BELOW ARE CORRECT OR WE'RE OFF IN UNITS IN THE DICT BELOW
#  - 100mA for vdda 
#  - 1mA for all other ASIC power rails
#  - 100mA for level translators (LT) power rails
#  - 10uA for others     
V_CURR_LIMIT = {# SMU_A
                  "vdda": 0.1,
                  "Vref_adc":  0.00001,
                  "Vdd12": 0.00001,
                # PSU_A
                  "VDDIO_LT": 0.1,                  
                  "VCC_LT":   0.3, #Changed from 0.1
                # PSU_B
                  "VCC_ASIC": 0.02, #Edit 11/15: Double currents to 20mA and 200mA for cryo.
                  "VDD_ASIC": 0.20, # this is correct: fixes latchup by giving the ASIC 100mA
                  "Vref_fe" : 0.1,
                  "Ibdig"   : 0.1
                  }

#Global dict to hold the port objects created for each of these.
V_PORT = {"vdda": None, # SMU_A
          "Vref_adc":  None, # SMU_A
          "Vdd12": None, # SMU_A
          "Ib2": None,
          "VDDIO_LT": None, # PSU_A                  
          "VCC_LT":   None, # PSU_A
          "VCC_ASIC": None, # PSU_B
          "VDD_ASIC": None,  # PSU_B  
          "Vref_fe" : None,
          "Ibdig"   : None
         }


#Current Channels
I_SEQUENCE = ["Icomp", "Ib1", "Ibuf", "Ib2", "Iterm"]
I_INSTR = {
          "Iterm":   "SMU_B",
          "Ib1":     "SMU_B",
          "Ibuf": "SMU_B",
          "Ib2":     "SMU_A",
          "Icomp":   "SMU_B"
          }
I_CHAN  = {
          "Iterm":   0,
          "Ib1":     1,
          "Ibuf": 2,
          "Ib2": 3,
          "Icomp":   3
          }

I_LEVEL  = {
            "Iterm":     80e-6,
            "Ib1":      -50e-6,
            "Ibuf":  -60e-6,
            "Ib2":   -10e-6,
            "Icomp":    -20e-6
           }
            
I_PORT  = {
           "Iterm":   None,
           "Ib1":     None,
           "Ibuf": None,
           "Ib2": None,
           "Icomp":   None
          }

I_VOLT_LIMIT = 2.5

I_WARN_VOLTAGE = {"Iterm": [1,2],
                  "Ib1":   [1,2],
                  "Ibuf":  [1,2],
                  "Ib2":   [1,2],
                  "Icomp": [1,2]}
