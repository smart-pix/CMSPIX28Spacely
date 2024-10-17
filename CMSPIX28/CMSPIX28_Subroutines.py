
#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *
import os
import time
import io
import numpy as np
from numpy import genfromtxt
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
    #!/bin/python3
    import os
    import time
    import io
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
    #!/bin/python3
    import os
    import time
    import io
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

def time_sw_read32(ran=10):
    
    # read value of register
    start =time.process_time()
    for i in range(ran):
        sw_read32_0 = sg.INSTR["car"].get_memory("sw_read32_0")
        #sw_read32_1 = sg.INSTR["car"].get_memory("sw_read32_1")
        
    read_time = time.process_time() - start
    print(f"readtime={read_time}")


def dnnConfig(weightsCSVFile, pixelConfig=None):
	# load dnn, append 12 zero's, prepend 8 zero's, reshape to 16 word blocks
	dnn = list(genfromtxt(weightsCSVFile, delimiter=',').astype(int))
	dnn = [0]*12 + dnn + [0]*8

	# if user gave 512 PIXEL_CONFIG_F2 then replace the last bits
	if pixelConfig:
		dnn[-512-8:-8] = pixelConfig

	# reshape into 16 bit words
	dnn = np.array(dnn).reshape(-1, 16)

	# split into array 1 and 2
	array_1 = { 69+i : dnn[i][::-1].tolist() for i in range(187) }
	array_2 = { iA : dnn[i][::-1].tolist() for iA, i in enumerate(range(187, 324)) }

	# convert to hex_list for programming
	hex_list = []
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

