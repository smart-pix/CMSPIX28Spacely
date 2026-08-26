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


def PreProgSCurve_v2_DEBUG(
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
        debug_samples = 2,  # Only test burst on first N samples
):
    """
    DEBUG VERSION: Tests burst read capabilities within the S-curve loop.
    Identical to v2 except it tests stream_memory() on first few samples.
    """

    print("\n" + "="*70)
    print(f"DEBUG S-CURVE: Will test burst read on first {debug_samples} samples")
    print("="*70)

    x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
    scanLoadPhase1= hex(int(x[:2], 2))[2:]
    scanLoadPhase0= hex(int(x[2:], 2))[2:]
    hex_lists = [
        ["4'h2", "4'h2", f"4'h{scanLoadPhase0}", "1'h0",f"6'h{scan_load_delay}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclk_delay}", f"6'h{bxclk_period}"],
        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"19'h0"],
    ]
    sw_write32_0(hex_lists)

    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    nWord = 24
    ipixel = (V_PORT["vdda"].get_current())*1000000/(512*10)

    bxclk_period_inMhz = 400/int(bxclk_period, 16)
    injection_delay_in_ns = int(injection_delay,16)*2.5
    bxclk_delay_in_ns = int(bxclk_delay,16)*2.5

    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}_DEBUG"
    testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}"

    outDir = os.path.join(dataDir, chipInfo, testInfo, "")
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # Only test first voltage step to speed up
    test_voltages = vasic_steps[:1]

    for i in tqdm.tqdm(test_voltages, desc="Voltage Step"):
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0
            return

        SDG7102A_SWEEP(v_asic*2)

        save_data = []
        debug_results = {
            'per_word': [],
            'stream_batch': [],
            'mismatch_count': 0,
        }

        for j in tqdm.tqdm(range(min(nsample, 10)), desc="Number of Samples", leave=False):  # Only 10 samples for speed

            # write configuration
            hex_lists = [
                [
                    "4'h2", "4'hF", "1'h1",
                    f"6'h{injection_delay}",
                    f"1'h{scanLoopBackBit}",
                    "4'h8",
                    f"6'h{test_sample}",
                    f"6'h{test_delay}"
                ]
            ]
            sw_write32_0(hex_lists)

            if nPix == None:
                wordList = list(range(24))
            else:
                if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
                    wordList = [int(((nPix-1)*3+1)/32)]
                else:
                    wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]

            words = ["0"*32] * nWord

            # ============================================================
            # DEBUG TEST: Compare per-word vs stream reads
            # ============================================================
            if j < debug_samples:
                sg.log.info(f"\n{'='*60}")
                sg.log.info(f"SAMPLE {j}: Testing burst read")
                sg.log.info(f"{'='*60}")

                # Method 1: Per-word reads (known to work)
                sg.log.info(f"\nMethod 1: Per-word reads")
                per_word_vals = []
                for iW in wordList:
                    address = "8'h" + hex(iW)[2:]
                    hex_lists = [
                        ["4'h2", "4'hC", address, "16'h0"]
                    ]
                    sw_write32_0(hex_lists)
                    word = sg.INSTR["car"].get_memory("sw_read32_0")
                    per_word_vals.append(word)

                sg.log.info(f"  → {len(per_word_vals)} words read")
                sg.log.info(f"  → First 5: {[hex(w) for w in per_word_vals[:5]]}")
                debug_results['per_word'].append(per_word_vals)

                # Method 2: Batch stream reads
                sg.log.info(f"\nMethod 2: Batch stream_memory()")

                # Send all read commands
                for iW in wordList:
                    address = "8'h" + hex(iW)[2:]
                    hex_lists = [
                        ["4'h2", "4'hC", address, "16'h0"]
                    ]
                    sw_write32_0(hex_lists)

                # Now try to read batch
                stream_raw = sg.INSTR["car"].stream_memory("sw_read32_0", len(wordList))
                sg.log.info(f"  stream_memory() returned: {type(stream_raw).__name__}")

                if isinstance(stream_raw, bytes):
                    sg.log.info(f"  → Byte length: {len(stream_raw)}")
                    if len(stream_raw) > 0:
                        sg.log.info(f"  → First 16 bytes (hex): {stream_raw[:16].hex()}")

                        # Parse as integers
                        stream_vals = []
                        for idx in range(min(len(wordList), len(stream_raw) // 4)):
                            word = int.from_bytes(stream_raw[idx*4:(idx+1)*4], 'little')
                            stream_vals.append(word)
                        sg.log.info(f"  → Parsed {len(stream_vals)} words")
                        sg.log.info(f"  → First 5: {[hex(w) for w in stream_vals[:5]]}")
                        debug_results['stream_batch'].append(stream_vals)

                        # Compare
                        if stream_vals == per_word_vals:
                            sg.log.info(f"\n✓ SUCCESS: Stream data matches per-word!")
                        else:
                            sg.log.warning(f"\n✗ MISMATCH: Stream data differs from per-word")
                            sg.log.warning(f"  Differences at indices: {[i for i in range(len(per_word_vals)) if i < len(stream_vals) and per_word_vals[i] != stream_vals[i]]}")
                            debug_results['mismatch_count'] += 1
                    else:
                        sg.log.warning(f"\n✗ FAIL: stream_memory() returned empty bytes!")
                        sg.log.warning(f"  This means the 128-word buffer isn't capturing data")

                elif isinstance(stream_raw, list):
                    sg.log.info(f"  → List length: {len(stream_raw)}")
                    sg.log.info(f"  → Content: {stream_raw[:5]}")
                    debug_results['stream_batch'].append(stream_raw)

                sg.log.info(f"{'='*60}\n")

            # ============================================================
            # Continue with normal read (use per-word for now)
            # ============================================================
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

        # Save data
        save_data = np.stack(save_data, 0)
        save_data = save_data[:, 0:-3]
        save_data = save_data.reshape(-1, 255, 3)
        save_data = save_data[:, nPix]
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)

        # Print debug summary
        sg.log.info(f"\n{'='*70}")
        sg.log.info(f"DEBUG SUMMARY:")
        sg.log.info(f"  Per-word reads: {len(debug_results['per_word'])} samples tested")
        sg.log.info(f"  Stream reads: {len(debug_results['stream_batch'])} samples tested")
        sg.log.info(f"  Mismatches: {debug_results['mismatch_count']}")

        if debug_results['mismatch_count'] == 0 and len(debug_results['stream_batch']) > 0:
            sg.log.info(f"\n✓ BURST READ WORKS! Ready to implement batching.")
        elif len(debug_results['stream_batch']) == 0:
            sg.log.warning(f"\n✗ stream_memory() is not returning data")
            sg.log.warning(f"  Check: Is the 128-word buffer enabled in firmware?")
        sg.log.info(f"{'='*70}\n")

    return debug_results
