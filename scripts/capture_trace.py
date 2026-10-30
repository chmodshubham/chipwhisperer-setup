"""Test 3: capture one AES power trace from the SAM4S target and check the ciphertext."""

import matplotlib.pyplot as plt
from Crypto.Cipher import AES

from husky_common import connect_scope, connect_target, cw, disconnect, fail, reset_target


def main():
    """Run one AES encryption on the target while the Husky records its power use.
    Checks the target's ciphertext against a reference AES, then plots the trace."""
    scope = None
    target = None
    try:
        scope = connect_scope()
        target = connect_target(scope)
        reset_target(scope)

        # Fixed key 2B7E1516...4F3C (the FIPS-197 example key) and a new random 16-byte plaintext.
        key, plaintext = cw.ktp.Basic().next()

        # Sends key and plaintext, arms the ADC, triggers the encryption and reads back trace and ciphertext.
        trace = cw.capture_trace(scope, target, plaintext, key)
        if trace is None:
            fail("no trace captured. The target did not trigger the Husky.")

        ciphertext = bytes(trace.ciphertext)
        print(f"Samples captured: {len(trace.trace)}")
        print(f"Ciphertext: {ciphertext.hex()}")

        # Reference result from pycryptodome, an independent AES library installed with ChipWhisperer.
        # AES is deterministic, so a match proves the target's tinyAES firmware encrypted correctly.
        expected = AES.new(bytes(key), AES.MODE_ECB).encrypt(bytes(plaintext))
        if ciphertext != expected:
            fail(f"wrong ciphertext. Expected {expected.hex()}.")
        print("PASS: AES result correct")
    except Exception as error:
        # No ack means the target is not running the AES firmware, usually because Test 2 was skipped or failed.
        if "ack" in str(error):
            fail(f"capture failed: {error}. Run scripts/flash_target.py, then retry.")
        fail(f"capture failed: {error}")
    finally:
        disconnect(target, scope)

    # The repeating blocks in the plot are the AES rounds.
    plt.plot(trace.trace)
    plt.title("Husky power trace: one AES-128 encryption")
    plt.xlabel("Sample")
    plt.ylabel("ADC value")
    plt.show()


if __name__ == "__main__":
    main()
