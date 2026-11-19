# Pro Micro nRF52840 — восстановление прошивки через USB

[English](README_EN.md) · [Результаты аппаратного испытания](docs/TEST_RESULTS.md) · [Скрипт входа в DFU](scripts/dfu_touch.py)

**Проверено на реальной плате 19 ноября 2026 года.** Удалось восстановить программирование Pro Micro nRF52840 + SX1262 без SWD, J-Link, массового стирания Flash и замены загрузчика. После установки тестовой программы успешно загрузилась и рабочая пользовательская прошивка.

> **Область применения.** Метод подходит для случая, когда установленный nice!nano-совместимый загрузчик ещё исправен, а приложение кратковременно предоставляет USB CDC-порт. Если порт вообще не появляется или загрузчик повреждён, может потребоваться SWD. Ниже — **отчёт о проверенной конфигурации**, а не универсальная прошивка для всех nRF52840.

## 1. Симптомы

После установки сторонней прошивки плата перестала входить в загрузчик при двойном замыкании RST–GND. Web Flasher не успевал выполнить **Enter DFU Mode**. При подключении к Mac появлялся `/dev/cu.usbmodem14301` примерно на три секунды и исчезал; UF2-диск не монтировался. Сама плата оставалась работоспособной.

На проверенном экземпляре USB-идентификаторы были такими:

| Режим | VID:PID | Описание |
|---|---|---|
| Кратковременный порт приложения | `239A:8029` | `Pro Micro nRF52840` |
| Загрузчик после 1200 baud touch | `239A:00B3` | `nice!nano` |

**Не ориентируйтесь только на имя порта**: macOS может сохранить тот же путь после переподключения. Сверяйте VID:PID.

## 2. Установка инструментов на macOS

Понадобятся Python 3, USB-кабель с линиями данных, Arduino IDE и пакет Adafruit nRF52 1.7.0. На macOS с Homebrew Python установка через глобальный `pip` может блокироваться сообщением `externally-managed-environment`. Используйте отдельное виртуальное окружение:

```bash
python3 -m venv "$HOME/nrf52840-venv"
source "$HOME/nrf52840-venv/bin/activate"
python -m pip install -r requirements.txt
adafruit-nrfutil --help
```

Команды выполняются из каталога этого репозитория. В новом окне Terminal виртуальное окружение нужно активировать снова. Не используйте `sudo pip` или `--break-system-packages` для обхода защиты Python.

## 3. Проверка USB (без записи в плату)

Запустите наблюдение **до** подключения устройства:

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

На проверенной плате порт появился в `22:27:23` и исчез в `22:27:26`. Остановите монитор сочетанием **Ctrl+C**. Для дополнительной проверки USB-дескрипторов можно выполнить `system_profiler SPUSBDataType -detailLevel full`, пока устройство доступно.

## 4. Вход в загрузчик без двойного RST

1. Отключите плату от USB и закройте Serial Monitor / Web Flasher — они не должны занимать порт.
2. В активированном Python-окружении запустите **до подключения платы**:

   ```bash
   python scripts/dfu_touch.py
   ```

3. Когда появится `Waiting for Pro Micro...`, подключите плату к USB.
4. На проверенном экземпляре получено:

   ```text
   Found: /dev/cu.usbmodem14301
   1200 baud touch sent
   Watching USB for 8 seconds...
   USB: ()
   USB: (('/dev/cu.usbmodem14301', 9114, 179),)
   ```

   Значения `9114` и `179` в десятичном представлении означают `239A:00B3`.

5. Остановите скрипт **Ctrl+C**, не отключая плату. Подтвердите режим:

   ```bash
   python -m serial.tools.list_ports -v
   ```

   На тестовой плате было: `desc: nice!nano`, `USB VID:PID=239A:00B3`.

Скрипт выполняет *1200-baud touch* (открывает/закрывает USB CDC-порт и меняет DTR), **но не стирает и не прошивает Flash**. Если другие VID/PID — сначала установите их назначение; не используйте бездумно этот скрипт для постороннего USB-устройства.

## 5. Подготовка Arduino IDE и поддержки Pro Micro

В Arduino IDE 1.8.13 через **Preferences → Additional Boards Manager URLs** добавьте:

```text
https://adafruit.github.io/arduino-board-index/package_adafruit_index.json
```

Через **Boards Manager** установите **Adafruit nRF52 by Adafruit — 1.7.0**. Для поддержки Pro Micro использовалось дополнительное описание платы:

- <https://github.com/somik123/Adafruit_nRF52_Arduino_ProMicro>

Следуйте README этого проекта: сохраните резервную копию `boards.txt`, добавьте описание `promicronrf52840` и каталог `variants/pro_micro_nrf52840` к установленному Adafruit nRF52 core. На испытанном Mac ядро находилось здесь:

```text
~/Library/Arduino15/packages/adafruit/hardware/nrf52/1.7.0/
```

Проверьте, что `boards.txt` содержит `promicronrf52840.name=Pro Micro nRF52840`, а `build.variant=pro_micro_nrf52840` указывает на существующий каталог. **Полностью закройте и откройте Arduino IDE**, чтобы плата появилась в списке. Не выбирайте «Burn Bootloader».

Настройки проверенной сборки: **Board: Pro Micro nRF52840**, **SoftDevice: S140 6.1.1**, **Debug Level: Level 0 (Release)**, **Debug Port: Serial**.

## 6. Сборка диагностической прошивки

Исходный скетч: [`firmware/PROMICRO-USB-RECOVERY-01/PROMICRO-USB-RECOVERY-01.ino`](firmware/PROMICRO-USB-RECOVERY-01/PROMICRO-USB-RECOVERY-01.ino).

Программа только открывает USB Serial на 115200 бод и раз в секунду печатает `PROMICRO-USB-RECOVERY-01 | Uptime: ... s`. Радиомодуль SX1262, BLE, SPI и I²C не используются.

Откройте `.ino` в Arduino IDE, выберите указанную выше плату, нажмите **Verify**, затем **Sketch → Export Compiled Binary**. Для ядра Adafruit обязательно подключение `#include <Adafruit_TinyUSB.h>` — без него в нашем случае компоновщик выдавал `undefined reference to Serial`.

В испытании экспортированный файл назывался `nrf_boot.ino.pro_micro_nrf52840.hex` (у вас имя может отличаться).

### Почему нельзя сразу прошивать HEX

Сначала проверьте, что адреса и расположение приложения соответствуют **фактически установленной** связке загрузчик/SoftDevice. У проверенной сборки S140 v6 линкерный файл `nrf52840_s140_v6.ld` задавал `FLASH ORIGIN = 0x26000` и конец области `0xED000` (исключительно). Проверенный HEX занимал `0x00026000–0x00032E33` (52 788 байт). 

**Внимание к формату Intel HEX:** запись типа **02** — это *Extended Segment Address*. Анализатор, учитывающий только тип 04, неверно покажет начало `0x00000000`. Эти диапазоны — параметры конкретной проверенной конфигурации, не универсальные адреса nRF52840.

## 7. Упаковка приложения в DFU ZIP

В активированном окружении задайте пути к **собранному вами** HEX-файлу и выходному ZIP:

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

`0x00B6` соответствует требованию к SoftDevice S140 6.1.1. В тестовом ZIP находились **только** `.bin` (52 788 байт), `.dat` (14 байт) и `manifest.json` с разделом `application` и `dfu_version: 0.5`. В архиве не было отдельного образа загрузчика или SoftDevice.

**Не меняйте `--sd-req` на универсальное значение для обхода отказа загрузчика.** У нас нет независимого дампа версии SoftDevice, но конкретный пакет был принят загрузчиком и тестовое приложение запустилось.

## 8. Прошивка по Serial DFU

> **Это единственный шаг, который меняет Flash.** Он заменяет пользовательское приложение. Убедитесь, что нужные данные сохранены, выбран правильный порт, а ZIP подходит вашей плате и SoftDevice. Не отключайте USB во время записи.

Убедитесь, что устройство по-прежнему определено как `239A:00B3`. Если нет — повторите шаг 4. Затем подставьте реальные пути и номер порта:

```bash
ZIP="$HOME/Documents/Arduino/nrf_boot/PROMICRO-USB-RECOVERY-01.zip"
PORT="/dev/cu.usbmodem14301"

adafruit-nrfutil --verbose dfu serial \
  --package "$ZIP" \
  --port "$PORT" \
  --baudrate 115200 \
  --singlebank
```

Зафиксированный результат:

```text
Sending DFU start packet
Sending DFU init packet
Sending firmware file
Activating new firmware
DFU upgrade took 3.8958027362823486s
Device programmed.
```

Если DFU сообщает о несовместимости SoftDevice или повреждённом пакете, **остановитесь** и проверьте конфигурацию. Не стирайте загрузчик и не используйте принудительное восстановление без отдельной диагностики.

## 9. Проверка результата

Откройте Serial Monitor на **115200**. При испытании приложение печатало:

```text
PROMICRO-USB-RECOVERY-01 | Uptime: 75 s
PROMICRO-USB-RECOVERY-01 | Uptime: 76 s
PROMICRO-USB-RECOVERY-01 | Uptime: 77 s
```

После диагностической программы на **ту же плату успешно загрузили рабочую пользовательскую прошивку**. Таким образом, возможность перепрошивки через USB восстановлена. Сам по себе этот тест не подтверждает работу SX1262 или всех периферийных устройств.

## 10. Если что-то не работает

| Симптом | Действие |
|---|---|
| `externally-managed-environment` | Использовать виртуальное окружение Python |
| `adafruit-nrfutil: command not found` | Выполнить `source ~/nrf52840-venv/bin/activate` |
| `dfu_touch.py: No such file` | Запускать `python scripts/dfu_touch.py` из корня репозитория |
| Порт доступен лишь 2–3 секунды | Запустить скрипт до подключения USB |
| Плата не видна в Arduino IDE | Проверить `boards.txt`, `variants` и полностью перезапустить IDE |
| `undefined reference to Serial` | Проверить `#include <Adafruit_TinyUSB.h>` |
| Нет UF2-диска | Проверить Serial DFU по VID:PID, отсутствие диска не исключает DFU |
| `Device not configured` при чтении порта | USB переопределился/отключился; искать загрузчик после touch |
| DFU отклоняет ZIP | Проверить тип пакета, SoftDevice, карту памяти; не обходить проверки |
| Порта нет даже кратковременно | Метод может быть неприменим; рассмотреть SWD |

## 11. Ограничения и ссылки

Испытана **одна конкретная плата**, macOS и приведённые версии инструментов. Метод не гарантирован для других вариантов загрузчика, ревизий Pro Micro, SoftDevice и USB-дескрипторов. Не прошивайте этот исходник наугад в устройство с неизвестной картой памяти.

- [Adafruit nRF52 Arduino Core](https://github.com/adafruit/Adafruit_nRF52_Arduino)
- [Adafruit nRF52 Bootloader](https://github.com/adafruit/Adafruit_nRF52_Bootloader)
- [Adafruit nRF52 Arduino ProMicro add-on](https://github.com/somik123/Adafruit_nRF52_Arduino_ProMicro)
- [Adafruit nRF52 nrfutil](https://github.com/adafruit/Adafruit_nRF52_nrfutil)
- [nice!nano Troubleshooting](https://nicekeyboards.com/docs/nice-nano/troubleshooting/)

## Лицензия

[MIT](LICENSE). Файлы сторонних проектов не включены: устанавливайте их из соответствующих репозиториев и соблюдайте их лицензии. Готовый универсальный DFU ZIP намеренно **не** публикуется.
