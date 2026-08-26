# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains CMSPIX28 ASIC configuration and testing routines for the PySpacely platform. It consists of Python scripts that execute testing procedures and measurements on a CMS Pixel detector ASIC (CMSPIX28).

**Key Characteristics:**
- Modular architecture with configuration, routines, and subroutines separated by responsibility
- Heavy integration with the PySpacely framework (Master_Config, Spacely_Globals, Spacely_Utils)
- Test/measurement workflows include: initialization, programming, S-curve measurements, DNN-based testing, and power measurements
- Data-driven: extensive use of CSV files for configuration arrays and measurement results

## Architecture

### File Organization

- **Config File** (`CMSPIX28Spacely_Config.py`): Defines instrument connections (CaR board), voltage/current sequences, port mappings
- **Routines** (`CMSPIX28Spacely_Routines.py`): High-level workflow orchestration and setup functions
- **Subroutines** (`CMSPIX28Spacely_Subroutines_*.py`): Modular test implementations organized by category:
  - `A0`: Core ASIC operations
  - `A1-A2`: Specific test operations (Peary, Firmware)
  - `B0`: Programming operations
  - `B1`: Scan chain verification
  - `B2`: S-curve measurements
  - `B3`: DNN-based testing
  - `B4`: Settings scanning
  - `B5`: DNN model training

### Dependency Chain

All subroutines import from `Master_Config`, which provides global state, and use:
- `Spacely_Globals (sg)`: Global instrument objects and state
- `Spacely_Utils`: Helper functions and utilities

The `Master_Config` and Spacely support modules are expected to be in the parent PySpacely directory; import statements have fallback error handling.

### Data Flow

1. Configuration defines which instrument (CaR board) controls which voltage/current measurements
2. Routines initialize and orchestrate test sequences
3. Subroutines execute individual test steps and capture data
4. Results are written to CSV files in the `csv/` directory for post-processing

## Development Workflow

### Running Tests

Most workflows are driven interactively through the PySpacely shell. Test routines can be executed by:
1. Starting the PySpacely environment from parent directory
2. Calling functions defined in the routines and subroutines modules

For testing this specific config, import and call functions directly:
```python
from CMSPIX28Spacely_Routines import onstartup
onstartup()
```

### Key Dependencies (External to this Directory)

- **Master_Config.py** (parent): Global configuration, voltage/current port definitions
- **Spacely_Globals.py** (parent): Instrument instances and logging
- **Spacely_Utils.py** (parent): Common utility functions

These must be available in sys.path for imports to work correctly.

### Data Handling

- Configuration data: stored in Python dicts (INSTR, V_SEQUENCE, I_SEQUENCE, port mappings)
- Measurement results: written to CSV files in `csv/` directory
- Model weights: stored in `newModelWeights/` directory
- S-curve and DNN output data: individual CSV files with timestamps

## Common Development Tasks

### Adding a New Test Routine

1. Create a new `CMSPIX28Spacely_Subroutines_*.py` file following naming convention
2. Import required Spacely modules with error handling (see existing files for pattern)
3. Define test functions that accept configuration parameters
4. Use `sg.INSTR["car"]` for hardware communication
5. Write results to CSV files with descriptive names

### Modifying Configuration

Edit `CMSPIX28Spacely_Config.py` to:
- Change instrument host/port settings
- Add or reorder voltage/current sequences
- Update port mappings for measurements

### Working with CSV Data

- Configuration arrays go in `csv/` directory
- Read with `np.genfromtxt()` or `csv` module (see B0_Prog, B2_SCurve for examples)
- Write results with Python's csv module, preserving row/column structure for downstream analysis

## Important Notes

- This codebase depends on NI hardware drivers and should primarily run on Windows with proper hardware setup
- Fallback error handling is used for Spacely imports to allow development without full environment setup
- CSV files can become large; backup important runs before rerunning tests
- DNN model files (.h5, .tar.gz) are in `newModelWeights/`; do not delete without backup
