

INSTR = {"car" : {"type": "Caribou",
                  "host":"192.168.1.24",
                  "port":12345,
                  "device":"SpacelyCaribouBasic"}}



V_SEQUENCE = ["vdda", "vddd", "VTH2", "VTH1","VTH0", "VMC", "SUPERPIX", "INJ_1"]

V_INSTR = {"vdda": "car",
           "vddd": "car",
           "VTH2":"car",
           "VTH1":"car",
           "VTH0":"car",
           "VMC":"car",
           "SUPERPIX":"car",
           "INJ_1": "car"}

V_CHAN = {"vdda": "PWR_OUT_4",
           "vddd": "PWR_OUT_3",
           "VTH2":"BIAS_1",
           "VTH1":"BIAS_3",
           "VTH0":"BIAS_5",
           "VMC":"BIAS_2",
           "SUPERPIX":"BIAS_4",
           "INJ_1":"INJ_1"}

V_LEVEL = {"vdda": 0.9,
           "vddd": 0.9,
           "VTH2": 1,
            "VTH1": 0.04,
            "VTH0": 0.04,
           "VMC": 0.4,
           "SUPERPIX":0,
           "INJ_1": 2
           }

V_WARN_VOLTAGE = {"vdda": [0.82,0.99],
           "vddd": [0.82,0.99]
      }

V_PORT  = {"vdda": None,
           "vddd": None,
           "VTH2": None,
           "VTH1": None,
           "VTH0": None,                      
           "VMC":None,
           "SUPERPIX":None,
           "INJ_1": None}
