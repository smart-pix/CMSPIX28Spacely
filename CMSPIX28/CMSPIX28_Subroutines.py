
#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *


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
