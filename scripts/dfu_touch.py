#!/usr/bin/env python3
"""Detect a short-lived Pro Micro USB CDC port and request nice!nano DFU.

Tested on macOS with application VID:PID 239A:8029 and bootloader 239A:00B3.
This intentionally mirrors the tested recovery script, without flashing memory.
"""
import time
import serial
from serial.tools import list_ports

VID = 0x239A
PID = 0x8029

print("Waiting for Pro Micro...", flush=True)
previous = None

while True:
    ports = list(list_ports.comports())
    target = next(
        (p for p in ports if p.vid == VID and p.pid == PID),
        None
    )

    if target and previous != target.device:
        print("Found:", target.device, flush=True)

        try:
            with serial.Serial(
                target.device,
                1200,
                timeout=0.1,
                dsrdtr=False,
                rtscts=False
            ) as ser:
                ser.dtr = False
                print("1200 baud touch sent", flush=True)

            print("Watching USB for 8 seconds...", flush=True)

            end = time.monotonic() + 8
            last = None

            while time.monotonic() < end:
                current = tuple(sorted(
                    (p.device, p.vid, p.pid)
                    for p in list_ports.comports()
                    if p.vid == VID
                ))

                if current != last:
                    print("USB:", current, flush=True)
                    last = current

                time.sleep(0.1)

        except (serial.SerialException, OSError) as e:
            print("Error:", e, flush=True)

        previous = target.device

    elif not target:
        previous = None

    time.sleep(0.05)
