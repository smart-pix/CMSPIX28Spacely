# SPROCKET1 Test Pixel Routines


R0_VTEST_MIN = 470
R0_VTEST_MAX = 515
R0_VTEST_INCR = 1000



# config_AWG_as_Skipper - Sets up the AWG to mimic the output of a Skipper-CCD
# source follower, based on the external trigger.
#
# GZ 6/9/2023: I removed all flush_buffer() calls here; you shouldn't manipulate buffers externally
#              unless there's some proven bug existing that it needs it
def config_AWG_as_Skipper(pedestal_mag_mV: int, signal_mag_mV: int) -> None:
    sg.AWG.set_output(False)

    #Output a user-defined function...
    sg.AWG.send_line_awg("FUNC USER")

    #Set up the skipper arbitrary waveform
    sg.AWG.send_line_awg("FREQ 1000000") #50 ns / div
    sg.AWG.send_line_awg("VOLT:OFFS 2.5") #4.0 Vreset

    #NOTE: With Vpp = 2.0V, +1.0 = +1.0V and -1.0 = -1.0V.
    p = round(pedestal_mag_mV / 1000,6)
    s = round((signal_mag_mV + pedestal_mag_mV)/1000,6)

    #wave = [0,-p,-p,-p,-p,-p,-s,-s,-s,-s,-s,-s,0,0,0,0,0,0,0,0]

    # Modified timing:
    wave = [0,-p,-p,-p,-s,-s,-s,-s,-s,-s,0,0,0,0,0,0,0,0]

    print(wave)

    sg.AWG.send_line_awg("DATA VOLATILE, "+", ".join([str(x) for x in wave])+"\n")

    #NOTE: There is a bug in the AWG, where sending data w/ DATA VOLATILE
    #will completely scramble the Vpp magnitude. So we need to write Vpp
    #just after sending data. EDIT: Still doesn't solve the problem. :(
    sg.AWG.send_line_awg("VOLT 2.0") #2 Volt pp magnitude
    #sg.AWG.send_line("VOLT:HIGH 3.5") #2 Volt pp magnitude
    #sg.AWG.send_line("VOLT:LOW 1.5") #2 Volt pp magnitude

    #Bursts will be triggered by Trig In (w/ a positive slope)
    #Note: Trig In will be connected to PostSamp
    sg.AWG.send_line_awg("BURS:MODE TRIG")
    sg.AWG.send_line_awg("TRIG:SOUR EXT")
    sg.AWG.send_line_awg("TRIG:SLOP POS")
    #Each Trig In will result in 1 burst
    sg.AWG.send_line_awg("BURS:NCYC 1")

    #Enable bursts
    sg.AWG.send_line_awg("BURS:STAT ON")

    sg.AWG.send_line_awg("FUNC:USER VOLATILE")

    sg.AWG.set_output(True)



def ROUTINE0_CDAC_Trim():
    """r0: Measure the DNL for every CDAC Trim code, and report the best."""
    print(ROUTINE0_CDAC_Trim.__doc__)

    global R0_VTEST_MIN, R0_VTEST_MAX, R0_VTEST_INCR

    if not check_dependencies(["ARDUINO_CONNECTED",["EMULATE_ASIC","AWG_CONNECTED"]]):
        return

    if EMULATE_ASIC:
        print("**ASIC will be EMULATED by ARDUINO**")

    Vtest_min_mV=R0_VTEST_MIN
    Vtest_max_mV=R0_VTEST_MAX
    increment_uV=R0_VTEST_INCR

    print("STATIC VALUES:\n\t> Vtest_min_mV = "+str(Vtest_min_mV)+"\n\t> Vtest_max_mV = "\
          +str(Vtest_max_mV)+"\n\t> increment_uV = "+str(increment_uV))

    print("""REQUIREMENTS:
    > Chip voltages are powered on.
    > AWG is connected to Vtest.
    > VINSF is connected to 0.0V""")

    input("Press Enter to proceed.")


    filename = reserve_dated_file(f"CapTrim DNL Sweep", directory='output/dnl')
    logfilename = reserve_dated_file(f"CapTrim DNL Sweep", directory='output/dnl', extension='log')
    logfile = open(logfilename,'w')

    with open(filename, 'wb') as write_file:
        write_file.write(b'CapTrim Code,CapTrim String,DNL\n')

        for captrim_code in range(0,64):
            captrim_string = format(captrim_code,'b').zfill(6)

            #Reverse the string because in the set_config HAL command, CapTrim is reported as little-endian.
            # Range2 = 0, TestEn = 1
            command_ng(log, port, "sc:"+captrim_string[::-1]+"01")

            print(progress_pct(captrim_code,63)," Finding DNL for CapTrim=0b"+captrim_string)

            dnl = find_DNL(Vtest_min_mV=Vtest_min_mV,Vtest_max_mV=Vtest_max_mV,increment_uV=increment_uV, logfile=logfile)

            write_file.write((",".join([str(x) for x in [captrim_code,captrim_string,dnl]])+"\n").encode())

    logfile.close()
    print("ROUTINE 0 Complete!")



def fix_latchup():
    V_PORT["VDD_ASIC"].set_voltage(1.2,current_limit=1)

#Simply do one conversion for each CapTrim value.
def ROUTINE1_CapTrim_Debug():

    for captrim_code in range(0,64):
        captrim_string = format(captrim_code,'b').zfill(6)
        #Reverse the string because in the set_config HAL command, CapTrim is reported as little-endian.
        # Range2 = 0, TestEn = 1
        command_ng(log, port, "sc:"+captrim_string[::-1]+"01")
        r = command_ng(log, port, "conv")
        r = r.replace("conv","").replace("?","").strip()
        print(captrim_code, captrim_string, int(r,2))

def ROUTINE2_Full_Channel_Scan():
    """r2: Do a Vin sweep, across the full channel (including preamplifier)."""
    Vin_sweep_full_chain(Vtest_min_mV=100,Vtest_max_mV=1000,increment_uV=10000)


def ROUTINE3_FPGA_Buffer_Lint():
    """r3: Send patterns to GlueFPGA and confirm they are read back."""


    print("""REQUIREMENTS:
        > ASIC should NOT be connected.
        """)
    input("Press Enter to continue...")
    
    fpga = NiFpga(log, "PXI1Slot5")

    #Must be a GlueDirect bitfile.
    fpga.start("C:\\Users\\Public\\Documents\\LABVIEWTEST\\GlueDirectBitfile_6_22_a.lvbitx")
    #time.sleep(1)

    dbg = NiFpgaDebugger(log, fpga)

    #Default values for several registers.
    fpga_default_config = { "Write_to_Mem" : False,
                        "Read_from_Mem": False,
                        "Run_Pattern"  : False,
                        "Buffer_In_Size": 1024,
                        "Buffer_Pass_Size":1024,
                        "FPGA_Loop_Dis": False,
                        "SE_Data_Dir":65535,
                        "SE_Data_Default":60,
                        "Set_Voltage_Family":True,
                        "Voltage_Family":4}

    #Set all registers to their default values.
    for cfg in fpga_default_config.keys():
        dbg.interact("w", cfg, fpga_default_config[cfg])

    print(dbg.interact("r","Set_Voltage_Done"))
    print(dbg.interact("r","Voltage_Family"))
    print(dbg.interact("r","Set_Voltage_Family"))
    testpat = PatternRunner(log,fpga, "C:\\Users\\Public\\Documents\\Glue_Waveforms\\test_iospec.txt")

    #NOTE: FPGA Needs > 2 seconds of delay in between setup and running the first test pattern!
    time.sleep(3)

    print("~ Test Pattern 1 ~")
    tp1_in = [i for i in range(31)]
    tp1_out = testpat.run_pattern(tp1_in)
    print("IN:",tp1_in)
    print("OUT:",tp1_out)

    print("~ Test Pattern 2 ~")
    tp2_in = [i for i in range(50000)] *2
    tp2_out = testpat.run_pattern(tp2_in,outfile="test_out.txt")
    print("IN:",abbreviate_list(tp2_in))
    print("OUT:",abbreviate_list(tp2_out))
    
    diagnose_fifo_timeout(tp2_out)
