
#Import Spacely functions
try:
    from Master_Config import *
    import Spacely_Globals as sg
    from Spacely_Utils import *
except:
    print("Likely importing functions from outside of Spacely. Be careful.")

# python modules
import sys
try:
    import os
    import time
    import io
    import numpy as np
    from numpy import genfromtxt
    import sys
    import importlib 
    import csv
except ImportError as e:
    print("\033[93;1m" + f"Import error in {__file__}: {str(e)}".upper() + "\033[0m")
    sys.exit(1)  # Exit script immediately

CHANNEL = "C2"  # Change this to the appropriate channel for your device (e.g., "C1", "C2", etc.)

# Persistent USBTMC connections, keyed by device path. Opening a USBTMC
# character device has real overhead (USB control transfers, driver init);
# re-opening it on every voltage step was the dominant per-step cost for the
# pulse generator sweep calls, so the file object is opened once and reused.
_USBTMC_FILES = {}

def _usbtmc_write(path, cmd, max_retries=10, retry_delay=0.1):
    """
    Write a single SCPI command to a persistently-held USBTMC device file,
    opening (and caching) it on first use instead of on every call. Re-opens
    on failure (device unplugged, transient USB error, etc.).
    """
    retries = 0
    while retries < max_retries:
        d = _USBTMC_FILES.get(path)
        try:
            if d is None:
                d = open(path, 'r+b', buffering = 0)
                _USBTMC_FILES[path] = d
            d.write(cmd.encode())
            if cmd.endswith("?"):
                time.sleep(1)  # Give the device time to respond
                out = d.read(1024)
                print(out.decode())
            return
        except (OSError, FileNotFoundError) as e:
            print(f"USBTMC write to {path} failed: {e}. Retrying ({retries + 1}/{max_retries})...")
            _USBTMC_FILES.pop(path, None)
            if d is not None:
                try:
                    d.close()
                except OSError:
                    pass
            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)
    print(f"Max retries reached. Could not write to {path}.")

def _usbtmc_query(path, cmd, max_retries=10, retry_delay=0.1, wait=0.1):
    """
    Same as _usbtmc_write for a query ("...?") but returns the decoded answer
    instead of printing it. Shares the persistent connection in _USBTMC_FILES.
    Returns None if the device could not be reached.
    """
    retries = 0
    while retries < max_retries:
        d = _USBTMC_FILES.get(path)
        try:
            if d is None:
                d = open(path, 'r+b', buffering = 0)
                _USBTMC_FILES[path] = d
            d.write(cmd.encode())
            time.sleep(wait)  # Give the device time to respond
            return d.read(1024).decode()
        except (OSError, FileNotFoundError) as e:
            print(f"USBTMC query to {path} failed: {e}. Retrying ({retries + 1}/{max_retries})...")
            _USBTMC_FILES.pop(path, None)
            if d is not None:
                try:
                    d.close()
                except OSError:
                    pass
            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)
    print(f"Max retries reached. Could not query {path}.")
    return None

# # # # ## # # # # # # # # # # # # # # # # # # # # 
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
    # One-time setup of everything that doesn't change across a voltage sweep
    # (waveform shape, burst timing, trigger source, output state). Routed
    # through _usbtmc_write so it shares the same persistent connection that
    # BK4600HLEV_SWEEP() reuses on every step, instead of leaving its own
    # separate fd open on the same device.
    input = [
    "*IDN?",
    "C1:BSWV WVTP,PULSE",
    "C1:BSWV FRQ,1000HZ",
    "C1:BSWV PERI,8e-6S",
    "C1:BSWV HLEV,0.200V",
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
    for cmd in input:
        print(cmd)
        _usbtmc_write('/dev/usbtmc0', cmd)

def BK4600HLEV_SWEEP(HLEV=0.2, max_retries=10, retry_delay=0.1):
    # Only update the high-level voltage per step; everything else (waveform
    # shape, burst timing, trigger source, output state) is configured once
    # by BK4600_INIT() and does not need to be re-sent every voltage step.
    # Reuses the persistent connection instead of opening/closing the device
    # file on every call.
    start = time.time()
    _usbtmc_write('/dev/usbtmc0', f"C1:BSWV HLEV,{HLEV}V", max_retries=max_retries, retry_delay=retry_delay) 
    _usbtmc_write('/dev/usbtmc0', "C1:BTWV STATE,ON", max_retries=max_retries, retry_delay=retry_delay)   
    end = time.time()
    print("Elapsed time =", round(end-start,8), "seconds")

def SDG7102A_QUERY():
    d = os.open('/dev/usbtmc1', os.O_RDWR)
    input = [
    "*IDN?",    
    f"{CHANNEL}:BSWV?",
    f"{CHANNEL}:BTWV?",
    f"{CHANNEL}:OUTP?"
    f"{CHANNEL}:BSWV?",
    f"{CHANNEL}:BTWV?",
    f"{CHANNEL}:OUTP?"
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
    d = os.open('/dev/usbtmc1', os.O_RDWR)
    input = [
    "*IDN?",
    f"{CHANNEL}:BSWV WVTP,PULSE",
    f"{CHANNEL}:BSWV FRQ,10e6HZ",
    f"{CHANNEL}:BSWV PERI,8e-6S",
    f"{CHANNEL}:BSWV HLEV,0.2V",
    f"{CHANNEL}:BSWV LLEV,0V",
    f"{CHANNEL}:BSWV DUTY,20",
    f"{CHANNEL}:BSWV RISE,5e-10S",
    f"{CHANNEL}:BSWV FALL,5e-10S",
    f"{CHANNEL}:BSWV DLY,-0S",
    f"{CHANNEL}:BSWV?",

    f"{CHANNEL}:BTWV STATE,ON",
    # "C1:BTWV PRD,0.00200099S",
    f"{CHANNEL}:BTWV PRD,80e-6S",
    f"{CHANNEL}:BTWV TRSR,EXT",
    f"{CHANNEL}:BTWV TIME,1",
    f"{CHANNEL}:BTWV COUNT,1",
    f"{CHANNEL}:BTWV DLAY,2.106e-06S",   
    f"{CHANNEL}:BTWV EDGE,FALL",     # we trigger with the INJ_OUT_1 from carboard
    #"C1:BTWV EDGE,RISE",   
    f"{CHANNEL}:BTWV CARR,WVTP,PULSE",
    f"{CHANNEL}:BTWV FRQ,10e6HZ",
    f"{CHANNEL}:BTWV PERI,8e-6S",
    f"{CHANNEL}:BTWV HLEV,0.2V",
    f"{CHANNEL}:BTWV LLEV,0V",
    f"{CHANNEL}:BTWV DUTY,20",
    f"{CHANNEL}:BTWV RISE,5e-10S",
    f"{CHANNEL}:BTWV FALL,5e-10S",
    f"{CHANNEL}:BTWV DLY,-0S",
    f"{CHANNEL}:BTWV?",
    f"{CHANNEL}:OUTN ON",
    #"C1:OUTP LOAD,50",
    f"{CHANNEL}:OUTP LOAD,HZ",
    f"{CHANNEL}:OUTP PLRT, INVT"
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


def SDG7102A_INJ_BURST():
    d = os.open('/dev/usbtmc1', os.O_RDWR)
    input = [
    "*IDN?",
    f"{CHANNEL}:BSWV WVTP,PULSE",
    f"{CHANNEL}:BSWV PERI,8e-6S",
    f"{CHANNEL}:BSWV WIDTH, 1.6e-6S",
    f"{CHANNEL}:BTWV STATE,ON",
    f"{CHANNEL}:OUTN ON",
    f"{CHANNEL}:OUTP LOAD,HZ",
    f"{CHANNEL}:OUTP PLRT, INVT"
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

def SDG7102A_INJ_CONT_BURST():
    d = os.open('/dev/usbtmc1', os.O_RDWR)
    input = [
    "*IDN?",
    "C1:BSWV WVTP,PULSE",
    "C1:BSWV PERI,8e-6S",
    "C1:BSWV WIDTH, 1.6e-6S",
    "C1:BTWV STATE,ON",
    "C1:OUTN ON",
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

def SDG7102A_INJ_CONT():
    d = os.open('/dev/usbtmc0', os.O_RDWR)
    input = [
    "*IDN?",
    "C1:BSWV WVTP,PULSE",
    # "C1:BSWV FRQ,666666HZ",

    "C1:BSWV PERI 1.5e-6S",
    
    "C1:BSWV WIDTH, 0.75e-6S",
    # "C1:BSWV PERI,1.5e-6S",

    "C1:BTWV STATE,ON",
   
    "C1:OUTN ON",
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
def SDG7102A_SWEEP_FALL(TFALL=5e-10, max_retries=10, retry_delay=0.1):
    start = time.time()
    input_commands = [
        f"{CHANNEL}:BSWV RISE,{TFALL}S",# Set low-level voltage FALL TIME is set with RISE TIME because the PG is inverted !!!!
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
    end = time.time()
    print("Elapsed time =", round(end-start,8), "seconds")



def SDG7102A_SWEEP(HLEV=0.2, max_retries=10, retry_delay=0.1):
    # Only the high-level voltage changes per step; reuses the persistent
    # connection instead of opening/closing the device file on every call.
    start = time.time()
    _usbtmc_write('/dev/usbtmc1', f"{CHANNEL}:BSWV HLEV,{HLEV}V", max_retries=max_retries, retry_delay=retry_delay)
    end = time.time()
    print("Elapsed time =", round(end-start,8), "seconds")


# # # # # # # # # # # # # # # # # # # # # # # # # #
# Agilent 81104A pulse generator through a Prologix GPIB-USB controller
# # # # # # # # # # # # # # # # # # # # # # # # # #
# The Prologix shows up as a USB serial port (FTDI, /dev/ttyUSB*), no GPIB driver needed (needs pyserial).
# The ZCU serial console (minicom) also uses /dev/ttyUSB*, and the numbers can change after a reboot or replug,
# so the Prologix is found by its stable name in /dev/serial/by-id (port = None) instead of a ttyUSB number.
# Levels follow the BK4600 / SDG7102A convention: the 81104A expects a high impedance load (:OUTP:IMP:EXT 1E6OHM),
# so the programmed high level is the open circuit voltage and the chip sees half of it (the board terminates in 50 Ohm).
# The scans call set_hlev(2*v_asic) for every generator, the attenuator between the 81104A and the board is corrected here:
# programmed high level = 2*v_asic / atten_gain. Without attenuator the 81104A minimum amplitude (~100 mV into 50 Ohm,
# ~200 mV open circuit) is ~100 mV at the chip; with 20 dB it is ~10 mV.
# Measure atten_gain (and base_delay) once on the scope at the board and put the measured values in A81104A_SETTINGS.
A81104A_SETTINGS = {
    "port"       : None,           # None: find the Prologix in /dev/serial/by-id; or give its /dev/serial/by-id/... path
    "gpib_addr"  : 10,             # GPIB address set on the 81104A (front panel: MORE -> GPIB address)
    "out"        : 1,              # output channel (1 or 2)
    "atten_dB"   : 20,             # fixed 50 Ohm attenuator between the 81104A output and the board, 0 if none
    "atten_gain" : None,           # measured amplitude ratio (board/81104A); None uses 10**(-atten_dB/20)
    "min_hlev"   : 0.200,          # smallest open circuit amplitude the 81104A accepts [V] (100 mVpp into 50 Ohm): check on the instrument
    "max_hlev"   : 20.0,           # largest open circuit high level [V] (10 V into 50 Ohm): check on the instrument
    "trig_level" : 1.0,            # EXT INPUT threshold [V] for INJ_OUT_1
    "trig_slope" : "NEG",          # trigger on the falling edge of INJ_OUT_1 (same as the BK4600 / SDG7102A)
    "rise"       : 6e-9,           # leading edge (trailing edge follows), same as the BK4600
    "width"      : 1.6e-6,         # pulse width, same as the BK4600 (8 us period, 20 % duty)
    "polarity"   : "INV",          # negative-going injection like the other benches (SDG7102A OUTP PLRT,INVT, BK4600 inverted):
                                   # idles at the high level and drops to 0 V. "NORM" injects the wrong sign (low peak, no flat top)
}

_PROLOGIX = {}

def _prologix_port():
    # the Prologix serial port: A81104A_SETTINGS["port"] if set, else the unique Prologix entry in /dev/serial/by-id
    if A81104A_SETTINGS["port"]:
        return A81104A_SETTINGS["port"]
    import glob
    ports = sorted(glob.glob("/dev/serial/by-id/*Prologix*"))
    if len(ports) != 1:
        raise IOError(f"Expected one Prologix in /dev/serial/by-id, found {ports}. Set A81104A_SETTINGS['port'] "
                      f"to its /dev/serial/by-id/... path (ls -l /dev/serial/by-id shows which ttyUSB is which).")
    return ports[0]

def _prologix(port=None, gpib_addr=None):
    # persistent serial connection to the Prologix, configured as GPIB controller talking to gpib_addr
    port = port or _prologix_port()
    gpib_addr = A81104A_SETTINGS["gpib_addr"] if gpib_addr is None else gpib_addr
    ser = _PROLOGIX.get(port)
    if ser is None or not ser.is_open:
        import serial # pyserial
        ser = serial.Serial(port, baudrate=115200, timeout=1)
        for cmd in ["++mode 1", "++auto 0", "++eoi 1", "++eos 2", "++read_tmo_ms 1000", "++ifc"]:
            ser.write((cmd + "\n").encode())
        time.sleep(0.1)
        _PROLOGIX[port] = ser
    ser.write(f"++addr {gpib_addr}\n".encode())
    return ser

def _gpib_write(cmd, max_retries=10, retry_delay=0.1):
    retries = 0
    while retries < max_retries:
        try:
            ser = _prologix()
            ser.write((cmd + "\n").encode())
            return
        except Exception as e:
            print(f"GPIB write '{cmd}' failed: {e}. Retrying ({retries + 1}/{max_retries})...")
            for ser in list(_PROLOGIX.values()):
                try:
                    ser.close()
                except Exception:
                    pass
            _PROLOGIX.clear()
            retries += 1
            time.sleep(retry_delay)
    print(f"Max retries reached. Could not write '{cmd}' to GPIB address {A81104A_SETTINGS['gpib_addr']}.")

def _gpib_query(cmd, max_retries=10, retry_delay=0.1):
    # returns the answer as a string, None if the instrument could not be reached
    retries = 0
    while retries < max_retries:
        try:
            ser = _prologix()
            ser.reset_input_buffer()
            ser.write((cmd + "\n").encode())
            ser.write(b"++read eoi\n")
            out = ser.readline().decode().strip()
            if out:
                return out
            raise IOError("no answer")
        except Exception as e:
            print(f"GPIB query '{cmd}' failed: {e}. Retrying ({retries + 1}/{max_retries})...")
            for ser in list(_PROLOGIX.values()):
                try:
                    ser.close()
                except Exception:
                    pass
            _PROLOGIX.clear()
            retries += 1
            time.sleep(retry_delay)
    print(f"Max retries reached. Could not query '{cmd}' from GPIB address {A81104A_SETTINGS['gpib_addr']}.")
    return None

def A81104A_ERRORS():
    # read and print the 81104A error queue, returns the list of errors (empty if none)
    errors = []
    for _ in range(20):
        err = _gpib_query(":SYST:ERR?")
        if err is None or err.startswith("0") or err.startswith("+0"):
            break
        errors.append(err)
    for err in errors:
        print(f"81104A ERROR: {err}")
    return errors

# Console helpers (names starting with "_" are not imported into the Spacely console)
def A81104A_QUERY(cmd):
    # send a query to the 81104A and return the answer, e.g. A81104A_QUERY("*IDN?")
    return _gpib_query(cmd)

def A81104A_WRITE(cmd):
    # send a command to the 81104A, then print any error it caused, e.g. A81104A_WRITE(":VOLT1:HIGH 2V")
    _gpib_write(cmd)
    return A81104A_ERRORS()

def A81104A_LIMITS():
    # print the installed options and the level / amplitude range the instrument accepts in its current state
    o = A81104A_SETTINGS["out"]
    for q in ["*IDN?", "*OPT?", ":ARM:SOUR?", ":ARM:IMP?", ":ARM:LEV?", f":OUTP{o}?", f":OUTP{o}:IMP?", f":OUTP{o}:IMP:EXT?", ":HOLD?",
              f":VOLT{o}:HIGH?", f":VOLT{o}:HIGH? MIN", f":VOLT{o}:HIGH? MAX",
              f":VOLT{o}:LOW?", f":VOLT{o}:LOW? MIN", f":VOLT{o}:LOW? MAX",
              f":VOLT{o}?", f":VOLT{o}? MIN", f":VOLT{o}? MAX",
              f":VOLT{o}:LIM:STAT?"]:
        print(f"{q:24s} {_gpib_query(q)}")

def A81104A_INIT(base_delay=None, hlev=0.2):
    # One time setup: single pulse per falling edge of INJ_OUT_1 on EXT INPUT, delay base_delay.
    # hlev = 2*v_asic as in A81104A_HLEV_SWEEP (default 0.2: v_asic = 100 mV), corrected for the attenuator.
    # Prints the error queue at the end: commands the instrument did not accept show up there.
    st = A81104A_SETTINGS
    o = st["out"]
    if base_delay is None:
        base_delay = PULSEGEN["A81104A"]["base_delay"]
    cmds = [
        "*CLS",
        f":OUTP{o} OFF",
        ":DIG:PATT OFF",                       # pulse mode, not pattern mode
        ":ARM:SOUR EXT",                       # each EXT INPUT edge starts the pulses
        ":ARM:SENS EDGE",
        f":ARM:SLOP {st['trig_slope']}",
        ":ARM:IMP 1E4OHM",                     # EXT INPUT 10 kOhm: 50 Ohm loads the CaR INJ_1 trigger below the threshold (no triggers)
        f":ARM:LEV {st['trig_level']}V",
        ":TRIG:COUN 1",                        # one pulse per trigger
        ":PULS:PER 10us",                      # internal period, only sets the limits (one pulse per trigger)
        f":PULS:WIDT{o} {st['width']:.6e}S",
        f":PULS:DEL{o}:HOLD TIME",
        f":PULS:DEL{o} {base_delay:.6e}S",
        f":PULS:TRAN{o}:LEAD {st['rise']:.6e}S",
        f":PULS:TRAN{o}:TRA:AUTO ON",          # trailing edge = leading edge
        f":OUTP{o}:IMP 50OHM",                 # source impedance
        f":OUTP{o}:IMP:EXT 1E6OHM",            # expected load: high impedance, levels are open circuit voltages (BK4600 convention). NOT "1MOHM": in SCPI M = milli
        ":HOLD VOLT",
        f":VOLT{o}:HIGH {_a81104a_hlev(hlev):.6f}V",  # high first: low = 0 V with the old high could fall below the minimum amplitude
        f":VOLT{o}:LOW 0V",
        f":OUTP{o}:POL {st['polarity']}",
        f":OUTP{o} ON",
    ]
    print(_gpib_query("*IDN?"))
    errors = []
    for cmd in cmds:
        print(cmd)
        _gpib_write(cmd)
        errors += A81104A_ERRORS()             # errors are printed right under the command that caused them
    print(f"Delay readback: {A81104A_GET_DLAY()} s")
    print(f"Levels readback: high {_gpib_query(f':VOLT{o}:HIGH?')} V, low {_gpib_query(f':VOLT{o}:LOW?')} V")
    errors += A81104A_ERRORS()
    if errors:
        print(f"A81104A_INIT done with {len(errors)} error(s), see above. A81104A_LIMITS() shows the allowed ranges.")
    else:
        print("A81104A_INIT done, no errors")

def _a81104a_hlev(HLEV):
    # HLEV = 2*v_asic (open circuit at the board) -> high level to program on the 81104A, corrected for the attenuator
    st = A81104A_SETTINGS
    gain = st["atten_gain"] if st["atten_gain"] is not None else 10**(-st["atten_dB"]/20)
    hlev = HLEV/gain
    if hlev < st["min_hlev"] - 1e-9:
        raise ValueError(f"81104A: v_asic = {HLEV/2*1e3:.2f} mV needs {hlev*1e3:.1f} mV open circuit, below the minimum {st['min_hlev']*1e3:.0f} mV "
                         f"(smallest v_asic with {st['atten_dB']} dB: {st['min_hlev']*gain/2*1e3:.1f} mV). Use a larger attenuator.")
    if hlev > st["max_hlev"] + 1e-9:
        raise ValueError(f"81104A: v_asic = {HLEV/2*1e3:.1f} mV needs {hlev:.2f} V open circuit, above the maximum {st['max_hlev']:.1f} V "
                         f"(largest v_asic with {st['atten_dB']} dB: {st['max_hlev']*gain/2*1e3:.0f} mV). Use a smaller attenuator.")
    return hlev

def A81104A_HLEV_SWEEP(HLEV=0.2, max_retries=10, retry_delay=0.1):
    # HLEV = 2*v_asic as for the BK4600 / SDG7102A; corrected for the attenuator before programming
    _gpib_write(f":VOLT{A81104A_SETTINGS['out']}:HIGH {_a81104a_hlev(HLEV):.6f}V", max_retries=max_retries, retry_delay=retry_delay)

def A81104A_SET_DLAY(DLAY, max_retries=10, retry_delay=0.1):
    _gpib_write(f":PULS:DEL{A81104A_SETTINGS['out']} {DLAY:.6e}S", max_retries=max_retries, retry_delay=retry_delay)

def A81104A_GET_DLAY(max_retries=10, retry_delay=0.1):
    out = _gpib_query(f":PULS:DEL{A81104A_SETTINGS['out']}?", max_retries=max_retries, retry_delay=retry_delay)
    try:
        return float(out)
    except (TypeError, ValueError):
        return None


def pulseGenName(pulseGen=None):
    # pulse generator key for a scan: pulseGen if given, else the bench default FNAL_SETTINGS["pulseGen"] (BK4600 if not set)
    if pulseGen is None:
        try:
            pulseGen = FNAL_SETTINGS.get("pulseGen", "BK4600")
        except NameError:
            pulseGen = "BK4600"
    if pulseGen not in PULSEGEN:
        raise ValueError(f"Unknown pulse generator '{pulseGen}', choose one of {list(PULSEGEN)}")
    return pulseGen

# Pulse generators that can inject the test pulse, with the burst trigger delay
# set in their INIT function. Used by the pulse delay scan (B6).
# Optional "set_dlay" / "get_dlay": delay setter and readback for generators without the BK / Siglent BTWV DLAY command
PULSEGEN = {
    "BK4600"   : {"path" : '/dev/usbtmc0', "channel" : "C1",    "base_delay" : 6.68e-7,  "set_hlev" : BK4600HLEV_SWEEP},
    "SDG7102A" : {"path" : '/dev/usbtmc1', "channel" : CHANNEL, "base_delay" : 2.106e-6, "set_hlev" : SDG7102A_SWEEP},
    # base_delay is a placeholder: measure on the scope so the pulse reaches the chip at the same time after the INJ_OUT_1 edge as on the BK bench
    "A81104A"  : {"path" : "Prologix GPIB", "channel" : A81104A_SETTINGS["out"], "base_delay" : 6.68e-7, "set_hlev" : A81104A_HLEV_SWEEP,
                  "set_dlay" : A81104A_SET_DLAY, "get_dlay" : A81104A_GET_DLAY},
}

def PULSEGEN_DLAY_SWEEP(DLAY, pulseGen="BK4600", verify=False, max_retries=10, retry_delay=0.1):
    # Set the burst trigger delay (time from the external trigger edge to the injected pulse)
    # DLAY is in seconds. Only the delay changes, everything else is set once by BK4600_INIT() / SDG7102A_INIT().
    # If verify is True, read back BTWV? and return the DLAY value reported by the pulse generator (in seconds)
    pg = PULSEGEN[pulseGen]
    if "set_dlay" in pg:
        pg["set_dlay"](DLAY, max_retries=max_retries, retry_delay=retry_delay)
        if not verify:
            return None
        readback = pg["get_dlay"](max_retries=max_retries, retry_delay=retry_delay)
        if readback is None:
            print(f"WARNING: could not read back the delay from {pulseGen}")
        elif abs(readback - DLAY) > 1e-12:
            print(f"WARNING: requested delay {DLAY:.6e}S but {pulseGen} reports {readback:.6e}S")
        return readback
    _usbtmc_write(pg["path"], f"{pg['channel']}:BTWV DLAY,{DLAY:.6e}S", max_retries=max_retries, retry_delay=retry_delay)
    if not verify:
        return None

    # response looks like "C1:BTWV STATE,ON,...,DLAY,6.68e-07S,..."
    out = _usbtmc_query(pg["path"], f"{pg['channel']}:BTWV?", max_retries=max_retries, retry_delay=retry_delay)
    readback = None
    if out:
        fields = out.strip().split(",")
        if "DLAY" in fields:
            readback = float(fields[fields.index("DLAY")+1].rstrip("S"))
    if readback is None:
        print(f"WARNING: could not read back DLAY from {pulseGen}")
    elif abs(readback - DLAY) > 1e-12:
        print(f"WARNING: requested DLAY {DLAY:.6e}S but {pulseGen} reports {readback:.6e}S")
    return readback


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
