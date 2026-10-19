# spacely
try:
    from Master_Config import *
except:
    print("Cannot import Master_Config likely you are not running spacely.")

# python modules
import sys
try:
    # os settings
    import os
    os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices'
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    # Standard library imports
    import math
    import re
    import shutil
    import h5py
    from fxpmath import Fxp
    import pandas as pd
    import csv

    # Third-party imports
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns
    import tensorflow as tf
    from pandas import read_csv
    from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error
    from sklearn.model_selection import StratifiedKFold, train_test_split
    from sklearn.preprocessing import StandardScaler

    # TensorFlow imports
    from tensorflow.keras import datasets, layers, models
    from tensorflow.keras.callbacks import CSVLogger, EarlyStopping
    from tensorflow.keras.layers import Activation, Conv2D, Dense, Dropout, Flatten, Input, Lambda, MaxPooling2D
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.losses import SparseCategoricalCrossentropy
    from tensorflow.keras.metrics import SparseCategoricalAccuracy
    from tensorflow.keras.utils import Progbar
    from tensorflow.keras.models import clone_model

    # QKeras imports
    from qkeras import *

    # Let qkeras' fused *Batchnorm layers survive a save/load round trip under
    # Keras 3 (see qkeras_keras3_compat for the details). No-op if the installed
    # qkeras already handles it.
    #
    # Master_Config imports this file as a dotted package module from the
    # PySpacely root ("spacely-asic-config.<TARGET>.<TARGET>_Subroutines_..."),
    # so this directory is not on sys.path and a bare import of a sibling module
    # does not resolve. Add it explicitly rather than relying on the cwd.
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.append(_HERE)
    from qkeras_keras3_compat import patch_qkeras_batchnorm_synchronized
    patch_qkeras_batchnorm_synchronized()

    # Bit-accurate C++ mirror of the RTL, for separating fixed-point deviation
    # from readout error in asicFidelityCheck(). Optional: it needs g++ and the
    # newModelWeights/ tree, and the diagnostic degrades to QKeras-only without
    # it rather than failing.
    try:
        import hls_reference
    except Exception as _hls_err:
        hls_reference = None
        _HLS_IMPORT_ERROR = _hls_err

except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately



# Fixed-point format of the *output* layer's (dense2) bias, as both the qkeras
# quantizer that trains it and the Fxp format prepareWeights() encodes it with.
#
# Why this is a knob: on the 1000_2000_3000 dataset the trained bias sits pinned
# at both rails of the default 4-bit/0-integer grid -- [-0.25, -1.0, +0.875] on a
# grid of [-1, +0.875] step 0.125 -- while the loss-optimal per-class logit
# offsets for that dataset's class prior are about [+2.0, -2.25, +0.03]. The
# network cannot represent the prior it needs, which costs roughly 0.54 of
# cross-entropy and 16 points of accuracy (measured: fitting 3 free logit offsets
# on the train split takes held-out val_loss 0.864 -> 0.326, acc 70.4% -> 86.7%).
# Giving the output bias integer bits is the cheapest way to buy that back.
#
# !! CHANGING THIS REQUIRES A MATCHING FIRMWARE CHANGE. !!
# prepareWeights() packs b5/w5/b2/w2 into one fixed-length scan-chain bit vector.
# n_word here sets the b5 field width, so raising it lengthens the chain (3 extra
# bits per added bit of width) and shifts every field after it; the chip's
# fixed-point interpretation of that field has to move with it. n_int changes the
# implied binary point, i.e. the scale at which the chip's adder combines bias
# with the w5 partial sums -- also a firmware-side constant.
#
# Left at the current on-chip format so nothing changes silently. Set to e.g.
# (4, 2) to keep the field width and rescale (range +/-4, step 0.5), or (6, 2)
# for range +/-4 at step 0.125, once the firmware side is ready.
OUTPUT_BIAS_FXP = (4, 0)  # (n_word, n_int)

# Keep QDenseBatchnorm's batchnorm moving statistics fixed during training.
# Correct when fine-tuning a converged checkpoint (the default flow here); set
# False if you ever train one of these models from scratch, where the stats do
# need to adapt. See freezeBatchnormStats().
FREEZE_BATCHNORM_STATS = True


# ---------------------------------------------------------------------------
# Per-experiment defaults: the knobs that have to move together when the
# operating point changes.
#
# These are defaults only. DNNTraining() and asicFidelityCheck() take every one
# of them as an argument. Spacely can only invoke ~r9/~r10 with *default*
# arguments, so the routine signatures in CMSPIX28Spacely_Routines.py are where
# a run launched from the Spacely prompt gets configured; call
# DNNTraining(...) / asicFidelityCheck(...) directly to override without
# editing any file.
# ---------------------------------------------------------------------------

# Discriminator thresholds in electrons, (vth0, vth1, vth2).
VTH_DEFAULT = (700, 1400, 2100)

# Pattern-generator high level (V) for the injection pulse. Retuned per
# threshold set, so it travels with VTH.
PG_HLEV_DEFAULT = 0.2

# Readout time slice scored as "the answer". The chip reports 40 slices per
# event; this picks one. It is NOT a settled value being held -- measured on
# the 2026-08-30 run, only 7.5% of events read the same class across the live
# window (slices 13-22) and 18.4% pass through the invalid [1,1] state
# somewhere in it. See scanTimeSlices(), which prints the whole curve.
TIMESTAMP_DEFAULT = 19

DATA_ROOT = ("/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/"
             "tmp_16x16_hlevOptimized")

# Checkpoint fine-tuning starts from. Note this is NOT derived from VTH_DEFAULT:
# the whole point of the flow is to start from a model converged at one
# threshold and adapt it to another, so the two are deliberately independent.
INIT_MODEL_DEFAULT = os.path.join(
    DATA_ROOT, "trainedModel_850_1700_2550", "model0", "models",
    "tmp_padded_noscaling_qkeras_foldbatchnorm_d58w4a8model_0.h5")


def datasetDir(vth=VTH_DEFAULT, root=DATA_ROOT):
    """Directory holding yprofiles.csv / clslabels.csv for a threshold triple.

    The dataset directories under DATA_ROOT are named <vth0>_<vth1>_<vth2> in
    electrons, so deriving the path from the thresholds the chip is actually
    biased at is what keeps the two in sync. Training on 700e- data while the
    chip sat at 1000e- was a real bug, caught only by reading the source; it is
    not expressible if nobody types the path by hand.
    """
    return os.path.join(root, "_".join(str(int(v)) for v in vth))


def vthToVolts(vth):
    """Threshold triple in electrons -> the volts DNN() wants.

    Per-channel linear calibration: each of the three comparators has its own
    offset and slope, so this cannot collapse into one shared formula.
    """
    vth0, vth1, vth2 = vth
    return (round((vth0 - 196.84) / 16960.09, 3),
            round((vth1 - 223.96) / 16853.41, 3),
            round((vth2 - 224.42) / 16922.43, 3))


def decodeReadout(readout_csv, n_slices=40, n_empty=24):
    """Decode EVERY readout time slice, not just one.

    DNN_analyse_2() scores a single slice; the chip already reports 40 of them
    per event and they are sitting unused in readout.csv. Returns
    (n_events, n_slices) of class codes, matching DNN_analyse_2's encoding:
    0/1/2 valid, 3 = the invalid [msb,lsb]=[1,1] state.
    """
    r = np.genfromtxt(readout_csv, delimiter=',', dtype=int).reshape(-1, 4, 64)
    lsb = r[:, -1, n_empty:n_empty + n_slices]
    msb = r[:, -2, n_empty:n_empty + n_slices]
    return msb * 2 + lsb


def scanTimeSlices(readout_csv, y_ref, timestamp=TIMESTAMP_DEFAULT,
                   ref_name="reference"):
    """Disagreement vs y_ref at every readout slice, plus a settling summary.

    Costs no chip time -- it re-reads a readout.csv the chip already produced.

    The point is that the DNN output is not a settled value being held across
    the window: it transitions, and different input vectors settle at different
    slices, so a fixed `timestamp` samples some vectors before they are done.
    Two things to read off the output:

      - whether `timestamp` sits at the minimum of the disagreement curve, and
      - "stable" -- the fraction of events whose scored slice is confirmed by
        both of its neighbours. Events failing that are being sampled mid
        transition and their class is arbitrary.

    A majority vote over the settled part of the window is reported too: it
    costs nothing (the slices are already there) and is immune to any single
    slice landing mid-transition.
    """
    code = decodeReadout(readout_csv)
    y_ref = np.asarray(y_ref).astype(int).reshape(-1)
    if len(code) != len(y_ref):
        print(f"  scanTimeSlices: {len(code)} readout rows vs {len(y_ref)} "
              f"reference rows; skipping")
        return None
    n_ev, n_sl = code.shape

    # Which slices carry information -- see liveWindow. Deliberately shared with
    # it rather than reimplemented here: the two copies drifted once already.
    lo, hi = liveWindow(code)

    # The number every slice below has to beat to mean anything.
    counts = np.bincount(y_ref[y_ref != 3], minlength=3)
    baseline = 1.0 - counts.max() / max(1, counts.sum())

    print(f"\n=== readout time slice scan (vs {ref_name}) ===")
    print(f"  live window = slices {lo}..{hi} (slices whose code varies across "
          f"events); outside it every event reads the same code")
    print(f"  constant-'class {int(counts.argmax())}' baseline: {baseline:.4f} "
          f"-- a dead slice scores this while carrying no information")
    print("  slice  disagree   invalid   stable")
    best_t, best_d = None, 2.0
    for t in range(max(0, lo - 1), min(n_sl, hi + 2)):
        c = code[:, t]
        inv = (c == 3)
        dis = ((c != y_ref) & ~inv).mean()
        if t - 1 >= 0 and t + 1 < n_sl:
            stable = ((code[:, t - 1] == c) & (code[:, t + 1] == c)).mean()
            stable_s = f"{stable:7.3f}"
        else:
            stable_s = "      -"
        # Only the live window is eligible: a dead neighbour slice is printed
        # for context but must never be nominated as "best".
        if lo <= t <= hi and dis < best_d:
            best_t, best_d = t, dis
        mark = "  <-- scored" if t == timestamp else ""
        print(f"   {t:3d}  {dis:8.4f}  {inv.mean():8.4f}  {stable_s}{mark}")

    win = code[:, lo:hi + 1]
    maj = np.full(n_ev, -1)
    for i in range(n_ev):
        v = win[i][win[i] != 3]
        if len(v):
            maj[i] = np.bincount(v).argmax()
    ok = maj >= 0
    print(f"  majority vote over {lo}..{hi}: "
          f"disagree {((maj != y_ref) & ok).mean():.4f}  "
          f"invalid {1 - ok.mean():.4f}")
    print(f"  best single slice: {best_t} at {best_d:.4f}  "
          f"(currently scoring {timestamp})")
    if best_t != timestamp:
        print(f"  => slice {best_t} beats the configured {timestamp}; pass "
              f"timestamp={best_t} to move it.")
    if best_d >= baseline:
        print(f"  !! no slice beats the constant-class baseline ({baseline:.4f}); "
              f"the readout is carrying little class information at any slice.")
    return best_t


def bitErrorBreakdown(y_chip, y_ref, ref_name="reference"):
    """Split the chip's errors into the two readout lines that carry them.

    A class is driven as two bits -- class0=[msb,lsb]=[0,0], class1=[0,1],
    class2=[1,0] -- so every disagreement is a flip of msb (dnn1), lsb (dnn0),
    or both. Which bit flips, and in which direction, is what says which
    discriminator line to retune and which way: a line that reads high when it
    should read low needs its threshold moved so it asserts less readily.

    "both" flips are not a threshold story -- one comparator setting cannot
    flip two lines at once -- and point at timing/settling instead.
    """
    y_chip = np.asarray(y_chip).astype(int).reshape(-1)
    y_ref = np.asarray(y_ref).astype(int).reshape(-1)
    ok = (y_chip != 3) & (y_ref != 3)
    c, r = y_chip[ok], y_ref[ok]

    # class code == msb*2 + lsb for the three valid codes.
    c_msb, c_lsb = c // 2, c % 2
    r_msb, r_lsb = r // 2, r % 2
    msb_bad, lsb_bad = c_msb != r_msb, c_lsb != r_lsb
    err = msb_bad | lsb_bad
    n_err = int(err.sum())

    print(f"\n=== readout bit errors (vs {ref_name}) ===")
    print(f"  {n_err} disagreements over {int(ok.sum())} valid readouts")
    if not n_err:
        return
    both_bad = msb_bad & lsb_bad
    both = int(both_bad.sum())
    for name, line, bad, c_bit in (("msb", "dnn1", msb_bad, c_msb),
                                   ("lsb", "dnn0", lsb_bad, c_lsb)):
        alone = bad & ~both_bad
        n_alone = int(alone.sum())
        # Direction: the chip drove this bit high where the reference wanted it
        # low (line asserts too readily -> make its threshold harder to cross),
        # or the reverse.
        hi_for_lo = int((alone & (c_bit == 1)).sum())
        lo_for_hi = n_alone - hi_for_lo
        print(f"  {name} ({line}) wrong alone : {n_alone:5d} "
              f"({n_alone / n_err:6.1%})   HIGH-for-LOW {hi_for_lo}, "
              f"LOW-for-HIGH {lo_for_hi}")
    print(f"  both wrong               : {both:5d} ({both / n_err:6.1%})"
          f"   <- one threshold cannot flip two lines; timing/settling")


# ---------------------------------------------------------------------------
# Readout decoding strategies.
#
# DNN_analyse_2() scores ONE fixed slice. The chip reports 40 per event, and the
# rest are already in readout.csv -- so every alternative below is free to
# evaluate, and can be re-evaluated offline on a saved readout without touching
# the chip. That matters because the readout is not a settled level being held:
# different input vectors reach their final value at different slices, so a
# fixed slice necessarily samples some of them mid-transition.
# ---------------------------------------------------------------------------

def liveWindow(code, frac=0.01):
    """Slices that carry information, as (lo, hi).

    A dead slice reads [0,0] for every event, which is indistinguishable from a
    genuine class-0 answer -- and since class 0 is ~85% of the data, a dead slice
    SCORES BETTER than the real readout while carrying no information at all.
    Excluding those is the whole job here.

    The test is VARIATION, not activity: a slice is live if at least `frac` of
    events read something other than its most common code. Do NOT go back to
    scoring slices by how often they read non-zero and keeping the busiest --
    that inverts the answer. During the settling transient nearly every line is
    asserted (measured 2026-08-30: slice 14 read class 1 for 77% of events, when
    the true non-class-0 fraction is ~15%), so the busiest slice is the most
    CORRUPTED one, and the settled slices look quiet precisely because they are
    reporting the real, mostly-class-0 answer. Thresholding off the busiest
    slice therefore selected the transient and rejected the signal: it collapsed
    the window to 13..16, hid the fact that slice 19 sits at 0.0713, and
    recommended moving to slice 16 at 0.2515.

    Transient slices stay in the window under this definition -- they vary
    plenty. That is intended: they are then rejected on their measured score,
    which is the honest way to reject them.
    """
    n_ev, n_sl = code.shape
    if not n_ev:
        return 0, n_sl - 1
    varies = np.array([
        1.0 - np.bincount(code[:, t], minlength=4).max() / n_ev
        for t in range(n_sl)])
    live = np.flatnonzero(varies >= frac)
    if not len(live):
        return 0, n_sl - 1
    return int(live.min()), int(live.max())


def _majority(win):
    """Per-event majority class over a slice window, ignoring invalid codes."""
    out = np.full(len(win), 3)
    for i, row in enumerate(win):
        v = row[row != 3]
        if len(v):
            out[i] = np.bincount(v).argmax()
    return out


def _firstStable(win, k):
    """Per-event: the first value that holds for k slices running.

    The only decode here that adapts PER VECTOR, so it is the direct answer to a
    settling time that depends on the input: a vector that resolves late is read
    late, instead of being sampled mid-transition (what a fixed slice does) or
    outvoted by its own pre-settling slices (what a majority vote does).

    Events that never hold a value for k slices return 3. That is deliberate --
    falling back to "best guess" would hide exactly the events this is meant to
    identify, and scoreDecodes() counts 3 as an error rather than excluding it.
    """
    out = np.full(len(win), 3)
    n_sl = win.shape[1]
    for i, row in enumerate(win):
        for t in range(n_sl - k + 1):
            v = row[t]
            if v != 3 and (row[t:t + k] == v).all():
                out[i] = v
                break
    return out


def applyDecode(readout_csv, name):
    """Decode a readout.csv with one named strategy from decodeStrategies().

    Names carry their own slice indices ("maj[17:21]"), so a strategy chosen by
    the tuner reproduces exactly on a later run without depending on the live
    window being re-detected the same way.
    """
    code = decodeReadout(readout_csv)
    m = re.fullmatch(r"slice=(\d+)", name)
    if m:
        return code[:, int(m.group(1))]
    m = re.fullmatch(r"maj\[(\d+):(\d+)\]", name)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return _majority(code[:, a:b + 1])
    m = re.fullmatch(r"stable\((\d+)\)@\[(\d+):(\d+)\]", name)
    if m:
        k, a, b = (int(g) for g in m.groups())
        return _firstStable(code[:, a:b + 1], k)
    raise ValueError(
        f"unknown decode strategy {name!r}; expected 'slice=T', 'maj[A:B]' "
        f"or 'stable(K)@[A:B]'")


def decodeStrategies(code, lo=None, hi=None, stable_k=(2, 3)):
    """Every decode worth scoring, as {name: per-event class array}.

      slice=T          what DNN_analyse_2 does today: one fixed slice.
      maj[A:B]         majority vote over a contiguous window, invalid codes
                       ignored. Immune to any single slice landing
                       mid-transition, but a late-settling vector is outvoted
                       by its own pre-settling slices.
      stable(K)@[A:B]  first value that holds K slices running -- per-vector
                       adaptive, see _firstStable().

    All confined to the live window: a decode reaching outside it is reading
    slices that are [0,0] for every event.
    """
    if lo is None or hi is None:
        lo, hi = liveWindow(code)
    out = {}
    for t in range(lo, hi + 1):
        out[f"slice={t}"] = code[:, t]
    for a in range(lo, hi + 1):
        for b in range(a + 1, hi + 1):
            out[f"maj[{a}:{b}]"] = _majority(code[:, a:b + 1])
    # Only the START of a stable search is varied: where you begin looking is
    # what matters, the end just has to be far enough out to catch late vectors.
    for k in stable_k:
        for a in range(lo, hi - k + 2):
            out[f"stable({k})@[{a}:{hi}]"] = _firstStable(code[:, a:hi + 1], k)
    return out


def _decodeScore(y_pred, y_ref, y_true=None):
    """Error rates for one decode.

    'err' counts an invalid ([1,1]) readout as WRONG and divides by every event,
    which is the operationally meaningful number: how often the readout fails to
    give the right answer. scanTimeSlices() excludes invalids instead, so its
    numbers read slightly lower -- that is fine for comparing slices, but a
    search would exploit it by preferring a decode that bails out often.

    'bal' is 1 - balanced accuracy. With class 0 at ~78% of the data, plain
    error is minimised by a readout that under-asserts; bal is the guard that
    makes that visible rather than rewarding it.
    """
    y_pred = np.asarray(y_pred).astype(int).reshape(-1)
    y_ref = np.asarray(y_ref).astype(int).reshape(-1)
    err = float((y_pred != y_ref).mean())
    recalls = [float((y_pred[y_ref == c] == c).mean())
               for c in range(3) if (y_ref == c).any()]
    out = dict(err=err, bal=1.0 - float(np.mean(recalls)) if recalls else 1.0,
               invalid=float((y_pred == 3).mean()),
               se=math.sqrt(max(err * (1 - err), 1e-9) / max(1, len(y_pred))))
    if y_true is not None:
        y_true = np.asarray(y_true).astype(int).reshape(-1)
        out["err_true"] = float((y_pred != y_true).mean())
    return out


def scoreDecodes(readout_csv, y_ref, y_true=None, ref_name="reference",
                 timestamp=None, top=10, quiet=False):
    """Score every decode strategy on one saved readout. No chip time.

    Comparing decodes is far cheaper statistically than comparing thresholds:
    every strategy is scored on the SAME events of the SAME readout, so the
    chip's run-to-run instability is common to all of them and largely cancels.
    Threshold comparisons do not get that -- they need a fresh chip run each.

    Returns [(name, score_dict), ...] sorted best first.
    """
    code = decodeReadout(readout_csv)
    y_ref = np.asarray(y_ref).astype(int).reshape(-1)
    if len(code) != len(y_ref):
        if not quiet:
            print(f"  scoreDecodes: {len(code)} readout rows vs {len(y_ref)} "
                  f"reference rows; skipping")
        return []
    scored = [(n, _decodeScore(p, y_ref, y_true))
              for n, p in decodeStrategies(code).items()]
    scored.sort(key=lambda kv: kv[1]["err"])
    if quiet:
        return scored

    cur = f"slice={timestamp}" if timestamp is not None else None
    print(f"\n=== decode strategy scan (vs {ref_name}) ===")
    print("  invalid readouts count as errors here, so a strategy that bails "
          "out cannot win by abstaining")
    print("  strategy               err      +/-      bal_err  invalid")
    shown = scored[:top]
    if cur and cur not in [n for n, _ in shown]:
        shown += [kv for kv in scored if kv[0] == cur]
    for name, s in shown:
        mark = "  <-- in use" if name == cur else ""
        print(f"  {name:<20} {s['err']:7.4f}  {s['se']:7.4f}  "
              f"{s['bal']:7.4f}  {s['invalid']:7.4f}{mark}")
    best, bs = scored[0]
    if cur:
        cs = dict(scored).get(cur)
        if cs and best != cur:
            gain = cs["err"] - bs["err"]
            sig = gain / max(bs["se"], 1e-9)
            verdict = ("real" if sig >= 2 else
                       "NOT significant -- more samples needed")
            print(f"  => {best} beats {cur} by {gain:.4f} "
                  f"({sig:.1f} sigma, {verdict})")
            if sig >= 2:
                print(f"     pass decode={best!r} to use it.")
    return scored


def tuneTimeWindow(readout_csv, y_ref, **kw):
    """Best decode strategy for a saved readout. Thin wrapper on scoreDecodes."""
    scored = scoreDecodes(readout_csv, y_ref, **kw)
    return scored[0][0] if scored else None


# ---------------------------------------------------------------------------
# Discriminator threshold tuning.
# ---------------------------------------------------------------------------

DNN_LINE_PORTS = {"dnn0": "dnn0", "dnn1": "dnn1"}

# CaR board DAC7678 on the 4.096 V external reference (TI REF5040): one code is
# 4.096/4096 = exactly 1 mV. Every threshold on these lines is therefore an
# INTEGER NUMBER OF MILLIVOLTS, and there is no setting between two codes.
DNN_DAC_LSB = 4.096 / 4096


def dnnDacCode(v):
    """The code the CaR board will actually program for a requested voltage.

    Carboard.cpp does `static_cast<uint16_t>(voltage * 4096 / CAR_VREF_4P0)`,
    which TRUNCATES. Two ways that bites on this line:

      a half-LSB value is floored, not rounded -- 0.0795 V programs code 79
      (0.0790 V), so a scan written on a half-mV grid runs 0.5 mV below its own
      labels;

      and binary floating point puts some exact-mV values just under their code
      -- 0.071*4096/4.096 is 70.99999999999999, so asking for 0.071 V silently
      gives code 70, i.e. 0.070 V.

    Rounding here lands a requested voltage on the NEAREST code instead of
    silently one code low. It adds no resolution: 1 mV is the floor.
    """
    return max(0, min(4095, int(round(v / DNN_DAC_LSB))))


def dnnDacVolts(v):
    """Requested voltage snapped to the code the DAC will really hold."""
    return dnnDacCode(v) * DNN_DAC_LSB


def _dacSettable(v):
    """The float to hand set_voltage so the firmware lands on dnnDacCode(v).

    Carboard.cpp truncates, so sending the code's own voltage is a coin flip:
    the float may represent as the code exactly or a hair under it, and a hair
    under truncates to code-1. Sending the MIDDLE of the code's 1 mV window is
    half an LSB from either edge, so it truncates to the intended code
    regardless of which way the float rounds.
    """
    return (dnnDacCode(v) + 0.5) * DNN_DAC_LSB


def _fmtDnn(v, steps=False):
    """One threshold setting, written the way the operator sees it.

    In step mode a setting is a POSITION ON THE DIAL relative to wherever the
    pot sat when the scan started, not a voltage -- printing volts there would
    be inventing a number nobody at the bench can read back.
    """
    return f"step {v:+.0f}" if steps else f"{v:.4f} V"


def _tagDnn(v, steps=False):
    """Filename-safe form of a setting (no decimal/sign ambiguity in a glob)."""
    return f"s{v:+03.0f}" if steps else f"{v:.4f}"


def setDnnLines(dnn0=None, dnn1=None, manual=None,
                approach=None, overshoot=0.0, steps=False, prev=None):
    """Set the two off-chip discriminator thresholds.

    Today these are manual potentiometers, so the default is to PROMPT the
    operator and wait. The moment the CaR-board DAC is wired up and the ports
    appear in V_PORT, the same call drives them directly and every loop built on
    top of this becomes unattended -- nothing above here changes.

    HYSTERESIS. The discriminator has hysteresis, so the voltage on the line
    does not by itself determine the effective threshold: the direction the line
    was moving when it arrived does too. Setting 1.5880 V on the way down and
    setting 1.5880 V on the way up are two DIFFERENT operating points, separated
    by the width of the loop. A scan that changes direction partway through --
    which the bracketing default does, and which the drift re-check does -- would
    otherwise put its points on two different branches and compare them as if
    they were the same curve.

    approach='above'/'below' with overshoot > 0 removes that: the line is driven
    PAST the target by `overshoot` and then brought back, so every measurement
    lands on the same branch regardless of where the line was before. Make
    overshoot comfortably larger than the hysteresis width (3x is a reasonable
    default) -- undershooting it puts you back inside the loop and silently
    reintroduces the problem.

    approach=None keeps the plain "set it and go" behaviour.

    Pass manual=True/False to force one path (e.g. manual=False in a dry run).

    STEP MODE (steps=True). Everything above assumes the operator can read the
    voltage on the line. With a bare potentiometer and no meter they cannot:
    "set 1.5840 V" is not an instruction anybody can follow. So in step mode a
    setting is a POSITION ON THE DIAL -- an integer count of whatever increment
    the operator picked -- and the prompt is a RELATIVE MOVE from wherever the
    pot is now, which is the one thing that can actually be executed by hand:

        >> dnn1: turn 1 step CCW   (step +0 -> step -1)

    `prev` is where the pot currently sits, {"dnn0": p, "dnn1": p}; the caller
    owns that state because only it knows which moves were actually made. Lines
    that do not move are not mentioned, and if nothing moves there is no prompt.

    CW/CCW is a rotation, not a direction on the threshold: which way the pot
    raises the threshold is a property of the board that software cannot check.
    That is fine, and is why the scans bracket -- the measured curve establishes
    the sign once, and after that you scan one side only.

    The voltage-approach protocol is off in step mode. There is no voltage to
    overshoot by, and nothing to program a DAC with, so this path is always a
    prompt. Hysteresis is still physically there; the honest way to handle it on
    a dial is to keep every move going the same way, which is what a monotonic
    scan order does.
    """
    if approach not in (None, "above", "below"):
        raise ValueError(f"approach must be None, 'above' or 'below', "
                         f"got {approach!r}")
    ports = globals().get("V_PORT") or {}
    have = all(ports.get(p) is not None for p in DNN_LINE_PORTS.values())
    if manual is None:
        manual = not have
    if steps:
        # A dial position is not a voltage: there is nothing to program.
        manual = True
    want = [(n, v) for n, v in (("dnn0", dnn0), ("dnn1", dnn1)) if v is not None]
    if not want:
        return manual
    if steps:
        prev = prev or {}
        moves = []
        for n, p in want:
            was = prev.get(n, 0)
            d = int(round(p - was))
            if d:
                moves.append(
                    f"  >> {n}: turn {abs(d)} step{'' if abs(d) == 1 else 's'} "
                    f"{'CW' if d > 0 else 'CCW'}"
                    f"   ({_fmtDnn(was, True)} -> {_fmtDnn(p, True)})")
        if not moves:
            print("  (pot already where it needs to be -- nothing to turn)")
            return manual
        for m in moves:
            print(m)
        input("     one step = the increment you picked at the start; keep it "
              "identical all scan    then press enter >")
        return manual
    use_approach = approach is not None and overshoot > 0
    sign = 1.0 if approach == "above" else -1.0
    if manual:
        if use_approach:
            # Spelled out as two moves on purpose: "set it to X" invites the
            # operator to arrive from whichever side is closer, which is exactly
            # what makes the measurement unrepeatable.
            turn = "UP" if approach == "above" else "DOWN"
            back = "DOWN" if approach == "above" else "UP"
            for n, v in want:
                print(f"  >> {n}: turn {turn} past {v + sign * overshoot:.4f} V,"
                      f" then back {back} to {v:.4f} V")
            input(f"     (always approach from {approach} -- hysteresis)"
                  f"    then press enter >")
        else:
            req = ",  ".join(f"{n} = {v:.4f} V" for n, v in want)
            input(f"  >> set the pot:  {req}    then press enter >")
    else:
        for n, v in want:
            if use_approach:
                ports[DNN_LINE_PORTS[n]].set_voltage(
                    _dacSettable(v + sign * overshoot))
            ports[DNN_LINE_PORTS[n]].set_voltage(_dacSettable(v))
        note = f" (approached from {approach})" if use_approach else ""
        print(f"  set " + ",  ".join(
            f"{n}={dnnDacVolts(v):.4f}V[c{dnnDacCode(v)}]"
            for n, v in want) + note)
    return manual


def dnnLineRates(runs, y_ref):
    """Per-line 0->1 and 1->0 readout bit error rates, pooled over runs.

    The asymmetry is the signature of a threshold offset. dnn0/dnn1 leave the
    chip through an AC-coupled discriminator, so:

      p10 >> p01  => threshold too HIGH: real pulses fall under it.
      p01 >> p10  => threshold too LOW: baseline rides over it.
      balanced    => centred; what is left is noise, not offset.

    Invalid ([1,1]) readouts are included on purpose -- that is just both lines
    reading high, a bit error like any other.

    CAUTION on reading these: "balanced" is the right target only if the two bit
    populations are the same size. They are not -- the reference drives dnn1
    high on ~10% of events -- so the setting that minimises TOTAL errors sits
    well away from p01 == p10, and pushing to equalise them will make total
    disagreement worse. Use these for DIRECTION; use the measured error curve
    for the stopping point.
    """
    rates = {}
    for shift, line in ((1, "dnn1"), (0, "dnn0")):
        b_ref = (np.asarray(y_ref).astype(int) >> shift) & 1
        n0 = n1 = f01 = f10 = 0
        for run in runs:
            b_ch = (np.asarray(run).astype(int) >> shift) & 1
            n0 += int((b_ref == 0).sum())
            n1 += int((b_ref == 1).sum())
            f01 += int(((b_ref == 0) & (b_ch == 1)).sum())
            f10 += int(((b_ref == 1) & (b_ch == 0)).sum())
        rates[line] = dict(n0=n0, n1=n1, f01=f01, f10=f10,
                           p01=f01 / max(1, n0), p10=f10 / max(1, n1))
    return rates


def _loadModelForChip(model_file, verbose=True):
    """Load a .h5 in exactly the configuration that was programmed onto the chip.

    retargetOutputBias + freezeBatchnormStats must match training, or the
    software side of any chip comparison is not the model the chip is running.
    Shared by asicFidelityCheck() and tuneDnnThresholds() so the two cannot
    drift apart.
    """
    co = {}
    utils._add_supported_quantized_objects(co)
    model = tf.keras.models.load_model(model_file, custom_objects=co, compile=False)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
        run_eagerly=True)
    retargetOutputBias(model, verbose=False)
    if FREEZE_BATCHNORM_STATS:
        freezeBatchnormStats(model, verbose=False)
    if verbose:
        print(f"Loaded {model_file}")
    return model


def tuneDnnThresholds(model_file="model.h5",
                      dnn0=0.079, dnn1=0.070,
                      dnn1_scan=None, dnn0_scan=None,
                      n_samples=2048, repeats=1, passes=1,
                      vth=VTH_DEFAULT, pg_hlev=PG_HLEV_DEFAULT, data_dir=None,
                      use_val=True, timestamp=TIMESTAMP_DEFAULT,
                      objective="err", manual=None, tune_decode=True,
                      hysteresis=0.003, approach="above", hyst_check=False,
                      pot_steps=True, save_dir="./tmp/tune"):
    """Trim dnn0/dnn1 against a fixed chunk of the dataset, and pick the decode.

    The chip's job is to reproduce the model it was programmed with, so the
    objective is disagreement against the C++ (RTL-precision) reference, NOT
    against ground truth: a threshold cannot fix the model's own errors, and
    scoring against truth folds the two together and moves the optimum.

    What makes this measurable at all is that the reference and the evaluation
    vectors are computed ONCE and held fixed, so every setting is scored on
    identical inputs against an identical target -- and settings are then
    compared PAIRED (_pairedGain), counting only the events that actually
    flipped. That is much more sensitive than comparing two error rates through
    their binomial bars, which is what makes small threshold steps detectable
    without an enormous batch.

    Three separate things limit how small a step can be resolved, and only the
    first responds to n_samples:

      counting noise   binomial, sqrt(p(1-p)/n): 1.3 points at n=512, 0.9 at
                       1024, 0.44 at 4096. The paired test does better than
                       this, but it is the right order of magnitude.
      chip noise       the chip disagrees with ITSELF on ~1.5% of events
                       between identical back-to-back runs. Measured here when
                       repeats>1 and reported as the floor; no threshold can be
                       shown to beat it.
      drift            the chip moves at a FIXED setting over the course of a
                       scan. No batch size fixes this. The starting setting is
                       re-measured at the END of every line scan to detect it,
                       because a sequential scan otherwise reports drift as a
                       threshold effect.

    A fourth thing is not noise at all but would look like it: the discriminator
    has HYSTERESIS, so a voltage reached on the way down and the same voltage
    reached on the way up are different operating points. Every setting here is
    therefore approached from the same side (see setDnnLines) -- overshoot past
    it by `hysteresis`*3, then come back -- which is what makes the bracketing
    scan and the drift re-check legitimate despite both reversing direction. Set
    `hysteresis` to the real loop width; the default 3 mV is a guess, and
    hyst_check measures what it actually costs.

    dnn0/dnn1 are treated as independent, which the data supports: in the
    2026-08-30 run only 1.1% of disagreements flipped both lines. So this is a
    coordinate descent (scan dnn1, fix the winner, scan dnn0), not a 2-D grid,
    which is what keeps the number of manual pot adjustments bounded.

    Resolution is hardware, not statistics: the CaR DAC7678 on its 4.096 V
    reference has a 1 mV code, so every setting here is an integer number of
    millivolts and no scan can be finer. Requested voltages are snapped to that
    grid on the way in (dnnDacCode), so two labels inside one code are one
    measurement, not two.

    args
      dnn1_scan/dnn0_scan  voltages to try for each line; None skips that line.
                           Give them in monotonic order -- with a pot, that is
                           one continuous turn rather than hunting back and
                           forth. A single measurement at the current setting
                           (both scans None) still reports the direction.
                           In voltage mode these land on 1 mV DAC codes, so
                           values differing by less than that are the same
                           point and the duplicate is served from the cache.
      repeats              chip runs per setting. >1 averages down the chip's
                           own instability at linear cost in time.
      objective            'err'      minimise disagreement vs the reference.
                           'bal'      minimise 1 - balanced accuracy. Use this
                                      if the classes matter equally: 'err' with
                                      a 78% majority class can be reduced by a
                                      readout that simply asserts less.
                           'err_true' minimise disagreement vs ground truth.
      tune_decode          also score every time-slice decode at each setting
                           (free -- no extra chip time) and report the best
                           (threshold, decode) pair jointly.
      hysteresis           discriminator hysteresis width, volts. Sets the
                           overshoot (3x) and warns when a refinement step would
                           be finer than the loop the pot has to traverse.
                           0 disables the overshoot protocol entirely.
      approach             which side every setting is approached from,
                           'above' or 'below'. Which one does not matter as long
                           as it never changes: the winner is only valid for the
                           branch it was found on, so set the pot the same way
                           when you adopt it.
      pot_steps            no meter on the line -- you can only turn the pot.
                           Scan values become STEP COUNTS on the dial relative
                           to where it sits now (0), and every prompt becomes a
                           relative move you can actually execute:

                             >> dnn1: turn 1 step CCW   (step +0 -> step -1)

                           This turns OFF the whole voltage-approach protocol
                           (hysteresis/approach/hyst_check are ignored) because
                           all of it needs a voltage you cannot read. What
                           replaces the hysteresis floor is the dial itself: the
                           verdict refuses to refine below one step, since that
                           is the finest move you can make. See setDnnLines.

                           CW/CCW is a rotation, not a threshold direction --
                           software cannot know which way your pot raises the
                           threshold. That is why the default scan brackets both
                           ways; the measured curve fixes the sign once, and
                           after that you scan one side only.

      hyst_check           OFF by default: it is an extra setting and an extra
                           pot move, and the scan is perfectly valid without it.
                           Turn it on when you want to know how much of what you
                           are seeing is the pot rather than the chip.

                           There is nothing special to do at the bench -- it is
                           the ordinary two-move prompt with the directions
                           swapped, and it names the same voltage you are already
                           sitting at:

                             >> dnn1: turn DOWN past 1.5790 V,
                                      then back UP to 1.5880 V

                           i.e. return to where you started, from underneath.
                           The paired difference against the first measurement
                           at that same voltage is what the loop costs you, in
                           the same units as every other number here.

    Costs n_samples * repeats * 23 ms of chip time per setting (~12 s at the
    defaults), plus one operator pot adjustment per setting while the lines are
    on potentiometers.
    """
    if objective not in ("err", "bal", "err_true"):
        raise ValueError(f"objective must be 'err', 'bal' or 'err_true', "
                         f"got {objective!r}")
    if pot_steps:
        # A step is a rotation. There is no voltage to overshoot BY, none to
        # program, and none to re-approach from the other side -- so the entire
        # voltage-approach protocol switches off rather than printing
        # instructions nobody can follow. Silently, and on purpose: this is not
        # a degraded mode, it is the correct one for a bare pot.
        hysteresis, approach, hyst_check, manual = 0.0, None, False, True
        # The origin in step mode is "wherever the pot is right now", so any
        # voltage passed for dnn0/dnn1 is meaningless here -- taking it at face
        # value would turn 1.588 into 1588 steps of the dial.
        dnn0, dnn1 = 0.0, 0.0
    model = _loadModelForChip(model_file)
    data_dir = datasetDir(vth) if data_dir is None else data_dir
    print(f"Data      {data_dir}")
    print(f"Chip      vth={tuple(vth)} e-  pg_hlev={pg_hlev} V")
    x, y = loadDataset(data_dir)

    pipeline = ModelPipeline(
        model, tf.keras.optimizers.Adam(),
        tf.keras.metrics.SparseCategoricalAccuracy(),
        tf.keras.metrics.SparseCategoricalAccuracy(),
        batch_size=n_samples, asic_training=True,
        vth=vth, pg_hlev=pg_hlev, timestamp=timestamp)
    pipeline.split_data(x, y)
    ds = pipeline.val_dataset if use_val else pipeline.train_dataset
    x_batch, y_batch = next(iter(ds))
    y_true = np.asarray(y_batch).astype(int).reshape(-1)

    # Computed once and reused for every setting: the reference does not depend
    # on the thresholds, and holding it fixed is what makes the comparison
    # between settings paired instead of two independent noisy samples.
    y_sw = np.argmax(
        np.asarray(pipeline.forward_pass(x_batch, training=False)),
        axis=1).astype(int)
    y_ref, ref_name = y_sw, "software (QKeras)"
    if hls_reference is not None:
        try:
            y_ref = np.argmax(
                hls_reference.hlsPredict(model, x_batch,
                                         writeWeightsFn=writeWeights),
                axis=1).astype(int)
            ref_name = "C++ (RTL precision)"
        except Exception as e:
            print(f"  C++ reference unavailable ({e}); scoring against QKeras")
    print(f"Reference {ref_name}, {len(y_true)} vectors from the "
          f"{'validation' if use_val else 'training'} split")

    # Weights are written once: they do not change during tuning, so every chip
    # run below is a same-weights/same-inputs replay with only the thresholds
    # moving. Anything else would confound the measurement.
    dnn_csv, compout_csv = pipeline.prepare_weights_asic(x_batch)
    os.makedirs(save_dir, exist_ok=True)

    overshoot = 3.0 * hysteresis
    if hysteresis > 0:
        print(f"Approach  every setting from {approach}, overshooting by "
              f"{overshoot * 1000:.0f} mV (hysteresis {hysteresis * 1000:.0f} mV)")
    if pot_steps:
        print("Pot       step mode: settings are dial positions relative to "
              "where the pot sits now")
        print("          Pick one increment now -- a mark, a click, a full turn "
              "of the trimmer -- and")
        print("          use exactly that for every move. Its size does not "
              "matter; its consistency does.")
        print("          'too HIGH / too LOW' below is about the THRESHOLD, not "
              "the dial: which rotation")
        print("          moves it which way is exactly what this scan finds "
              "out, so it goes both ways.")

    cache = {}
    # Where the pot physically sits. Only this loop knows, because only it knows
    # which moves were actually prompted -- a cache hit turns nothing.
    pos = {"dnn0": dnn0, "dnn1": dnn1}

    def measure(v0, v1, force=False, appr=None):
        # The approach direction is part of the operating point, not an
        # incidental detail of how we got there -- so it is part of the cache
        # key. The same voltage reached from the other side is a DIFFERENT
        # measurement and must not be served from the cache.
        appr = approach if appr is None else appr
        if not pot_steps:
            # Snap to the DAC grid up front so a setting is identified by the
            # code the line will actually hold. Two requested voltages inside
            # one 1 mV code are the SAME operating point: keying the cache on
            # the raw float would measure it twice and report one physical
            # setting as two scan points.
            v0, v1 = dnnDacVolts(v0), dnnDacVolts(v1)
        key = (round(v0, 6), round(v1, 6), appr)
        if key in cache and not force:
            return cache[key]
        print(f"\n--- dnn0={_fmtDnn(v0, pot_steps)}  dnn1={_fmtDnn(v1, pot_steps)}"
              f"{f'  (from {appr})' if hysteresis > 0 else ''} ---")
        setDnnLines(v0, v1, manual=manual, approach=appr, overshoot=overshoot,
                    steps=pot_steps, prev=dict(pos))
        pos["dnn0"], pos["dnn1"] = v0, v1
        runs, saved = [], None
        for r in range(repeats):
            runs.append(np.asarray(
                pipeline.forward_pass_asic(x_batch, dnn_csv, compout_csv)
            ).astype(int).reshape(-1))
            # forward_pass_asic reuses one output directory, so readout.csv is
            # overwritten on every call. Copy it out: it is the full 40-slice
            # record for this setting, and keeping it means the decode search
            # can be redone offline without paying for the chip run again.
            tag = f"_{appr}" if hysteresis > 0 else ""
            saved = os.path.join(
                save_dir,
                f"readout_{_tagDnn(v0, pot_steps)}_{_tagDnn(v1, pot_steps)}"
                f"{tag}_r{r}.csv")
            shutil.copy(pipeline.last_readout_csv, saved)
        m = _decodeScore(runs[0], y_ref, y_true)
        m.update(dnn0=v0, dnn1=v1, approach=appr, runs=runs, readout=saved,
                 rates=dnnLineRates(runs, y_ref))
        if tune_decode:
            scored = scoreDecodes(saved, y_ref, y_true, quiet=True)
            if scored:
                m["best_decode"], m["best_decode_score"] = scored[0]
        print(f"  err {m['err']:.4f} +/-{m['se']:.4f}   bal_err {m['bal']:.4f}"
              f"   invalid {m['invalid']:.4f}")
        for line, rt in m["rates"].items():
            print(f"    {line}: 0->1 {rt['f01']:4d}/{rt['n0']:<5d}"
                  f"={rt['p01']:.4f}   1->0 {rt['f10']:4d}/{rt['n1']:<5d}"
                  f"={rt['p10']:.4f}   {_thresholdHint(rt)}")
        if "best_decode" in m:
            print(f"    best decode here: {m['best_decode']} at "
                  f"{m['best_decode_score']['err']:.4f} "
                  f"(scored slice={timestamp} at {m['err']:.4f})")
        cache[key] = m
        return m

    results = []
    cur0, cur1 = dnn0, dnn1
    base = measure(cur0, cur1)
    results.append(base)

    # The chip's disagreement with ITSELF at one fixed setting. This is the
    # number every threshold improvement has to beat to mean anything, and it
    # is only available when repeats > 1 -- which is why repeats=2 is worth
    # paying for on the first setting even if the rest of the scan uses 1.
    floor = None
    if len(base["runs"]) > 1:
        self_dis = float((base["runs"][0] != base["runs"][1]).mean())
        floor = self_dis / 2.0
        print(f"\n  chip vs itself at a fixed setting: {self_dis:.4f} of events "
              f"flip between runs")
        print(f"  => per-run noise ~{floor:.4f}; no threshold can be shown to "
              f"do better than this")

    # What the hysteresis actually costs, in the same units as everything else:
    # the SAME voltage, approached from the other side. Paired, so only the
    # events that flip count. This is the one number that says how finely these
    # lines can be trimmed at all -- a threshold step whose effect is smaller
    # than this is not reproducible on the bench, however significant it looks.
    hyst = None
    if hysteresis > 0 and hyst_check:
        other = "below" if approach == "above" else "above"
        print(f"\n=== hysteresis check: {cur1:.4f} V approached from {other} "
              f"instead of {approach} ===")
        print(f"  Same voltage you are already on -- just return to it from the "
              f"other side. Nothing else changes.")
        flip = measure(cur0, cur1, appr=other)
        hyst = _pairedGain(flip["runs"][0], base["runs"][0], y_ref)
        print(f"  same voltage, other branch: {objective} "
              f"{base[objective]:.4f} -> {flip[objective]:.4f}   "
              f"paired {hyst['gain']:+.4f} "
              f"({hyst['c']} flipped one way, {hyst['b']} the other, "
              f"z={hyst['z']:+.1f})")
        if abs(hyst["z"]) >= 2:
            print(f"  !! the branch matters: {abs(hyst['gain']):.4f} of events "
                  f"depend on WHICH WAY the pot was turned, not on its value.")
            print(f"     Every setting below is approached from {approach}. The "
                  f"winner is only valid on that branch -- adopt it the same "
                  f"way, and treat {abs(hyst['gain']):.4f} as the floor on what "
                  f"a threshold step has to beat.")
        else:
            print(f"  the two branches are indistinguishable here; hysteresis "
                  f"is not limiting the trim.")

    for _ in range(passes):
        for line, scan in (("dnn1", dnn1_scan), ("dnn0", dnn0_scan)):
            if not scan:
                continue
            print(f"\n=== scanning {line} over {len(scan)} settings ===")
            start = cache[(round(cur0, 6), round(cur1, 6), approach)]
            best, line_results = start, [start]
            for v in scan:
                v0, v1 = (v, cur1) if line == "dnn0" else (cur0, v)
                m = measure(v0, v1)
                # Paired against the setting this scan started from: the same
                # vectors decided by both, so only the flips count.
                m["paired"] = _pairedGain(m["runs"][0], start["runs"][0], y_ref)
                p = m["paired"]
                print(f"    vs start: gain {p['gain']:+.4f} "
                      f"({p['c']} fixed, {p['b']} broken, z={p['z']:+.1f})")
                results.append(m)
                line_results.append(m)
                if m[objective] < best[objective]:
                    best = m
            cur0, cur1 = best["dnn0"], best["dnn1"]
            print(f"\n  {line} -> {_fmtDnn(best[line], pot_steps)} "
                  f"({objective} {best[objective]:.4f})")

            # Re-measure the starting setting LAST. If the chip has drifted
            # during the scan -- and the per-run table in asicFidelityCheck has
            # shown it moving between back-to-back runs -- then a sequential
            # scan attributes that drift to the threshold. This is the only way
            # to catch it, and it costs one extra setting.
            #
            # This re-measurement arrives at the start voltage from the far end
            # of the scan, i.e. travelling the OPPOSITE way from the first time.
            # Without the overshoot protocol above that alone would change the
            # effective threshold and the check would report hysteresis as
            # drift. `appr` is unchanged, so both land on the same branch and
            # the difference really is the chip.
            recheck = measure(start["dnn0"], start["dnn1"], force=True)
            dr = _pairedGain(recheck["runs"][0], start["runs"][0], y_ref)
            print(f"  drift check (same setting, re-measured last): "
                  f"{dr['gain']:+.4f}  z={dr['z']:+.1f}")
            if abs(dr["z"]) >= 2:
                print(f"  !! the chip moved by {abs(dr['gain']):.4f} at a FIXED "
                      f"setting during this scan.")
                print(f"     Any threshold gain smaller than that is drift, not "
                      f"tuning. Re-run with the scan order reversed; if the "
                      f"winner changes, it is drift.")
            _scanVerdict(scan, line_results, best, line, objective, floor,
                         hysteresis=hysteresis, steps=pot_steps)

    print(f"\n=== tuning summary (objective={objective}, vs {ref_name}) ===")
    print(f"  {'dnn0':>9}  {'dnn1':>9}     err      +/-      bal_err  invalid  "
          f"best decode")
    for m in sorted(results, key=lambda r: r[objective]):
        bd = m.get("best_decode", "-")
        print(f"  {_fmtDnn(m['dnn0'], pot_steps):>9}  "
              f"{_fmtDnn(m['dnn1'], pot_steps):>9}  {m['err']:7.4f}  "
              f"{m['se']:7.4f}  {m['bal']:7.4f}  {m['invalid']:7.4f}  {bd}")

    best = min(results, key=lambda r: r[objective])
    print(f"\n  start : dnn0={_fmtDnn(base['dnn0'], pot_steps)} "
          f"dnn1={_fmtDnn(base['dnn1'], pot_steps)}  "
          f"{objective}={base[objective]:.4f}")
    print(f"  best  : dnn0={_fmtDnn(best['dnn0'], pot_steps)} "
          f"dnn1={_fmtDnn(best['dnn1'], pot_steps)}  "
          f"{objective}={best[objective]:.4f}")
    if len(results) == 1:
        print("  (single measurement -- pass dnn1_scan=[...] to actually search)")
    else:
        # Paired against the starting setting, not a binomial bar: see
        # _pairedGain. The unpaired number is printed too because it is what a
        # reader would compute by hand from the two error rates, and it is
        # systematically more pessimistic.
        pg = _pairedGain(best["runs"][0], base["runs"][0], y_ref)
        unp = (base[objective] - best[objective]) / max(best["se"], 1e-9)
        print(f"  improvement {pg['gain']:+.4f}  ({pg['c']} events fixed, "
              f"{pg['b']} broken)  z={pg['z']:+.1f} paired "
              f"[{unp:+.1f} unpaired]")
        if pg["z"] >= 2 and pot_steps:
            # The pot is wherever the last measurement left it (the drift
            # re-check, i.e. back at the start), NOT at the winner. Without a
            # meter the only way to land on the winner is a counted move from
            # here, so spell it out rather than naming a position.
            print(f"  -> real. Move the pot to the winner and confirm with "
                  f"asicFidelityCheck():")
            moved = False
            for n in ("dnn0", "dnn1"):
                d = int(round(best[n] - pos[n]))
                if d:
                    moved = True
                    print(f"       {n}: turn {abs(d)} "
                          f"step{'' if abs(d) == 1 else 's'} "
                          f"{'CW' if d > 0 else 'CCW'}   "
                          f"({_fmtDnn(pos[n], True)} -> "
                          f"{_fmtDnn(best[n], True)})")
            if not moved:
                print(f"       nothing to turn -- the pot is already there.")
            print(f"     Then note where the dial is: this position is the new "
                  f"origin, and the next scan brackets it.")
        elif pg["z"] >= 2:
            print(f"  -> real. Set this on the pot/DAC -- approaching from "
                  f"{approach}, the branch it was measured on -- and confirm "
                  f"with asicFidelityCheck().")
        else:
            print("  -> NOT significant. Raise n_samples (sigma scales as "
                  "1/sqrt(n)) or repeats, or widen the scan -- do not adopt "
                  "this setting yet.")
        if floor is not None and best[objective] <= floor + 0.5 * best["se"]:
            print(f"  -> and you are at the {floor:.4f} noise floor; there is "
                  f"nothing left to win by tuning thresholds.")
        if hyst is not None and abs(pg["gain"]) <= abs(hyst["gain"]):
            print(f"  -> CAUTION: this gain ({abs(pg['gain']):.4f}) is no "
                  f"bigger than what the hysteresis alone moves "
                  f"({abs(hyst['gain']):.4f}). It is real on this branch, but "
                  f"it will not survive the pot being approached the other "
                  f"way, so it is not worth chasing further.")
    if tune_decode and best.get("readout"):
        scoreDecodes(best["readout"], y_ref, y_true, ref_name=ref_name,
                     timestamp=timestamp)
    print(f"\n  readouts saved under {save_dir}/ -- rerun scoreDecodes() on "
          f"them to redo the decode search without the chip.")
    return best


def _pairedGain(y_cand, y_base, y_ref):
    """Is `cand` really better than `base`? McNemar on the events that FLIPPED.

    The plain binomial error bar treats the two settings as independent samples,
    which throws away the fact that they were measured on the SAME vectors
    against the SAME reference. Nearly every event is decided identically by
    both; only the handful that flip carry any information about which setting
    is better, and the variance that matters is theirs, not the whole batch's.

    So: c = events base got wrong and cand got right, b = the reverse. The
    improvement is (c - b)/n and its standard error is sqrt(b + c)/n, which is
    far tighter than two binomial bars added in quadrature whenever b + c is
    small -- i.e. exactly when comparing two nearby threshold settings. This is
    what makes a 1 mV step detectable at a batch size that would otherwise need
    to be several times larger.
    """
    y_cand = np.asarray(y_cand).astype(int).reshape(-1)
    y_base = np.asarray(y_base).astype(int).reshape(-1)
    y_ref = np.asarray(y_ref).astype(int).reshape(-1)
    base_ok, cand_ok = y_base == y_ref, y_cand == y_ref
    b = int((base_ok & ~cand_ok).sum())      # cand made it worse
    c = int((~base_ok & cand_ok).sum())      # cand made it better
    n = len(y_ref)
    se = math.sqrt(max(b + c, 1)) / n
    return dict(gain=(c - b) / n, b=b, c=c, se=se,
                z=(c - b) / math.sqrt(max(b + c, 1)))


def _scanVerdict(scan, results, best, line, objective, floor, hysteresis=0.0,
                 steps=False):
    """Whether to stop, refine, or extend the bracket -- the stopping rule.

    Three distinguishable outcomes, and they call for different next steps:

      minimum at an endpoint  the true optimum is OUTSIDE the range scanned.
                              Refining inside it is wasted chip time; extend
                              the bracket in that direction instead.
      interior minimum        bracketed. Rescan at a third of the step around
                              it, and stop when the gain stops clearing 2 sigma
                              or the step reaches the DAC/pot resolution.
      at the noise floor      the chip disagrees with ITSELF by about this much
                              (measured from `repeats`, else the ~1.5%/event
                              implied by the run-to-run check). No threshold
                              buys anything below that; stop.

    `hysteresis` is a hard limit on refinement independent of any of these: a
    refinement step finer than the discriminator's loop width cannot be set
    reproducibly on the bench, so refining past it produces numbers that will
    not survive the pot being touched again.

    In step mode the dial supplies that limit instead, and more honestly: one
    step is the finest move that exists, so a scan already at unit spacing has
    nowhere left to refine to.
    """
    vals = sorted(set(scan))
    step = min((b - a for a, b in zip(vals, vals[1:])), default=0.0)
    at_edge = best[line] in (vals[0], vals[-1])
    unit = "step" if steps else "V"
    here = _fmtDnn(best[line], steps)
    print(f"\n  -- {line} verdict --")
    if floor is not None and best[objective] <= floor + 0.5 * best["se"]:
        print(f"     {objective}={best[objective]:.4f} is at the measured noise "
              f"floor ({floor:.4f}); further tuning cannot be verified. STOP.")
        return "stop"
    if at_edge:
        d = "lower" if best[line] == vals[0] else "higher"
        nxt = best[line] - 3 * step if d == "lower" else best[line] + 3 * step
        print(f"     best is at the {d} EDGE of the scan -- the optimum is "
              f"outside this bracket.")
        print(f"     extend: rerun with {line}_scan reaching "
              f"{_fmtDnn(nxt, steps)} before refining"
              f"{', re-zeroed on the winner' if steps else ''}.")
        return "extend"
    if steps and step <= 1:
        print(f"     interior minimum at {here}, bracketed -- and the scan is "
              f"already at one-step spacing.")
        print(f"     One step is the finest move the dial has, so there is "
              f"nothing to refine to. This line is trimmed as far as the "
              f"hardware allows. STOP.")
        return "stop"
    fine = max(1, int(round(step / 3.0))) if steps else step / 3.0
    if not steps:
        # The DAC grid is the hard floor: a third of the step is a real number,
        # but the line can only sit on 1 mV codes. Snap the proposal onto that
        # grid, and if it has nowhere left to go, say so instead of printing a
        # scan whose three points are the same code.
        fine = round(fine / DNN_DAC_LSB) * DNN_DAC_LSB
        if fine < DNN_DAC_LSB:
            print(f"     interior minimum at {here}, bracketed -- but a "
                  f"refinement step would be finer than the DAC's "
                  f"{DNN_DAC_LSB * 1000:.0f} mV code.")
            print(f"     The three points would program the same code. This "
                  f"line is trimmed as far as the hardware allows. STOP.")
            return "stop"
    if hysteresis > 0 and fine < hysteresis:
        print(f"     interior minimum at {here}, bracketed -- but a refinement "
              f"step would be {fine:.4f} V, finer than the "
              f"{hysteresis:.4f} V hysteresis.")
        print(f"     You cannot set the pot that precisely in a way that "
              f"repeats: the loop is wider than the step. This line is trimmed "
              f"as far as the hardware allows. STOP.")
        return "stop"
    fmt = (lambda v: f"{v:+.0f}") if steps else (lambda v: f"{v:.4f}")
    print(f"     interior minimum at {here}, bracketed. "
          f"Refine with {fine if steps else f'{fine:.4f}'} {unit} spacing:")
    print(f"     {line}_scan=[{fmt(best[line] - fine)}, {fmt(best[line])}, "
          f"{fmt(best[line] + fine)}]  (stop when the gain stops clearing "
          f"2 sigma, or the step hits your "
          f"{'dial' if steps else 'DAC'} resolution)")
    if steps:
        print(f"     NOTE: those are positions in THIS scan's frame. Re-zero on "
              f"the winner before the next run -- leave the pot there and pass "
              f"the new scan as offsets from it.")
    return "refine"


def _thresholdHint(rt):
    """Which way to push one line, from its 0->1 vs 1->0 asymmetry."""
    if rt["p10"] > 3 * rt["p01"]:
        return "<- too HIGH, lower it"
    if rt["p01"] > 3 * rt["p10"]:
        return "<- too LOW, raise it"
    return "<- roughly centred"


def loadDataset(data_dir):
    """Load (x, y) from a dataset directory as plain numpy arrays."""
    x = np.array(pd.read_csv(os.path.join(data_dir, "yprofiles.csv"),
                             header=None).values.tolist())
    y = np.array(pd.read_csv(os.path.join(data_dir, "clslabels.csv"),
                             header=None).values.tolist()).flatten()
    return x, y


def _output_bias_quantizer():
    """qkeras quantizer matching OUTPUT_BIAS_FXP.

    quantized_bits(bits, integer) spends 1 bit on sign and `integer` bits on the
    integer part, which is the same split Fxp(signed=True, n_word, n_int) uses --
    so the trained grid and the grid prepareWeights() encodes onto stay identical.
    """
    n_word, n_int = OUTPUT_BIAS_FXP
    return quantized_bits(n_word, n_int, alpha=1)

def retargetOutputBias(model, verbose=True):
    """Point the output layer's bias quantizer at OUTPUT_BIAS_FXP.

    A model loaded from .h5 carries whatever quantizer it was built with baked
    into its config, so widening the format means rebinding it after load rather
    than only at CreateQModel() time.
    """
    dense = [l for l in model.layers if isinstance(l, (QDense, QDenseBatchnorm))]
    if not dense:
        return model
    out = dense[-1]
    q = _output_bias_quantizer()
    was = str(out.bias_quantizer_internal)
    out.bias_quantizer = q
    out.bias_quantizer_internal = q
    # .quantizers is what get_quantizers()/hls-style export reads; keep it in sync
    # or the exported config would still advertise the old format.
    if getattr(out, "quantizers", None):
        out.quantizers[-1] = q
    if verbose and was != str(q):
        print(f"  output bias quantizer: {was} -> {q} (layer {out.name})")
    return model

# number with dense
def CreateModel(shape, nb_classes, first_dense):
    x = x_in = Input(shape, name="input")
    x = Dense(first_dense, name="dense1")(x)
    x = keras.layers.BatchNormalization()(x)
    x = Activation("relu", name="relu1")(x)
    x = Dense(nb_classes, name="dense2")(x)
    x = Activation("linear", name="linear")(x)
    model = Model(inputs=x_in, outputs=x)
    return model

# Fold BatchNormalization in QDense
def CreateQModel(shape, nb_classes):
    x = x_in = Input(shape, name="input1")
    x = QDenseBatchnorm(58,
      kernel_quantizer=quantized_bits(4,0,alpha=1),
      bias_quantizer=quantized_bits(4,0,alpha=1),
      name="dense1")(x)
    x = QActivation("quantized_relu(8,0)", name="relu1")(x)
    x = QDense(3,
        kernel_quantizer=quantized_bits(4,0,alpha=1),
        bias_quantizer=_output_bias_quantizer(),
        name="dense2")(x)
    x = Activation("linear", name="linear")(x)
    model = Model(inputs=x_in, outputs=x)
    return model

# hls4ml's only job in this flow was to emit the four weight text files that
# prepareWeights() reads back; nothing here ever synthesized the HLS project it
# also wrote. Emitting them directly drops a heavyweight dependency from the
# inner training loop (prepare_weights_asic used to run a full convert+write per
# ASIC batch) and sidesteps hls4ml 1.3.0, which has no QDenseBatchnorm handler in
# either its keras-v3 or its legacy converter.
#
# The naming (w2/b2 for the first dense layer, w5/b5 for the second) and the flat
# C-order layout reproduce hls4ml's output because prepareWeights() hardcodes
# both the names and the element counts.
DENSE_WEIGHT_FILES = [("w2", "b2"), ("w5", "b5")]

def freezeBatchnormStats(model, verbose=True):
    """Stop QDenseBatchnorm's internal BatchNormalization from adapting its
    moving statistics during training.

    QDenseBatchnorm.call() passes `training` straight into self.batchnorm(...),
    so every training=True forward pass rewrites moving_mean/moving_variance with
    the statistics of whatever data is being trained on -- and at inference the
    folded kernel is gamma * rsqrt(moving_variance + eps) times the raw kernel.
    Fine-tuning a converged model on a *different* dataset therefore degrades it
    with no gradient involved at all: measured on the 850_1700_2550-trained model
    fine-tuned against 1000_2000_3000, one epoch moved the trainable weights by
    ~0.1% but moving_variance by 21%, taking val_loss 0.560 -> 0.864. Grafting
    the original moving stats back recovered 0.577.
    Note ema_freeze_delay does NOT prevent this -- it only selects which stats the
    *fold* reads, while the update above happens regardless. trainable=False is
    what actually puts Keras' BatchNormalization in inference mode.

    ema_freeze_delay still has to be set too, for a second and independent
    reason: left at None it holds bn_training True, so the training-time forward
    pass folds with *batch* statistics and applies the y_corr batch-vs-moving
    correction, while inference folds with the moving statistics. Gradients then
    optimize a model that is not the one that gets deployed. Pinning it to 0
    (with _iteration past the delay) makes the two passes identical. Measured on
    the same fine-tune: trainable=False alone still degraded the model
    (val_loss 0.561 -> 0.603 and rising); with ema_freeze_delay=0 as well it
    trains properly, 0.561 -> 0.367 over 20 epochs.

    Set FREEZE_BATCHNORM_STATS False to restore the old adapt-during-training
    behaviour (appropriate when training from scratch rather than fine-tuning).
    """
    frozen = []
    for layer in model.layers:
        bn = getattr(layer, "batchnorm", None)
        if bn is None:
            continue
        bn.trainable = False
        if hasattr(layer, "ema_freeze_delay"):
            layer.ema_freeze_delay = 0
            # bn_training is (training AND _iteration <= ema_freeze_delay), and a
            # freshly built layer starts at -1, so without this the first two
            # steps would still take the batch-stats path.
            if hasattr(layer, "_iteration"):
                layer._iteration.assign(tf.maximum(layer._iteration, 1))
        frozen.append(layer.name)
    if verbose and frozen:
        print(f"  froze batchnorm (moving stats + folding path) on: {', '.join(frozen)}")
    return model

def chipWeights(layer):
    """(kernel, bias) as the chip is actually programmed with them: batchnorm
    folded into the dense weights, then quantized."""
    if isinstance(layer, QDenseBatchnorm):
        kernel, bias = layer.get_folded_weights()
    else:
        kernel, bias = layer.kernel, layer.bias
    if layer.kernel_quantizer_internal is not None:
        kernel = layer.kernel_quantizer_internal(kernel)
    if layer.bias_quantizer_internal is not None:
        bias = layer.bias_quantizer_internal(bias)
    return np.asarray(kernel), np.asarray(bias)

def writeWeights(model, path):
    """Write the model's dense weights in the layout prepareWeights() expects."""
    os.makedirs(path, exist_ok=True)
    dense = [l for l in model.layers if isinstance(l, (QDense, QDenseBatchnorm))]
    if len(dense) != len(DENSE_WEIGHT_FILES):
        raise ValueError(
            f"prepareWeights() reads a fixed {len(DENSE_WEIGHT_FILES)}-dense-layer "
            f"layout, but the model has {len(dense)}: {[l.name for l in dense]}")
    for layer, (kernel_file, bias_file) in zip(dense, DENSE_WEIGHT_FILES):
        kernel, bias = chipWeights(layer)
        for name, arr in ((kernel_file, kernel), (bias_file, bias)):
            with open(os.path.join(path, name + ".txt"), "w") as fh:
                # .12g keeps every value exact on the quantizer grid; hls4ml's
                # own %.3f is only lossless up to 4-bit weights.
                fh.write(", ".join(f"{v:.12g}" for v in arr.flatten()) + "\n")
    return path

# convert code from hsl4ml style output to chip style input
def prepareWeights(path):
    data_fxp = Fxp(None, signed=True, n_word=4, n_int=0)
    data_fxp.rounding = 'around'
    def to_fxp(val):
        return data_fxp(val)

    # The output-layer bias (b5) is the one field whose format is configurable
    # (see OUTPUT_BIAS_FXP); everything else is fixed at the chip's 4b/0i grid.
    b5_n_word, b5_n_int = OUTPUT_BIAS_FXP
    b5_fxp = Fxp(None, signed=True, n_word=b5_n_word, n_int=b5_n_int)
    b5_fxp.rounding = 'around'
    def to_fxp_b5(val):
        return b5_fxp(val)

    b5_data = pd.read_csv(os.path.join(path, 'b5.txt'), header=None)
    w5_data = pd.read_csv(os.path.join(path, 'w5.txt'), header=None)
    b2_data = pd.read_csv(os.path.join(path, 'b2.txt'), header=None)
    w2_data = pd.read_csv(os.path.join(path, 'w2.txt'), header=None)
    # print(b5_data)

    b5_data_list = []
    w5_data_list = []
    b2_data_list = []
    w2_data_list = []

    for i in range(2, -1, -1):
        b5_data_list.append(to_fxp_b5(b5_data.values[0][i]).bin())

    for i in range(173, -1, -1):
        w5_data_list.append(to_fxp(w5_data.values[0][i]).bin())

    for i in range(57, -1, -1):
        b2_data_list.append(to_fxp(b2_data.values[0][i]).bin())

    for i in range(927, -1, -1):
        w2_data_list.append(to_fxp(w2_data.values[0][i]).bin())

    b5_bin_list = [int(bin_string) for data in b5_data_list for bin_string in data]
    w5_bin_list = [int(bin_string) for data in w5_data_list for bin_string in data]
    b2_bin_list = [int(bin_string) for data in b2_data_list for bin_string in data]
    w2_bin_list = [int(bin_string) for data in w2_data_list for bin_string in data]
    pixel_list = [0 for _ in range(512)]
    b5_w5_b2_w2_pixel_list = b5_bin_list + w5_bin_list + b2_bin_list + w2_bin_list + pixel_list

    csv_file = os.path.join(path, 'b5_w5_b2_w2_pixel_bin.csv')
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(b5_w5_b2_w2_pixel_list)
    
    return csv_file

def input_to_pixelout(x):
    N_INFERENCES = x.shape[0]

    # first create compout
    encoder_values_Ninferences = []
    for i in range(N_INFERENCES):
        encoder_values = []
        for j in range(16):
            a = x[i][j]
            encoder_sum = []
            if(a==0):
                encoder_sum = [0 for _ in range(16)]
                encoder_sum.reverse()
                
            elif(a==1):
                encoder_sum = [1]+[0 for _ in range(15)]
                encoder_sum.reverse()

            elif(a==2):
                encoder_sum = [2]+[0 for _ in range(15)]
                encoder_sum.reverse()

            elif(a==3):
                encoder_sum = [3]+[0 for _ in range(15)]
                encoder_sum.reverse()

            else:
                l3=[]
                if a%3 == 0:
                    result = int(a/3)
                    l3 = [3 for _ in range(result)]
                    l_diff = 16-len(l3)
                    encoder_sum = l3 + [0 for _ in range(l_diff)]
                    encoder_sum.reverse()
                else:
                    result = int(a//3)
                    l3 = [3 for _ in range(result)]
                    diff = a-sum(l3)
                    l3.append(diff)
                    l_diff = 16-len(l3)
                    encoder_sum = l3 + [0 for _ in range(l_diff)]
                    encoder_sum.reverse()

            encoder_values.append(encoder_sum)
        encoder_values = [j for i in encoder_values for j in i]
        encoder_values_Ninferences.append(encoder_values)
        
    compout_values_Ninferences = []
    for i in range(N_INFERENCES):
        compout_values = []
        for j in range(256):
            a = encoder_values_Ninferences[i][j]
            if(a==3):
                compout_values.append(7)
            elif(a==2):
                compout_values.append(3)
            elif(a==1):
                compout_values.append(1)
            else:
                compout_values.append(0)
        compout_values_Ninferences.append(compout_values)

    return compout_values_Ninferences

class ModelPipeline:
    def __init__(self, model, optimizer, train_acc_metric, val_acc_metric, batch_size=32,
                 asic_training=False, alpha=1.0, asic_every=1, asic_warmup_epochs=1,
                 vth=VTH_DEFAULT, pg_hlev=PG_HLEV_DEFAULT,
                 timestamp=TIMESTAMP_DEFAULT, decode=None):
        self.model = model
        self.optimizer = optimizer
        self.train_acc_metric = train_acc_metric
        self.val_acc_metric = val_acc_metric
        self.batch_size = batch_size
        self.asic_training = asic_training

        # asic-in-the-loop settings
        # alpha: samples the chip gets wrong count (1 + alpha) times as much in
        #   the supervised loss. alpha=0 disables the ASIC term entirely.
        # asic_every: only query the chip every N batches. Each query reprograms
        #   the chip and runs it, so N=1 is expensive.
        # asic_warmup_epochs: number of leading epochs to run with alpha=0, so a
        #   run can be checked against the pre-trained baseline before the chip
        #   starts influencing the gradients.
        self.alpha = alpha
        self.asic_every = asic_every
        self.asic_warmup_epochs = asic_warmup_epochs

        # Chip operating point, applied by forward_pass_asic() on every query.
        # This lives on the pipeline rather than inside forward_pass_asic()
        # because it is the one setting that must match the dataset: whoever
        # chose the yprofiles.csv also has to choose these, and both callers
        # (DNNTraining, asicFidelityCheck) go through here.
        self.vth = tuple(vth)
        self.pg_hlev = pg_hlev
        # Readout slice scored as the answer, and the path to the last
        # readout.csv so every OTHER slice can be scored for free afterwards.
        self.timestamp = timestamp
        # Alternative decode (see decodeStrategies): a strategy name such as
        # "maj[17:21]" or "stable(2)@[13:22]" overrides the single-slice read.
        # None keeps DNN_analyse_2's behaviour exactly, so this changes nothing
        # until a tuneDnnThresholds() result is deliberately plugged in.
        self.decode = decode
        self.last_readout_csv = None

        # Initialize custom loss function
        self.loss_fn = self.custom_loss_function

    def print_model(self):
        """
        Iterate through each layer and print weights and biases
        """
        for layer in self.model.layers:
            print(f"Layer: {layer.name}")
            for weight in layer.weights:
                print(f"  {weight.name}: shape={weight.shape}")
                print(f"    Values:\n{weight.numpy()}\n")

    def custom_loss_function(self, y_true, y_pred, sample_weight=None):
        """
        Masked sparse categorical crossentropy (from_logits=True).

        y_true == 3 marks an entry with no usable label and is dropped from the
        loss. sample_weight optionally reweights the surviving entries; the
        asic-in-the-loop term uses it to push harder on samples the chip fails.
        """

        # cast explicitly: y_true may arrive as int32/float depending on how the
        # label CSV was parsed, and the mask multiply below requires a match.
        y_true = tf.cast(y_true, tf.int64)

        # only valid y_true is 0,1,2. Any patterns with a 3 should be ignored
        mask = tf.cast(tf.not_equal(y_true, 3), dtype=tf.float32)

        # artificially set y_true = 3 values to 0 so the CE call stays in range
        y_true = y_true * tf.cast(mask, dtype=tf.int64)

        # compute per-sample loss
        loss = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred, from_logits=True)

        # mask, then optionally reweight
        weights = mask
        if sample_weight is not None:
            weights = weights * tf.cast(sample_weight, tf.float32)
        loss *= weights

        # weighted mean over the surviving entries. divide_no_nan guards the
        # fully-masked batch: a plain 0/0 yields NaN, and one NaN gradient step
        # permanently destroys the weights.
        loss = tf.math.divide_no_nan(tf.reduce_sum(loss), tf.reduce_sum(weights))

        return loss


    def split_data(self, x_data, y_data, test_size=0.2, shuffle=True, random_state=42):
        """
        Splits data into training and testing datasets.
        """
        x_train, x_val, y_train, y_val = train_test_split(
            x_data, y_data, test_size=test_size, random_state=random_state, shuffle=shuffle
        )
        self.train_dataset = tf.data.Dataset.from_tensor_slices((x_train, y_train)).batch(self.batch_size)
        self.val_dataset = tf.data.Dataset.from_tensor_slices((x_val, y_val)).batch(self.batch_size)
    
    # @tf.function
    def forward_pass(self, x, training=False):
        """
        Performs a forward pass of the model.
        """
        return self.model(x, training=training)
    
    def prepare_weights_asic(self, x):        

        # write the current weights to file
        weights_dir = writeWeights(self.model, "./tmp/test_prj/firmware/weights/")
        dnn_csv = prepareWeights(weights_dir)
        
        # generate input csv
        # convert out of TF first: input_to_pixelout does scalar python arithmetic
        # (a % 3, int(a / 3)) per element, which is both slow and dtype-fragile on
        # eager tensors.
        pixelout = input_to_pixelout(np.asarray(x).astype(int))
        pixel_compout_csv = './tmp/compouts.csv'
        # pixel_compout_csv = '/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/850_1700_2550/compouts_ylocal_0.00_1.35.csv'
        with open(pixel_compout_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(pixelout)

        return dnn_csv, pixel_compout_csv

    def forward_pass_asic(self, x, dnn_csv = None, pixel_compout_csv = None):
        """
        Performs a forward pass of the model on the asic
        """

        # print("   within forward pass asic")

        # run to chip -> output saved to readout.csv
        vth_0_mv, vth_1_mv, vth_2_mv = vthToVolts(self.vth)
        freq = '3F'
        outDir = DNN(
            progDebug=False, loopbackBit=0, patternIndexes = None, verbose=False, # update range when finished
            injection_delay='1E', bxclk_period='28', startBxclkState='0',scan_load_delay='13', 
            cfg_test_delay='5', cfg_test_sample='20', progResetMask='0', configclk_period='64', 
            test_delay='14', test_sample='0F', bxclk_delay='12',configClkGate='0',scanLoadPhase ='26',
            vth0 = vth_0_mv, vth1=vth_1_mv, vth2=vth_2_mv, pg_hlev=self.pg_hlev,
            dnn_csv = dnn_csv,
            pixel_compout_csv = pixel_compout_csv,
            # DNN() builds its own output path as dataDir/chipInfo/testInfo and
            # returns it. A fixed dateTime keeps every training query in one
            # reused directory instead of creating hundreds of timestamped ones.
            dataDir = "./tmp",
            dateTime = "asic_training",
            readYproj=False,
        )
        if outDir is None:
            raise RuntimeError(
                "DNN() returned no output directory, so there is no readout to score")

        #Take in the pixel_compout_csv files and return the DNN output value in decimal
        self.last_readout_csv = os.path.join(outDir, "readout.csv")
        if self.decode:
            # A multi-slice decode chosen by tuneDnnThresholds(). Same encoding
            # DNN_analyse_2 returns (0/1/2 valid, 3 invalid), so everything
            # downstream -- asic_sample_weights, the disagreement metric -- is
            # unaffected by which one is in use.
            dnnOut = applyDecode(self.last_readout_csv, self.decode)
        else:
            dnnOut=DNN_analyse_2(readout_CSV = self.last_readout_csv,
                                 timestamp=self.timestamp)
        # print(dnnOut.shape)
        dnnOut = tf.convert_to_tensor(dnnOut)
        return dnnOut


    def asic_sample_weights(self, y_asic, y_true, alpha):
        """
        Turn the chip's predictions into per-sample loss weights.

            w_i = 1 + alpha   if the ASIC got sample i wrong
            w_i = 1           if it got it right, or the readout was invalid (3)

        This deliberately does NOT use the ASIC output as a training target.
        Adding `alpha * CE(y_asic, logits)` to the loss gives a gradient of
        `alpha * (p - onehot(y_asic))`, which pushes probability mass *toward*
        the chip's own mistakes wherever y_asic != y_true -- i.e. it trains the
        model to reproduce its hardware errors. And because the ASIC is a
        quantized copy of this same model, y_asic ~= argmax(p) on the remaining
        samples, so that term degenerates into entropy minimisation on the
        model's own predictions: no new information, just overconfidence.

        Reweighting keeps every gradient pointing at the true label and simply
        pushes harder on the samples the deployed hardware actually fails, which
        is the one thing the chip knows that the surrogate model does not.

        Returns (weights, stats).
        """
        y_asic = tf.cast(tf.reshape(y_asic, [-1]), tf.int64)
        y_true = tf.cast(tf.reshape(y_true, [-1]), tf.int64)

        # A short/long readout means readout.csv is out of sync with the inputs
        # that were written to pixel_compout_csv. Broadcasting that mismatch
        # silently would corrupt every weight in the batch.
        tf.debugging.assert_equal(
            tf.shape(y_asic)[0], tf.shape(y_true)[0],
            message="ASIC readout row count does not match the batch size")

        # 3 is the invalid [1,1] codeword (see DNN_analyse_2): the readout failed,
        # so it carries no information either way -- weight it as 1, NOT as a
        # disagreement, or readout noise would drive the reweighting.
        invalid = tf.equal(y_asic, 3)
        wrong = tf.logical_and(tf.not_equal(y_asic, y_true), tf.logical_not(invalid))

        weights = 1.0 + alpha * tf.cast(wrong, tf.float32)

        n = tf.cast(tf.shape(y_true)[0], tf.float32)
        stats = {
            "err_frac": tf.reduce_sum(tf.cast(wrong, tf.float32)) / n,
            "invalid_frac": tf.reduce_sum(tf.cast(invalid, tf.float32)) / n,
        }
        return weights, stats

    # @tf.function
    def train_step(self,
                   x_batch, y_batch,
                   dnn_csv = None, pixel_compout_csv = None,
                   alpha = 1.0, use_asic = False, # for asic training
    ):
        """
        Performs a single training step.

        Returns (loss_value, asic_stats); asic_stats is None when the chip was
        not queried for this batch.
        """

        # Query the chip outside the tape: its output is a constant as far as
        # autodiff is concerned, and it only enters the loss as a weight.
        sample_weight, asic_stats = None, None
        if use_asic:
            y_asic = self.forward_pass_asic(x_batch, dnn_csv, pixel_compout_csv)
            sample_weight, asic_stats = self.asic_sample_weights(y_asic, y_batch, alpha)

        with tf.GradientTape() as tape:
            logits = self.forward_pass(x_batch, training=True)
            loss_value = self.loss_fn(y_batch, logits, sample_weight=sample_weight)

        grads = tape.gradient(loss_value, self.model.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.model.trainable_weights))
        self.train_acc_metric.update_state(y_batch, logits)
        return loss_value, asic_stats

    # @tf.function
    def val_step(self, x_batch, y_batch):
        """
        Performs a single validation step.
        """
        logits = self.forward_pass(x_batch, training=False)
        val_loss = self.loss_fn(y_batch, logits)
        self.val_acc_metric.update_state(y_batch, logits)
        return val_loss

    def evaluate_val(self):
        """Mean masked val loss over the whole validation set, no progbar."""
        val_loss = 0.0
        for x_batch, y_batch in self.val_dataset:
            val_loss += float(self.val_step(x_batch, y_batch))
        self.val_acc_metric.reset_state()
        return val_loss / len(self.val_dataset)

    def _checkpoint(self, checkpoint_dir, epoch, train_loss, train_acc,
                    val_loss, val_acc, alpha, asic_err, asic_invalid,
                    asic_batches, improved):
        """Persist this epoch's weights and metrics.

        A checkpoint failure must never abort the run: on an asic_training run
        the epoch that just finished cost ~an hour of chip time, and losing it
        to a disk error would be worse than losing the checkpoint.
        """
        os.makedirs(checkpoint_dir, exist_ok=True)
        path = os.path.join(checkpoint_dir, f"model_epoch{epoch:02d}.h5")
        try:
            self.model.save(path)
        except Exception as e:
            print(f"  WARNING: checkpoint failed ({e}); training continues")
            return

        row = {
            "epoch": epoch,
            "train_loss": train_loss, "train_acc": train_acc,
            "val_loss": val_loss, "val_acc": val_acc,
            "alpha": alpha,
            # The chip's own view of this epoch. val_loss cannot see it, so this
            # is the only per-epoch record of whether the hardware improved.
            "asic_disagreement": (asic_err / asic_batches) if asic_batches else "",
            "asic_invalid": (asic_invalid / asic_batches) if asic_batches else "",
            "asic_batches": asic_batches,
            "best_by_val_loss": int(improved),
            "checkpoint": os.path.basename(path),
        }
        hist = os.path.join(checkpoint_dir, "history.csv")
        try:
            write_header = not os.path.exists(hist)
            with open(hist, "a", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(row))
                if write_header:
                    w.writeheader()
                w.writerow(row)
        except Exception as e:
            print(f"  WARNING: history.csv append failed ({e})")
        print(f"  checkpoint: {path}")

    def train(self, epochs, patience=20, checkpoint_dir=None):
        """
        Trains the model for a specified number of epochs with early stopping.

        checkpoint_dir: if set, write one .h5 per epoch plus a history.csv row
        there. Without it train() keeps only best_weights in memory and discards
        every other epoch -- unrecoverable on a multi-hour chip run. It also
        matters because the criterion selecting best_weights is chip-blind:
        val_step() passes no sample_weight, so val_loss never sees the ASIC, and
        the epoch it picks is not necessarily the one that adapted best to the
        hardware. Keeping every epoch lets asicFidelityCheck() decide afterwards.
        """
        # Seed the early-stopping baseline with the *incoming* weights, so epoch 0
        # is a candidate for "best". Starting from inf means the first epoch always
        # wins by default and the pipeline is structurally unable to notice it has
        # made a pre-converged model worse -- exactly the failure mode when
        # fine-tuning, where every epoch can be worse than the checkpoint we loaded.
        best_val_loss = self.evaluate_val()
        best_weights = self.model.get_weights()
        print(f"Baseline val_loss before training: {best_val_loss:.4f} "
              f"(early stopping will not save anything worse than this)")
        best_epoch = 0
        wait = 0

        for epoch in range(epochs):
            print(f"Epoch {epoch + 1}/{epochs}")

            # warmup: hold alpha at 0 for the first epoch(s) so the run can be
            # compared against the pre-trained baseline before the chip starts
            # influencing gradients.
            alpha = 0.0 if epoch < self.asic_warmup_epochs else self.alpha

            # Training loop
            train_loss = 0
            train_steps = len(self.train_dataset)
            train_progbar = Progbar(target=train_steps, stateful_metrics=["loss", "sparse_categorical_accuracy"])
            asic_err, asic_invalid, asic_batches = 0.0, 0.0, 0

            for step, (x_batch, y_batch) in enumerate(self.train_dataset):
                # print(f"Batch {step}/{len(self.train_dataset)}")

                use_asic = (self.asic_training and alpha > 0.0
                            and step % self.asic_every == 0)

                # prepare weights for asic
                if use_asic:
                    dnn_csv, pixel_compout_csv = self.prepare_weights_asic(x_batch)
                    loss_value, asic_stats = self.train_step(
                        x_batch, y_batch, dnn_csv, pixel_compout_csv,
                        alpha=alpha, use_asic=True)
                else:
                    loss_value, asic_stats = self.train_step(x_batch, y_batch)

                if asic_stats is not None:
                    asic_err += float(asic_stats["err_frac"])
                    asic_invalid += float(asic_stats["invalid_frac"])
                    asic_batches += 1

                train_loss += float(loss_value)
                train_acc = self.train_acc_metric.result()
                # Report the running epoch mean, not this batch's value. These are
                # declared stateful_metrics, so Progbar prints whatever it is
                # handed verbatim -- passing loss_value made the displayed "loss"
                # the last batch only, which is why it never reconciled with the
                # epoch mean early stopping actually compares.
                train_progbar.update(step + 1, values=[("loss", train_loss / (step + 1)), ("sparse_categorical_accuracy", train_acc.numpy())])

            train_loss /= train_steps
            train_acc = self.train_acc_metric.result()
            self.train_acc_metric.reset_state()

            # An invalid rate above ~1% points at readout/timing rather than
            # random bit errors, and masking it would hide a real hardware bug.
            if asic_batches:
                print(f"  ASIC over {asic_batches} chip batches (alpha={alpha}): "
                      f"disagreement {asic_err / asic_batches:.4f}, "
                      f"invalid readout (==3) {asic_invalid / asic_batches:.4f}")

            # Validation loop
            val_loss = 0
            val_steps = len(self.val_dataset)
            val_progbar = Progbar(target=val_steps, stateful_metrics=["val_loss", "val_sparse_categorical_accuracy"])
            
            for step, (x_batch, y_batch) in enumerate(self.val_dataset):
                val_loss_batch = self.val_step(x_batch, y_batch)
                # float(), so best_val_loss stays comparable and formattable
                # against the python-float baseline seeded before the loop
                val_loss += float(val_loss_batch)
                val_acc = self.val_acc_metric.result()
                # running epoch mean, same reason as the training progbar above
                val_progbar.update(step + 1, values=[("val_loss", val_loss / (step + 1)), ("val_sparse_categorical_accuracy", val_acc.numpy())])

            val_loss /= val_steps
            val_acc = self.val_acc_metric.result()
            self.val_acc_metric.reset_state()

            # Early stopping logic
            improved = val_loss < best_val_loss
            if improved:
                best_val_loss = val_loss
                best_epoch = epoch + 1
                wait = 0
                best_weights = self.model.get_weights()
            else:
                wait += 1

            # Checkpoint before the break, so the epoch that triggered the stop
            # is on disk too.
            if checkpoint_dir is not None:
                self._checkpoint(checkpoint_dir, epoch + 1, train_loss,
                                 float(train_acc), val_loss, float(val_acc),
                                 alpha, asic_err, asic_invalid, asic_batches,
                                 improved)

            if not improved and wait >= patience:
                print("Early stopping triggered.")
                break

        # Restore the best weights however the loop ended. Doing this only on the
        # early-stopping branch leaves the model on the final epoch's weights
        # whenever the epoch budget runs out first -- which is exactly the case
        # when fine-tuning an already-converged model, where val loss can drift
        # upward from epoch 1 and never recover.
        print(f"Restoring best weights (val_loss={best_val_loss:.4f}).")
        if best_epoch == 0:
            print("  NOTE: no epoch beat the pre-training baseline; the incoming "
                  "weights are being kept unchanged. Training accomplished nothing.")
        else:
            print(f"  from epoch {best_epoch}/{epochs}")
        self.model.set_weights(best_weights)


def asicFidelityCheck(model_file="model.h5", n_samples=1024, repeats=2,
                      use_val=True, batch_stride=None,
                      vth=VTH_DEFAULT, pg_hlev=PG_HLEV_DEFAULT, data_dir=None,
                      timestamp=TIMESTAMP_DEFAULT):
    """Measure how faithfully the chip reproduces the QKeras model it runs.

    Every number train() reports scores the chip against `y_true`
    ("disagreement"), which cannot separate "the chip is a worse classifier"
    from "the chip is a *different* classifier". Both look like 22.6%.

    This scores one batch three ways -- software vs truth, chip vs truth, and
    chip vs software -- decomposes the chip's errors into ones the software
    model also makes (shared task difficulty) versus ones it does not (loss in
    the model->chip mapping), and reruns the chip on byte-identical weights and
    inputs to check its answers are reproducible at all.

    By default this samples only the FIRST n_samples rows of the split
    (next(iter(ds))). train() does not: with asic_every=k it queries the chip
    at batches 0, k, 2k, ... spread across the *entire* epoch, e.g. 14 batches
    of 1024 covering rows 0-1024, 10240-11264, ..., 133120-134144 out of
    135685 -- nearly the full training set, not just its front. Measured
    14.1-14.2% chip error at both n_samples=1024 and 4096 sampling only the
    front of the split, against train()'s reported 22.6% pooled over its
    stride-10 sample -- consistent with the front of the split being an easier
    subset than the stride-10 sample train() actually saw.

    Pass batch_stride=k (matching asic_every) to reproduce train()'s sample
    exactly: every k-th batch of n_samples rows is gathered from `ds` and
    pooled, instead of only the first. Costs ceil(num_batches/k) times as much
    chip time as the default.

    Costs about n_samples * repeats * 23 ms of chip time (~46 s at defaults),
    times the number of batches gathered when batch_stride is set.

    vth/pg_hlev must be the operating point the model was TRAINED at, or every
    number below is measured on a different chip configuration than the one
    being diagnosed. data_dir defaults to the dataset generated at `vth`.
    """
    model = _loadModelForChip(model_file)

    data_dir = datasetDir(vth) if data_dir is None else data_dir
    print(f"Data      {data_dir}")
    print(f"Chip      vth={tuple(vth)} e-  pg_hlev={pg_hlev} V")
    x, y = loadDataset(data_dir)

    # Reuse ModelPipeline purely for split_data / prepare_weights_asic /
    # forward_pass_asic; nothing here trains, so the optimizer is a placeholder.
    # split_data's random_state is fixed, so with the same data_dir this sees
    # exactly the split train() saw.
    pipeline = ModelPipeline(
        model, tf.keras.optimizers.Adam(),
        tf.keras.metrics.SparseCategoricalAccuracy(),
        tf.keras.metrics.SparseCategoricalAccuracy(),
        batch_size=n_samples, asic_training=True,
        alpha=1.0, asic_every=1, asic_warmup_epochs=0,
        vth=vth, pg_hlev=pg_hlev, timestamp=timestamp)
    pipeline.split_data(x, y)
    ds = pipeline.val_dataset if use_val else pipeline.train_dataset
    if batch_stride is None:
        x_batch, y_batch = next(iter(ds))
    else:
        # Reproduce train()'s asic_every stride over the WHOLE split, not just
        # its front, so this batch is the same one disagreement was computed
        # on -- pooled the same way, over the same rows.
        xs, ys, picked = [], [], 0
        for i, (xb, yb) in enumerate(ds):
            if i % batch_stride == 0:
                xs.append(xb)
                ys.append(yb)
                picked += 1
        x_batch = tf.concat(xs, axis=0)
        y_batch = tf.concat(ys, axis=0)
        print(f"batch_stride={batch_stride}: gathered {picked} batches "
              f"of {n_samples} (matches asic_every={batch_stride} over a "
              f"full epoch)")
    y_true = np.asarray(y_batch).astype(int).reshape(-1)
    print(f"Batch: {len(y_true)} samples from the "
          f"{'validation' if use_val else 'training'} split")

    logits = np.asarray(pipeline.forward_pass(x_batch, training=False))
    y_sw = np.argmax(logits, axis=1).astype(int)

    # The chip runs fixed-point arithmetic; QKeras accumulates in float32. Run
    # the C++ hls4ml emits alongside the RTL so that deviation is measured here
    # rather than left inside the chip-vs-software gap. y_ref is then the value
    # the chip *should* have driven, and everything below scores against it.
    y_hls, hls_note = None, None
    if hls_reference is not None:
        try:
            hls_logits = hls_reference.hlsPredict(
                model, x_batch, writeWeightsFn=writeWeights)
            y_hls = np.argmax(hls_logits, axis=1).astype(int)
        except Exception as e:
            hls_note = f"C++ reference unavailable ({e})"
    else:
        hls_note = f"C++ reference not imported ({_HLS_IMPORT_ERROR})"
    y_ref = y_hls if y_hls is not None else y_sw
    ref_name = "C++ (RTL precision)" if y_hls is not None else "software (QKeras)"

    print("\n=== hls4ml C++ (RTL fixed point) vs QKeras ===")
    if y_hls is None:
        print(f"  {hls_note}")
        print("  falling back to QKeras as the reference; any fixed-point")
        print("  deviation stays folded into the chip-vs-software gap below.")
    else:
        n_dev = int((y_hls != y_sw).sum())
        print(f"  agreement : {(y_hls == y_sw).mean():.4f}   "
              f"({n_dev} of {len(y_sw)} decisions differ)")
        # input_t is ap_fixed<16,6> with the default AP_WRAP, so a y-profile bin
        # above 31 folds mod 64. Every accumulator downstream is sized to be
        # lossless, so these are the only samples where the two can disagree.
        wrap = hls_reference.inputWrapMask(x_batch)
        print(f"  input bins outside ap_fixed<16,6> = [-32,+32): "
              f"{int(wrap.sum())} of {len(wrap)} samples ({wrap.mean():.4f})")
        if wrap.any():
            print(f"    of those, {int((y_hls != y_sw)[wrap].sum())} flipped "
                  f"(these wrap mod 64 in the RTL, they do not saturate)")
        if n_dev == 0:
            print("  => fixed-point costs nothing here; the chip gap is not precision.")

    runs, readouts = [], []
    for r in range(repeats):
        # Weights are identical on every pass (the model is not being updated),
        # so repeat runs are a true same-input/same-config replay.
        dnn_csv, pixel_compout_csv = pipeline.prepare_weights_asic(x_batch)
        y_asic = np.asarray(
            pipeline.forward_pass_asic(x_batch, dnn_csv, pixel_compout_csv)
        ).astype(int).reshape(-1)
        if len(y_asic) != len(y_true):
            raise RuntimeError(
                f"chip returned {len(y_asic)} rows for a {len(y_true)}-row batch")
        runs.append(y_asic)
        # forward_pass_asic reuses one output directory, so readout.csv is
        # overwritten on every run. Keep a copy of each: without this the slice
        # scan below would score the LAST run while every other number here
        # describes the first, and the two differ by ~3% of events -- enough to
        # make the sections of this report quietly inconsistent.
        keep = os.path.join(os.path.dirname(pipeline.last_readout_csv),
                            f"readout_run{r}.csv")
        shutil.copy(pipeline.last_readout_csv, keep)
        readouts.append(keep)
        print(f"  chip run {r + 1}/{repeats}: "
              f"{int((y_asic == 3).sum())} invalid readouts")

    a = runs[0]
    lab_ok = y_true != 3          # usable ground-truth label
    chip_ok = a != 3              # usable chip readout
    both = lab_ok & chip_ok

    sw_acc = (y_sw[lab_ok] == y_true[lab_ok]).mean()
    chip_acc = (a[both] == y_true[both]).mean()
    agree = (a[chip_ok] == y_sw[chip_ok]).mean()

    print("\n=== accuracy vs ground truth ===")
    print(f"  software (QKeras) : {sw_acc:.4f}   over {int(lab_ok.sum())} samples")
    if y_hls is not None:
        print(f"  C++ (RTL precision): "
              f"{(y_hls[lab_ok] == y_true[lab_ok]).mean():.4f}   "
              f"over {int(lab_ok.sum())} samples")
    print(f"  chip              : {chip_acc:.4f}   over {int(both.sum())} samples")
    print(f"  invalid readout   : {1.0 - chip_ok.mean():.4f}")

    print("\n=== chip vs software (the fidelity number) ===")
    print(f"  vs QKeras : {agree:.4f}   over {int(chip_ok.sum())} valid readouts")
    if y_hls is not None:
        # The honest readout-error number: fixed-point deviation already removed.
        print(f"  vs C++    : {(a[chip_ok] == y_hls[chip_ok]).mean():.4f}   "
              f"<- readout error with RTL precision accounted for")
    print("  >0.97 => chip is a faithful copy; the error is task difficulty.")
    print("  <0.95 => the model->chip mapping is lossy; training cannot fix it.")

    # Where the chip's errors come from. "chip only" is the mapping loss: the
    # software model got these right and the chip did not.
    sw_right = y_sw == y_true
    chip_right = a == y_true
    n = int(both.sum())
    quad = {
        "both right": int((both & sw_right & chip_right).sum()),
        "chip only wrong": int((both & sw_right & ~chip_right).sum()),
        "sw only wrong": int((both & ~sw_right & chip_right).sum()),
        "both wrong": int((both & ~sw_right & ~chip_right).sum()),
    }
    print("\n=== error decomposition (valid label + valid readout) ===")
    for k, v in quad.items():
        print(f"  {k:<15} : {v:6d}  ({v / n:.4f})")
    chip_err = quad["chip only wrong"] + quad["both wrong"]
    if chip_err:
        print(f"  -> of the chip's {chip_err} errors, "
              f"{quad['chip only wrong'] / chip_err:.1%} are mapping loss "
              f"(software got them right)")

    bitErrorBreakdown(a, y_ref, ref_name=ref_name)
    if readouts:
        # readouts[0] is run 1, the same run `a` came from, so these agree with
        # every other number above instead of describing a different pass.
        scanTimeSlices(readouts[0], y_ref,
                       timestamp=timestamp, ref_name=ref_name)
        scanTimeSlices(readouts[0], y_true,
                       timestamp=timestamp, ref_name="ground truth")
        # Whether any multi-slice decode is worth switching to. Free: it rescores
        # a readout the chip already produced.
        scoreDecodes(readouts[0], y_ref, y_true, ref_name=ref_name,
                     timestamp=timestamp)

    print("\n=== chip vs software confusion (rows = software, cols = chip) ===")
    cm = np.zeros((3, 3), dtype=int)
    for s, c in zip(y_sw[chip_ok], a[chip_ok]):
        cm[s, c] += 1
    print("          chip0   chip1   chip2")
    for i, row in enumerate(cm):
        print(f"  sw{i}   " + "".join(f"{v:8d}" for v in row))

    # DNN_analyse_2 decodes [msb, lsb] = [dnn1[ts], dnn0[ts]] into the class
    # index, so the class index IS the 2-bit codeword: 0=[0,0] 1=[0,1] 2=[1,0]
    # 3=[1,1]=invalid, and the two output lines come straight out with shifts.
    #
    # dnn0/dnn1 leave the chip through an AC-coupled off-chip discriminator on a
    # 50 ohm load (~100 mV of swing), thresholded by a manual pot. Taking the
    # C++ reference as the value the chip *should* have driven, every difference
    # is a readout bit error on one of those two lines, and the 0->1 vs 1->0
    # asymmetry is what a threshold offset looks like. Invalid (==3) readouts
    # are deliberately included: [1,1] is just both lines reading high, which is
    # a bit error like any other.
    print(f"\n=== readout bit errors vs {ref_name} (all runs pooled) ===")
    print("  line       0->1 (thresh LOW)        1->0 (thresh HIGH)")
    bit_rates = {}
    for shift, name in ((1, "dnn1/msb"), (0, "dnn0/lsb")):
        n0 = n1 = f01 = f10 = 0
        for run in runs:
            b_sw = (y_ref >> shift) & 1
            b_ch = (run >> shift) & 1
            n0 += int((b_sw == 0).sum())
            f01 += int(((b_sw == 0) & (b_ch == 1)).sum())
            n1 += int((b_sw == 1).sum())
            f10 += int(((b_sw == 1) & (b_ch == 0)).sum())
        r01 = f01 / n0 if n0 else float("nan")
        r10 = f10 / n1 if n1 else float("nan")
        bit_rates[name] = (r01, r10)
        print(f"  {name}  {f01:6d}/{n0:<7d} = {r01:.4f}   "
              f"{f10:6d}/{n1:<7d} = {r10:.4f}")
    print("  1->0 >> 0->1 => threshold too HIGH on that line (ones fall under it)")
    print("  0->1 >> 1->0 => threshold too LOW  on that line (zeros ride over it)")
    print("  balanced     => threshold centred; the residue is noise, not offset")

    # The coupling capacitor forces the mean to zero, so the baseline -- and
    # with it the effective threshold -- follows the recent duty cycle. A run
    # after the chip has been idle is therefore a different operating point
    # from the 14-per-epoch back-to-back cadence train() drives it at.
    print("\n=== per-run drift (AC-coupled baseline follows sustained rate) ===")
    print("   run   chip_acc   agree_ref   invalid   dnn1 1->0   dnn0 1->0")
    for r, run in enumerate(runs):
        ok = run != 3
        sel = ok & lab_ok
        acc = (run[sel] == y_true[sel]).mean() if sel.any() else float("nan")
        ag = (run[ok] == y_ref[ok]).mean() if ok.any() else float("nan")
        hi = []
        for shift in (1, 0):
            m = ((y_ref >> shift) & 1) == 1
            hi.append((((run >> shift) & 1)[m] == 0).mean() if m.any() else float("nan"))
        print(f"   {r + 1:3d}   {acc:.4f}     {ag:.4f}     "
              f"{1.0 - ok.mean():.4f}    {hi[0]:.4f}      {hi[1]:.4f}")
    print("  a monotonic trend down the chip_acc column means the baseline is")
    print("  still settling; use repeats=6 or more to see it clearly.")

    # Settling *within* a burst, which drift-across-runs cannot see. train()
    # drives the chip in batch_size=1024 bursts separated by ~18 s of idle
    # (asic_every=10 leaves 9 software-only steps between them), so a transient
    # occupying the first quarter of a 4096-vector run would occupy all of a
    # 1024-vector one. That is the shape of train()'s 22.6% disagreement against
    # this diagnostic's ~14% on the same split.
    #
    # split_data() never reshuffles (it is .batch() with no .shuffle()), so
    # position is fixed -- but train_test_split already randomised the rows, so
    # position carries no class structure. The software column is the control:
    # it must stay flat. If it does and chip_acc rises, the effect is the chip's.
    print("\n=== position within the burst (all runs pooled) ===")
    print("  chunk   samples       sw_acc   chip_acc   agree_ref   dnn1 1->0   dnn0 1->0")
    n_chunk = 8
    edges = np.linspace(0, len(y_true), n_chunk + 1).astype(int)
    for c in range(n_chunk):
        lo, hi = int(edges[c]), int(edges[c + 1])
        tru, ref = y_true[lo:hi], y_ref[lo:hi]
        lab = tru != 3
        sw_c = (y_sw[lo:hi][lab] == tru[lab]).mean() if lab.any() else float("nan")
        accs, ags, hi1, hi0 = [], [], [], []
        for run in runs:
            seg = run[lo:hi]
            ok = seg != 3
            sel = ok & lab
            if sel.any():
                accs.append((seg[sel] == tru[sel]).mean())
            if ok.any():
                ags.append((seg[ok] == ref[ok]).mean())
            for shift, sink in ((1, hi1), (0, hi0)):
                m = ((ref >> shift) & 1) == 1
                if m.any():
                    sink.append((((seg >> shift) & 1)[m] == 0).mean())
        avg = lambda v: (float(np.mean(v)) if len(v) else float("nan"))
        print(f"  {c + 1:3d}   {lo:5d}-{hi:<7d}  {sw_c:.4f}     {avg(accs):.4f}"
              f"     {avg(ags):.4f}      {avg(hi1):.4f}      {avg(hi0):.4f}")
    print("  sw_acc flat + chip_acc rising => the chip is still settling into the")
    print("  burst, and train()'s 1024-vector bursts never leave the transient.")
    print("  both flat => burst length is not the explanation; look elsewhere.")

    print("\n=== determinism (identical weights + identical inputs) ===")
    for r in range(1, repeats):
        same = (runs[0] == runs[r]).mean()
        # Compare only where BOTH runs read out cleanly, so invalid-codeword
        # noise is not counted as a decision flip.
        clean = (runs[0] != 3) & (runs[r] != 3)
        same_clean = (runs[0][clean] == runs[r][clean]).mean() if clean.any() else float("nan")
        print(f"  run 1 vs run {r + 1}: {same:.4f} identical "
              f"({same_clean:.4f} excluding invalid readouts)")
    if repeats < 2:
        print("  (skipped: repeats < 2)")
    else:
        print("  <1.0 excluding invalid => the chip is nondeterministic; no "
              "amount of alpha fixes that.")

    return {
        "sw_acc": float(sw_acc), "chip_acc": float(chip_acc),
        "agreement": float(agree), "quadrants": quad, "runs": runs,
        "y_sw": y_sw, "y_true": y_true, "bit_rates": bit_rates,
        "y_hls": y_hls, "y_ref": y_ref, "ref_name": ref_name,
        "hls_agreement": (None if y_hls is None
                          else float((y_hls == y_sw).mean())),
        "chip_vs_hls": (None if y_hls is None
                        else float((a[chip_ok] == y_hls[chip_ok]).mean())),
    }


def DNNTraining(asic_training=False,
                vth=VTH_DEFAULT, pg_hlev=PG_HLEV_DEFAULT, data_dir=None,
                init_model=INIT_MODEL_DEFAULT, out_model="model.h5",
                checkpoint_dir=None, alpha=1.0, asic_every=1,
                asic_warmup_epochs=0, epochs=12, patience=None,
                batch_size=1024, learning_rate=1e-4,
                timestamp=TIMESTAMP_DEFAULT):
    """Fine-tune the QKeras model, optionally with the chip in the loop.

    Everything that changes when the operating point changes is an argument:

      vth            (vth0, vth1, vth2) in electrons. Sets the chip's
                     discriminator bias AND, via data_dir, which dataset is
                     trained on -- the two cannot drift apart.
      pg_hlev        injection pulse high level (V); retuned per threshold set.
      data_dir       yprofiles.csv + clslabels.csv. None -> datasetDir(vth).
      init_model     .h5 checkpoint to fine-tune from.
      out_model      where the finished model is written.
      checkpoint_dir per-epoch .h5 + history.csv. None -> ./checkpoints_<vth>,
                     derived so two runs at different thresholds cannot append
                     to each other's history.csv.
      alpha          weight multiplier on samples the chip gets wrong; 0
                     disables the ASIC term.
      asic_every     query the chip every N batches. The only knob that moves
                     chip cost: an epoch runs len(train)/asic_every vectors at
                     ~23 ms each, independent of batch_size.
      patience       early-stopping patience. None -> epochs, i.e. disabled.

    Call it directly to override; ~r9 runs it with these defaults, which live
    in ROUTINE_DNNTraining.
    """

    data_dir = datasetDir(vth) if data_dir is None else data_dir
    if checkpoint_dir is None:
        checkpoint_dir = "./checkpoints_" + "_".join(str(int(v)) for v in vth)
    # patience defaults to epochs, i.e. early stopping effectively off. The val
    # curve plateaus for 3-6 epochs at a time before dropping again (a no-ASIC
    # run sat at 0.3887-0.3900 for seven epochs, then fell to 0.3671), so even
    # patience=5 can cut a run short one epoch before it would have improved. At
    # asic_every=1 an epoch is ~1 h of chip time on a run that cannot be
    # repeated overnight, and every epoch is checkpointed anyway -- so it costs
    # nothing to let them all run and pick the winner afterwards.
    # best_weights is still restored at the end.
    patience = epochs if patience is None else patience

    print(f"Data      {data_dir}")
    print(f"Init      {init_model}")
    print(f"Chip      vth={tuple(vth)} e-  pg_hlev={pg_hlev} V  "
          f"asic_training={asic_training} alpha={alpha} asic_every={asic_every}")
    print(f"Out       {out_model}  (checkpoints -> {checkpoint_dir})")

    # create model
    model_shape = 16 # y-profile ... why is this 16 and not 8?
    nb_classes = 3 # positive low pt, negative low pt, high pt
    first_dense = 58 # shape of first dense layer

    mtype = "qkeras"

    # keras
    if mtype == "keras":
        # initiate model
        model = CreateModel(model_shape, nb_classes, first_dense)
        model.summary()
        # load the model
        model_file = "/fasic_home/gdg/research/projects/CMS_PIX_28/directional-pixel-detectors/multiclassifier/models/ds8l6_padded_noscaling_keras_d58model.h5"
        model = tf.keras.models.load_model(model_file)

    # qkeras
    if mtype == "qkeras":
        # initiate model
        # model = CreateQModel(model_shape, nb_classes)
        # model.summary()
        # load the model
        # model_file = "/fasic_home/gdg/research/projects/CMS_PIX_28/directional-pixel-detectors/multiclassifier/models/ds8l6_padded_noscaling_qkeras_foldbatchnorm_d58w4a8model.h5"
        model_file = init_model
        co = {}
        utils._add_supported_quantized_objects(co)
        # compile=False: the saved training config uses a Keras-2-era loss
        # serialization Keras 3 can't deserialize; recompile manually instead.
        model = tf.keras.models.load_model(model_file, custom_objects=co, compile=False)
        # run_eagerly: qkeras quantizers call .numpy() internally, which raises
        # under tf.function graph tracing (as used by evaluate/predict/fit).
        model.compile(
            optimizer=tf.keras.optimizers.Adam(),
            loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
            run_eagerly=True)
        # The .h5 was built with whatever quantizer it was trained under; rebind
        # the output bias to OUTPUT_BIAS_FXP (no-op while that stays at the
        # chip's current 4b/0i format).
        retargetOutputBias(model)
        # We are fine-tuning a model converged on a *different* dataset, so the
        # batchnorm moving stats must not adapt to this one -- see
        # freezeBatchnormStats() for what that costs when they do.
        if FREEZE_BATCHNORM_STATS:
            freezeBatchnormStats(model)
        # write the weights the chip is programmed with, then convert to chip format
        output_dir = "newModelWeights"
        prepareWeights(writeWeights(model, os.path.join(output_dir, "firmware/weights/")))

    # load example inputs and outputs
    x_test, y_test = loadDataset(data_dir)
    print(x_test.shape, y_test.shape)

    # decide if train
    train_and_save = True # <<< PAY ATTENTION <<<
    model_file = out_model if train_and_save == True else model_file
    history = None
    if train_and_save:
        
        # 1e-4. An earlier note here claimed 1e-3 "destroys it within a few
        # steps" and pinned this at 1e-5, but that was the batchnorm moving-stat
        # drift being blamed on the learning rate (see freezeBatchnormStats).
        # With the stats frozen, a no-ASIC sweep from this checkpoint gives val
        # loss after 12 epochs: 1e-5 -> 0.390, 3e-5 -> 0.354, 1e-4 -> 0.305,
        # 3e-4 -> 0.300, 1e-3 -> 0.301. Everything bottoms out near 0.300, so
        # the choice is only how many epochs it takes to get there.
        #
        # 1e-4 rather than the faster 3e-4/1e-3 because this is the ASIC-in-the-
        # loop flow: at 3e-4 and above the plain-CE optimization is essentially
        # finished within one or two epochs, leaving the chip term acting on an
        # already-converged model with negligible gradients. 1e-4 reaches the
        # same floor while giving the chip ~12 epochs of influence.
        optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        # loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        train_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()
        val_acc_metric = tf.keras.metrics.SparseCategoricalAccuracy()

        # Initialize pipeline
        # asic_every=1 queries the chip on every batch (reprogram + hardware run
        # each time); raise it to trade ASIC signal for wall-clock. It is the only
        # knob that moves the chip cost: a chip epoch evaluates
        # len(train) / asic_every vectors regardless of batch_size, so at ~23 ms
        # per vector and 135685 training rows, asic_every=10 is ~315 s/epoch and
        # batch_size does not enter into it.
        #
        # asic_warmup_epochs=0, not 1: the warmup epoch existed to give a
        # pre-chip baseline to compare against, and train() now measures that
        # baseline directly before the loop. Spending an epoch at alpha=0 only
        # lets the plain-CE optimization consume the part of the run where the
        # gradients are still large enough for the chip term to matter.
        pipeline = ModelPipeline(model, optimizer, train_acc_metric, val_acc_metric,
                                 batch_size=batch_size, asic_training=asic_training,
                                 alpha=alpha, asic_every=asic_every,
                                 asic_warmup_epochs=asic_warmup_epochs,
                                 vth=vth, pg_hlev=pg_hlev, timestamp=timestamp)
        pipeline.split_data(x_test, y_test)
        pipeline.train(epochs=epochs, patience=patience,
                       checkpoint_dir=checkpoint_dir)

        # save model
        model.save(model_file)
        print('Save:', model_file)

        # load model
        co = {}
        utils._add_supported_quantized_objects(co)
        model = tf.keras.models.load_model(model_file, custom_objects=co, compile=False)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(),
            loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
            run_eagerly=True)

    # get loss, accuracy
    loss, accuracy = model.evaluate(x_test, y_test)
    print(f"Test loss: {loss}")
    print(f"Test accuracy: {accuracy}")

    # # make predictions
    # predictions = model.predict(x_test)
    # predictions = np.argmax(predictions, axis=1)
    # # print some to screen
    # for x, y, p in zip(x_test, y_test, predictions):
    #    print("x, y, prediction: ", x, y, p)

if __name__ == "__main__":
    DNNTraining()
