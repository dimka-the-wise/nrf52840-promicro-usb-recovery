# Hardware validation / Результаты испытания

**Test date / Дата:** 2026-11-19  
**Tested board / Плата:** Pro Micro nRF52840 + SX1262  
**Environment / Среда:** macOS, Arduino IDE 1.8.13, Adafruit nRF52 core 1.7.0

| Check / Проверка | Result / Результат |
|---|---|
| USB CDC port appears for ~3 seconds / Кратковременное появление USB CDC | PASS |
| Application USB VID:PID `239A:8029` | Observed |
| 1200-baud touch triggers re-enumeration / Переключение USB | PASS |
| Bootloader USB VID:PID `239A:00B3` | Observed |
| `adafruit-nrfutil` transfers an application-only DFU ZIP | PASS |
| `Device programmed.` after approximately 3.90 seconds | PASS |
| Diagnostic program prints USB Serial uptime every second | PASS |
| A subsequent user firmware image uploads successfully / Повторная загрузка пользовательской прошивки | PASS |

The test firmware contained **52,788 application bytes**, mapped in the Arduino-generated Intel HEX file to **`0x00026000–0x00032E33`**. The selected linker script used the application region `0x26000–0xECFFF`. The DFU package specified `--dev-type 0x0052` and `--sd-req 0x00B6` (S140 v6.1.1). DFU transfer success is evidence that the bootloader accepted the package; a separate independent readback of the SoftDevice version was not performed.

The board printed at least 77 seconds of uptime following the diagnostic upload, and later accepted a working user firmware upload. No dedicated LoRa/BLE/peripheral qualification tests were performed as part of this recovery record.

**Not a universal guarantee:** other board revisions and bootloader/SoftDevice combinations can differ. The original board's unique USB serial number is deliberately excluded.
