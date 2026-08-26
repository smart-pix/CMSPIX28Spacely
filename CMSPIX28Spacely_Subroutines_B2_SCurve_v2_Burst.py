# spacely
from Master_Config import *

# python modules
import sys
try:
    import tqdm
    import numpy as np
    import math
    import h5py
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately


#-----------------------------------------------------------------------
# PreProgSCurveBurst_v2 function - FULL SCAN CHAIN BURST
#-----------------------------------------------------------------------
# Optimized S-curve using firmware buffer to accumulate full 24-word scan
# chain readouts, then bulk-reads via stream_memory()
#
# Key improvements over PreProgSCurve_v2:
# - Firmware accumulates scan chain data in 4096-bit buffer (128 words)
# - Reads 5-6 samples' worth at once (~120-144 words) via stream_memory()
# - Expected speedup: ~120× (200 batch reads vs 24,000 per-word reads)
# - Data stored locally on FPGA, transferred once after test completes
#
# Firmware requirements:
# - DATA_ARRAY_1 (opcode 0xD) supports full 24-word scan chain accumulation
# - Auto-appends each scan readout to buffer (no overflow handling needed)
# - stream_memory() returns buffered words as binary data
#-----------------------------------------------------------------------

def PreProgSCurveBurst_v2(
        scanLoadPhase = '26',
        scan_load_delay = '13',
        startBxclkState = '0',
        bxclk_delay = '12',
        bxclk_period = '28',
        injection_delay = '1E',
        scanLoopBackBit = '0',
        test_sample = '0F',
        test_delay = '14',
        v_min = 0.01,
        v_max = 0.4,
        v_step = 0.01,
        nsample = 1000,
        nPix = 0,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        dateTime = None,
        testType = "Single",
        parameter = None,
        tsleep = 100e-3,  # Sleep time for pulse generator settling
        batch_size = 5,   # How many samples to accumulate before reading buffer
):

    """
    PreProgSCurveBurst_v2: Full scan chain S-curve with FPGA buffering.

    Accumulates full 24-word scan chain outputs in firmware buffer, then
    bulk-reads via stream_memory() to achieve 120× speedup.

    Args:
        batch_size: How many samples' worth of data to accumulate before
                   flushing buffer. Default 5 = ~120 words (fits in 128-word buffer).
                   Can be tuned based on wordList length.
    """

    print("\n" + "="*70)
    print("PreProgSCurveBurst_v2: Full Scan Chain with Stream Buffering")
    print("="*70)

    x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
    scanLoadPhase1 = hex(int(x[:2], 2))[2:]
    scanLoadPhase0 = hex(int(x[2:], 2))[2:]

    # Configure static arrays (same as PreProgSCurve)
    hex_lists = [
        ["4'h2", "4'h2", f"4'h{scanLoadPhase0}", "1'h0", f"6'h{scan_load_delay}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclk_delay}", f"6'h{bxclk_period}"],
        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"19'h0"],
    ]
    sw_write32_0(hex_lists)

    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # For full scan chain (24 words), calculate words to read
    nWord = 24
    ipixel = (V_PORT["vdda"].get_current())*1000000/(512*10)

    bxclk_period_inMhz = 400/int(bxclk_period, 16)
    injection_delay_in_ns = int(injection_delay,16)*2.5
    bxclk_delay_in_ns = int(bxclk_delay,16)*2.5

    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}_BurstV2"
    testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_pixPower{ipixel*0.9:.3f}_nPix{nPix}_streamBurstV2"

    outDir = os.path.join(dataDir, chipInfo, testInfo, "")
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # Main voltage sweep loop
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):
        v_asic = round(i, 3)
        if v_asic > 0.9:
            v_asic = 0
            return

        SDG7102A_SWEEP(v_asic*2)
        time.sleep(tsleep)

        save_data = []
        batch_count = 0
        batch_buffer = []  # Accumulate parsed words from one batch

        # ====================================================================
        # SAMPLE LOOP: Batch samples, then flush to local storage
        # ====================================================================
        for j in tqdm.tqdm(range(nsample), desc="Number of Samples", leave=False):

            # Configure and execute test
            hex_lists = [
                [
                    "4'h2",  # firmware id
                    "4'hF",  # op code for execute
                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                    f"6'h{injection_delay}",
                    f"1'h{scanLoopBackBit}",
                    "4'h8",  # Test 2 (full scan chain)
                    f"6'h{test_sample}",
                    f"6'h{test_delay}"
                ]
            ]
            sw_write32_0(hex_lists)

            # Determine which words to read (full scan chain or single pixel)
            if nPix == None:
                wordList = list(range(24))
            else:
                if(int(((nPix-1)*3+1)/32) == int(((nPix-1)*3+3)/32)):
                    wordList = [int(((nPix-1)*3+1)/32)]
                else:
                    wordList = [int(((nPix-1)*3+1)/32), int(((nPix-1)*3+3)/32)]

            # Send read commands for all words in this sample
            # (These accumulate in firmware buffer, no reads yet)
            for iW in wordList:
                address = "8'h" + hex(iW)[2:]
                hex_lists = [
                    ["4'h2", "4'hC", address, "16'h0"]  # OP_CODE_R_DATA_ARRAY_0
                ]
                sw_write32_0(hex_lists)

            batch_count += 1

            # ================================================================
            # FLUSH BATCH: When buffer filled or last sample, read everything
            # ================================================================
            if batch_count >= batch_size or j == nsample - 1:

                # Calculate total words to read from buffer
                total_words_in_batch = batch_count * len(wordList)

                # Resend all read commands (they queue in firmware buffer)
                sample_start = j - batch_count + 1
                for sample_offset in range(batch_count):
                    for iW in wordList:
                        address = "8'h" + hex(iW)[2:]
                        hex_lists = [
                            ["4'h2", "4'hC", address, "16'h0"]
                        ]
                        sw_write32_0(hex_lists)

                # Read entire batch at once via stream
                try:
                    sg.log.debug(f"Reading batch: {batch_count} samples × {len(wordList)} words = {total_words_in_batch} words total")

                    stream_raw = sg.INSTR["car"].stream_memory("sw_read32_0", total_words_in_batch)

                    # Parse stream response to array of integers
                    batch_words = parse_stream_response_burst(stream_raw, total_words_in_batch)

                    sg.log.debug(f"  → Got {len(batch_words)} words from stream")

                    # Parse batch into individual samples
                    for sample_offset in range(batch_count):
                        words = ["0"*32] * nWord

                        for word_idx, iW in enumerate(wordList):
                            global_idx = sample_offset * len(wordList) + word_idx
                            if global_idx < len(batch_words):
                                words[iW] = int_to_32bit(batch_words[global_idx])[::-1]

                        # Save sample
                        s = [int(i) for i in "".join(words)]
                        save_data.append(s)

                except Exception as e:
                    sg.log.warning(f"Stream read failed: {e}. Falling back to per-word reads.")

                    # Fallback: per-word reads for this batch
                    for sample_offset in range(batch_count):
                        words = ["0"*32] * nWord

                        for iW in wordList:
                            address = "8'h" + hex(iW)[2:]
                            hex_lists = [
                                ["4'h2", "4'hC", address, "16'h0"]
                            ]
                            sw_write32_0(hex_lists)
                            sw_read32_0, _, _, _ = sw_read32()
                            words[iW] = int_to_32bit(sw_read32_0)[::-1]

                        s = [int(i) for i in "".join(words)]
                        save_data.append(s)

                batch_count = 0

        # ====================================================================
        # Save epoch data
        # ====================================================================
        save_data = np.stack(save_data, 0)
        save_data = save_data[:, 0:-3]
        save_data = save_data.reshape(-1, 255, 3)
        save_data = save_data[:, nPix]
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)

    print("="*70)
    print("✓ PreProgSCurveBurst_v2 complete")
    print("="*70 + "\n")

    return None


def parse_stream_response_burst(stream_data, N):
    """
    Convert stream_memory() output to array of N 32-bit integers.

    Handles multiple return formats:
    - bytes: raw binary data (little-endian 32-bit words)
    - str: file path (read and parse)
    - list: already parsed

    Args:
        stream_data: Raw output from stream_memory()
        N: Number of 32-bit words expected

    Returns:
        List of N integers
    """
    if isinstance(stream_data, str):
        # File path — read file
        try:
            with open(stream_data, 'rb') as f:
                raw_bytes = f.read()
        except Exception as e:
            sg.log.error(f"Failed to read stream file {stream_data}: {e}")
            return [0] * N

    elif isinstance(stream_data, bytes):
        # Already raw bytes
        raw_bytes = stream_data

    else:
        # Might be a list or other iterable
        return list(stream_data)[:N]

    # Parse as N 32-bit little-endian integers
    words = []
    for i in range(N):
        if i*4 + 4 <= len(raw_bytes):
            word = int.from_bytes(raw_bytes[i*4:(i+1)*4], byteorder='little')
        else:
            word = 0  # Pad with zeros if data truncated
        words.append(word)

    return words
