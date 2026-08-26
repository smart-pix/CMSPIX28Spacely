import csv
import os
import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


N_PIXEL_BITS = 512
N_MODEL_BITS = 5164
N_HIDDEN_BITS = 24
N_CHAIN_BITS = N_MODEL_BITS + N_HIDDEN_BITS  # 5188


@dataclass
class VerificationResult:
    name: str
    passed: bool
    expected_length: int
    actual_length: int
    mismatch_count: int
    mismatches: List[Tuple[int, int, int]]


def normalize_word32(value) -> str:
    """
    Convert an integer or binary string to a 32-character binary string
    displayed MSB first.
    """
    if isinstance(value, int):
        return f"{value & 0xFFFFFFFF:032b}"

    text = str(value).strip().replace("_", "")

    if text.startswith("0b"):
        text = text[2:]

    if text.startswith("0x"):
        return f"{int(text, 16):032b}"

    if not re.fullmatch(r"[01]+", text):
        raise ValueError(f"Invalid 32-bit binary word: {value!r}")

    if len(text) > 32:
        raise ValueError(
            f"Binary word contains {len(text)} bits; expected at most 32: {value!r}"
        )

    return text.zfill(32)


def normalize_bits(values: Iterable) -> List[int]:
    """
    Flatten common list/string representations into a list containing
    integer zeros and ones.
    """
    bits = []

    def add_value(value):
        if isinstance(value, (list, tuple)):
            for element in value:
                add_value(element)
            return

        if isinstance(value, int):
            if value not in (0, 1):
                raise ValueError(f"Expected a bit, got integer {value}")
            bits.append(value)
            return

        text = str(value).strip()

        if not text:
            return

        # A string may contain comma-separated bits, whitespace, brackets, etc.
        tokens = re.findall(r"(?<![0-9])[01](?![0-9])", text)

        if tokens:
            bits.extend(int(token) for token in tokens)
            return

        raise ValueError(f"Could not interpret value as binary data: {value!r}")

    add_value(values)
    return bits


def read_binary_csv(filename: str) -> List[int]:
    """
    Read all isolated zero and one values from a CSV file.
    """
    bits = []

    with open(filename, "r", newline="") as file:
        reader = csv.reader(file)

        for row_number, row in enumerate(reader, start=1):
            for column_number, value in enumerate(row, start=1):
                value = value.strip()

                if value == "":
                    continue

                if value in ("0", "1"):
                    bits.append(int(value))
                else:
                    # Allow a cell containing a long comma/space-separated
                    # binary sequence.
                    tokens = re.findall(r"(?<![0-9])[01](?![0-9])", value)

                    if tokens:
                        bits.extend(int(token) for token in tokens)
                    else:
                        raise ValueError(
                            f"Nonbinary value in {filename}, "
                            f"row {row_number}, column {column_number}: {value!r}"
                        )

    return bits


def save_combined_arrays(
    filename: str,
    arrays: Sequence[Tuple[str, Sequence[Sequence[str]]]],
) -> None:
    """
    Save several firmware arrays in one CSV.

    Output columns:
        array, address_hex, address_decimal, word_hex, word_binary
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "array",
                "address_hex",
                "address_decimal",
                "word_hex",
                "word_binary",
            ]
        )

        for array_name, words in arrays:
            for address, word in words:
                address_int = int(str(address), 16)
                word_binary = normalize_word32(word)
                word_hex = f"{int(word_binary, 2):08X}"

                writer.writerow(
                    [
                        array_name,
                        f"0x{address_int:02X}",
                        address_int,
                        f"0x{word_hex}",
                        word_binary,
                    ]
                )


def arrays_to_serial_bits(
    arrays: Sequence[Tuple[str, Sequence[Sequence[str]]]],
    reverse_each_word: bool = True,
) -> List[int]:
    """
    Reconstruct the serial chronological bitstream.

    int_to_32bit() displays bit 31 first. Based on the previous data,
    the firmware memory stores serial samples with the earliest sample
    in bit 0. Therefore each displayed 32-bit word must be reversed.
    """
    serial_bits = []

    for _, words in arrays:
        ordered_words = sorted(
            words,
            key=lambda entry: int(str(entry[0]), 16),
        )

        for _, word in ordered_words:
            word_binary = normalize_word32(word)

            if reverse_each_word:
                word_binary = word_binary[::-1]

            serial_bits.extend(int(bit) for bit in word_binary)

    return serial_bits


def compare_bits(
    name: str,
    expected: Sequence[int],
    actual: Sequence[int],
    maximum_reported_mismatches: int = 50,
) -> VerificationResult:
    comparison_length = min(len(expected), len(actual))

    all_mismatches = [
        (position, int(expected[position]), int(actual[position]))
        for position in range(comparison_length)
        if int(expected[position]) != int(actual[position])
    ]

    length_difference = abs(len(expected) - len(actual))
    mismatch_count = len(all_mismatches) + length_difference

    return VerificationResult(
        name=name,
        passed=(mismatch_count == 0),
        expected_length=len(expected),
        actual_length=len(actual),
        mismatch_count=mismatch_count,
        mismatches=all_mismatches[:maximum_reported_mismatches],
    )


def print_verification_result(result: VerificationResult) -> None:
    status = "PASS" if result.passed else "FAIL"

    print()
    print("=" * 72)
    print(f"{result.name}: {status}")
    print(f"Expected bits:   {result.expected_length}")
    print(f"Actual bits:     {result.actual_length}")
    print(f"Mismatch count:  {result.mismatch_count}")

    if result.mismatches:
        print()
        print("First mismatches:")
        print(" position   expected   actual")

        for position, expected, actual in result.mismatches:
            print(f" {position:8d}      {expected}         {actual}")

    if result.expected_length != result.actual_length:
        print()
        print(
            "Length mismatch: the comparison includes "
            f"{abs(result.expected_length - result.actual_length)} "
            "missing or extra bits."
        )


def build_programmed_model_bits(
    model_path: str,
    pixel_config,
) -> List[int]:
    """
    Construct the expected 5164-bit normal configuration image.

    Assumption:
        The model CSV contains the full 5164-bit configuration image,
        and dnnConfig() replaces its first 512 entries with pixelConfig.

    This is consistent with the previous test, where all differences
    relative to the model CSV were confined to the pixel field.
    """
    model_bits = read_binary_csv(model_path)
    pixel_bits = normalize_bits(pixel_config)

    if len(model_bits) != N_MODEL_BITS:
        raise ValueError(
            f"{model_path} contains {len(model_bits)} bits; "
            f"expected exactly {N_MODEL_BITS}."
        )

    if len(pixel_bits) != N_PIXEL_BITS:
        raise ValueError(
            f"pixelConfig contains {len(pixel_bits)} bits; "
            f"expected exactly {N_PIXEL_BITS}."
        )

    programmed_bits = model_bits.copy()
    programmed_bits[0:N_PIXEL_BITS] = pixel_bits

    return programmed_bits


def verify_shift_register_debug_capture(
    model_path: str,
    hidden_bit_path: str,
    pixel_config,
    words_A0,
    words_A1,
    words_A2,
    words_DA0,
    words_DA1,
    maximum_reported_mismatches: int = 50,
) -> bool:
    """
    Verify both firmware staging memory and serial readback.

    Expected CFG memory:
        programmed chain twice:
            [5164 programmed bits + 24 hidden bits] x 2
        followed by unused zero padding.

    Expected DATA memory:
        first chain output:
            5164 reset zeros + the hidden-bit state
        second chain output:
            5164 programmed bits + hidden bits
        followed by unused zero padding.

    Returns True only when every tested bit and its position match.
    """
    programmed_bits = build_programmed_model_bits(
        model_path=model_path,
        pixel_config=pixel_config,
    )

    hidden_bits = read_binary_csv(hidden_bit_path)

    if len(hidden_bits) != N_HIDDEN_BITS:
        raise ValueError(
            f"{hidden_bit_path} contains {len(hidden_bits)} hidden bits; "
            f"expected exactly {N_HIDDEN_BITS}."
        )

    expected_chain = programmed_bits + hidden_bits

    if len(expected_chain) != N_CHAIN_BITS:
        raise RuntimeError(
            f"Internal error: expected chain has {len(expected_chain)} bits, "
            f"not {N_CHAIN_BITS}."
        )

    cfg_actual = arrays_to_serial_bits(
        [
            ("CFG_ARRAY_0", words_A0),
            ("CFG_ARRAY_1", words_A1),
            ("CFG_ARRAY_2", words_A2),
        ]
    )

    data_actual = arrays_to_serial_bits(
        [
            ("DATA_ARRAY_0", words_DA0),
            ("DATA_ARRAY_1", words_DA1),
        ]
    )

    # The three CFG arrays hold 3 * 4096 = 12288 bits.
    expected_cfg_useful = expected_chain + expected_chain

    if len(cfg_actual) < len(expected_cfg_useful):
        raise ValueError(
            f"CFG arrays contain only {len(cfg_actual)} bits, but "
            f"{len(expected_cfg_useful)} bits are required for two chains."
        )

    # Unused staging-memory locations are expected to remain zero.
    expected_cfg = (
        expected_cfg_useful
        + [0] * (len(cfg_actual) - len(expected_cfg_useful))
    )

    # During the first load, configOut returns the old shift-register state.
    # Normal configuration flops were reset. The hidden bits use the hidden
    # debug image, as observed in the previous capture.
    previous_chain_state = [0] * N_MODEL_BITS + hidden_bits

    expected_data_useful = previous_chain_state + expected_chain

    if len(data_actual) < len(expected_data_useful):
        raise ValueError(
            f"DATA arrays contain only {len(data_actual)} bits, but "
            f"{len(expected_data_useful)} bits are required."
        )

    expected_data = (
        expected_data_useful
        + [0] * (len(data_actual) - len(expected_data_useful))
    )

    cfg_result = compare_bits(
        name="CFG arrays versus expected programming stream",
        expected=expected_cfg,
        actual=cfg_actual,
        maximum_reported_mismatches=maximum_reported_mismatches,
    )

    data_result = compare_bits(
        name="DATA arrays versus expected serial readback",
        expected=expected_data,
        actual=data_actual,
        maximum_reported_mismatches=maximum_reported_mismatches,
    )

    # Additional direct checks make failures easier to interpret.
    cfg_copy_0 = cfg_actual[0:N_CHAIN_BITS]
    cfg_copy_1 = cfg_actual[N_CHAIN_BITS:2 * N_CHAIN_BITS]

    first_copy_result = compare_bits(
        name="CFG first programmed copy",
        expected=expected_chain,
        actual=cfg_copy_0,
        maximum_reported_mismatches=maximum_reported_mismatches,
    )

    second_copy_result = compare_bits(
        name="CFG second programmed copy",
        expected=expected_chain,
        actual=cfg_copy_1,
        maximum_reported_mismatches=maximum_reported_mismatches,
    )

    repeated_copy_result = compare_bits(
        name="CFG copy 1 versus CFG copy 2",
        expected=cfg_copy_0,
        actual=cfg_copy_1,
        maximum_reported_mismatches=maximum_reported_mismatches,
    )

    data_readback_copy = data_actual[
        N_CHAIN_BITS:2 * N_CHAIN_BITS
    ]

    readback_result = compare_bits(
        name="Serial readback versus programmed chain",
        expected=expected_chain,
        actual=data_readback_copy,
        maximum_reported_mismatches=maximum_reported_mismatches,
    )

    results = [
        cfg_result,
        first_copy_result,
        second_copy_result,
        repeated_copy_result,
        data_result,
        readback_result,
    ]

    for result in results:
        print_verification_result(result)

    overall_pass = all(result.passed for result in results)

    print()
    print("=" * 72)
    print(
        "SHIFT-REGISTER DEBUG TEST: "
        + ("PASS" if overall_pass else "FAIL")
    )
    print("=" * 72)

    return overall_pass