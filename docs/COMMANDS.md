# ChipWhisperer Command Reference

Every ChipWhisperer command and setting for the Husky and a SimpleSerial target, in plain words.

> [!NOTE]
> This list was read from a connected Husky (firmware 1.5.0) running ChipWhisperer `v6.1.0`. NewAE's online docs follow newer code, so a few names there differ. See [Names that changed](#8-names-that-changed).

## Contents

1. [The usual order](#1-the-usual-order)
2. [Building target firmware](#2-building-target-firmware)
3. [Main cw commands](#3-main-cw-commands)
4. [Scope settings](#4-scope-settings)
5. [Scope commands](#5-scope-commands)
6. [Target settings and commands](#6-target-settings-and-commands)
7. [Saving traces](#7-saving-traces)
8. [Names that changed](#8-names-that-changed)
9. [References](#9-references)

## 1. The usual order

```python
import chipwhisperer as cw

# Connect to the Husky and apply standard settings
scope = cw.scope()
scope.default_setup()

# Open the serial link to the target
target = cw.target(scope, cw.targets.SimpleSerial)

# Load firmware onto the target (only after a rebuild)
cw.program_target(scope, cw.programmers.SAM4SProgrammer, "firmware.hex")

# Record the power while the target encrypts
key, text = cw.ktp.Basic().next()
trace = cw.capture_trace(scope, target, text, key)

# Release the Husky for other programs
scope.dis()
target.dis()
```

**Scope** means the Husky, the measuring device. **Target** means the chip being measured, here the SAM4S.

## 2. Building target firmware

```bash
make -C chipwhisperer/firmware/mcu/simpleserial-aes PLATFORM=CWHUSKY CRYPTO_TARGET=TINYAES128C SS_VER=SS_VER_1_1
```

| Option          | What it picks                        | Value used here                                      |
| --------------- | ------------------------------------ | ---------------------------------------------------- |
| `PLATFORM`      | The target chip                      | `CWHUSKY`: the SAM4S in the Husky kit                |
| `CRYPTO_TARGET` | The AES code built into the firmware | `TINYAES128C`: tinyAES, written in C                 |
| `SS_VER`        | SimpleSerial version                 | `SS_VER_1_1` (default). `SS_VER_2_1` for version 2.1 |

All `PLATFORM` values are in `firmware/mcu/hal/Makefile.hal`. All `CRYPTO_TARGET` values are in `firmware/mcu/crypto/Makefile.crypto`.

## 3. Main cw commands

**Connecting**

| Command                  | What it does                                                 |
| ------------------------ | ------------------------------------------------------------ |
| `cw.list_devices()`      | Lists ChipWhisperer devices on USB, without connecting       |
| `cw.scope()`             | Connects to the Husky and returns the `scope` object         |
| `cw.target(scope, type)` | Opens the link to the target and returns the `target` object |
| `cw.check_for_updates()` | Checks online whether a newer ChipWhisperer release exists   |

**Target types** for `cw.target()`:

| Type                                 | Use for                                           |
| ------------------------------------ | ------------------------------------------------- |
| `cw.targets.SimpleSerial`            | Firmware built with SimpleSerial 1.1              |
| `cw.targets.SimpleSerial2`           | Firmware built with SimpleSerial 2.1              |
| `cw.targets.SimpleSerial2_CDC`       | SimpleSerial 2.1 over a separate USB serial port  |
| `cw.targets.CW305`, `CW310`, `CW340` | NewAE's FPGA target boards (not in the Husky kit) |

**Flashing**

| Command                                            | What it does                                                                                             |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `cw.program_target(scope, programmer, "file.hex")` | Erases the target, writes the file, checks it and restarts the chip. Needs `scope.default_setup()` first |
| `cw.program_sam_firmware(...)`                     | Writes firmware to the Husky itself after it was erased. Only for Husky firmware recovery                |

| Programmer                         | Target chip                  |
| ---------------------------------- | ---------------------------- |
| `cw.programmers.SAM4SProgrammer`   | SAM4S (the Husky kit target) |
| `cw.programmers.STM32FProgrammer`  | STM32F                       |
| `cw.programmers.XMEGAProgrammer`   | XMEGA                        |
| `cw.programmers.AVRProgrammer`     | AVR                          |
| `cw.programmers.NEORV32Programmer` | NEORV32 (RISC-V)             |
| `cw.programmers.iCE40Programmer`   | iCE40 FPGA                   |

**Capturing**

| Command                                      | What it does                                                                                                        |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `cw.ktp.Basic()`                             | Key and plaintext maker: fixed key `2B7E151628AED2A6ABF7158809CF4F3C`, random plaintext                             |
| `.next()`                                    | Returns the next key and plaintext                                                                                  |
| `cw.capture_trace(scope, target, text, key)` | Sends key and plaintext, records the power during encryption, returns a trace. `None` if the target never triggered |
| `cw.plot(data)`                              | Quick interactive plot in a notebook                                                                                |

What a trace holds:

| Field              | Contents                         |
| ------------------ | -------------------------------- |
| `trace.trace`      | Power samples, one number each   |
| `trace.plaintext`  | Plaintext sent                   |
| `trace.ciphertext` | Encrypted result from the target |
| `trace.key`        | Key used                         |

## 4. Scope settings

Read a setting with `print(scope.adc.samples)`. Change it with `scope.adc.samples = 3000`. `print(scope)` shows all of them at once.

Values marked "default" are what `scope.default_setup()` sets.

### Identity

| Setting                | What it shows                                |
| ---------------------- | -------------------------------------------- |
| `scope.sn`             | Serial number of this Husky                  |
| `scope.fw_version`     | Husky firmware version as numbers            |
| `scope.fw_version_str` | Husky firmware version as text, e.g. `1.5.0` |
| `scope.fpga_buildtime` | When the Husky's FPGA design was built       |

### scope.gain: signal strength

| Setting           | What it controls                                 | Values                    |
| ----------------- | ------------------------------------------------ | ------------------------- |
| `scope.gain.db`   | How much the power signal is amplified           | -6.5 to 56 dB. Default 25 |
| `scope.gain.mode` | Amplifier range. Updates itself when `db` is set | `"low"`, `"high"`         |
| `scope.gain.gain` | Raw amplifier number behind `db`                 | Number                    |

Too little gain gives a flat, noisy trace. Too much clips the peaks.

### scope.adc: recording

| Setting                              | What it controls                                                                              | Values                                                         |
| ------------------------------------ | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `scope.adc.samples`                  | Samples recorded per trace                                                                    | Number. Default 5000                                           |
| `scope.adc.offset`                   | Samples to skip after the trigger before recording                                            | Number. Default 0                                              |
| `scope.adc.presamples`               | Samples to keep from just before the trigger                                                  | Number. Default 0                                              |
| `scope.adc.basic_mode`               | What counts as a trigger                                                                      | `"rising_edge"` (default), `"falling_edge"`, `"high"`, `"low"` |
| `scope.adc.timeout`                  | Seconds to wait for a trigger before giving up                                                | Number. Default 2                                              |
| `scope.adc.decimate`                 | Keeps only every Nth sample, for longer recordings                                            | Number. 1 keeps all                                            |
| `scope.adc.trig_count`               | How many samples the trigger stayed on in the last capture. Shows how long the operation took | Read only                                                      |
| `scope.adc.state`                    | Whether the trigger pin is on right now                                                       | Read only                                                      |
| `scope.adc.bits_per_sample`          | Detail per sample                                                                             | `12` (default) or `8`                                          |
| `scope.adc.stream_mode`              | Sends samples to the computer while recording, for very long traces                           | `True`, `False`                                                |
| `scope.adc.test_mode`                | Records a test pattern instead of real data                                                   | `True`, `False`                                                |
| `scope.adc.segments`                 | Number of short recordings packed into one capture                                            | Number. Default 1                                              |
| `scope.adc.segment_cycles`           | Clock cycles between those recordings                                                         | Number                                                         |
| `scope.adc.segment_cycle_counter_en` | Starts segments by cycle count instead of by trigger                                          | `True`, `False`                                                |
| `scope.adc.clip_errors_disabled`     | Stops the warning when the signal is too strong                                               | `True`, `False`                                                |
| `scope.adc.lo_gain_errors_disabled`  | Stops the warning when the signal is too weak                                                 | `True`, `False`                                                |
| `scope.adc.errors`                   | Recording errors from the last capture                                                        | Read only                                                      |

### scope.clock: timing

| Setting                              | What it controls                                  | Values                                                    |
| ------------------------------------ | ------------------------------------------------- | --------------------------------------------------------- |
| `scope.clock.clkgen_freq`            | Clock speed sent to the target                    | Hz. Default 7.37 MHz                                      |
| `scope.clock.clkgen_src`             | Where that clock comes from                       | `"system"` (Husky, default), `"extclk"` (from the target) |
| `scope.clock.clkgen_locked`          | Whether the clock is stable                       | Read only                                                 |
| `scope.clock.adc_mul`                | Samples per target clock cycle                    | Number. Default 4                                         |
| `scope.clock.adc_freq`               | Sampling speed (`clkgen_freq` × `adc_mul`)        | Read only                                                 |
| `scope.clock.adc_rate`               | Actual sampling speed in samples per second       | Read only                                                 |
| `scope.clock.adc_phase`              | Shifts sampling slightly against the target clock | Percent of one sample period                              |
| `scope.clock.freq_ctr`               | Measured frequency of the selected input          | Read only                                                 |
| `scope.clock.freq_ctr_src`           | What `freq_ctr` measures                          | `"clkgen"`, `"extclk"`                                    |
| `scope.clock.extclk_monitor_enabled` | Warns when an external clock changes speed        | `True`, `False`                                           |
| `scope.clock.extclk_tolerance`       | How big a change counts                           | Hz                                                        |
| `scope.clock.extclk_error`           | Whether that warning fired                        | Read only                                                 |

Because `adc_mul` ties sampling to the target clock, every trace lines up with the target's instructions.

### scope.trigger: when recording starts

| Setting                           | What it controls                         | Values                                                          |
| --------------------------------- | ---------------------------------------- | --------------------------------------------------------------- |
| `scope.trigger.triggers`          | Which pin starts a capture               | `"tio4"` (default). Pins can be combined, e.g. `"tio3 OR tio4"` |
| `scope.trigger.module`            | Kind of trigger                          | See below                                                       |
| `scope.trigger.sequencer_enabled` | Chains two triggers, one after the other | `True`, `False`                                                 |

| `module` value   | Starts recording when                                      |
| ---------------- | ---------------------------------------------------------- |
| `"basic"`        | The trigger pin changes (default)                          |
| `"ADC"`          | The power signal crosses a level                           |
| `"SAD"`          | The power signal matches a saved pattern (see `scope.SAD`) |
| `"UART"`         | Certain serial data passes by                              |
| `"edge_counter"` | The pin has changed a set number of times                  |
| `"trace"`        | A debug-trace event happens (see `scope.trace`)            |

### scope.io: target pins

| Setting                    | What it controls                                       | Values                                                                                                                                                                         |
| -------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `scope.io.target_pwr`      | Target power                                           | `True` (on), `False` (off)                                                                                                                                                     |
| `scope.io.tio1` to `tio4`  | Job of each general pin                                | `"serial_rx"`, `"serial_tx"`, `"high_z"` (listen only), `"gpio_low"`, `"gpio_high"`, `"gpio_disabled"`. Defaults: `tio1` serial_rx, `tio2` serial_tx, `tio3` and `tio4` high_z |
| `scope.io.tio_states`      | Current on/off level of `tio1` to `tio4`               | Read only, e.g. `(1, 1, 1, 0)`                                                                                                                                                 |
| `scope.io.nrst`            | Target reset pin. `"low"` holds the chip in reset      | `"low"`, `"high"`, `"high_z"`                                                                                                                                                  |
| `scope.io.pdic`            | Control pin. On the SAM4S it erases the chip           | `"low"`, `"high"`, `"high_z"`                                                                                                                                                  |
| `scope.io.pdid`            | Second control pin, used for programming some chips    | `"low"`, `"high"`, `"high_z"`                                                                                                                                                  |
| `scope.io.hs2`             | What goes out on the clock pin to the target           | `"clkgen"` (default), `"glitch"`, `"disabled"`                                                                                                                                 |
| `scope.io.extclk_src`      | Where an external clock comes in                       | Read only: `"hs1"`                                                                                                                                                             |
| `scope.io.glitch_hp`       | Turns on the strong voltage-glitch switch              | `True`, `False`                                                                                                                                                                |
| `scope.io.glitch_lp`       | Turns on the weak voltage-glitch switch                | `True`, `False`                                                                                                                                                                |
| `scope.io.aux_io_mcx`      | Job of the AUX MCX connector                           | `"high_z"` (input), `"hs2"` (clock out)                                                                                                                                        |
| `scope.io.glitch_trig_mcx` | Job of the Trigger/Glitch MCX connector                | `"trigger"`, `"glitch"`, `"inverted trigger"`, `"inverted glitch"`                                                                                                             |
| `scope.io.cdc_settings`    | Whether the USB serial port may change serial settings | List of 4 numbers. Default all 0                                                                                                                                               |

Resetting the target so its firmware starts fresh:

```python
import time
scope.io.nrst = "low"
time.sleep(0.05)
scope.io.nrst = "high_z"
```

### scope.glitch: fault injection

Glitching briefly disturbs the target's clock or power so it makes mistakes. It is used for fault attacks, not for power analysis.

| Setting                          | What it controls                           | Values                                                                                             |
| -------------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| `scope.glitch.enabled`           | Powers the glitch circuit on               | `True`, `False` (default)                                                                          |
| `scope.glitch.clk_src`           | Clock the glitches are timed against       | `"target"`, `"pll"`                                                                                |
| `scope.glitch.mmcm_locked`       | Whether the glitch clock is stable         | Read only                                                                                          |
| `scope.glitch.output`            | Kind of glitch                             | Clock: `"clock_xor"`, `"clock_or"`. Voltage: `"glitch_only"`, `"enable_only"`. Also `"clock_only"` |
| `scope.glitch.trigger_src`       | What fires a glitch                        | `"manual"`, `"ext_single"`, `"ext_continuous"`, `"continuous"`                                     |
| `scope.glitch.arm_timing`        | Order of arming glitch and scope           | `"after_scope"` (default), `"before_scope"`, `"no_glitch"`                                         |
| `scope.glitch.width`             | Length of one glitch pulse                 | Number                                                                                             |
| `scope.glitch.offset`            | Position of the pulse within a clock cycle | Number                                                                                             |
| `scope.glitch.ext_offset`        | Clock cycles between trigger and glitch    | Number                                                                                             |
| `scope.glitch.repeat`            | Glitch pulses per trigger                  | Number                                                                                             |
| `scope.glitch.num_glitches`      | Separate glitch events per trigger         | Number                                                                                             |
| `scope.glitch.phase_shift_steps` | Fine timing steps per clock cycle          | Read only                                                                                          |

### scope.SAD: pattern trigger

SAD (sum of absolute differences) compares the live power signal with a saved pattern and triggers when they match.

| Setting                          | What it controls                                  |
| -------------------------------- | ------------------------------------------------- |
| `scope.SAD.threshold`            | How close a match must be. Lower is stricter      |
| `scope.SAD.interval_threshold`   | How close each single sample must be              |
| `scope.SAD.trigger_sample`       | Which point of the pattern fires the trigger      |
| `scope.SAD.sad_reference_length` | Length of the saved pattern (read only)           |
| `scope.SAD.emode`                | Doubles the pattern length                        |
| `scope.SAD.multiple_triggers`    | Allows more than one trigger per capture          |
| `scope.SAD.num_triggers_seen`    | Triggers fired in the last capture                |
| `scope.SAD.always_armed`         | Lets SAD trigger even when the scope is not armed |

### scope.ADS4128: the sampling chip

| Setting                   | What it controls                                  | Values               |
| ------------------------- | ------------------------------------------------- | -------------------- |
| `scope.ADS4128.mode`      | Normal recording or a test pattern                | `"normal"` (default) |
| `scope.ADS4128.low_speed` | Low-speed mode, better below 80 million samples/s | `True`, `False`      |
| `scope.ADS4128.hi_perf`   | High-performance level                            | `0`, `1`, `2`        |

### scope.LA: logic analyzer

Records on/off signals inside the Husky, such as glitch timing, for checking setups. It shares memory with `scope.trace`, so only one can be on.

| Setting                             | What it controls                               |
| ----------------------------------- | ---------------------------------------------- |
| `scope.LA.present`                  | Whether this Husky has the feature (read only) |
| `scope.LA.enabled`                  | Turns it on                                    |
| `scope.LA.clkgen_enabled`           | Powers its sampling clock                      |
| `scope.LA.locked`                   | Whether that clock is stable (read only)       |
| `scope.LA.clk_source`               | Clock it samples with                          |
| `scope.LA.oversampling_factor`      | Samples per clock cycle                        |
| `scope.LA.sampling_clock_frequency` | Actual sampling speed (read only)              |
| `scope.LA.downsample`               | Keeps only every Nth sample                    |
| `scope.LA.trigger_source`           | What starts recording                          |
| `scope.LA.capture_group`            | Which group of signals is recorded             |
| `scope.LA.capture_depth`            | Samples recorded per signal                    |

### scope.trace: code tracing

Reads the Arm debug-trace pins of the target to see which code runs when. Needs firmware built for tracing.

| Setting                                      | What it controls                                     |
| -------------------------------------------- | ---------------------------------------------------- |
| `scope.trace.present`                        | Whether this Husky has the feature (read only)       |
| `scope.trace.enabled`                        | Turns tracing on                                     |
| `scope.trace.trace_mode`                     | `"parallel"` or `"SWO"` (single-wire) trace          |
| `scope.trace.trace_width`                    | Number of parallel trace pins                        |
| `scope.trace.trace_synced`                   | Whether trace data is arriving correctly (read only) |
| `scope.trace.errors`                         | Internal errors. Write to clear                      |
| `scope.trace.clock.fe_clock_src`             | Clock used to read trace data                        |
| `scope.trace.clock.fe_clock_alive`           | Whether that clock is running (read only)            |
| `scope.trace.clock.fe_freq`                  | Its measured frequency (read only)                   |
| `scope.trace.clock.clkgen_enabled`           | Powers the trace sampling clock                      |
| `scope.trace.clock.swo_clock_locked`         | Whether the SWO clock is stable (read only)          |
| `scope.trace.clock.swo_clock_freq`           | SWO clock frequency (read only)                      |
| `scope.trace.capture.trigger_source`         | What starts trace recording                          |
| `scope.trace.capture.use_husky_arm`          | Arms tracing together with `scope.arm()`             |
| `scope.trace.capture.mode`                   | How long trace recording lasts                       |
| `scope.trace.capture.count`                  | Recording length when not tied to the trigger        |
| `scope.trace.capture.raw`                    | Keeps raw trace data or only pattern matches         |
| `scope.trace.capture.rules`                  | Patterns to look for                                 |
| `scope.trace.capture.rules_enabled`          | Which patterns are active                            |
| `scope.trace.capture.max_triggers`           | Most triggers trace events may cause                 |
| `scope.trace.capture.triggers_generated`     | Triggers caused in the last capture (read only)      |
| `scope.trace.capture.record_syncs`           | Keeps or drops trace sync frames                     |
| `scope.trace.capture.matched_pattern_data`   | Data of the last match (read only)                   |
| `scope.trace.capture.matched_pattern_counts` | Matches per pattern (read only)                      |

### scope.XADC: health

| Setting                                  | What it shows                                    |
| ---------------------------------------- | ------------------------------------------------ |
| `scope.XADC.temp`                        | FPGA temperature now                             |
| `scope.XADC.max_temp`                    | Highest temperature since power-on               |
| `scope.XADC.temp_trigger`                | Temperature at which clocks shut down (settable) |
| `scope.XADC.temp_reset`                  | Temperature at which they come back (settable)   |
| `scope.XADC.ot_temp_trigger`             | Hard over-temperature limit (read only)          |
| `scope.XADC.ot_temp_reset`               | Recovery point for that limit (read only)        |
| `scope.XADC.status`                      | `"good"` or an alarm                             |
| `scope.XADC.vccint`, `vccaux`, `vccbram` | Internal supply voltages                         |

### scope.userio: front USERIO header

| Setting                   | What it controls                                      |
| ------------------------- | ----------------------------------------------------- |
| `scope.userio.mode`       | What the header pins are used for. Default `"normal"` |
| `scope.userio.direction`  | Which data pins are outputs. One bit per pin D0 to D7 |
| `scope.userio.drive_data` | Values driven on output pins                          |
| `scope.userio.status`     | Current level of all header pins (read only)          |

### scope.LEDs and scope.errors

| Setting              | What it controls                                        |
| -------------------- | ------------------------------------------------------- |
| `scope.LEDs.setting` | What the front-panel lights show. `0` means as labelled |
| `scope.errors`       | Summary of errors from every part of the Husky          |

## 5. Scope commands

**Everyday**

| Command                  | What it does                                                      |
| ------------------------ | ----------------------------------------------------------------- |
| `scope.default_setup()`  | Applies NewAE's standard settings. Run after connecting           |
| `scope.arm()`            | Gets ready to record at the next trigger                          |
| `scope.capture()`        | Waits for the trigger and records. Returns `True` if it timed out |
| `scope.get_last_trace()` | Returns the samples just recorded                                 |
| `scope.dis()`            | Disconnects so other programs can use the Husky                   |
| `scope.con()`            | Connects again after `dis()`                                      |

The manual version of `cw.capture_trace`:

```python
scope.arm()
target.simpleserial_write("p", text)
timed_out = scope.capture()
samples = scope.get_last_trace()
```

**Segmented capture** (several short recordings at once, see `scope.adc.segments`)

| Command                            | What it does                      |
| ---------------------------------- | --------------------------------- |
| `scope.capture_segmented()`        | Records all segments              |
| `scope.get_last_trace_segmented()` | Returns them, one row per segment |

**Glitching**

| Command                     | What it does                                                                  |
| --------------------------- | ----------------------------------------------------------------------------- |
| `scope.cglitch_setup()`     | Standard settings for clock glitching                                         |
| `scope.vglitch_setup("hp")` | Standard settings for voltage glitching. `"hp"` strong, `"lp"` weak, `"both"` |
| `scope.glitch_disable()`    | Turns glitching off                                                           |

**Checks and maintenance**

| Command                               | What it does                                                    |
| ------------------------------------- | --------------------------------------------------------------- |
| `scope.get_name()`                    | Name of the connected device                                    |
| `scope.feature_list()`                | Features this Husky and firmware support                        |
| `scope.check_feature("name")`         | Whether one feature is supported                                |
| `scope.adc_test()`                    | Runs a self-test of the sampling chip                           |
| `scope.get_serial_ports()`            | Serial ports belonging to the Husky                             |
| `scope.scope_diff(a, b)`              | Shows the differences between two saved setting lists           |
| `scope.try_wait_clkgen_locked(count)` | Waits until the target clock is stable                          |
| `scope.reset_fpga()`                  | Resets the FPGA. All settings go back to power-on values        |
| `scope.reload_fpga()`                 | Loads the FPGA design again                                     |
| `scope.reset_sam3u()`                 | Restarts the Husky's own microcontroller                        |
| `scope.upgrade_firmware()`            | Updates the Husky firmware                                      |
| `scope.enable_MPSSE()`                | Turns the Husky into a JTAG/SWD debug adapter, then disconnects |

> [!WARNING]
> `scope.upgrade_firmware()` changes the Husky firmware. ChipWhisperer `v6.1.0` expects firmware 1.5.0, and a newer firmware needs a newer ChipWhisperer.

Not needed in normal use: `fpga_reg_read`, `fpga_reg_write` (raw FPGA access for developers), `getLastTrace` (old name of `get_last_trace`), `dcmTimeout`, `getCurrentScope`, `setCurrentScope`, `was_fpga_prog_on_con`, `finish_mpsse_setup`, `add_read_only`, `remove_read_only`, `enable_newattr`, `disable_newattr`, `disable_strict_newattr`.

## 6. Target settings and commands

SimpleSerial messages are one command letter plus data. The target answers with `r` plus data for results, and `z` plus a status code as an acknowledgement. `z00` means "OK".

**Sending and reading, the easy way**

| Command                                    | What it does                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------------ |
| `target.simpleserial_write("p", data)`     | Sends command `p` (encrypt) with 16 bytes of `data`                                  |
| `target.simpleserial_write("k", key)`      | Sends command `k` (set key) with a 16-byte key                                       |
| `target.simpleserial_read("r", 16)`        | Reads a 16-byte `r` reply and the `z00` after it. `None` if nothing came             |
| `target.simpleserial_read_witherrors(...)` | Same, but also returns broken replies. Useful when glitching                         |
| `target.simpleserial_wait_ack()`           | Waits for a `z` reply. `0` means OK, `None` means no reply                           |
| `target.set_key(key)`                      | Sends the key and waits for the OK. Skips sending if it is the same key as last time |
| `target.get_simpleserial_commands()`       | Asks the firmware which commands it supports (SimpleSerial 2 firmware)               |

> [!IMPORTANT]
> Each reply can be read only once. `simpleserial_read()` already reads the `z00`, so a `simpleserial_wait_ack()` right after it finds nothing and prints `Target did not ack`.

**Sending and reading, the manual way**

| Command                              | What it does                                                  |
| ------------------------------------ | ------------------------------------------------------------- |
| `target.write("p" + "00"*16 + "\n")` | Sends text exactly as written. Data as hex text, `\n` ends it |
| `target.read()`                      | Returns everything received so far, as text                   |
| `target.in_waiting()`                | Number of characters waiting to be read                       |
| `target.in_waiting_tx()`             | Number of characters still waiting to be sent                 |
| `target.flush()`                     | Throws away anything waiting                                  |

**Settings**

| Setting                                                                        | What it controls                                                   |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `target.baud`                                                                  | Serial speed. 38400 for the SAM4S firmware                         |
| `target.output_len`                                                            | Length of the reply expected from encryption, in bytes. Default 16 |
| `target.protver`                                                               | SimpleSerial version in use                                        |
| `target.simpleserial_last_sent`                                                | Last message sent (read only)                                      |
| `target.simpleserial_last_read`                                                | Last message received (read only)                                  |
| `target.parity`, `target.stop_bits`, `target.xonxoff`, `target.currently_xoff` | Low-level serial line settings. Leave as they are                  |

**Connection**

| Command             | What it does    |
| ------------------- | --------------- |
| `target.dis()`      | Disconnects     |
| `target.con(scope)` | Connects again  |
| `target.close()`    | Closes the link |

Not needed in normal use: `go`, `loadEncryptionKey`, `loadInput`, `readOutput`, `isDone`, `is_done`, `checkEncryptionKey`, `checkPlaintext`, `getExpected`, `keyLen`, `textLen`, `setModeEncrypt`, `setModeDecrypt` (older internal steps that `capture_trace` handles), plus `inWaiting` (old name of `in_waiting`), `init`, `reinit`, `getName`, `getStatus`, `setConnection`, `setSomething`, `validateSettings`, `add_read_only`, `remove_read_only`, `enable_newattr`, `disable_newattr`, `disable_strict_newattr`.

## 7. Saving traces

| Command                                            | What it does                                           |
| -------------------------------------------------- | ------------------------------------------------------ |
| `proj = cw.Project("my_traces")`                   | Creates a project: a folder on disk that stores traces |
| `proj.append(trace)`                               | Adds one trace from `capture_trace`                    |
| `proj.traces`                                      | All stored power samples                               |
| `proj.plaintexts`, `proj.ciphertexts`, `proj.keys` | The matching plaintexts, results and keys              |
| `proj.save("my_traces.zip")`                       | Saves everything as one zip file                       |
| `cw.open_project("my_traces")`                     | Opens a saved project, folder or `.zip`                |

## 8. Names that changed

Some NewAE notebooks, including those on the `main` branch of chipwhisperer-jupyter, use older names. In `v6.1.0` they fail with `AttributeError`.

| Old name                    | Name in `v6.1.0`     |
| --------------------------- | -------------------- |
| `cw.create_project(...)`    | `cw.Project(...)`    |
| `proj.traces.append(trace)` | `proj.append(trace)` |
| `trace.wave`                | `trace.trace`        |
| `trace.textin`              | `trace.plaintext`    |
| `trace.textout`             | `trace.ciphertext`   |
| `proj.waves`                | `proj.traces`        |
| `proj.textins`              | `proj.plaintexts`    |

## 9. References

NewAE's [Scope API page](https://chipwhisperer.readthedocs.io/en/latest/scope-api.html) explains each scope setting in depth. The [Target API page](https://chipwhisperer.readthedocs.io/en/latest/target-api.html) covers targets, SimpleSerial commands and programmers. The [Capture API page](https://chipwhisperer.readthedocs.io/en/latest/capture-api.html) covers `capture_trace()`, key/text makers and projects. The [SimpleSerial page](https://chipwhisperer.readthedocs.io/en/latest/simpleserial.html) explains the message format and versions 1.1 and 2.1. The [Husky hardware page](https://chipwhisperer.readthedocs.io/en/latest/Capture/ChipWhisperer-Husky.html) shows every port and pin.

Inside Python, `help(scope.adc)` or `help(target.simpleserial_read)` prints the full built-in description of any setting or command.
