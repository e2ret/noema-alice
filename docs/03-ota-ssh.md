# 3. Отключение обновлений и SSH

Без этого Яндекс пришлёт обновление и закроет root. SSH (dropbear, порт 2222) переживает перезагрузки, ADB остаётся запасным входом. Подход — из проекта [yandex-station-extended](https://github.com/Marker284/yandex-station-extended) и вики [hackalice.me](https://hackalice.me/).

## 1. Блокировка OTA

Скрипт подменяет ключ подписи обновлений, поэтому ни один OTA-пакет не пройдёт проверку.

```bash
cd ~ && git clone https://github.com/Marker284/yandex-station-extended
cd yandex-station-extended
adb push contrib/yandex-noupdate.sh /data/opt/yandex-noupdate.sh
adb shell sh /data/opt/yandex-noupdate.sh
adb shell reboot
# через минуту
adb disconnect; adb connect 192.168.1.102:5555
adb shell sh /data/opt/yandex-noupdate.sh status   # ota key : подменён
```

На Мини процесс `maind --updatesd` продолжит работать: скрипт писался под Лайт, и в `launch.json` процесса нет, лаунчер его перезапускает. Поставить обновление он всё равно не сможет. Цикл обновлений окончательно гасится в [части 5](05-redirect.md).

## 2. Dropbear

```bash
adb shell mkdir -p /data/opt/bin /data/opt/etc/dropbear
adb push contrib/bin/dropbear contrib/bin/dropbearkey /data/opt/bin/
adb shell chmod +x /data/opt/bin/dropbear /data/opt/bin/dropbearkey
adb shell /data/opt/bin/dropbearkey -t ed25519 -f /data/opt/etc/dropbear/hk_ed25519
```

## 3. Автозапуск SSH

Скрипт автозапуска лежит в репозитории: [station/S99zdropbear](../station/S99zdropbear). Залейте его на колонку:

```bash
adb shell mount -o remount,rw /
adb push station/S99zdropbear /etc/init.d/S99zdropbear
adb shell "chmod +x /etc/init.d/S99zdropbear; sync; mount -o remount,ro /; /etc/init.d/S99zdropbear start"
# если команда повисла — Ctrl+C, dropbear уже запущен
ssh -p 2222 root@192.168.1.102   # пароль пустой, Enter
```

> У root нет пароля. Порты 2222 и 5555 нельзя открывать наружу.

## 4. Вернуть сеть

В роутере верните прежний DNS DHCP и закрепите за колонкой IP. Стенд lite-kit для привязки больше не нужен, но папку `~/lite-kit` **не удаляйте**: из неё мост берёт сертификаты.

Дальше: [4. Мост](04-bridge.md).
