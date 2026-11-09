
INSTR = {"car" : {"type": "Caribou",
                  "host":"192.168.1.24",
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
              "Ibias"
]

I_SEQUENCE = [
              "Ileak",
              "OUTsink",
              "ThresholdOut",
              "ThresholdDown",
              "ThresholdUp",
              "Source1mA",
              "VlogSink1mA",
              "ISource10uA"
              ]

V_INSTR = {"vdda": "car",
           "vddd": "car",
           "vth0":"car",
           "vth1":"car",
           "vth2":"car",
           "VMC":"car",
           "SUPERPIX":"car",
           "INJ_1": "car",
           "Ibias": "car"
}

I_INSTR = {
           "Ileak": "car",
           "OUTsink": "car",
           "ThresholdOut": "car",
           "ThresholdDown": "car",
           "ThresholdUp": "car",
           "Source1mA": "car",
           "VlogSink1mA": "car",
           "ISource10uA": "car"
           }

V_CHAN = {"vdda": "PWR_OUT_1",
           "vddd": "PWR_OUT_2",
           "vth0":"BIAS_4",
           "vth1":"BIAS_3",
           "vth2":"BIAS_2",
           "VMC":"BIAS_1",
           "SUPERPIX":"BIAS_5",
           "INJ_1":"INJ_1",
           "Ibias":"BIAS_26"
}

I_CHAN = {
           "Ileak":"CUR_8",
           "OUTsink":"CUR_1",
           "ThresholdOut":"CUR_2",
           "ThresholdDown":"CUR_3",
           "ThresholdUp":"CUR_4",
           "Source1mA":"CUR_5",
           "VlogSink1mA":"CUR_6",
           "ISource10uA":"CUR_7"
           }

V_LEVEL = {"vdda": 0.9,
           "vddd": 0.9,
           "vth0": 0.031, #0.05 is 1000e-
           "vth1": 0.031, #0.08 is 1500e-
           "vth2": 0.031, #0.11 is 2000e-
           "VMC": 0.4,
           "SUPERPIX":0,
           "INJ_1": 2,
           "Ibias": 0.6            #TUNE TO have 5uW/pixel
}

I_LEVEL = {
           "Ileak": -0.00001,  # SINK 10uA
           "OUTsink": -0.00001, # SOURCE 10uA
           "ThresholdOut": -0.00001,
           "ThresholdDown": -0.00001,
           "ThresholdUp": -0.00001,
           "Source1mA": -0.00001,
           "VlogSink1mA": -0.00001,
           "ISource10uA": -0.00001
           }

V_WARN_VOLTAGE = {"vdda": [0.82,0.99],
           "vddd": [0.82,0.99],
           "vth0": [0,0.9],
           "vth1": [0,0.9],
           "vth2": [0,0.9],
           "VMC": [0,0.4],
           "SUPERPIX":[0,0.99],
           "INJ_1": [1.8,2.2],
           "Ibias": [0,0.9]
      }

V_PORT  = {"vdda": None,
           "vddd": None,
           "vth0": None,
           "vth1": None,
           "vth2": None,
           "VMC":None,
           "SUPERPIX":None,
           "INJ_1": None,
           "Ibias": None
}

I_PORT = {
           "Ileak": None,
           "OUTsink": None,
           "ThresholdOut": None,
           "ThresholdDown": None,
           "ThresholdUp": None,
           "Source1mA": None,
           "VlogSink1mA": None,
           "ISource10uA": None
           }

I_VOLT_LIMIT = {
              "Ileak": 0.01,
              "OUTsink": 0.01,
              "ThresholdOut": 0.01,
              "ThresholdDown": 0.01,
              "ThresholdUp": 0.01,
              "Source1mA": 0.01,
              "VlogSink1mA": 0.01,
              "ISource10uA": 0.01
    }

I_WARN_VOLTAGE = {
                "Ileak": [0,0.9],
              "OUTsink": [0,0.9],
              "ThresholdOut": [0,0.9],
              "ThresholdDown": [0,0.9],
              "ThresholdUp": [0,0.9],
              "Source1mA": [0,0.9],
              "VlogSink1mA": [0,0.9],
              "ISource10uA": [0,0.9]
      }


FNAL_SETTINGS = {
    "storageDirectory" : "/mnt/local/CMSPIX28/data",#"/home/bparpill/Documents/test_bench_2_output",#"/mnt/local/CMSPIX28/data/ChipVersion1_ChipID17_SuperPix1/Pnoise",#"/mnt/local/CMSPIX28/Scurve/data",#
    "chipVersion" : 1,
    "chipID" : 30
}


# ---------------------------------------------------------------------------
# Test bench timing profiles
# The only thing a user needs to change is TESTBENCH (or set the environment
# variable CMSPIX28_TB, e.g. CMSPIX28_TB=TB1). Every ROUTINE_* that takes these
# delays and is called without them picks them up from the profile below.
# Precedence: value passed on the call > USER_DELAY_OVERRIDES > TB_DELAYS.
# delayMode ("PG" pulse generator steps, "FW" 2.5 ns firmware steps) and base_delay (pulse generator delay [s] that
# the scans are an offset from, 0 ns of the scan) only apply to the delay scans (~r10 to ~r14, ~r16).
# In "FW" mode the scan sets the firmware injection_delay itself (0 to half a BxCLK period, pulse generator moved in
# half period blocks), so the injection_delay of the profile is not used by the delay scans.
# ---------------------------------------------------------------------------
import os as _os

TESTBENCH = _os.environ.get("CMSPIX28_TB", "TB1")

TB_DELAYS = {
    "TB2": dict(scan_load_delay='5',  startBxclkState='0', bxclk_delay='10', bxclk_period='28',
                injection_delay='5',  scanLoopBackBit='0', test_delay='14', scanLoadPhase='26',
                pulseGen='SDG7102A', delayMode='FW', base_delay=2.64e-6),
    "TB1": dict(scan_load_delay='19', startBxclkState='0', bxclk_delay='11', bxclk_period='28',
                injection_delay='1E', scanLoopBackBit='0', test_delay='14', scanLoadPhase='26',
                pulseGen='SDG7102A', delayMode='FW', base_delay=2.74e-6),
}

# Optional per-user tweaks on top of a test bench, keyed by login name then test bench, e.g.
# USER_DELAY_OVERRIDES = {"bparpill": {"TB2": dict(injection_delay='1F')}}
USER_DELAY_OVERRIDES = {}
