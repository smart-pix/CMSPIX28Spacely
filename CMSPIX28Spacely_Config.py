

INSTR = {"car" : {"type": "Caribou",
                  "host":"mud.uchicago.edu",
                  "port":12345,
                  "device":"SpacelyCaribouBasic"}}



V_SEQUENCE = ["vdda", 
              "vddd", 
              "vth0", 
              "vth1",
              "vth2", 
              "VMC", 
              "SUPERPIX", 
              "INJ_1",
              "Ibias",
              "disc0",
              "disc1",
]

I_SEQUENCE = [
        #       "Ileak", 
            #   "OUTsink",
            #   "ThresholdOut",
            #   "ThresholdDown",
            #   "ThresholdUp",
            #   "Source1mA",
            #   "VlogSink1mA"
              ]

V_INSTR = {"vdda": "car",
           "vddd": "car",
           "vth0":"car",
           "vth1":"car",
           "vth2":"car",
           "VMC":"car",
           "SUPERPIX":"car",
           "INJ_1": "car",
           "Ibias": "car",
           "disc0": "car",
           "disc1": "car",
}

I_INSTR = {
        #    "Ileak": "car",
        #    "OUTsink": "car",
        #    "ThresholdOut": "car",
        #    "ThresholdDown": "car",
        #    "ThresholdUp": "car",
        #    "Source1mA": "car",
        #    "VlogSink1mA": "car"
           }

V_CHAN = {"vdda": "PWR_OUT_1",
           "vddd": "PWR_OUT_2",
           "vth0":"BIAS_4",
           "vth1":"BIAS_3",
           "vth2":"BIAS_2",
           "VMC":"BIAS_1",
           "SUPERPIX":"BIAS_5",
           "INJ_1":"INJ_1",
           "Ibias":"BIAS_26",
           "disc0":"BIAS_7",
           "disc1":"BIAS_9",
}

I_CHAN = {
        #    "Ileak":"CUR_8",
        #    "OUTsink":"CUR_1",
        #    "ThresholdOut":"CUR_2",
        #    "ThresholdDown":"CUR_3",
        #    "ThresholdUp":"CUR_4",
        #    "Source1mA":"CUR_5",
        #    "VlogSink1mA":"CUR_6"
           }

V_LEVEL = {"vdda": 0.9,
           "vddd": 0.9,
           "vth0": 0.05,#0.031, #0.05 is 1000e-
           "vth1": 0.08,#0.031, #0.08 is 1500e-
           "vth2": 0.11,#0.031, #0.11 is 2000e-
           "VMC": 0.4,
           "SUPERPIX":0,#0.9,#0,
           "Ibias": 0.6,            #TUNE TO have 5uW/pixel
           "INJ_1": 2,
           "disc0":0,
           "disc1":0,
}

I_LEVEL = {
        #    "Ileak": 0.01,  # 10uA
        #    "OUTsink": 0,
        #    "ThresholdOut": 0,
        #    "ThresholdDown": 0,
        #    "ThresholdUp": 0,
        #    "Source1mA": 0,
        #    "VlogSink1mA": 0
           }

V_WARN_VOLTAGE = {"vdda": [0.82,0.99],
           "vddd": [0.82,0.99],
           "vth0": [0,0.4],
           "vth1": [0,0.4],
           "vth2": [0,0.4],
           "VMC": [0,0.4],
           "SUPERPIX":[0,0.99],
           "INJ_1": [1.8,2.2],
           "Ibias": [0,0.9],
           "disc0": [0,2],
           "disc1": [0,2],
      }

V_PORT  = {"vdda": None,
           "vddd": None,
           "vth0": None,
           "vth1": None,
           "vth2": None,                      
           "VMC":None,
           "SUPERPIX":None,
           "INJ_1": None,
           "Ibias": None,
           "disc0": None,
           "disc1": None,
}

I_PORT = {
        #    "Ileak": None,
        #    "OUTsink": None,
        #    "ThresholdOut": None,
        #    "ThresholdDown": None,
        #    "ThresholdUp": None,
        #    "Source1mA": None,
        #    "VlogSink1mA": None
           }

I_VOLT_LIMIT = {
            #   "Ileak": 0.01,
            #   "OUTsink": 0.01,
            #   "ThresholdOut": 0.01,
            #   "ThresholdDown": 0.01,
            #   "ThresholdUp": 0.01,
            #   "Source1mA": 0.01,
            #   "VlogSink1mA": 0.01
    }


FNAL_SETTINGS = {
    "storageDirectory" : "/local/d1/smartpixLab/scurveData", # "/mnt/local/CMSPIX28/data",#"/mnt/local/CMSPIX28/data/ChipVersion1_ChipID17_SuperPix1/Pnoise",#"/mnt/local/CMSPIX28/Scurve/data",#
    "chipVersion" : 1,
    "chipID" : 22,#16,
    "pixel_compout_csv" : "/local/d1/smartpixLab/filter/model_pipeline/tmp/923_1847_3695/compouts_ylocal_0.00_1.35.csv",
    "dnn_csv" : "/local/d1/smartpixLab/filter/model_pipeline/tmp/firmware/weights/b5_w5_b2_w2_pixel_bin.csv",
        
}

ROUTINE_SETTINGS_UC = {
    "configclk_period" : '64',
    "cfg_test_delay" : '5',
    "cfg_test_sample" :'20',
    "cfg_test_gate_config_clk" :'1',
    "scan_load_delay" : '19',#'13', #in some parts of the code, this is #superpix1 '1C', superpix2 '1E',
    "startBxclkState" : '0',
    "bxclk_delay" : '12',   #in some parts of the code, this is '11' for superpix 1 and '12' for superpixel 2
    "bxclk_period" : '28',
    "injection_delay" : 'c',# '1E', #original was '1E' in ~r3 and ~r6 and ~r7, but for some reason '1D' in ~r4 #in some parts of the code, #superpix1 '1C', superpix2 '1E',
    "scanLoopBackBit" : '0',
    "test_sample" : 'F',
    "test_delay" : '14',
    "scanLoadPhase" : '26', #in some parts of the code, this is  #superpix1 '25', superpix2 '26',
    "loopbackBit" : 0,
    "progResetMask" : '0', #seems only for DNN function and ROUTINE_DNN
    "configClkGate" : '0', #seems only for DNN function and ROUTINE_DNN

}

#TODO: Update for FNAL
ROUTINE_SETTINGS_FNAL = {
    "configclk_period" : '64',
    "cfg_test_delay" : '5',
    "cfg_test_sample" :'20',
    "cfg_test_gate_config_clk" :'1',
    "scan_load_delay" : '19',#'13', #in some parts of the code, this is #superpix1 '1C', superpix2 '1E',
    "startBxclkState" : '0',
    "bxclk_delay" : '12',   #in some parts of the code, this is '11' for superpix 1 and '12' for superpixel 2
    "bxclk_period" : '28',
    "injection_delay" : 'c',# '1E', #original was '1E' in ~r3 and ~r6 and ~r7, but for some reason '1D' in ~r4 #in some parts of the code, #superpix1 '1C', superpix2 '1E',
    "scanLoopBackBit" : '0',
    "test_sample" : 'F',
    "test_delay" : '14',
    "scanLoadPhase" : '26', #in some parts of the code, this is  #superpix1 '25', superpix2 '26',
    "loopbackBit" : 0,
    "progResetMask" : '0', #seems only for DNN function and ROUTINE_DNN
    "configClkGate" : '0', #seems only for DNN function and ROUTINE_DNN
}

#TODO: Update for Cornell
ROUTINE_SETTINGS_CORNELL = {
    "configclk_period" : '64',
    "cfg_test_delay" : '5',
    "cfg_test_sample" :'20',
    "cfg_test_gate_config_clk" :'1',
    "scan_load_delay" : '19',#'13', #in some parts of the code, this is #superpix1 '1C', superpix2 '1E',
    "startBxclkState" : '0',
    "bxclk_delay" : '12',   #in some parts of the code, this is '11' for superpix 1 and '12' for superpixel 2
    "bxclk_period" : '28',
    "injection_delay" : 'c',# '1E', #original was '1E' in ~r3 and ~r6 and ~r7, but for some reason '1D' in ~r4 #in some parts of the code, #superpix1 '1C', superpix2 '1E',
    "scanLoopBackBit" : '0',
    "test_sample" : 'F',
    "test_delay" : '14',
    "scanLoadPhase" : '26', #in some parts of the code, this is  #superpix1 '25', superpix2 '26',
    "loopbackBit" : 0,
    "progResetMask" : '0', #seems only for DNN function and ROUTINE_DNN
    "configClkGate" : '0', #seems only for DNN function and ROUTINE_DNN
}


#Set it to FNAL or Cornell when using those test stands
ROUTINE_SETTINGS=ROUTINE_SETTINGS_UC
