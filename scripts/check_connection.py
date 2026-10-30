"""Test 1: connect to the ChipWhisperer-Husky and print its firmware version and settings."""

from husky_common import connect_scope, disconnect, fail


def main():
    """Connect to the Husky, then print its firmware version and current settings.
    Exits with status 1 if the Husky cannot be reached or its FPGA fails to load."""
    scope = None
    try:
        # Finds the Husky over USB, loads its FPGA bitstream and applies default settings.
        scope = connect_scope()

        # ChipWhisperer v6.1.0 expects Husky firmware 1.5.0.
        print(f"Husky firmware: {scope.fw_version_str}")

        # Dumps clock, ADC, trigger and I/O settings. A full dump confirms two-way communication.
        print(scope)
        print("PASS: Husky connected")
    except Exception as error:
        fail(f"cannot connect to the Husky: {error}")
    finally:
        disconnect(scope)


if __name__ == "__main__":
    main()
