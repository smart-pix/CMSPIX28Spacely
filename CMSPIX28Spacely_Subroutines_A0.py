
#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *
import os
import time
import io
import numpy as np
from numpy import genfromtxt
import sys

# # # # # # # # # # # # # # # # # # # # # # # # # # 
#            SUB-ROUTINES                         #
# # # # # # # # # # # # # # # # # # # # # # # # # # 
# These are mini functions that execute a small part of a routine.

# Function to convert each hex value to a binary string with proper bit width
def hex_to_bin(hex_str):
    bit_width, hex_value = hex_str.split("'h") # get the bit length and hex value
    bit_width = int(bit_width) # convert bit length to an int
    decimal_value = int(hex_value, 16) # Convert the hexadecimal number to an integer
    binary_str = bin(decimal_value)[2:].zfill(bit_width) # Convert the hexadecimal number to an integer
    return binary_str

def gen_sw_write32_0(hex_list):
    # Convert the list of hex values to a single binary string
    binary_str = ''.join(hex_to_bin(hex_str) for hex_str in hex_list)
    # Convert the binary string to an integer
    resulting_int = int(binary_str, 2)
    # return
    # print(binary_str, resulting_int)
    return resulting_int

def shift_right(lst, n):
    # Handle cases where n is larger than the list length
    n = n % len(lst) if lst else 0
    return lst[-n:] + lst[:-n]
    
def int_to_32bit_hex(number):
    # Ensure the number is treated as a 32-bit number
    # by masking with 0xFFFFFFFF
    hex_number = format(number & 0xFFFFFFFF, '08x')
    return hex_number

def int_to_32bit(number):
    return format(number & 0xFFFFFFFF, '032b')

def print_test_header(word, div="*"):
    print(word)
    print(div*len(word))

def print_test_footer(PASS):
    print("****")
    print("Test result:", "Pass" if PASS else "Fail")
    print("****")
    print("\n")

def split_bits_to_numpy(bit_string, chunk_size=3):
    """
    Split a bit string into chunks of specified size and convert to a numpy array.

    Args:
    bit_string (str): A string containing the bits.
    chunk_size (int): Size of each chunk to split into (default is 3).

    Returns:
    np.array: A numpy array of shape [n_chunks, chunk_size].
    """
    # Check if the bit_string is divisible by the chunk size
    if len(bit_string) % chunk_size != 0:
        raise ValueError(f"Bit string length ({len(bit_string)}) is not divisible by {chunk_size}.")
    
    # Split the bit string into chunks of 3 bits each
    bit_chunks = [list(map(int, bit_string[i:i + chunk_size])) for i in range(0, len(bit_string), chunk_size)]
    
    # Convert the list of bit chunks into a numpy array
    return np.array(bit_chunks)

def BK4600_INIT():
    d = os.open('/dev/usbtmc0', os.O_RDWR)
    input = [
    "*IDN?",
    "C1:BSWV WVTP,PULSE",
    "C1:BSWV FRQ,1000HZ",
    "C1:BSWV PERI,0.001S",
    "C1:BSWV HLEV,0.2V",
    "C1:BSWV LLEV,0V",
    "C1:BSWV DUTY,20",
    "C1:BSWV RISE,6e-09S",
    "C1:BSWV FALL,6e-09S",
    "C1:BSWV DLY,0",
    "C1:BSWV?",
    "C1:BTWV STATE,ON",
    "C1:BTWV TRSR,EXT",
    "C1:BTWV TIME,1",
    #"C1:BTWV DLAY,6.69e-07S",
    "C1:BTWV DLAY,6.68e-07S",   
    "C1:BTWV EDGE,FALL",
    "C1:BTWV CARR,WVTP,PULSE",
    "C1:BTWV FRQ,1000HZ",
    "C1:BTWV PERI,0.001S",
    "C1:BTWV HLEV,0.2V",
    "C1:BTWV LLEV,0V",
    "C1:BTWV DUTY,20",
    "C1:BTWV RISE,6e-09S",
    "C1:BTWV FALL,6e-09S",
    "C1:BTWV DLY,0",
    "C1:BTWV?",
    "C1:OUTP ON",
    "C1:OUTP LOAD,HZ"
    ]
    nlist=len(input)
    for i in range(nlist): 
        os.write(d,input[i].encode())
        out = b' '
        # let's wait one second before reading output (let's give device time to answer)
        print(input[i])
        if(input[i][-1]=="?"):   #If the last character of the request is a question 
            out=os.read(d,1024)  #Print out the response
            print(out.decode())

def BK4600HLEV_SWEEP(HLEV=0.2):
    d = os.open('/dev/usbtmc0', os.O_RDWR)
    input = [
    #"*IDN?",
    "C1:BSWV WVTP,PULSE",
    "C1:BSWV FRQ,1000HZ",
    "C1:BSWV PERI,0.001S",
    f"C1:BSWV HLEV,{HLEV}V",
    "C1:BSWV LLEV,0V",
    "C1:BSWV DUTY,20",
    "C1:BSWV RISE,6e-09S",
    "C1:BSWV FALL,6e-09S",
    "C1:BSWV DLY,0",
    #"C1:BSWV?",
    "C1:BTWV STATE,ON",
    "C1:BTWV TRSR,EXT",
    "C1:BTWV TIME,1",
    #"C1:BTWV DLAY,6.69e-07S",
    "C1:BTWV DLAY,6.68e-07S",
    "C1:BTWV EDGE,FALL",
   # "C1:BTWV CARR,WVTP,PULSE",
    #"C1:BTWV FRQ,1000HZ",
   # "C1:BTWV PERI,0.001S",
    #f"C1:BTWV HLEV,{HLEV}V",
    #"C1:BTWV?"
    ]
    nlist=len(input)
    for i in range(nlist): 
        os.write(d,input[i].encode())
        out = b' '
        # let's wait one second before reading output (let's give device time to answer)
        #print(input[i])
        if(input[i][-1]=="?"):   #If the last character of the request is a question 
            time.sleep(1)
            out=os.read(d,1024)  #Print out the response
            print(out.decode())
    os.close(d)

def BSDG7102A_QUERY():
    d = os.open('/dev/usbtmc0', os.O_RDWR)
    input = [
    "*IDN?",    
    "C1:BSWV?",
    "C1:BTWV?",
    "C1:OUTP?"
        ]
    nlist=len(input)
    for i in range(nlist): 
        os.write(d,input[i].encode())
        out = b' '
        # let's wait one second before reading output (let's give device time to answer)
        print(input[i])
        if(input[i][-1]=="?"):   #If the last character of the request is a question 
            out=os.read(d,1024)  #Print out the response
            print(out.decode())
    os.close(d)

def SDG7102A_INIT():
    d = os.open('/dev/usbtmc0', os.O_RDWR)
    input = [
    "*IDN?",
    "C1:BSWV WVTP,PULSE",
    "C1:BSWV FRQ,10e6HZ",
    "C1:BSWV PERI,8e-6S",
    "C1:BSWV HLEV,0.2V",
    "C1:BSWV LLEV,0V",
    "C1:BSWV DUTY,20",
    "C1:BSWV RISE,5e-10S",
    "C1:BSWV FALL,5e-10S",
    "C1:BSWV DLY,-0S",
    "C1:BSWV?",

    "C1:BTWV STATE,ON",
    # "C1:BTWV PRD,0.00200099S",
    "C1:BTWV PRD,80e-6S",
    "C1:BTWV TRSR,EXT",
    "C1:BTWV TIME,1",
    "C1:BTWV COUNT,1",
    "C1:BTWV DLAY,2.106e-06S",   
    "C1:BTWV EDGE,FALL",     # we trigger with the INJ_OUT_1 from carboard
    #"C1:BTWV EDGE,RISE",   
    "C1:BTWV CARR,WVTP,PULSE",
    "C1:BTWV FRQ,10e6HZ",
    "C1:BTWV PERI,8e-6S",
    "C1:BTWV HLEV,0.2V",
    "C1:BTWV LLEV,0V",
    "C1:BTWV DUTY,20",
    "C1:BTWV RISE,5e-10S",
    "C1:BTWV FALL,5e-10S",
    "C1:BTWV DLY,-0S",
    "C1:BTWV?",
    "C1:OUTP ON",
    #"C1:OUTP LOAD,50",
    "C1:OUTP LOAD,HZ",
    "C1:OUTP PLRT, INVT"
    ]
    nlist=len(input)
    for i in range(nlist): 
        os.write(d,input[i].encode())
        out = b' '
        # let's wait one second before reading output (let's give device time to answer)
        print(input[i])
        if(input[i][-1]=="?"):   #If the last character of the request is a question 
            out=os.read(d,1024)  #Print out the response
            print(out.decode())
    os.close(d)

# def SDG7102A_SWEEP(HLEV=0.2):

#     d = os.open('/dev/usbtmc0', os.O_RDWR)
#     #with os.open('/dev/usbtmc0', os.O_RDWR) as d:
#     input = [
#     #"*IDN?",
#     # "C1:BTWV STATE,ON",
#     # "C1:BTWV PRD,0.00200099S",
#     # "C1:BTWV TRSR,EXT",
#     # "C1:BTWV TIME,1",
#     # "C1:BTWV COUNT,1",
#     # "C1:BTWV DLAY,2.106e-06S",
#     # "C1:BTWV EDGE,RISE",
#     # "C1:BTWV WVTP,PULSE",
#     # "C1:BTWV FRQ,1000000HZ",
#     f"C1:BSWV HLEV,{HLEV}V",
#     "C1:BSWV LLEV,0V",
#     # "C1:BSWV RISE,5e-10S",
#     # "C1:BSWV FALL,5e-10S",
#     # "C1:BSWV  DLY,-0S",
#     ]
#     nlist=len(input)
#     for i in range(nlist): 
#         os.write(d,input[i].encode())
#         out = b' '
#         # let's wait one second before reading output (let's give device time to answer)
#         #print(input[i])
#         if(input[i][-1]=="?"):   #If the last character of the request is a question 
#             time.sleep(1)
#             out=os.read(d,1024)  #Print out the response
#             print(out.decode())
#     os.close(d)


def SDG7102A_SWEEP(HLEV=0.2, max_retries=10, retry_delay=0.1):
    input_commands = [
        f"C1:BSWV HLEV,{HLEV}V",  # Set high-level voltage
        # "C1:BSWV LLEV,0V",  # Set low-level voltage
    ]
    
    retries = 0
    while retries < max_retries:
        try:
            # Attempt to open the device file in read/write binary mode using 'with'
            with open('/dev/usbtmc0', 'r+b') as d:
                # print("Device connected successfully.")
                for cmd in input_commands:
                    d.write(cmd.encode())  # Send command to device

                    # Only wait and read response if command ends with "?"
                    if cmd.endswith("?"):
                        time.sleep(1)  # Give the device time to respond
                        out = d.read(1024)  # Read the response
                        print(out.decode())  # Print the decoded output

                    # If the command is not a query, we just continue
                    else:
                        out = b''  # No output for non-query commands

                break  # Exit the loop once the connection and commands are successful

        except (OSError, FileNotFoundError) as e:
            # Catch specific exceptions related to the device connection
            print(f"Connection failed at voltage {HLEV}: {e}. Retrying ({retries + 1}/{max_retries})...")
            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)  # Delay before retrying
            else:
                print("Max retries reached. Could not connect to the device.")
                break



 

def time_sw_read32(ran=10):
    
    # read value of register
    start =time.process_time()
    for i in range(ran):
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        #sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        
    read_time = time.process_time() - start
    print(f"readtime={read_time}")

def time_sw_write32(ran=10):
    
    # read value of register
    start =time.process_time()
    for i in range(ran):
        sw_write32_0 = sg.INSTR["car"].set_memory("sw_write32_0",0)
        #sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        
    write_time = time.process_time() - start
    print(f"write time={write_time}")

def dnnConfig(weightsCSVFile=None, pixelConfig=None, hiddenBitCSV=None):
    
    if weightsCSVFile != None:   
    # load dnn, append 12 zero's, prepend 8 zero's, reshape to 16 word blocks
        dnn = list(genfromtxt(weightsCSVFile, delimiter=',').astype(int))
    else: 
        dnn = [0]*5164
    dnn_frame1 = [0]*24 + dnn + [0]*12   # first frame
    dnn_frame2 = [0]*28 + dnn + [0]*8  # second frame

    
    # if user gave 512 PIXEL_CONFIG_F2 then replace the last bits
    if pixelConfig != None:
        dnn_frame1[-512-12:-12] = pixelConfig
        dnn_frame2[-512-8:-8] = pixelConfig

    # if user gave 24 hidden values then replace the first bits
    if hiddenBitCSV != None:
        hiddenBit = list(genfromtxt(hiddenBitCSV, delimiter=',').astype(int))
        dnn_frame1[0:24] = hiddenBit
        dnn_frame2[4:24+4] = hiddenBit

    # reshape into 16 bit words
    dnn_frame1 = np.array(dnn_frame1).reshape(-1, 16)
    dnn_frame2 = np.array(dnn_frame2).reshape(-1, 16) 

    # split into array 0 and 1
    array_0 = { i : dnn_frame1[i][::-1].tolist() for i in range(256) }
    array_1 = { iA : dnn_frame1[i][::-1].tolist() for iA, i in enumerate(range(256,325)) }

    # convert to hex_list for programming
    hex_list = []
    for hexArray, array_i in zip(["6", "8"], [array_0, array_1]):
        for key, val in array_i.items():
            address = hex(key)[2:]
            data = hex(int("".join([str(i) for i in val]),2))[2:]
            data = "0"*(4-len(data)) + data
            temp = ["4'h1", f"4'h{hexArray}", f"8'h{address}", f"16'h{data}"]  #spells out 0x0FFF instead of 0xFFF
            hex_list.append(temp)
            #print(key, val, temp)

    # split into array 1 and 2
    array_1 = { i : dnn_frame2[iA][::-1].tolist() for iA, i in enumerate(range(68,256)) }    #256-69 = 187
    array_2 = { iA : dnn_frame2[i][::-1].tolist() for iA, i in enumerate(range((256-68), 325)) }

    # convert to hex_list for programming
    # hex_list = []
    for hexArray, array_i in zip(["8", "A"], [array_1, array_2]):
        for key, val in array_i.items():
            address = hex(key)[2:]
            data = hex(int("".join([str(i) for i in val]),2))[2:]
            data = "0"*(4-len(data)) + data
            temp = ["4'h1", f"4'h{hexArray}", f"8'h{address}", f"16'h{data}"] 
            hex_list.append(temp)
            #print(key, val, temp)

    #print(len(hex_list))
    return hex_list

# programming pixel

# Define the grid as a 2D list, where each inner list represents a row
grid = [
    [63,  62,  59,  58,  55,  54,  51,  50,  47,  46,  43,  42,  39,  38,  35,  34,  31,  30,  27,  26,  23,  22,  19,  18,  15,  14,  11,  10,   7,   6,   3,    2],
    [60,  61,  56,  57,  52,  53,  48,  49,  44,  45,  40,  41,  36,  37,  32,  33,  28,  29,  24,  25,  20,  21,  16,  17,  12,  13,   8,   9,   4,   5,   0,    1],
    [127, 126, 123, 122, 119, 118, 115, 114, 111, 110, 107, 106, 103, 102, 99,  98,  95,  94,  91,  90,  87,  86,  83,  82,  79,  78,  75,  74,  71,  70,  67,   66],
    [124, 125, 120, 121, 116, 117, 112, 113, 108, 109, 104, 105, 100, 101, 96,  97,  92,  93,  88,  89,  84,  85,  80,  81,  76,  77,  72,  73,  68,  69,  64,   65],
    [191, 190, 187, 186, 183, 182, 179, 178, 175, 174, 171, 170, 167, 166, 163, 162, 159, 158, 155, 154, 151, 150, 147, 146, 143, 142, 139, 138, 135, 134, 131, 130],
    [188, 189, 184, 185, 180, 181, 176, 177, 172, 173, 168, 169, 164, 165, 160, 161, 156, 157, 152, 153, 148, 149, 144, 145, 140, 141, 136, 137, 132, 133, 128, 129],
    [255, 254, 251, 250, 247, 246, 243, 242, 239, 238, 235, 234, 231, 230, 227, 226, 223, 222, 219, 218, 215, 214, 211, 210, 207, 206, 203, 202, 199, 198, 195, 194],
    [252, 253, 248, 249, 244, 245, 240, 241, 236, 237, 232, 233, 228, 229, 224, 225, 220, 221, 216, 217, 212, 213, 208, 209, 204, 205, 200, 201, 196, 197, 192, 193]
]

# Define the grid from the image, with -1 for the darker blue, purple, and black cells
grid_with_address = {
    104: [62,  -1, 61,  -1, 63,  -1, 60,  -1, -1,  -1, -1,  -1, -1,  -1, -1,  -1],
    105: [54,  -1, 53,  -1, 55,  -1, 52,  -1, 58,  -1, 57,  -1, 59,  -1, 56,  -1],
    106: [46,  -1, 45,  -1, 47,  -1, 44,  -1, 50,  -1, 49,  -1, 51,  -1, 48,  -1],
    107: [38,  -1, 37,  -1, 39,  -1, 36,  -1, 42,  -1, 41,  -1, 43,  -1, 40,  -1],
    108: [30,  -1, 29,  -1, 31,  -1, 28,  -1, 34,  -1, 33,  -1, 35,  -1, 32,  -1],
    109: [22,  -1, 21,  -1, 23,  -1, 20,  -1, 26,  -1, 25,  -1, 27,  -1, 24,  -1],
    110: [14,  -1, 13,  -1, 15,  -1, 12,  -1, 18,  -1, 17,  -1, 19,  -1, 16,  -1],
    111: [6,   -1, 5,   -1, 7,   -1, 4,   -1, 10,  -1, 9,   -1, 11,  -1, 8,   -1],
    112: [126, -1, 125, -1, 127, -1, 124, -1, 2,   -1, 1,   -1, 3,   -1, 0,   -1],
    113: [118, -1, 117, -1, 119, -1, 116, -1, 122, -1, 121, -1, 123, -1, 120, -1],
    114: [110, -1, 109, -1, 111, -1, 108, -1, 114, -1, 113, -1, 115, -1, 112, -1],
    115: [102, -1, 101, -1, 103, -1, 100, -1, 106, -1, 105, -1, 107, -1, 104, -1],
    116: [94,  -1, 93,  -1, 95,  -1, 92,  -1, 98,  -1, 97,  -1, 99,  -1, 96,  -1],
    117: [86,  -1, 85,  -1, 87,  -1, 84,  -1, 90,  -1, 89,  -1, 91,  -1, 88,  -1],
    118: [78,  -1, 77,  -1, 79,  -1, 76,  -1, 82,  -1, 81,  -1, 83,  -1, 80,  -1],
    119: [70,  -1, 69,  -1, 71,  -1, 68,  -1, 74,  -1, 73,  -1, 75,  -1, 72,  -1],
    120: [190, -1, 189, -1, 191, -1, 188, -1, 66,  -1, 65,  -1, 67,  -1, 64,  -1],
    121: [182, -1, 181, -1, 183, -1, 180, -1, 186, -1, 185, -1, 187, -1, 184, -1],
    122: [174, -1, 173, -1, 175, -1, 172, -1, 178, -1, 177, -1, 179, -1, 176, -1],
    123: [166, -1, 165, -1, 167, -1, 164, -1, 170, -1, 169, -1, 171, -1, 168, -1],
    124: [158, -1, 157, -1, 159, -1, 156, -1, 162, -1, 161, -1, 163, -1, 160, -1],
    125: [150, -1, 149, -1, 151, -1, 148, -1, 154, -1, 153, -1, 155, -1, 152, -1],
    126: [142, -1, 141, -1, 143, -1, 140, -1, 146, -1, 145, -1, 147, -1, 144, -1],
    127: [134, -1, 133, -1, 135, -1, 132, -1, 138, -1, 137, -1, 139, -1, 136, -1],
    128: [254, -1, 253, -1, 255, -1, 252, -1, 130, -1, 129, -1, 131, -1, 128, -1],
    129: [246, -1, 245, -1, 247, -1, 244, -1, 250, -1, 249, -1, 251, -1, 248, -1],
    130: [238, -1, 237, -1, 239, -1, 236, -1, 242, -1, 241, -1, 243, -1, 240, -1],
    131: [230, -1, 229, -1, 231, -1, 228, -1, 234, -1, 233, -1, 235, -1, 232, -1],
    132: [222, -1, 221, -1, 223, -1, 220, -1, 226, -1, 225, -1, 227, -1, 224, -1],
    133: [214, -1, 213, -1, 215, -1, 212, -1, 218, -1, 217, -1, 219, -1, 216, -1],
    134: [206, -1, 205, -1, 207, -1, 204, -1, 210, -1, 209, -1, 211, -1, 208, -1],
    135: [198, -1, 197, -1, 199, -1, 196, -1, 202, -1, 201, -1, 203, -1, 200, -1],
    136: [-1,  -1, -1,  -1,  -1, -1,  -1, -1, 194, -1, 193, -1, 195, -1, 192, -1]
}

# Define the grid as a 2D list, where each inner list represents a row
grid_ben = {
   7: [63,  62,  59,  58,  55,  54,  51,  50,  47,  46,  43,  42,  39,  38,  35,  34,  31,  30,  27,  26,  23,  22,  19,  18,  15,  14,  11,  10,   7,   6,   3,    2],
   6: [60,  61,  56,  57,  52,  53,  48,  49,  44,  45,  40,  41,  36,  37,  32,  33,  28,  29,  24,  25,  20,  21,  16,  17,  12,  13,   8,   9,   4,   5,   0,    1],
   5: [127, 126, 123, 122, 119, 118, 115, 114, 111, 110, 107, 106, 103, 102, 99,  98,  95,  94,  91,  90,  87,  86,  83,  82,  79,  78,  75,  74,  71,  70,  67,   66],
   4: [124, 125, 120, 121, 116, 117, 112, 113, 108, 109, 104, 105, 100, 101, 96,  97,  92,  93,  88,  89,  84,  85,  80,  81,  76,  77,  72,  73,  68,  69,  64,   65],
   3: [191, 190, 187, 186, 183, 182, 179, 178, 175, 174, 171, 170, 167, 166, 163, 162, 159, 158, 155, 154, 151, 150, 147, 146, 143, 142, 139, 138, 135, 134, 131, 130],
   2: [188, 189, 184, 185, 180, 181, 176, 177, 172, 173, 168, 169, 164, 165, 160, 161, 156, 157, 152, 153, 148, 149, 144, 145, 140, 141, 136, 137, 132, 133, 128, 129],
   1: [255, 254, 251, 250, 247, 246, 243, 242, 239, 238, 235, 234, 231, 230, 227, 226, 223, 222, 219, 218, 215, 214, 211, 210, 207, 206, 203, 202, 199, 198, 195, 194],
   0: [252, 253, 248, 249, 244, 245, 240, 241, 236, 237, 232, 233, 228, 229, 224, 225, 220, 221, 216, 217, 212, 213, 208, 209, 204, 205, 200, 201, 196, 197, 192, 193]
}

# needed helper functions
def get_number(row, column):
    # Check if the row and column are within the valid range
    if 0 <= row < 8 and 0 <= column < 32:
        return grid[7-row][column]
    else:
        return "Invalid row or column"

# find address, column
def find_grid_cell(grid_number):
    # Iterate over the rows and their corresponding address
    for address, row in grid_with_address.items():
        if grid_number in row:
            column = 15 - row.index(grid_number)
            return (address, column)
    return "Grid number not found"

def find_grid_cell_superpix(grid_number):
    # Iterate over the rows and their corresponding address
    for address, row in grid_ben.items():
        if grid_number in row:
            column = row.index(grid_number)
            return (address, column)
    return "Grid number not found"
# helper function
def find_values_in_2d_array(array, values, settings):
    positions = []
    for value, setting in zip(values, settings):
        found = False
        for row_index, row in enumerate(array):
            if value in row:
                col_index = row.index(value)
                positions.append([7 - row_index, col_index, setting])
                found = True
                break
        if not found:
            positions.append(None)  # Value not found
    return positions

def genPixelProgramList(p, s):
    
    # get the pixel row and columns
    toprogram = find_values_in_2d_array(grid, p, s)
    # prepare temporary programming lists
    address_lists = {key : [0] * 16 for key in grid_with_address.keys()}

    for row, column, value in toprogram:
        # get pixel number
        pixelNum = get_number(row, column)

        # convert value to binary
        val = bin(value)[2:][::-1]
        if len(val) == 1:
            val = val + "0"

        # find the address from the grid cell
        address, bitHigh = find_grid_cell(pixelNum)

        # set values to hex list
        address_lists[address][15 - bitHigh] = int(val[0])
        address_lists[address][15 - (bitHigh-1)] = int(val[1])

    # create full pixel programming
    pixelConfig = []
    for key, val in address_lists.items():
        # print(key, val)
        pixelConfig += val[::-1]
    # remove first and last 8 bits which are not real
    pixelConfig = pixelConfig[8:-8]

    return pixelConfig

def thermometric_to_integer(binary_str):
    integer_values =0
    not_allowed = ["010", "101", "110","100"]   # should not be legal - check bit order though
    if binary_str in not_allowed:
        integer_value=0
    else:
        integer_values=binary_str.count('1')
    
    
    # Count the number of '1's in the binary string
    return integer_values

def ivdd_vs_vdd(power='vddd'):

    ivdd = []
    vdd_rd =[]
    ivvdd_vs_vdd = []
    outDir = "/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea/CMSPIX28_DAQ/spacely/PySpacely/data/power"
    os.makedirs(outDir, exist_ok=True)
    for i in range(0,90):
        if i/100<0.9:
            volt = i/100
            V_PORT[power].set_voltage(volt)
            time.sleep(0.5)
            print(V_PORT[power].get_voltage())
            print(V_PORT[power].get_current())
            ivdd.append(V_PORT[power].get_current())
            vdd_rd.append(V_PORT[power].get_voltage())
        else:
            V_PORT[power].set_voltage(0.9)
            break
    # ivvdd_vs_vdd = np.concatenate((vdd_rd,ivdd), axis=1)
    outFileName = os.path.join(outDir, f"ivvdd_vs_{power}.npz")
    np.savez(outFileName, **{"ivdd": ivdd, f"{power}_rd": vdd_rd })

def get_power():
    iDVDD = V_PORT["vddd"].get_current()
    iAVDD = V_PORT["vdda"].get_current()
    print(f"DVDD current is {iDVDD}")
    print(f"AVDD current is {iAVDD}")

def genPixelConfigFromInputCSV(filename):

    # Initialize an empty list to store the lists of numbers
    pixelLists = []
    pixelValues = []

    # Open the CSV file and read each line
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:

            # 256 numbers
            csvRow = [int(num) for num in row]

            # 8x32 starting with row 0 at the top like diagram
            pixels = [[0]*32]*8
            for i in range(0, 8):
                # pick up 32
                temp = csvRow[i*32 : (i+1)*32]
                # first 16 are right hand values (odd indices) and last 16 are left hand values (even indices)
                newrow = [0] * 32
                newrow[1::2] = reversed(temp[:16])
                newrow[0::2] = reversed(temp[16:])
                pixels[i] = newrow

            # reverse to match order of grid
            pixels = list(reversed(pixels))

            # assign to pixel list and values
            pixelList = []
            pixelValue = []
            for iR , (pixRow, gridRow) in enumerate(zip(pixels, grid)):
                for iC, (p, g) in enumerate(zip(pixRow, gridRow)):
                    if p != 0:
                        pixelList.append(g) # append pixel index from grid
                        thermValue = thermometric_to_integer(bin(int(p))[2:])
                        pixelValue.append(thermValue) # append pixel value as thermometric integer
                        # print(8 - iR, iC, g, p, thermValue)

            # append
            pixelLists.append(pixelList)
            pixelValues.append(pixelValue)

    return pixelLists, pixelValues

# helper function to print a loud message for the user
header_import_error = "IMPORT ERROR!"
def loud_message(header, body):
    print("\033[91;1m" + "="*80)  # Red, bold, and large separator
    print(" " * 20 + header) 
    print("="*80)
    print("\033[93;1m" + body.upper() + "\033[0m")  # Yellow, bold text
    print("\033[91;1m" + "="*80 + "\033[0m")  # Reset color