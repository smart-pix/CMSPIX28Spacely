

INSTR = {"car" : {"type": "Caribou",
                  "host":"192.168.1.24",
                  "port":12345,
                  "device":"SpacelyCaribouBasic"}}



V_SEQUENCE = ["vdda", "vddd", "VTH", "vleak","VTH0", "VMC", "SUPERPIX", "INJ_1"]

V_INSTR = {"vdda": "car",
           "vddd": "car",
           "VTH":"car",
           "vleak":"car",
           "VTH0":"car",
           "VMC":"car",
           "SUPERPIX":"car",
           "INJ_1": "car"}

V_CHAN = {"vdda": "PWR_OUT_4",
           "vddd": "PWR_OUT_3",
           "VTH":"BIAS_1",
           "vleak":"BIAS_3",
           "VTH0":"BIAS_5",
           "VMC":"BIAS_2",
           "SUPERPIX":"BIAS_4",
           "INJ_1":"INJ_1"}

V_LEVEL = {"vdda": 0.9,
           "vddd": 0.9,
           "VTH": 0.8,
            "vleak": 0,
            "VTH0": 0.04,
           "VMC": 0,
           "SUPERPIX":0.9,
           "INJ_1": 2
           }

V_WARN_VOLTAGE = {"vdda": [0.82,0.99],
           "vddd": [0.82,0.99]
      }

V_PORT  = {"vdda": None,
           "vddd": None,
           "VTH": None,
           "vleak": None,
           "VTH0": None,                      
           "VMC":None,
           "SUPERPIX":None,
           "INJ_1": None}

FNAL_SETTINGS = {
    "storageDirectory" : "/mnt/local/CMSPIX28/Scurve/data",
    "chipVersion" : 1,
    "chipID" : 4
}
