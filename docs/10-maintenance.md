# Обслуживание и диагностика

Три правила:

1. Не сбрасывайте колонку кнопками. Сброс стирает `/data` (dropbear, блокировку OTA, бэкапы). Правки в `/etc` и `/system` остаются. После сброса повторяются [части 2](02-root.md) и [3](03-ota-ssh.md).
2. Не выключайте контейнер Alice.
3. Не обновляйте quasard без нужды.

## Обновление quasard

После `git pull` патчи слетают. Повторите их по порядку:

```bash
cd ~/quasard && git pull
.venv/bin/python apply_ha.py && .venv/bin/python apply_say.py && .venv/bin/python apply_play.py && .venv/bin/python apply_stream.py && .venv/bin/python apply_restart.py && .venv/bin/python apply_config.py
sed -i 's|@r.get("/generate_204")|@r.api_route("/generate_204", methods=["GET", "HEAD"])|' alice_server/http_api.py
systemctl restart alice-ha
```

## Смена токена HA

Создайте новый токен, удалите старый, впишите его в `~/quasard/ha.env` через `nano` и выполните `systemctl restart alice-ha`. Ошибка `Illegal header value b'Bearer '` в логе значит, что токен пуст.

## Симптомы и причины

| Симптом | Где смотреть | Причина и решение |
| --- | --- | --- |
| Колонка слушает, но молчит | `journalctl -u alice-ha -n 50` | нет строки `ASR:` → голос идёт не на мост; проверьте `/etc/hosts` на колонке |
| Кольцо само мигает каждые ~15 с | `/data/quasar/daemons_logs/maind.log`, `Updater is ready to apply update` | цикл обновления: `quasar.yandex.net` не ведёт на мост |
| Служба `alice-ha` падает со `status=3` | `ss -tlpn \| grep -E ':(80\|443)'` | порты заняты ручным запуском или стендом lite-kit |
| `Home Assistant недоступен`, `ConnectError` | `ha.env` | неверный `HA_URL` (нужен порт 8123) или токен |
| Радио не играет | `/data/quasar/daemons_logs/mediad.log` | `Missing decoder: ICY` → не применён `apply_stream.py` |
| Информер отвечает `ok`, но молчит | `journalctl -u alice-ha` | не применён `apply_say.py` или пустой `STATION_IP` |
| Загрузка прошивки стоит на 32 КБ | `curl -o /tmp/t.zip <ссылка>` | блокировка хостинга из РФ → качать через VPN и `scp` |
| Интернет в сети пропал при привязке | DHCP роутера | DNS 1 = стенд; верните прежний DNS сразу после [части 3](03-ota-ssh.md) |

## Полезные команды

```bash
journalctl -u alice-ha -f | grep -E "ASR|HA:|Плеер|ERROR"        # лог моста вживую
ssh -p 2222 root@192.168.1.102                                    # консоль колонки
ssh -p 2222 root@192.168.1.102 'tail -30 /data/quasar/daemons_logs/maind.log | cut -c1-200'
ssh -p 2222 root@192.168.1.102 'cat /etc/hosts'
```

## Идеи на будущее

- Читать реальное состояние плеера по glagol WS (как в AlexxIT/YandexStation).
- Вынести патчи в форк quasard вместо `apply_*.py`.
- Несколько колонок: брать `STATION_IP` по `device_id`.
