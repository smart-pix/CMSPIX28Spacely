
#DEFAULT_IOSPEC = "./spacely-asic-config/SPROCKET3/SPROCKET3_iospec.txt"

INSTR = {"car" : {"type": "Caribou",
                  "host":"192.168.1.24",
                  "port":12345,
                  "device":"SpacelyCaribouBasic"}}




V_SEQUENCE = [] #"VDD", "VDDRX","VDDTX","VDD_refgen","vdda", "SFP_3V3_Cldbrd"]

"""
V_INSTR = {"vdda": "car",
           "VDD": "car",
           "VDDRX": "car",
           "VDDTX": "car",
           "VDD_refgen": "car",
           "SFP_3V3_Cldbrd":"car"}

V_CHAN = {"vdda": "PWR_OUT_2",
           "VDD": "PWR_OUT_3",
           "VDDRX": "PWR_OUT_4",
           "VDDTX": "PWR_OUT_1",
           "VDD_refgen": "PWR_OUT_5",
           "SFP_3V3_Cldbrd":"PWR_OUT_6"}

V_LEVEL = {"vdda": 2.5,
           "VDD": 1.3,
           "VDDRX": 1.2,
           "VDDTX": 1.4,
           "VDD_refgen": 1.2,
           "SFP_3V3_Cldbrd":3.3}

V_WARN_VOLTAGE = {"vdda": [2.4,2.6],
           "VDD": [1.1,1.3],
           "VDDRX": [1.1,1.3],
           "VDDTX": [1.1,1.3],
           "VDD_refgen":[1.1,1.3],
                  "SFP_3V3_Cldbrd":[3.1,3.5]}

V_PORT  = {"vdda": None,
           "VDD": None,
           "VDDRX": None,
           "VDDTX": None,
           "VDD_refgen": None,
           "SFP_3V3_Cldbrd":None}

"""