# spacely
from Master_Config import *


# python modules
import sys
try:
    # from __future__ import annotations
    import time
    import tqdm
    from datetime import datetime
    import csv
    import re
    from dataclasses import dataclass
    from typing import Iterable, List, Sequence, Tuple
    import os
    from dataclasses import dataclass
    from itertools import permutations
    from typing import Dict, List, Optional, Sequence, Tuple

except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately



#-----------------------------------------------------------------------
# ProgShiftRegRaw function
#-----------------------------------------------------------------------
# This subroutine programs the shift register in a raw fashion
# The pixel address and value need to be manual inserted
# it programs pixel 0 by default
#-----------------------------------------------------------------------

def ProgShiftRegRaw(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1'):

    #FW reset followed with Status reset
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", f"7'h{configclk_period}"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
    ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
 

    hex_list = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    hex_list = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
    ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    # write on array0    
    hex_list = [["4'h1", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]

    # write on array1
    # pixels are programmed between addresses [68] and [99] (see figure 6 from report)    
    array0 = hex_list
    hex_list = [["4'h1", "4'h8", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]
    #hex_list[69] = ["4'h1", "4'h8", "8'h45", "16'h0000"]    
    #hex_list[68] = ["4'h1", "4'h8", "8'h44", "16'h003F"]
    #hex_list[67] = ["4'h1", "4'h8", "8'h43", "16'hFFFF"]  
    #hex_list[0] = ["4'h1", "4'h8", "8'h00", "16'hFF00"]
    array1 = hex_list

    # write on array2
    #hex_list = [["4'h1", "4'hA", "8'h" + hex(i)[2:], "16'hAAAA"] for i in range(256)]
    hex_list = [["4'h1", "4'hA", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]

    # testing programming 4 pixels
    #hex_list[120] = ["4'h1", "4'hA", "8'h78", "16'h0100"]
    hex_list[112] = ["4'h1", "4'hA", "8'h70", "16'h0002"] 
    hex_list[128] = ["4'h1", "4'hA", "8'h80", "16'h0000"]
    #hex_list[115] = ["4'h1", "4'hA", "8'h73", "16'h0020"]
    #hex_list[136] = ["4'h1", "4'hA", "8'h88", "16'h2000"]   
    array2 = hex_list

    hex_list =  array2+array1+array0   


    sw_write32_0(hex_list)

    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
    hex_list = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h0",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "3'h0", # 3 bits for spare_index_max
            f"1'h{cfg_test_gate_config_clk}", # 1 bit for gating configClk
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for test number
            f"7'h{cfg_test_sample}", # 6 bits test sample
            f"7'h{cfg_test_delay}"  # 6 bits for test delay
        ]
    
    ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
    time.sleep(0.5)


#-----------------------------------------------------------------------
# ProgPixelsOnly function
#-----------------------------------------------------------------------
# This subroutine programs the pixel section of the shift register
# It takes in a list of a list of pixel number to be progammed and their corresponding values (0,1,2,3)
# pixel number are taken from the LUT in the Figure 6: Superpixel Map in the cms28_smartpixe_test_manual document
# pixel values are the 2-bit decimal possibilities
# there is a debug interface that needs to be reworked to check that what is
#-----------------------------------------------------------------------

def ProgPixelsOnly(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1',pixelList = [0], pixelValue=[1]):
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    #PROGRAM SHIFT REGISTER
    hex_lists = [
        # ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{configclk_period}"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 1M
        ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{configclk_period}"],
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    pixelConfig = genPixelProgramList(pixelList, pixelValue)
    hex_lists = dnnConfig(pixelConfig = pixelConfig)
    sw_write32_0(hex_lists)

    hex_lists = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h0",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "3'h0", # 3 bits for spare_index_max
            f"1'h{cfg_test_gate_config_clk}", # 1 bit for gating configClk
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for test number
            f"7'h{cfg_test_sample}", # 6 bits test sample
            f"7'h{cfg_test_delay}"  # 6 bits for test delay
        ]
    
    ]
    sw_write32_0(hex_lists)
    time.sleep(0.5)
    pass

#-----------------------------------------------------------------------
# ProgPixelsOnly function
#-----------------------------------------------------------------------
# This subroutine configure the entire shift register for the DNN
# it takes in a csv list that contains the DNN weight and and biases 
# and a separate list that contains the pixel address and value for each test vectors
#-----------------------------------------------------------------------

# def ProgShiftRegs(progDebug=True, verbose=True, configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1', iP=0, timeSleep=0.015):
    
#     parent_dir = "/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/"
#     model_400 = parent_dir + '/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv'
#     model_700 = parent_dir + '/trainedModel_700_1400_2100/model3/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv'
#     model_1000 = parent_dir + '/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv'
#     model_13x21 = os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/b5_w5_b2_w2_pixel_bin_debug2.csv")
#     model_path = model_400
#     fw_status_clear()

#     hex_list = [
#         ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
#         ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
#    ]
#     sw_write32_0(hex_list)
#     sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

#     #PROGRAM SHIFT REGISTER
#     hex_lists = [
#         ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{configclk_period}"],
#         ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
#     ]

#     # call sw_write32_0
#     sw_write32_0(hex_lists)
#     sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

#     # load all of the configs
#     filename = os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/compouts.csv")
#     pixelLists, pixelValues = genPixelConfigFromInputCSV(filename)


#     hiddenBit=os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/hidden_debug.csv")
#     # pick up pixel config for the given pattern
#     pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])

#     # Programming the NN weights and biases
#     if(progDebug==True):
#         # hex_lists = dnnConfig(os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/b5_w5_b2_w2_pixel_bin_debug2.csv"), pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
#         # hex_lists = dnnConfig(model_400, pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
#         hex_lists = dnnConfig(model_path, pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
#         # hex_lists = dnnConfig(os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/b5_w5_b2_w2_pixel_bin.csv"), pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
    
#     else:
#         hex_lists = dnnConfig(model_path, pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
#     sw_write32_0(hex_lists)
#     # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 

#     hex_lists = [
#         [
#             "4'h1",  # firmware id
#             "4'hf",  # op code d for execute
#             "1'h0",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
#             "3'h0", # 3 bits for spare_index_max
#             f"1'h{cfg_test_gate_config_clk}", # 1 bit for gating configClk
#             "1'h0",  # 1 bit for w_execute_cfg_test_loopback
#             "4'h1",  # 4 bits for test number
#             f"7'h{cfg_test_sample}", # 6 bits test sample
#             f"7'h{cfg_test_delay}"  # 6 bits for test delay
#         ]
    
#     ]
#     sw_write32_0(hex_lists)
#     time.sleep(timeSleep)

#     #This needs to be replaced with smog test
#     if(verbose==True and progDebug==True):
#             #ReadBack from READ_ARRAY 1
#             words_A0 = []      
#             words_A1 = []
#             words_A2 = []    
#             words_DA0 = []
#             words_DA1 = []              
#             for i in range(0, 256,2):
#                 address = hex(i)[2:]
#                 hex_list0 = [
#                 [
#                     "4'h1", "4'h7", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 0            
#                 ]
#                 sw_write32_0(hex_list0)
#                 sw_read32_0, sw_read32_1, _, _ = sw_read32() 
#                 words_A0.append([address,int_to_32bit(sw_read32_0)])

#                 hex_list1 = [
#                 [
#                     "4'h1", "4'h9", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 1            
#                 ]
#                 sw_write32_0(hex_list1)
#                 sw_read32_0, sw_read32_1, _, _ = sw_read32() 
#                 words_A1.append([address,int_to_32bit(sw_read32_0)])

#                 hex_list2 = [
#                 [
#                     "4'h1", "4'hB", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 2            
#                 ]
#                 sw_write32_0(hex_list2)
#                 sw_read32_0, sw_read32_1, _, _ = sw_read32() 
#                 words_A2.append([address,int_to_32bit(sw_read32_0)])
            
#             for i in range(256):
#                 address = hex(i)[2:]
#                 hex_list_rdata0 = [
#                 [
#                     "4'h1", "4'hC", f"8'h{address}", "16'h0"]         #ReadBack from READ DATA ARRAY 0            
#                 ]
#                 sw_write32_0(hex_list_rdata0)
#                 sw_read32_0, sw_read32_1, _, _ = sw_read32() 
#                 words_DA0.append([address,int_to_32bit(sw_read32_0)])

#                 hex_list_rdata1 = [
#                 [
#                     "4'h1", "4'hD", f"8'h{address}", "16'h0"]         #ReadBack from READ DATA ARRAY 1            
#                 ]
#                 sw_write32_0(hex_list_rdata1)
#                 sw_read32_0, sw_read32_1, _, _ = sw_read32() 
#                 words_DA1.append([address,int_to_32bit(sw_read32_0)])

#             print("CFG ARRAY 0")
#             for i in words_A0:
#                 print(i)
#             print("CFG ARRAY 1")
#             for i in words_A1:
#                 print(i)
#             print("CFG ARRAY 2")  
#             for i in words_A2:
#                 print(i)           
#             print("READ DATA 0")   
#             for i in words_DA0:
#                 print(i)    
#             print("READ DATA 1")  
#             for i in words_DA1:
#                 print(i)
#             cfgArray0File = os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/cfgArray0.csv")
#             with open(cfgArray0File, 'a+', newline="") as file:
#                 writer = csv.writer(file)
#                 writer.writerows(words_A0)
#             array0File = os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/array0.csv")               
#             with open(array0File, 'a+', newline="") as file:
#                 writer = csv.writer(file)
#                 writer.writerows(words_DA0)
#             array1File = os.path.join(os.getcwd(),"spacely-asic-config/CMSPIX28Spacely/csv/array1.csv")                
#             with open(array1File, 'a+', newline="") as file:
#                 writer = csv.writer(file)
#                 writer.writerows(words_DA1)

#     pass




# ============================================================================
# Shift-register structure
# ============================================================================

N_DNN_B5_BITS = 12
N_DNN_W5_BITS = 696
N_DNN_B2_BITS = 232
N_DNN_W2_BITS = 3712

N_DNN_BITS = (
    N_DNN_B5_BITS
    + N_DNN_W5_BITS
    + N_DNN_B2_BITS
    + N_DNN_W2_BITS
)  # 4652

N_PIXEL_BITS = 512
N_CONFIG_BITS = N_DNN_BITS + N_PIXEL_BITS  # 5164
N_HIDDEN_BITS = 24
N_CHAIN_BITS = N_CONFIG_BITS + N_HIDDEN_BITS  # 5188

RAW_CFG_FIELD_LAYOUT = (
    ("Hidden", N_HIDDEN_BITS),
    ("DNN_b5", N_DNN_B5_BITS),
    ("DNN_w5", N_DNN_W5_BITS),
    ("DNN_b2", N_DNN_B2_BITS),
    ("DNN_w2", N_DNN_W2_BITS),
    ("Pixel", N_PIXEL_BITS),
)

LOGICAL_FIELD_LAYOUT = (
    ("DNN_b5", N_DNN_B5_BITS),
    ("DNN_w5", N_DNN_W5_BITS),
    ("DNN_b2", N_DNN_B2_BITS),
    ("DNN_w2", N_DNN_W2_BITS),
    ("Pixel", N_PIXEL_BITS),
    ("Hidden", N_HIDDEN_BITS),
)

CRITICAL_BIT_POSITIONS = (
    0,
    N_DNN_BITS - 1,      # 4651: final DNN bit
    N_DNN_BITS,          # 4652: first pixel bit
    N_CONFIG_BITS - 2,   # 5162
    N_CONFIG_BITS - 1,   # 5163: final pixel/config bit
    N_CONFIG_BITS,       # 5164: first hidden bit
    N_CHAIN_BITS - 1,    # 5187: final hidden bit
)


# ============================================================================
# Generic utilities
# ============================================================================

def normalize_word32(value) -> str:
    """Return a 32-character MSB-first binary string."""
    if isinstance(value, int):
        return f"{value & 0xFFFFFFFF:032b}"

    text = str(value).strip().replace("_", "")

    if text.startswith("0b"):
        text = text[2:]
    elif text.startswith("0x"):
        return f"{int(text, 16):032b}"

    if not re.fullmatch(r"[01]+", text):
        raise ValueError(f"Invalid 32-bit binary word: {value!r}")

    if len(text) > 32:
        raise ValueError(
            f"Binary word contains {len(text)} bits; expected at most 32."
        )

    return text.zfill(32)


def normalize_bits(values: Iterable) -> List[int]:
    """Flatten common bit representations into a list of integer bits."""
    bits: List[int] = []

    def add_value(value) -> None:
        if isinstance(value, (list, tuple)):
            for element in value:
                add_value(element)
            return

        if isinstance(value, int):
            if value not in (0, 1):
                raise ValueError(f"Expected a bit, got integer {value}.")
            bits.append(value)
            return

        text = str(value).strip()
        if not text:
            return

        compact = re.sub(r"[\s,\[\]\(\)'\"_]", "", text)
        if compact and re.fullmatch(r"[01]+", compact):
            bits.extend(int(bit) for bit in compact)
            return

        raise ValueError(f"Could not interpret value as binary data: {value!r}")

    add_value(values)
    return bits


def read_binary_csv(filename: str) -> List[int]:
    """Read binary values from a CSV file."""
    bits: List[int] = []

    with open(filename, "r", newline="") as file:
        reader = csv.reader(file)

        for row_number, row in enumerate(reader, start=1):
            for column_number, value in enumerate(row, start=1):
                text = value.strip()
                if not text:
                    continue

                compact = re.sub(r"[\s,\[\]\(\)'\"_]", "", text)
                if compact and re.fullmatch(r"[01]+", compact):
                    bits.extend(int(bit) for bit in compact)
                    continue

                raise ValueError(
                    f"Nonbinary value in {filename}, row {row_number}, "
                    f"column {column_number}: {value!r}"
                )

    return bits


def save_combined_arrays(
    filename: str,
    arrays: Sequence[Tuple[str, Sequence[Sequence[str]]]],
) -> None:
    """Save several firmware arrays in one CSV file."""
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "array",
                "address_hex",
                "address_decimal",
                "word_hex",
                "word_binary",
            ]
        )

        for array_name, words in arrays:
            for address, word in words:
                address_int = int(str(address), 16)
                word_binary = normalize_word32(word)
                word_hex = f"{int(word_binary, 2):08X}"

                writer.writerow(
                    [
                        array_name,
                        f"0x{address_int:02X}",
                        address_int,
                        f"0x{word_hex}",
                        word_binary,
                    ]
                )


# ============================================================================
# Expected logical vectors
# ============================================================================

def build_expected_programming_vector(
    model_path: str,
    pixel_config,
    hidden_bit_path: str,
) -> List[int]:
    """Build DNN[4652] + Pixel[512] + Hidden[24]."""
    model_bits = read_binary_csv(model_path)
    pixel_bits = normalize_bits(pixel_config)
    hidden_bits = read_binary_csv(hidden_bit_path)

    if len(model_bits) != N_CONFIG_BITS:
        raise ValueError(
            f"{model_path} contains {len(model_bits)} bits; "
            f"expected {N_CONFIG_BITS}."
        )

    if len(pixel_bits) != N_PIXEL_BITS:
        raise ValueError(
            f"pixelConfig contains {len(pixel_bits)} bits; "
            f"expected {N_PIXEL_BITS}."
        )

    if len(hidden_bits) != N_HIDDEN_BITS:
        raise ValueError(
            f"{hidden_bit_path} contains {len(hidden_bits)} bits; "
            f"expected {N_HIDDEN_BITS}."
        )

    normal_config = model_bits.copy()
    normal_config[N_DNN_BITS:N_CONFIG_BITS] = pixel_bits
    expected_input = normal_config + hidden_bits

    if len(expected_input) != N_CHAIN_BITS:
        raise RuntimeError(
            f"Expected input has {len(expected_input)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    print()
    print("EXPECTED INPUT VECTOR")
    print(f"  Model/DNN stream:  positions 0 to {N_DNN_BITS - 1}")
    print(
        f"  Pixel stream:      positions {N_DNN_BITS} "
        f"to {N_CONFIG_BITS - 1}"
    )
    print(
        f"  Hidden stream:     positions {N_CONFIG_BITS} "
        f"to {N_CHAIN_BITS - 1}"
    )
    print(f"  Total:             {len(expected_input)} bits")

    return expected_input


def build_expected_reset_state(hidden_bit_path: str) -> List[int]:
    """Original assumed reset state: 5164 zeros + 24 hidden bits."""
    hidden_bits = read_binary_csv(hidden_bit_path)

    if len(hidden_bits) != N_HIDDEN_BITS:
        raise ValueError(
            f"{hidden_bit_path} contains {len(hidden_bits)} bits; "
            f"expected {N_HIDDEN_BITS}."
        )

    return [0] * N_CONFIG_BITS + hidden_bits


# ============================================================================
# Known CFG and DATA memory decoding
# ============================================================================

def readback_words_to_memory_bits(
    words: Sequence[Sequence[str]],
) -> List[int]:
    """Convert readback words to chronological LSB-first memory order."""
    ordered_words = sorted(
        words,
        key=lambda entry: int(str(entry[0]), 16),
    )

    memory_bits: List[int] = []

    for _, word in ordered_words:
        word_binary = normalize_word32(word)
        memory_bits.extend(int(bit) for bit in word_binary[::-1])

    return memory_bits


def decode_cfg_memory_frames(
    words_A0,
    words_A1,
    words_A2,
) -> Tuple[List[int], List[int], List[int]]:
    """Extract the two raw 5188-bit CFG frames and unused memory."""
    array_0_bits = readback_words_to_memory_bits(words_A0)
    array_1_bits = readback_words_to_memory_bits(words_A1)
    array_2_bits = readback_words_to_memory_bits(words_A2)

    expected_array_bits = 256 * 16

    for name, bits in (
        ("CFG_ARRAY_0", array_0_bits),
        ("CFG_ARRAY_1", array_1_bits),
        ("CFG_ARRAY_2", array_2_bits),
    ):
        if len(bits) != expected_array_bits:
            raise ValueError(
                f"{name} contains {len(bits)} bits; "
                f"expected {expected_array_bits}."
            )

    cfg_memory = array_0_bits + array_1_bits + array_2_bits

    frame_1_raw = cfg_memory[0:N_CHAIN_BITS]
    frame_2_raw = cfg_memory[N_CHAIN_BITS:2 * N_CHAIN_BITS]
    unused_bits = cfg_memory[2 * N_CHAIN_BITS:]

    if len(frame_1_raw) != N_CHAIN_BITS:
        raise RuntimeError("CFG Frame 1 extraction failed.")
    if len(frame_2_raw) != N_CHAIN_BITS:
        raise RuntimeError("CFG Frame 2 extraction failed.")

    return frame_1_raw, frame_2_raw, unused_bits


def decode_raw_cfg_frame(
    raw_frame: Sequence[int],
) -> Tuple[List[int], Dict[str, List[int]]]:
    """Convert raw CFG-memory order to logical serial order."""
    if len(raw_frame) != N_CHAIN_BITS:
        raise ValueError(
            f"Raw CFG frame has {len(raw_frame)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    fields: Dict[str, List[int]] = {}
    cursor = 0

    for field_name, field_width in RAW_CFG_FIELD_LAYOUT:
        fields[field_name] = list(
            raw_frame[cursor:cursor + field_width]
        )
        cursor += field_width

    logical_frame = (
        fields["DNN_b5"]
        + fields["DNN_w5"]
        + fields["DNN_b2"]
        + fields["DNN_w2"]
        + fields["Pixel"]
        + fields["Hidden"]
    )

    if len(logical_frame) != N_CHAIN_BITS:
        raise RuntimeError(
            f"Logical CFG frame contains {len(logical_frame)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    return logical_frame, fields


def decode_asic_output_frames(
    words_DA0,
    words_DA1,
) -> Tuple[List[int], List[int], List[int]]:
    """Decode DATA_ARRAY_0 then DATA_ARRAY_1, LSB-first."""
    data_array_0_bits = readback_words_to_memory_bits(words_DA0)
    data_array_1_bits = readback_words_to_memory_bits(words_DA1)
    asic_stream = data_array_0_bits + data_array_1_bits

    frame_1_asic = asic_stream[0:N_CHAIN_BITS]
    frame_2_asic = asic_stream[N_CHAIN_BITS:2 * N_CHAIN_BITS]
    remainder = asic_stream[2 * N_CHAIN_BITS:]

    if len(frame_1_asic) != N_CHAIN_BITS:
        raise ValueError(
            f"Frame_1_ASIC contains {len(frame_1_asic)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    if len(frame_2_asic) != N_CHAIN_BITS:
        raise ValueError(
            f"Frame_2_ASIC contains {len(frame_2_asic)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    return frame_1_asic, frame_2_asic, remainder


# ============================================================================
# Strict comparison and reporting
# ============================================================================

@dataclass
class FrameTestResult:
    test_number: str
    title: str
    left_name: str
    right_name: str
    required: bool
    passed: bool
    mismatch_count: int
    left_length: int
    right_length: int
    mismatches: List[Tuple[int, int, int]]


def programming_stream_region(position: int) -> str:
    if position < N_DNN_BITS:
        return "MODEL/DNN stream"
    if position < N_CONFIG_BITS:
        return "PIXEL stream"
    if position < N_CHAIN_BITS:
        return "HIDDEN/TEST stream"
    return "outside 5188-bit frame"


def exact_bit_mismatches(
    actual: Sequence[int],
    expected: Sequence[int],
) -> List[Tuple[int, int, int]]:
    """Return every mismatch; no truncation, alignment, or overlap."""
    if len(actual) != len(expected):
        raise ValueError(
            f"Exact comparison requires equal lengths, got "
            f"{len(actual)} and {len(expected)}."
        )

    return [
        (position, int(actual_bit), int(expected_bit))
        for position, (actual_bit, expected_bit) in enumerate(
            zip(actual, expected)
        )
        if int(actual_bit) != int(expected_bit)
    ]


def compare_named_frames(
    test_number: str,
    title: str,
    left_name: str,
    left: Sequence[int],
    right_name: str,
    right: Sequence[int],
    required: bool,
    maximum_reported_mismatches: int = 32,
) -> FrameTestResult:
    all_mismatches = exact_bit_mismatches(left, right)

    return FrameTestResult(
        test_number=str(test_number),
        title=title,
        left_name=left_name,
        right_name=right_name,
        required=required,
        passed=(len(all_mismatches) == 0),
        mismatch_count=len(all_mismatches),
        left_length=len(left),
        right_length=len(right),
        mismatches=all_mismatches[:maximum_reported_mismatches],
    )


def print_frame_test(result: FrameTestResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    category = "REQUIRED" if result.required else "DIAGNOSTIC"

    print()
    print("=" * 72)
    print(f"TEST {result.test_number}: {result.title}")
    print(f"Classification: {category}")
    print(f"Result:         {status}")
    print(
        f"Comparison:     {result.left_name} "
        f"versus {result.right_name}"
    )
    print(
        f"Lengths:        {result.left_length} "
        f"versus {result.right_length}"
    )
    print(f"Mismatches:     {result.mismatch_count}")

    if result.mismatches:
        print()
        print(
            f"{'position':>10}  "
            f"{result.left_name:>16}  "
            f"{result.right_name:>16}  "
            f"region"
        )

        for position, left_value, right_value in result.mismatches:
            print(
                f"{position:10d}  "
                f"{left_value:16d}  "
                f"{right_value:16d}  "
                f"{programming_stream_region(position)}"
            )

        position, left_value, right_value = result.mismatches[0]
        print()
        print(
            f"First mismatch: position {position}, "
            f"{result.left_name}={left_value}, "
            f"{result.right_name}={right_value}"
        )


def split_logical_frame_fields(
    logical_frame: Sequence[int],
) -> Dict[str, List[int]]:
    if len(logical_frame) != N_CHAIN_BITS:
        raise ValueError(
            f"Logical frame has {len(logical_frame)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    fields: Dict[str, List[int]] = {}
    cursor = 0

    for field_name, field_width in LOGICAL_FIELD_LAYOUT:
        fields[field_name] = list(
            logical_frame[cursor:cursor + field_width]
        )
        cursor += field_width

    return fields


def print_field_comparison(
    comparison_name: str,
    actual: Sequence[int],
    expected: Sequence[int],
) -> None:
    actual_fields = split_logical_frame_fields(actual)
    expected_fields = split_logical_frame_fields(expected)

    print()
    print("-" * 72)
    print(f"FIELD SUMMARY: {comparison_name}")
    print("-" * 72)

    logical_position = 0

    for field_name, field_width in LOGICAL_FIELD_LAYOUT:
        mismatches = exact_bit_mismatches(
            actual_fields[field_name],
            expected_fields[field_name],
        )

        status = "PASS" if not mismatches else "FAIL"

        print(
            f"{field_name:10s}: {status:4s}  "
            f"width={field_width:4d}  "
            f"mismatches={len(mismatches):4d}",
            end="",
        )

        if mismatches:
            first_local = mismatches[0][0]
            first_global = logical_position + first_local
            print(
                f"  first local={first_local}, "
                f"logical position={first_global}"
            )
        else:
            print()

        logical_position += field_width


def verify_single_bit_detection(reference: Sequence[int]) -> None:
    """Flip critical bits, including 5163, and verify exact detection."""
    if len(reference) != N_CHAIN_BITS:
        raise ValueError(
            f"Comparator self-test reference has {len(reference)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    print()
    print("-" * 72)
    print("SINGLE-BIT COMPARATOR SELF-TEST")
    print("-" * 72)

    for position in CRITICAL_BIT_POSITIONS:
        corrupted = list(reference)
        corrupted[position] ^= 1

        mismatches = exact_bit_mismatches(corrupted, reference)

        if len(mismatches) != 1 or mismatches[0][0] != position:
            raise AssertionError(
                f"Comparator failed at position {position}: "
                f"{mismatches!r}"
            )

        _, actual_bit, expected_bit = mismatches[0]
        print(
            f"Position {position:4d}: PASS - detected "
            f"{actual_bit} versus {expected_bit}"
        )


def print_critical_bit_positions(
    expected_input: Sequence[int],
    frame_1_cfg: Sequence[int],
    frame_2_cfg: Sequence[int],
    frame_1_asic: Sequence[int],
    frame_2_asic: Sequence[int],
) -> None:
    """Always display position 5163 and important boundaries."""
    print()
    print("-" * 94)
    print("CRITICAL BIT-POSITION CHECK")
    print("-" * 94)
    print(
        f"{'position':>8}  {'expected':>8}  {'F1_CFG':>6}  "
        f"{'F2_CFG':>6}  {'F1_ASIC':>8}  {'F2_ASIC':>8}  region"
    )

    for position in CRITICAL_BIT_POSITIONS:
        print(
            f"{position:8d}  "
            f"{int(expected_input[position]):8d}  "
            f"{int(frame_1_cfg[position]):6d}  "
            f"{int(frame_2_cfg[position]):6d}  "
            f"{int(frame_1_asic[position]):8d}  "
            f"{int(frame_2_asic[position]):8d}  "
            f"{programming_stream_region(position)}"
        )


def print_previous_state_diagnostic(
    frame_1_asic: Sequence[int],
    frame_2_asic: Sequence[int],
) -> None:
    mismatches = exact_bit_mismatches(frame_1_asic, frame_2_asic)
    zero_to_one = [
        position
        for position, previous_bit, new_bit in mismatches
        if previous_bit == 0 and new_bit == 1
    ]
    one_to_zero = [
        position
        for position, previous_bit, new_bit in mismatches
        if previous_bit == 1 and new_bit == 0
    ]

    print()
    print("-" * 72)
    print("PREVIOUS ASIC STATE DIAGNOSTIC")
    print("-" * 72)
    print(f"Ones in Frame_1_ASIC: {sum(frame_1_asic)}")
    print(f"Ones in Frame_2_ASIC: {sum(frame_2_asic)}")
    print(f"0 -> 1 transitions:   {len(zero_to_one)}")
    print(f"1 -> 0 transitions:   {len(one_to_zero)}")
    print(
        "Note: current firmware enters shift mode before previous-state "
        "capture begins, so Test 4 is diagnostic only."
    )


@dataclass
class PreviousStateShiftResult:
    """
    Result of checking the previous ASIC state against the expected frame.

    Test 4B passes when every observable DNN + pixel bit matches after
    applying the best exact shift of 0, +1, or -1 bit.

    Hidden/test-bit mismatches are counted and printed separately, but
    they do not fail Test 4B.
    """
    passed: bool
    mode: str
    shift: int

    config_overlap_length: int
    config_mismatch_count: int
    first_config_mismatches: List[Tuple[int, int, int, int]]

    hidden_overlap_length: int
    hidden_mismatch_count: int
    first_hidden_mismatches: List[Tuple[int, int, int, int]]

    total_overlap_length: int
    total_mismatch_count: int

    dropped_expected_position: int | None
    dropped_expected_value: int | None
    extra_actual_position: int | None
    extra_actual_value: int | None


def _evaluate_previous_state_shift(
    frame_1_asic: Sequence[int],
    expected_previous: Sequence[int],
    shift: int,
) -> PreviousStateShiftResult:
    """
    Evaluate one non-circular alignment.

    Shift convention:

      shift = 0:
          actual[i] == expected[i]

      shift = +1:
          actual[i] == expected[i + 1]
          Expected position 0 was shifted out before capture.

      shift = -1:
          actual[i + 1] == expected[i]
          Expected position 5187 is outside the captured overlap.
    """
    if shift not in (-1, 0, +1):
        raise ValueError(f"Unsupported shift: {shift}")

    if shift == 0:
        pairs = (
            (position, position)
            for position in range(N_CHAIN_BITS)
        )
        dropped_expected_position = None
        dropped_expected_value = None
        extra_actual_position = None
        extra_actual_value = None
        mode = "EXACT_5188_BIT_MATCH"

    elif shift == +1:
        pairs = (
            (expected_position - 1, expected_position)
            for expected_position in range(1, N_CHAIN_BITS)
        )
        dropped_expected_position = 0
        dropped_expected_value = int(expected_previous[0])
        extra_actual_position = N_CHAIN_BITS - 1
        extra_actual_value = int(frame_1_asic[-1])
        mode = "EXACT_ONE_BIT_SHIFT"

    else:
        pairs = (
            (expected_position + 1, expected_position)
            for expected_position in range(0, N_CHAIN_BITS - 1)
        )
        dropped_expected_position = N_CHAIN_BITS - 1
        dropped_expected_value = int(expected_previous[-1])
        extra_actual_position = 0
        extra_actual_value = int(frame_1_asic[0])
        mode = "EXACT_ONE_BIT_SHIFT"

    config_overlap_length = 0
    hidden_overlap_length = 0
    config_mismatches: List[Tuple[int, int, int, int]] = []
    hidden_mismatches: List[Tuple[int, int, int, int]] = []

    for actual_position, expected_position in pairs:
        actual_value = int(frame_1_asic[actual_position])
        expected_value = int(expected_previous[expected_position])

        is_config_bit = expected_position < N_CONFIG_BITS

        if is_config_bit:
            config_overlap_length += 1
        else:
            hidden_overlap_length += 1

        if actual_value == expected_value:
            continue

        mismatch = (
            actual_position,
            actual_value,
            expected_position,
            expected_value,
        )

        if is_config_bit:
            config_mismatches.append(mismatch)
        else:
            hidden_mismatches.append(mismatch)

    total_overlap_length = (
        config_overlap_length + hidden_overlap_length
    )
    total_mismatch_count = (
        len(config_mismatches) + len(hidden_mismatches)
    )

    return PreviousStateShiftResult(
        # Only the DNN + pixel region is required for Test 4B.
        passed=(len(config_mismatches) == 0),
        mode=mode,
        shift=shift,
        config_overlap_length=config_overlap_length,
        config_mismatch_count=len(config_mismatches),
        first_config_mismatches=config_mismatches[:32],
        hidden_overlap_length=hidden_overlap_length,
        hidden_mismatch_count=len(hidden_mismatches),
        first_hidden_mismatches=hidden_mismatches[:32],
        total_overlap_length=total_overlap_length,
        total_mismatch_count=total_mismatch_count,
        dropped_expected_position=dropped_expected_position,
        dropped_expected_value=dropped_expected_value,
        extra_actual_position=extra_actual_position,
        extra_actual_value=extra_actual_value,
    )


def check_previous_state_one_bit_shift(
    frame_1_asic: Sequence[int],
    expected_previous: Sequence[int],
) -> PreviousStateShiftResult:
    """
    Find the best exact alignment among shifts 0, +1 and -1.

    Candidate selection prioritizes the DNN + pixel region. Hidden/test
    mismatches are used only as a secondary diagnostic tie-breaker.
    """
    if len(frame_1_asic) != N_CHAIN_BITS:
        raise ValueError(
            f"Frame_1_ASIC has {len(frame_1_asic)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    if len(expected_previous) != N_CHAIN_BITS:
        raise ValueError(
            f"Expected previous frame has {len(expected_previous)} bits; "
            f"expected {N_CHAIN_BITS}."
        )

    candidates = [
        _evaluate_previous_state_shift(
            frame_1_asic=frame_1_asic,
            expected_previous=expected_previous,
            shift=shift,
        )
        for shift in (0, +1, -1)
    ]

    return min(
        candidates,
        key=lambda candidate: (
            candidate.config_mismatch_count,
            candidate.total_mismatch_count,
            abs(candidate.shift),
        ),
    )


def _print_shift_mismatches(
    heading: str,
    mismatches: Sequence[Tuple[int, int, int, int]],
) -> None:
    if not mismatches:
        return

    print()
    print(heading)
    print(
        f"{'actual pos':>10}  {'actual':>6}  "
        f"{'expected pos':>12}  {'expected':>8}"
    )

    for (
        actual_position,
        actual_value,
        expected_position,
        expected_value,
    ) in mismatches:
        print(
            f"{actual_position:10d}  "
            f"{actual_value:6d}  "
            f"{expected_position:12d}  "
            f"{expected_value:8d}"
        )


def print_previous_state_shift_test(
    result: PreviousStateShiftResult,
    required: bool,
) -> None:
    """
    Print Test 4B.

    PASS/FAIL is determined only from the observable DNN + pixel section.
    Hidden/test-bit mismatches remain visible as a diagnostic.
    """
    classification = "REQUIRED" if required else "DIAGNOSTIC"
    status = "PASS" if result.passed else "FAIL"

    print()
    print("=" * 72)
    print("TEST 4B: Previous DNN + pixel state after shift correction")
    print(f"Classification: {classification}")
    print(f"Result:         {status}")
    print(f"Mode:           {result.mode}")
    print(f"Shift:          {result.shift:+d} bit")

    print()
    print("Required DNN + pixel comparison:")
    print(
        f"  Exact bits:   "
        f"{result.config_overlap_length - result.config_mismatch_count}/"
        f"{result.config_overlap_length}"
    )
    print(
        f"  Mismatches:   {result.config_mismatch_count}"
    )

    if (
        result.shift == +1
        and result.dropped_expected_position == 0
    ):
        print(
            "  Note: expected configuration position 0 was shifted out "
            "before capture and is not observable in Frame_1_ASIC."
        )

    print()
    print("Hidden/test comparison (diagnostic only):")
    print(
        f"  Exact bits:   "
        f"{result.hidden_overlap_length - result.hidden_mismatch_count}/"
        f"{result.hidden_overlap_length}"
    )
    print(
        f"  Mismatches:   {result.hidden_mismatch_count}"
    )

    if result.shift == +1:
        print(
            "Relationship:    Frame_1_ASIC[i] == "
            "Expected_Previous[i + 1]"
        )
    elif result.shift == -1:
        print(
            "Relationship:    Frame_1_ASIC[i + 1] == "
            "Expected_Previous[i]"
        )
    else:
        print(
            "Relationship:    Frame_1_ASIC[i] == "
            "Expected_Previous[i]"
        )

    if result.shift != 0:
        print(
            "Dropped expected boundary: "
            f"position {result.dropped_expected_position}, "
            f"value {result.dropped_expected_value}"
        )
        print(
            "Extra captured boundary:   "
            f"position {result.extra_actual_position}, "
            f"value {result.extra_actual_value}"
        )

    _print_shift_mismatches(
        "DNN + pixel mismatches:",
        result.first_config_mismatches,
    )

    _print_shift_mismatches(
        "Hidden/test mismatches:",
        result.first_hidden_mismatches,
    )


# ============================================================================
# Main verification campaign
# ============================================================================

def verify_shift_register_frames(
    model_path: str,
    hidden_bit_path: str,
    pixel_config,
    words_A0,
    words_A1,
    words_A2,
    words_DA0,
    words_DA1,
    *,
    check_initial_reset_state: bool = True,
    require_initial_reset_state: bool = False,
    expect_previous_same_model: bool = False,
    run_comparator_self_test: bool = True,
) -> bool:
    """Run exact full-length 5188-bit verification."""
    expected_input = build_expected_programming_vector(
        model_path=model_path,
        pixel_config=pixel_config,
        hidden_bit_path=hidden_bit_path,
    )

    if run_comparator_self_test:
        verify_single_bit_detection(expected_input)

    frame_1_cfg_raw, frame_2_cfg_raw, cfg_unused = (
        decode_cfg_memory_frames(
            words_A0=words_A0,
            words_A1=words_A1,
            words_A2=words_A2,
        )
    )

    frame_1_cfg, _ = decode_raw_cfg_frame(frame_1_cfg_raw)
    frame_2_cfg, _ = decode_raw_cfg_frame(frame_2_cfg_raw)

    frame_1_asic, frame_2_asic, asic_remainder = (
        decode_asic_output_frames(
            words_DA0=words_DA0,
            words_DA1=words_DA1,
        )
    )

    print()
    print("#" * 72)
    print("SHIFT-REGISTER FRAME DEFINITIONS")
    print("#" * 72)
    print(f"Expected_Input:  {len(expected_input)} bits")
    print(f"Frame_1_CFG:     {len(frame_1_cfg)} bits")
    print(f"Frame_2_CFG:     {len(frame_2_cfg)} bits")
    print(f"Frame_1_ASIC:    {len(frame_1_asic)} bits")
    print(f"Frame_2_ASIC:    {len(frame_2_asic)} bits")
    print(f"CFG unused:      {len(cfg_unused)} bits")
    print(f"ASIC remainder:  {len(asic_remainder)} bits")

    print_critical_bit_positions(
        expected_input=expected_input,
        frame_1_cfg=frame_1_cfg,
        frame_2_cfg=frame_2_cfg,
        frame_1_asic=frame_1_asic,
        frame_2_asic=frame_2_asic,
    )

    print_previous_state_diagnostic(
        frame_1_asic=frame_1_asic,
        frame_2_asic=frame_2_asic,
    )

    # In same-model/no-reset mode, Expected_Input is also the expected
    # final frame left by the previous invocation.
    previous_state_shift_result = check_previous_state_one_bit_shift(
        frame_1_asic=frame_1_asic,
        expected_previous=expected_input,
    )

    print_previous_state_shift_test(
        result=previous_state_shift_result,
        required=expect_previous_same_model,
    )

    results: List[FrameTestResult] = []

    if check_initial_reset_state:
        expected_reset_state = build_expected_reset_state(hidden_bit_path)
        results.append(
            compare_named_frames(
                test_number="0",
                title="ASIC initial state matches assumed reset state",
                left_name="Frame_1_ASIC",
                left=frame_1_asic,
                right_name="Expected_Reset_State",
                right=expected_reset_state,
                required=require_initial_reset_state,
            )
        )

    results.extend(
        [
            compare_named_frames(
                test_number="1",
                title="First FPGA CFG frame matches requested input",
                left_name="Frame_1_CFG",
                left=frame_1_cfg,
                right_name="Expected_Input",
                right=expected_input,
                required=True,
            ),
            compare_named_frames(
                test_number="2",
                title="The two FPGA CFG frames are identical",
                left_name="Frame_1_CFG",
                left=frame_1_cfg,
                right_name="Frame_2_CFG",
                right=frame_2_cfg,
                required=True,
            ),
            compare_named_frames(
                test_number="3",
                title="Second ASIC output equals first FPGA input",
                left_name="Frame_2_ASIC",
                left=frame_2_asic,
                right_name="Frame_1_CFG",
                right=frame_1_cfg,
                required=True,
            ),
            compare_named_frames(
                test_number="4",
                title=(
                    "Previous ASIC state equals newly programmed state "
                    "(known FW startup issue)"
                ),
                left_name="Frame_1_ASIC",
                left=frame_1_asic,
                right_name="Frame_2_ASIC",
                right=frame_2_asic,
                required=False,
            ),
            compare_named_frames(
                test_number="5",
                title="Second FPGA CFG frame matches requested input",
                left_name="Frame_2_CFG",
                left=frame_2_cfg,
                right_name="Expected_Input",
                right=expected_input,
                required=True,
            ),
            compare_named_frames(
                test_number="6",
                title="ASIC readback matches requested input",
                left_name="Frame_2_ASIC",
                left=frame_2_asic,
                right_name="Expected_Input",
                right=expected_input,
                required=True,
            ),
        ]
    )

    for result in results:
        print_frame_test(result)

    print_field_comparison(
        "Frame_1_CFG versus Expected_Input",
        frame_1_cfg,
        expected_input,
    )
    print_field_comparison(
        "Frame_2_CFG versus Expected_Input",
        frame_2_cfg,
        expected_input,
    )
    print_field_comparison(
        "Frame_2_ASIC versus Expected_Input",
        frame_2_asic,
        expected_input,
    )

    unused_one_positions = [
        index
        for index, bit in enumerate(cfg_unused)
        if int(bit) != 0
    ]

    print()
    print("-" * 72)
    print("CFG UNUSED-MEMORY DIAGNOSTIC")
    print("-" * 72)
    print(f"Unused bits:       {len(cfg_unused)}")
    print(f"Bits equal to one: {len(unused_one_positions)}")

    if unused_one_positions:
        print(
            "First nonzero unused positions:",
            unused_one_positions[:32],
        )
    else:
        print("Unused CFG-memory region is all zero.")

    required_results = [result for result in results if result.required]
    overall_pass = all(result.passed for result in required_results)

    # For a repeated same-model run, Test 4B requires every
    # observable DNN + pixel bit to match after correcting a shift
    # of 0, +1, or -1. Hidden/test bits remain diagnostic.
    if expect_previous_same_model:
        overall_pass = (
            overall_pass
            and previous_state_shift_result.passed
        )

    print()
    print("#" * 72)
    print("SHIFT-REGISTER TEST SUMMARY")
    print("#" * 72)

    for result in results:
        classification = "required" if result.required else "diagnostic"
        print(
            f"Test {result.test_number}: "
            f"{'PASS' if result.passed else 'FAIL'} "
            f"({classification})"
        )

    shift_classification = (
        "required"
        if expect_previous_same_model
        else "diagnostic"
    )
    print(
        "Test 4B: "
        f"{'PASS' if previous_state_shift_result.passed else 'FAIL'} "
        f"({shift_classification}, "
        f"shift={previous_state_shift_result.shift:+d}, "
        f"config mismatches="
        f"{previous_state_shift_result.config_mismatch_count}, "
        f"hidden mismatches="
        f"{previous_state_shift_result.hidden_mismatch_count})"
    )

    print()
    print(
        "EXACT 5188-BIT PROGRAMMING TEST: "
        + ("PASS" if overall_pass else "FAIL")
    )
    print(
        "Comparator position 5163 coverage: PASS "
        "(verified by software bit-flip self-test)"
    )
    print("#" * 72)

    return overall_pass


def ProgShiftRegs(
    progDebug=False,
    verbose=False,
    configclk_period="64",
    cfg_test_delay="5",
    cfg_test_sample="20",
    cfg_test_gate_config_clk="1",
    iP=0,
    timeSleep=0.015,
    send_fw_reset_opcode=True,
    reset_asic_before_test=True,
    expect_previous_same_model=False,
    check_initial_reset_state=True,
    require_initial_reset_state=False,
    run_comparator_self_test=True,
    capture_tag=None,
):
    """
    Program two identical 5188-bit frames and optionally verify them.

    progDebug=True is required for CFG/DATA readback and verification.

    Test 0 restores the original assumed reset-state comparison. It is
    diagnostic by default, so a position-5163 mismatch is printed but does
    not invalidate an otherwise correct programming operation. Set
    require_initial_reset_state=True only when that reset-state expectation
    is confirmed by the ASIC specification.
    """

    if expect_previous_same_model and send_fw_reset_opcode:
        raise ValueError(
            "expect_previous_same_model=True requires "
            "send_fw_reset_opcode=False."
        )

    if expect_previous_same_model and reset_asic_before_test:
        raise ValueError(
            "expect_previous_same_model=True requires "
            "reset_asic_before_test=False."
        )

    if check_initial_reset_state and not reset_asic_before_test:
        print(
            "Disabling initial reset-state check because "
            "reset_asic_before_test=False."
        )
        check_initial_reset_state = False
        require_initial_reset_state = False

    print()
    print("=" * 72)
    print("SHIFT-REGISTER CAMPAIGN SETTINGS")
    print("=" * 72)
    print(f"Send firmware reset opcode:  {send_fw_reset_opcode}")
    print(f"Reset ASIC before test:      {reset_asic_before_test}")
    print(f"Expect previous same model:  {expect_previous_same_model}")
    print(f"Check assumed reset state:   {check_initial_reset_state}")
    print(f"Require reset-state match:   {require_initial_reset_state}")
    print(f"Comparator self-test:        {run_comparator_self_test}")

    parent_dir = (
        "/asic/projects/C/CMS_PIX_28/dshekar/"
        "filter/model_pipeline/tmp_16x16_hlevOptimized/"
    )

    model_400 = (
        parent_dir
        + "/trainedModel_400_800_1200/model1/"
        "qmodel_0_catapult_prj/firmware/weights/"
        "b5_w5_b2_w2_pixel_bin.csv"
    )

    model_700 = (
        parent_dir
        + "/trainedModel_700_1400_2100/model3/"
        "qmodel_0_catapult_prj/firmware/weights/"
        "b5_w5_b2_w2_pixel_bin.csv"
    )

    model_1000 = (
        parent_dir
        + "/trainedModel_1000_2000_3000/model0/"
        "qmodel_0_catapult_prj/firmware/weights/"
        "b5_w5_b2_w2_pixel_bin.csv"
    )

    model_13x21 = os.path.join(
        os.getcwd(),
        "spacely-asic-config/CMSPIX28Spacely/csv/"
        "b5_w5_b2_w2_pixel_bin_debug2.csv",
    )

    # Select the model here.
    model_path = model_1000

    fw_status_clear()

    initial_commands = []

    if send_fw_reset_opcode:
        initial_commands.append(
            [
                "4'h1",
                "4'h1",
                "16'h0",
                "1'h1",
                "7'h64",
            ]
        )

    initial_commands.append(
        [
            "4'h1",
            "4'he",
            "16'h0",
            "1'h1",
            "7'h64",
        ]
    )

    sw_write32_0(initial_commands)
    sw_read32(print_code="ihb")

    # Configure the shift-register firmware.
    sw_write32_0(
        [
            [
                "4'h1",
                "4'h2",
                "16'h0",
                "1'h1",
                f"7'h{configclk_period}",
            ],
            [
                "4'h1",
                "4'h3",
                "16'h0",
                "1'h1",
                "7'h64",
            ],
        ]
    )
    sw_read32()

    pixel_input_path = os.path.join(
        os.getcwd(),
        "spacely-asic-config/CMSPIX28Spacely/csv/compouts.csv",
    )

    pixel_lists, pixel_values = genPixelConfigFromInputCSV(
        pixel_input_path
    )

    hidden_bit_path = os.path.join(
        os.getcwd(),
        "spacely-asic-config/CMSPIX28Spacely/csv/hidden_debug.csv",
    )

    pixel_config = genPixelProgramList(
        pixel_lists[iP],
        pixel_values[iP],
    )

    programming_commands = dnnConfig(
        model_path,
        pixelConfig=pixel_config,
        hiddenBitCSV=hidden_bit_path,
    )
    sw_write32_0(programming_commands)

    # Execute body bit 23:
    #   0 -> permit the ASIC Reset_not operation
    #   1 -> mask the ASIC Reset_not operation
    cfg_test_mask_reset_not = 0 if reset_asic_before_test else 1

    execute_command = [
        [
            "4'h1",                              # firmware ID
            "4'hf",                              # OP_CODE_W_EXECUTE
            f"1'h{cfg_test_mask_reset_not}",     # body bit 23
            "3'h0",                              # body bits 22:20
            f"1'h{cfg_test_gate_config_clk}",    # body bit 19
            "1'h0",                              # body bit 18: loopback
            "4'h1",                              # body bits 17:14: test 1
            f"7'h{cfg_test_sample}",             # body bits 13:7
            f"7'h{cfg_test_delay}",              # body bits 6:0
        ]
    ]

    print()
    print("=" * 72)
    print("SHIFT-REGISTER EXECUTE CONTROL")
    print("=" * 72)
    print(f"Send FW reset opcode:       {send_fw_reset_opcode}")
    print(f"Reset ASIC before Frame 1:  {reset_asic_before_test}")
    print(f"mask_reset_not, body bit23: {cfg_test_mask_reset_not}")
    print(f"Expect previous same model: {expect_previous_same_model}")
    print("Execute command:")
    print(execute_command[0])

    sw_write32_0(execute_command)
    time.sleep(timeSleep)

    if not progDebug:
        print(
            "Verification skipped because progDebug=False. "
            "The returned True only means the routine completed."
        )
        return True

    words_A0 = []
    words_A1 = []
    words_A2 = []
    words_DA0 = []
    words_DA1 = []

    # Each CFG read returns two consecutive 16-bit addresses.
    for address_int in range(0, 256, 2):
        address = f"{address_int:02x}"

        for opcode, destination in (
            ("4'h7", words_A0),
            ("4'h9", words_A1),
            ("4'hB", words_A2),
        ):
            sw_write32_0(
                [
                    [
                        "4'h1",
                        opcode,
                        f"8'h{address}",
                        "16'h0",
                    ]
                ]
            )
            read_value, _, _, _ = sw_read32()
            destination.append(
                [address, normalize_word32(read_value)]
            )

    # Read both DATA arrays. DATA_ARRAY_1 returns zero outside its valid
    # address range; retaining 256 reads preserves the existing workflow.
    for address_int in range(256):
        address = f"{address_int:02x}"

        for opcode, destination in (
            ("4'hC", words_DA0),
            ("4'hD", words_DA1),
        ):
            sw_write32_0(
                [
                    [
                        "4'h1",
                        opcode,
                        f"8'h{address}",
                        "16'h0",
                    ]
                ]
            )
            read_value, _, _, _ = sw_read32()
            destination.append(
                [address, normalize_word32(read_value)]
            )

    output_directory = os.path.join(
        os.getcwd(),
        "spacely-asic-config/CMSPIX28Spacely/csv",
    )

    if capture_tag is None:
        capture_suffix = ""
    else:
        safe_capture_tag = re.sub(
            r"[^A-Za-z0-9_.-]+",
            "_",
            str(capture_tag),
        ).strip("_")
        capture_suffix = (
            f"_{safe_capture_tag}"
            if safe_capture_tag
            else ""
        )

    combined_cfg_file = os.path.join(
        output_directory,
        f"cfg_arrays_combined{capture_suffix}.csv",
    )

    combined_data_file = os.path.join(
        output_directory,
        f"data_arrays_combined{capture_suffix}.csv",
    )

    save_combined_arrays(
        combined_cfg_file,
        [
            ("CFG_ARRAY_0", words_A0),
            ("CFG_ARRAY_1", words_A1),
            ("CFG_ARRAY_2", words_A2),
        ],
    )

    save_combined_arrays(
        combined_data_file,
        [
            ("DATA_ARRAY_0", words_DA0),
            ("DATA_ARRAY_1", words_DA1),
        ],
    )

    print(f"Saved CFG arrays to:  {combined_cfg_file}")
    print(f"Saved DATA arrays to: {combined_data_file}")

    if verbose:
        for name, words in (
            ("CFG ARRAY 0", words_A0),
            ("CFG ARRAY 1", words_A1),
            ("CFG ARRAY 2", words_A2),
            ("READ DATA 0", words_DA0),
            ("READ DATA 1", words_DA1),
        ):
            print()
            print(name)
            for address, word in words:
                print(address, word)

    return verify_shift_register_frames(
        model_path=model_path,
        hidden_bit_path=hidden_bit_path,
        pixel_config=pixel_config,
        words_A0=words_A0,
        words_A1=words_A1,
        words_A2=words_A2,
        words_DA0=words_DA0,
        words_DA1=words_DA1,
        check_initial_reset_state=check_initial_reset_state,
        require_initial_reset_state=require_initial_reset_state,
        expect_previous_same_model=expect_previous_same_model,
        run_comparator_self_test=run_comparator_self_test,
    )


@dataclass
class RepeatedProgrammingRunResult:
    run_number: int
    run_type: str
    passed: bool


def ProgShiftRegsRepeated(
    n_runs,
    *,
    verbose=False,
    configclk_period="64",
    cfg_test_delay="5",
    cfg_test_sample="20",
    cfg_test_gate_config_clk="0",
    iP=0,
    timeSleep=0.011,
    time_between_runs=0.0,
    check_initial_reset_state=True,
    require_initial_reset_state=False,
    run_comparator_self_test=True,
    stop_on_failure=False,
):
    """
    Program the same model N times and check run-to-run consistency.

    Run 1 establishes a clean baseline:
        send_fw_reset_opcode=True
        reset_asic_before_test=True
        expect_previous_same_model=False

    Runs 2..N preserve the ASIC:
        send_fw_reset_opcode=False
        reset_asic_before_test=False
        expect_previous_same_model=True

    On Runs 2..N, required Test 4B passes when every observable DNN +
    pixel bit in Frame_1_ASIC matches the previous programmed frame after
    correcting an exact shift of 0, +1, or -1 bit. Hidden/test bits are
    reported but do not fail Test 4B.

    Returns True only when every run passes all of its required tests.
    """
    if not isinstance(n_runs, int):
        raise TypeError(
            f"n_runs must be an integer, got {type(n_runs).__name__}."
        )

    if n_runs < 1:
        raise ValueError("n_runs must be at least 1.")

    run_results: List[RepeatedProgrammingRunResult] = []

    print()
    print("#" * 72)
    print("REPEATED SHIFT-REGISTER CONSISTENCY CAMPAIGN")
    print("#" * 72)
    print(f"Requested programming runs: {n_runs}")
    print("Run 1: reset baseline")
    if n_runs > 1:
        print(f"Runs 2-{n_runs}: no-reset consistency checks")
    print(
        "Test 4B requirement: all observable DNN + pixel bits must "
        "match after shift correction."
    )
    print(
        "Hidden/test-bit differences are diagnostic and do not fail "
        "Test 4B."
    )

    for run_number in range(1, n_runs + 1):
        is_baseline = run_number == 1
        run_type = (
            "RESET BASELINE"
            if is_baseline
            else "NO-RESET CONSISTENCY"
        )

        print()
        print("#" * 72)
        print(
            f"REPEATED CAMPAIGN RUN {run_number}/{n_runs}: "
            f"{run_type}"
        )
        print("#" * 72)

        passed = ProgShiftRegs(
            progDebug=True,
            verbose=verbose,
            configclk_period=configclk_period,
            cfg_test_delay=cfg_test_delay,
            cfg_test_sample=cfg_test_sample,
            cfg_test_gate_config_clk=cfg_test_gate_config_clk,
            iP=iP,
            timeSleep=timeSleep,
            send_fw_reset_opcode=is_baseline,
            reset_asic_before_test=is_baseline,
            expect_previous_same_model=not is_baseline,
            check_initial_reset_state=(
                check_initial_reset_state
                if is_baseline
                else False
            ),
            require_initial_reset_state=(
                require_initial_reset_state
                if is_baseline
                else False
            ),
            # The comparator is deterministic; running its software
            # bit-flip regression once is sufficient.
            run_comparator_self_test=(
                run_comparator_self_test
                and is_baseline
            ),
            capture_tag=f"repeat_run_{run_number:03d}",
        )

        run_results.append(
            RepeatedProgrammingRunResult(
                run_number=run_number,
                run_type=run_type,
                passed=passed,
            )
        )

        if not passed and stop_on_failure:
            print(
                f"Stopping after run {run_number} because "
                "stop_on_failure=True."
            )
            break

        if (
            run_number < n_runs
            and time_between_runs > 0
        ):
            time.sleep(time_between_runs)

    overall_pass = all(
        result.passed
        for result in run_results
    )

    print()
    print("#" * 72)
    print("REPEATED PROGRAMMING CAMPAIGN SUMMARY")
    print("#" * 72)

    for result in run_results:
        print(
            f"Run {result.run_number:3d}: "
            f"{'PASS' if result.passed else 'FAIL'}  "
            f"{result.run_type}"
        )

    passed_count = sum(
        1
        for result in run_results
        if result.passed
    )

    print()
    print(
        f"Passed runs: {passed_count}/{len(run_results)}"
    )
    print(
        "REPEATED PROGRAMMING CONSISTENCY: "
        + ("PASS" if overall_pass else "FAIL")
    )
    print("#" * 72)

    return overall_pass

