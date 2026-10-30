"""Test 2: flash the AES firmware onto the SAM4S target through the Husky."""

from husky_common import FIRMWARE_HEX, connect_scope, connect_target, cw, disconnect, fail, require_firmware


def main():
    """Erase the SAM4S flash, write the AES firmware, and verify it.
    Exits with status 1 if the firmware file is missing or programming fails."""
    require_firmware()

    scope = None
    target = None
    try:
        # default_setup() inside connect_scope() sets the serial pins the SAM4S bootloader uses.
        scope = connect_scope()
        target = connect_target(scope)

        # Erases the SAM4S, writes the .hex file and reads it back. Raises an error on any mismatch.
        cw.program_target(scope, cw.programmers.SAM4SProgrammer, str(FIRMWARE_HEX))
        print(f"PASS: flashed {FIRMWARE_HEX.name}")
    except Exception as error:
        fail(f"flashing failed: {error}")
    finally:
        disconnect(target, scope)


if __name__ == "__main__":
    main()
