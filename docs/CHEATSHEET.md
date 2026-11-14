# ChipWhisperer Cheat Sheet

The commands used most with the Husky, each with when to use it and an example. The full list is in [COMMANDS.md](COMMANDS.md).

`scope` is the Husky, the measuring device. `target` is the SAM4S chip it measures.

## Contents

1. [Start and stop](#1-start-and-stop)
2. [Flash the target](#2-flash-the-target)
3. [Talk to the target](#3-talk-to-the-target)
4. [Capture power traces](#4-capture-power-traces)
5. [Adjust the recording](#5-adjust-the-recording)
6. [Fix a stuck target](#6-fix-a-stuck-target)
7. [Save and load traces](#7-save-and-load-traces)
8. [Everything together](#8-everything-together)

## 1. Start and stop

### `cw.scope()`: connect to the Husky

The first line of every script and notebook after the import. Nothing else works without it.

```python
import chipwhisperer as cw
scope = cw.scope()
```

If it fails with `LIBUSB_ERROR_ACCESS`, another script or notebook still holds the Husky.

### `scope.default_setup()`: standard settings

Run it right after connecting. It sets the clock, serial pins, trigger, gain and sample count to values that work for the Husky kit. Without it, flashing times out and captures fail.

```python
scope.default_setup()
```

It prints each setting it changed, for example `scope.adc.samples changed from 131124 to 5000`. That output is normal.

### `cw.target(...)`: open the link to the target

Needed for anything that sends commands to the chip: flashing, capturing, or manual SimpleSerial messages.

```python
target = cw.target(scope, cw.targets.SimpleSerial)
```

Use `cw.targets.SimpleSerial2` instead only if the firmware was built with `SS_VER=SS_VER_2_1`.

### `scope.fw_version_str`: check the Husky firmware

A quick check after connecting. ChipWhisperer `v6.1.0` expects `1.5.0`.

```python
print(scope.fw_version_str)
```

```
1.5.0
```

### `scope.dis()` and `target.dis()`: release the Husky

The last lines of every script and notebook. Only one program can use the Husky at a time. Without these, the next script fails with `LIBUSB_ERROR_ACCESS`.

```python
scope.dis()
target.dis()
```

The Husky stays powered and its lights stay on. Only the program's hold on it is released. Shutting down a notebook's kernel does the same.

## 2. Flash the target

### `cw.program_target(...)`: load firmware onto the SAM4S

Used after building new firmware with `make`, or when the target stops answering. The firmware stays on the chip after power-off, so this is not needed every session.

```python
cw.program_target(scope, cw.programmers.SAM4SProgrammer, "chipwhisperer/firmware/mcu/simpleserial-aes/simpleserial-aes-CWHUSKY.hex")
```

It prints nothing when it works. On failure it raises an error such as `OSError: timeout`. The usual cause is that `scope.default_setup()` was skipped.

## 3. Talk to the target

SimpleSerial messages are one letter plus data. The target answers `r` plus data for a result, then `z00` for "OK".

### `target.simpleserial_write(...)`: send a command

Used for setting a key or encrypting by hand, as in NewAE's SimpleSerial notebook.

```python
key = bytearray([0]*16)
target.simpleserial_write("k", key)

text = bytearray([0]*16)
target.simpleserial_write("p", text)
```

`k` sets the key. `p` encrypts the plaintext. Both take exactly 16 bytes.

### `target.simpleserial_read(...)`: read the answer

Used right after sending `p`, to get the ciphertext.

```python
ciphertext = target.simpleserial_read("r", 16)
print(ciphertext.hex())
```

With an all-zero key and plaintext:

```
66e94bd4ef8a2c3b884cfa59ca342b2e
```

It also reads the `z00` that follows. `None` means nothing arrived.

### `target.simpleserial_wait_ack()`: wait for "OK"

Used after a command that returns no data, such as `k`.

```python
target.simpleserial_write("k", key)
print(target.simpleserial_wait_ack())
```

```
0
```

`0` means OK. `None` with `Target did not ack` means no answer came.

> [!IMPORTANT]
> Each answer can be read only once. After `simpleserial_read()`, the `z00` is already used up, so `simpleserial_wait_ack()` finds nothing and prints `Target did not ack`.

### `target.write()` and `target.read()`: raw messages

Used to see exactly what goes over the wire, for example when debugging.

```python
target.write("p" + "00"*16 + "\n")
print(target.read())
```

```
r66E94BD4EF8A2C3B884CFA59CA342B2E
z00
```

Data is written as hex text, two characters per byte, and `\n` ends the message.

## 4. Capture power traces

### `cw.ktp.Basic()`: make a key and plaintext

Used before each capture. The key stays the same; the plaintext is random every time.

```python
ktp = cw.ktp.Basic()
key, text = ktp.next()
print(key.hex(), text.hex())
```

```
2b7e151628aed2a6abf7158809cf4f3c 9d1c...  (plaintext changes each time)
```

Create `ktp` once and call `ktp.next()` for each new trace.

### `cw.capture_trace(...)`: record one encryption

The main command for power analysis. It sends key and plaintext, starts the encryption, records the power, and returns everything together.

```python
trace = cw.capture_trace(scope, target, text, key)
```

| Field              | Contents                               |
| ------------------ | -------------------------------------- |
| `trace.trace`      | Power samples, 5000 numbers by default |
| `trace.plaintext`  | Plaintext sent                         |
| `trace.ciphertext` | Target's answer                        |
| `trace.key`        | Key used                               |

```python
print(len(trace.trace))
print(trace.ciphertext.hex())
```

`trace` is `None` if the target never started, usually because no firmware is loaded.

### Many traces in a loop

Attacks need hundreds or thousands of traces, all with the same key and different plaintexts.

```python
traces = []
for i in range(100):
    key, text = ktp.next()
    trace = cw.capture_trace(scope, target, text, key)
    if trace is not None:
        traces.append(trace)
print(len(traces), "traces captured")
```

### `cw.plot(...)`: look at a trace

Used in notebooks to check that a trace looks right before capturing many.

```python
cw.plot(trace.trace)
```

AES shows ten similar repeating blocks, one per round. A flat line means no signal: check the SMA cable and gain.

## 5. Adjust the recording

Each setting is read with `print(...)` and changed with `=`.

### `scope.adc.samples`: how long to record

Used when the operation is longer or shorter than the default 5000 samples. More samples means a longer recording and more data.

```python
scope.adc.samples = 10000
```

### `scope.adc.offset`: skip the start

Used to record only a later part, for example only the last AES round. The number counts samples after the trigger.

```python
scope.adc.offset = 2000
```

### `scope.adc.presamples`: keep a bit before the trigger

Used to see what happens just before the operation starts.

```python
scope.adc.presamples = 100
```

### `scope.gain.db`: signal strength

Used when traces look too flat (raise it) or the peaks are cut off (lower it). Default 25.

```python
scope.gain.db = 30
```

### `scope.adc.trig_count`: how long the operation took

Read after a capture. It shows how many samples the trigger stayed on, which is the length of the encryption. Used to choose a good `scope.adc.samples`.

```python
trace = cw.capture_trace(scope, target, text, key)
print(scope.adc.trig_count)
```

## 6. Fix a stuck target

### `scope.io.nrst`: restart the chip

Used when the target stops answering (`Target did not ack`) but the firmware is fine. It holds the reset pin, then releases it.

```python
import time
scope.io.nrst = "low"
time.sleep(0.05)
scope.io.nrst = "high_z"
```

### `scope.io.target_pwr`: power-cycle the target

A stronger restart: power off, then on.

```python
scope.io.target_pwr = False
time.sleep(1)
scope.io.target_pwr = True
```

### `target.flush()`: clear old messages

Used when leftover answers from an earlier command confuse the next read.

```python
target.flush()
```

If none of these help, flash the firmware again (section 2).

## 7. Save and load traces

### `cw.Project(...)` and `proj.append(...)`: collect traces

Used to keep traces after the notebook closes, so they can be analysed later without the hardware.

```python
proj = cw.Project("my_traces")
for i in range(100):
    key, text = ktp.next()
    trace = cw.capture_trace(scope, target, text, key)
    if trace is not None:
        proj.append(trace)
```

### `proj.save(...)`: write to disk

```python
proj.save("my_traces.zip")
```

### `cw.open_project(...)`: load saved traces

Works without the Husky connected.

```python
proj = cw.open_project("my_traces.zip")
print(proj.traces.shape)
```

```
(100, 5000)
```

That means 100 traces of 5000 samples each. `proj.plaintexts`, `proj.ciphertexts` and `proj.keys` hold the matching data.

> [!NOTE]
> In `v6.1.0`, open the `.zip` file. Opening the `my_traces` folder directly fails with `AssertionError`.

## 8. Everything together

A complete script: connect, capture 100 traces, save them, disconnect.

```python
import chipwhisperer as cw

scope = cw.scope()
scope.default_setup()
target = cw.target(scope, cw.targets.SimpleSerial)

ktp = cw.ktp.Basic()
proj = cw.Project("my_traces")

try:
    for i in range(100):
        key, text = ktp.next()
        trace = cw.capture_trace(scope, target, text, key)
        if trace is not None:
            proj.append(trace)
    proj.save("my_traces.zip")
    print(len(proj.traces), "traces saved")
finally:
    scope.dis()
    target.dis()
```

`try` and `finally` make sure the Husky is released even if something fails halfway.
