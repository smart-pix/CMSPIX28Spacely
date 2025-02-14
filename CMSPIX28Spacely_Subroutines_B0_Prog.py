# spacely
from Master_Config import *
import time
import tqdm
from datetime import datetime
import csv
# This subroutine programs the shift register
# The pixel address and value need to be manual inserted
def ProgShiftRegManualOnly(progFreq='64', progDly='5', progSample='20',progConfigClkGate='1'):

    #FW reset followed with Status reset
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", f"7'h{progFreq}"], # OP_CODE_W_RST_FW
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
            f"1'h{progConfigClkGate}", # 1 bit for gating configClk
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for test number
            f"7'h{progSample}", # 6 bits test sample
            f"7'h{progDly}"  # 6 bits for test delay
        ]
    
    ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
    time.sleep(0.5)

# This subroutine programs the pixel section of the shift register
# It takes in a list of a list of pixel number to be progammed and their corresponding values (0,1,2,3)
# pixel number are taken from the LUT in the Figure 6: Superpixel Map in the cms28_smartpixe_test_manual document
# pixel values are the 2-bit decimal possibilities
def ProgPixelsOnly(progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [0], pixelValue=[3]):
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    #PROGRAM SHIFT REGISTER
    hex_lists = [
        # ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{progFreq}"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 1M
        ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{progFreq}"],
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    pixelConfig = genPixelProgramList(pixelList, pixelValue)
    hex_lists = dnnConfig(pixelConfig = pixelConfig)
    sw_write32_0(hex_lists, doPrint=False)

    hex_lists = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h0",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "3'h0", # 3 bits for spare_index_max
            f"1'h{progConfigClkGate}", # 1 bit for gating configClk
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for test number
            f"7'h{progSample}", # 6 bits test sample
            f"7'h{progDly}"  # 6 bits for test delay
        ]
    
    ]
    sw_write32_0(hex_lists)
    time.sleep(0.5)
    pass


def ProgShiftRegs(progDebug=False, verbose=False, progFreq='64', progDly='5', progSample='20',progConfigClkGate='1', iP=0, timeSleep=0.015):
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{progFreq}"],
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    # load all of the configs
    filename = "/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_D/tb/dnn/csv/l6/compouts.csv"
    pixelLists, pixelValues = genPixelConfigFromInputCSV(filename)


    hiddenBit="/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/hidden_debug.csv"
    # pick up pixel config for the given pattern
    pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])

    # Programming the NN weights and biases
    if(progDebug==True):
        hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin_debug2.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
    else:
        hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
    sw_write32_0(hex_lists, doPrint=False)
    # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 

    hex_lists = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h0",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "3'h0", # 3 bits for spare_index_max
            f"1'h{progConfigClkGate}", # 1 bit for gating configClk
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 4 bits for test number
            f"7'h{progSample}", # 6 bits test sample
            f"7'h{progDly}"  # 6 bits for test delay
        ]
    
    ]
    sw_write32_0(hex_lists)
    time.sleep(timeSleep)

    #This needs to be replaced with smog test
    if(verbose==True and progDebug==True):
            #ReadBack from READ_ARRAY 1
            words_A0 = []      
            words_A1 = []
            words_A2 = []    
            words_DA0 = []
            words_DA1 = []              
            for i in range(0, 256,2):
                address = hex(i)[2:]
                hex_list0 = [
                [
                    "4'h1", "4'h7", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 0            
                ]
                sw_write32_0(hex_list0)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_A0.append([address,int_to_32bit(sw_read32_0)])

                hex_list1 = [
                [
                    "4'h1", "4'h9", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 1            
                ]
                sw_write32_0(hex_list1)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_A1.append([address,int_to_32bit(sw_read32_0)])

                hex_list2 = [
                [
                    "4'h1", "4'hB", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 2            
                ]
                sw_write32_0(hex_list2)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_A2.append([address,int_to_32bit(sw_read32_0)])
            
            for i in range(256):
                address = hex(i)[2:]
                hex_list_rdata0 = [
                [
                    "4'h1", "4'hC", f"8'h{address}", "16'h0"]         #ReadBack from READ DATA ARRAY 0            
                ]
                sw_write32_0(hex_list_rdata0)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_DA0.append([address,int_to_32bit(sw_read32_0)])

                hex_list_rdata1 = [
                [
                    "4'h1", "4'hD", f"8'h{address}", "16'h0"]         #ReadBack from READ DATA ARRAY 1            
                ]
                sw_write32_0(hex_list_rdata1)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_DA1.append([address,int_to_32bit(sw_read32_0)])

            print("CFG ARRAY 0")
            for i in words_A0:
                print(i)
            print("CFG ARRAY 1")
            for i in words_A1:
                print(i)
            print("CFG ARRAY 2")  
            for i in words_A2:
                print(i)           
            print("READ DATA 0")   
            for i in words_DA0:
                print(i)    
            print("READ DATA 1")  
            for i in words_DA1:
                print(i)
            cfgArray0File = "cfgArray0.csv"
            with open(cfgArray0File, 'a+', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(words_A0)
            array0File = "array0.csv"                  
            with open(array0File, 'a+', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(words_DA0)
            array1File = "array1.csv"                  
            with open(array1File, 'a+', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(words_DA1)

    pass
