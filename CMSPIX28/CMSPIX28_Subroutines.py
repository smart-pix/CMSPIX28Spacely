
#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *
import os
import time
import io

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

def BK4600():
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
    "C1:BTWV DLAY,6.75e-07S",
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
    


