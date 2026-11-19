# Pro Micro nRF52840 — USB Recovery Without SWD

[Русский](README.md) · [Hardware test results](docs/TEST_RESULTS.md) · [DFU touch script](scripts/dfu_touch.py)

**Hardware tested on November 19, 2026.** A Pro Micro nRF52840 + SX1262 board that would no longer reliably enter its bootloader via double RST–GND was recovered **without an SWD programmer, mass erase, or bootloader replacement**. Both a minimal diagnostic application and a subsequent working user firmware were uploaded successfully.

> **Scope:** This procedure requires a still-functioning nice!nano-compatible Serial DFU bootloader and a USB CDC port that appears briefly. If the bootloader is erased, or the board never enumerates over USB, SWD may be required. This is a tested case study, **not** a universal recovery image for every nRF52840.

## 1. Symptoms and identification

After flashing unrelated firmware, double-reset no longer reliably entered the bootloader; the Web Flasher's Enter DFU action could not connect in time. The macOS serial port appeared for about **3 seconds**, then disappeared. No UF2 drive appeared.

The tested board used the following USB IDs:

| State | USB VID:PID | Description |
|---|---|---|
| Short-lived application USB CDC | `239A:8029` | Pro Micro nRF52840 |
| Bootloader after 1200-baud touch | `239A:00B3` | nice!nano |

The serial device path may remain unchanged across re-enumeration: **verify VID:PID**, not just the port name.

## 2. Tools on macOS

Requirements: USB data cable, Python 3, Arduino IDE, and **Adafruit nRF52 Core 1.7.0** (used for the tested firmware build). A Python virtual environment avoids the Homebrew Python `externally-managed-environment` error:

```bash
python3 -m venv "$HOME/nrf52840-venv"
source "$HOME/nrf52840-venv/bin/activate"
python -m pip install -r requirements.txt
adafruit-nrfutil --help
```

Run the above from this repository directory. Reactivate the environment in every new terminal session. Do not use `sudo pip` or `--break-system-packages` to work around package protection.

## 3. Observe the short-lived USB port

Before plugging in the board, run:

```bash
prev=""
while true; do
  ports=$(ls /dev/cu.* 2>/dev/null | grep -E 'usbmodem|usbserial' | tr '\n' ' ')
  if [ "$ports" != "$prev" ]; then
    echo "$(date '+%H:%M:%S') $ports"
    prev="$ports"
  fi
  sleep 0.1
done
```

On the tested board `/dev/cu.usbmodem14301` was detected at `22:27:23` and gone at `22:27:26`. Stop with **Ctrl+C**. `system_profiler SPUSBDataType -detailLevel full` can provide device descriptors while the board is enumerated.

## 4. Enter Serial DFU via 1200-baud touch

1. Unplug the board and close serial monitors / browser flashers so that the port is free.
2. Run the included script **before connecting** the board:

   ```bash
   python scripts/dfu_touch.py
   ```

3. Connect the board when the script prints `Waiting for Pro Micro...`.
4. Observed output:

   ```text
   Found: /dev/cu.usbmodem14301
   1200 baud touch sent
   Watching USB for 8 seconds...
   USB: ()
   USB: (('/dev/cu.usbmodem14301', 9114, 179),)
   ```

   Decimal `9114:179` corresponds to hexadecimal `239A:00B3`.

5. Stop the script with **Ctrl+C**, leaving the board connected. Verify:

   ```bash
   python -m serial.tools.list_ports -v
   ```

   The tested device reported `desc: nice!nano` and `USB VID:PID=239A:00B3`.

This script opens and closes USB CDC at 1200 baud (with a DTR change) to request DFU. **It does not erase or write Flash.** It specifically targets the tested application VID:PID `239A:8029`; identify other devices before adapting those IDs.

## 5. Install the Arduino board definition

Using **Arduino IDE 1.8.13**, add the Adafruit Boards Manager index under **Preferences → Additional Boards Manager URLs**:

```text
https://adafruit.github.io/arduino-board-index/package_adafruit_index.json
```

Install **Adafruit nRF52 by Adafruit, version 1.7.0**, then follow the instructions for the Pro Micro add-on:

<https://github.com/somik123/Adafruit_nRF52_Arduino_ProMicro>

Back up the core's `boards.txt` before adding the `promicronrf52840` board definition and `variants/pro_micro_nrf52840`. The tested core directory was:

```text
~/Library/Arduino15/packages/adafruit/hardware/nrf52/1.7.0/
```

Verify `promicronrf52840.name=Pro Micro nRF52840` and `promicronrf52840.build.variant=pro_micro_nrf52840` in `boards.txt`, plus the matching variant directory. **Quit and reopen Arduino IDE** to reload the board menu. Do not select **Burn Bootloader**.

Tested configuration: **Pro Micro nRF52840**, **SoftDevice S140 6.1.1**, **Debug Level 0 (Release)**, **Debug Port: Serial**.

## 6. Build the diagnostic application

Open [`firmware/PROMICRO-USB-RECOVERY-01/PROMICRO-USB-RECOVERY-01.ino`](firmware/PROMICRO-USB-RECOVERY-01/PROMICRO-USB-RECOVERY-01.ino) in Arduino IDE. The sketch starts USB Serial at 115200 baud and prints a one-second uptime counter. It never accesses LoRa, BLE, SPI or I²C.

Click **Verify**, then **Sketch → Export Compiled Binary** to obtain the application `.hex` file. The tested build required `#include <Adafruit_TinyUSB.h>`; omitting it produced `undefined reference to Serial` during linking.

The original test export was named `nrf_boot.ino.pro_micro_nrf52840.hex`; your generated filename may differ.

### Check the application address range

The tested linker script `nrf52840_s140_v6.ld` placed the application at `0x26000`, with the memory region ending *before* `0xED000`. Its generated Intel HEX contained data from **`0x00026000` through `0x00032E33`**, totaling **52,788 bytes**.

A correct Intel HEX parser must handle both record type **02** (*Extended Segment Address*) and type **04** (*Extended Linear Address*). A parser that only reads type 04 can incorrectly report an origin of `0x00000000`.

These addresses are only validated for the tested core/SoftDevice configuration. **Do not flash images built for an unknown or mismatched flash layout.**

## 7. Generate an application-only DFU ZIP

Activate the Python environment and substitute your actual exported HEX path. For the tested naming:

```bash
HEX="$HOME/Documents/Arduino/nrf_boot/nrf_boot.ino.pro_micro_nrf52840.hex"
ZIP="$HOME/Documents/Arduino/nrf_boot/PROMICRO-USB-RECOVERY-01.zip"

adafruit-nrfutil dfu genpkg \
  --dev-type 0x0052 \
  --sd-req 0x00B6 \
  --application "$HEX" \
  "$ZIP"

unzip -l "$ZIP"
unzip -p "$ZIP" manifest.json
```

`0x00B6` is the S140 6.1.1 SoftDevice requirement. The verified archive contained only the application `.bin` (52,788 bytes), `.dat` (14 bytes), and `manifest.json` (`dfu_version: 0.5`). There was no bootloader or SoftDevice image in the archive.

**Do not bypass a SoftDevice mismatch** by replacing `--sd-req` with a permissive value. The bootloader accepted this package and the program worked; a separate independent readback of the installed SoftDevice version was not performed.

## 8. Flash via Serial DFU

> **This step writes Flash and replaces the currently installed application.** Make sure you have the right board, port and firmware package, and back up any data you need. Do not disconnect USB while flashing.

If the board is no longer visible as `239A:00B3`, repeat step 4. With the correct paths and detected port, execute:

```bash
ZIP="$HOME/Documents/Arduino/nrf_boot/PROMICRO-USB-RECOVERY-01.zip"
PORT="/dev/cu.usbmodem14301"

adafruit-nrfutil --verbose dfu serial \
  --package "$ZIP" \
  --port "$PORT" \
  --baudrate 115200 \
  --singlebank
```

The tested run ended with:

```text
Sending DFU start packet
Sending DFU init packet
Sending firmware file
Activating new firmware
DFU upgrade took 3.8958027362823486s
Device programmed.
```

If the bootloader refuses a package or reports SoftDevice incompatibility, **stop** and check the configuration. Do not mass erase or bypass its validation as a shortcut.

## 9. Verify and troubleshoot

Open Arduino Serial Monitor at **115200 baud**. The board printed:

```text
PROMICRO-USB-RECOVERY-01 | Uptime: 75 s
PROMICRO-USB-RECOVERY-01 | Uptime: 76 s
PROMICRO-USB-RECOVERY-01 | Uptime: 77 s
```

A **working user firmware was also subsequently uploaded** to the same board without errors. USB programmability was restored; this test alone does not qualify SX1262 radio, BLE or other peripherals.

| Symptom | Suggested action |
|---|---|
| `externally-managed-environment` | Use Python `venv` |
| `adafruit-nrfutil: command not found` | Run `source ~/nrf52840-venv/bin/activate` |
| `dfu_touch.py: No such file` | Run `python scripts/dfu_touch.py` from the repository root |
| USB CDC lasts only a few seconds | Start the script *before* connecting USB |
| Pro Micro not listed in Arduino IDE | Check `boards.txt`, variant directory; quit/restart IDE |
| `undefined reference to Serial` | Include `Adafruit_TinyUSB.h` |
| No UF2 volume | USB CDC Serial DFU may still be usable; check VID:PID |
| `Device not configured` during read | USB device disconnected/re-enumerated; inspect new VID:PID |
| DFU package rejected | Validate board, SoftDevice and package; don't bypass checks |
| Never enumerates over USB | USB recovery may not apply; consider SWD |

## 10. References, limitations and license

This documents **one hardware test on macOS**, not a guarantee for every Pro Micro clone. Revisions, bootloaders, SoftDevice versions and USB identifiers may differ. No ready-made universal DFU binary is distributed.

- [Adafruit nRF52 Arduino Core](https://github.com/adafruit/Adafruit_nRF52_Arduino)
- [Adafruit nRF52 Bootloader](https://github.com/adafruit/Adafruit_nRF52_Bootloader)
- [Pro Micro nRF52 board add-on](https://github.com/somik123/Adafruit_nRF52_Arduino_ProMicro)
- [Adafruit nRF52 nrfutil](https://github.com/adafruit/Adafruit_nRF52_nrfutil)
- [nice!nano troubleshooting](https://nicekeyboards.com/docs/nice-nano/troubleshooting/)

Released under the [MIT License](LICENSE). Third-party board cores and bootloaders are not included and retain their respective licenses. Device-specific serial identifiers are omitted intentionally.
