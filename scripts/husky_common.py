"""Shared configuration and helpers for the ChipWhisperer-Husky test scripts."""

import os
import sys
import time
from pathlib import Path

try:
    import chipwhisperer as cw
except ImportError:
    sys.exit("FAIL: chipwhisperer is not installed in this Python. Run 'conda activate cw' first.")

# Location of the cloned ChipWhisperer repository. Defaults to chipwhisperer/ in this project,
# resolved from this file so the scripts work from any directory. Set CHIPWHISPERER_DIR to override.
PROJECT_DIR = Path(__file__).resolve().parent.parent
CHIPWHISPERER_DIR = Path(os.environ.get("CHIPWHISPERER_DIR", PROJECT_DIR / "chipwhisperer")).expanduser()

# AES firmware for the Husky kit's SAM4S target, produced by the make command in the README.
FIRMWARE_HEX = CHIPWHISPERER_DIR / "firmware/mcu/simpleserial-aes/simpleserial-aes-CWHUSKY.hex"


def fail(message):
    """Print a failure message to stderr and exit with status 1.
    All scripts report errors through this function so the output and exit code stay consistent."""
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def require_firmware():
    """Stop with a clear message if the ChipWhisperer repo or the built firmware is missing.
    Call this before connecting, so a missing file never leaves the Husky half-configured."""
    if not CHIPWHISPERER_DIR.is_dir():
        fail(f"ChipWhisperer repo not found at {CHIPWHISPERER_DIR}. Set CHIPWHISPERER_DIR to its location.")
    if not FIRMWARE_HEX.is_file():
        fail(f"firmware not found at {FIRMWARE_HEX}. Build it with the make command in the README.")


def connect_scope():
    """Connect to the first Husky found and apply NewAE's default capture settings.
    default_setup() also routes the serial pins to the target, which flashing and capturing need."""
    scope = cw.scope()
    scope.default_setup()
    return scope


def connect_target(scope):
    """Open the SimpleSerial v1 link to the target through the Husky.
    The protocol version must match SS_VER_1_1, which the firmware is built with."""
    return cw.target(scope, cw.targets.SimpleSerial)


def reset_target(scope):
    """Pulse the target's reset line so its firmware starts from a clean state.
    A target left mid-command by an earlier run otherwise ignores the next command."""
    scope.io.nrst = "low"
    time.sleep(0.05)
    scope.io.nrst = "high_z"
    time.sleep(0.05)


def disconnect(*devices):
    """Release the Husky and target connections that were opened.
    Only one process can hold the Husky, so every script calls this before exiting."""
    for device in devices:
        if device is not None:
            device.dis()
