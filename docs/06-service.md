# 6. Служба systemd

Мост работает как служба `alice-ha` и поднимается сам после перезагрузки контейнера. Юнит лежит в [bridge/alice-ha.service](https://github.com/e2ret/noema-alice/blob/main/bridge/alice-ha.service).

Перед включением остановите все ручные запуски моста, иначе служба упадёт со `status=3` из-за занятых портов 80 и 443.

```bash
pkill -f "python -m alice_server"; sleep 2
cp ~/bridge/alice-ha.service /etc/systemd/system/alice-ha.service
systemctl daemon-reload
systemctl enable --now alice-ha
systemctl status alice-ha --no-pager | head -4   # active (running)
```

Лог вживую:

```bash
journalctl -u alice-ha -f | grep -E "ASR|HA:|Плеер|ERROR"
```

После `systemctl restart alice-ha` колонке нужно около 30 секунд, чтобы переподключиться.

Дальше: [7. Информер, плеер и радио](07-player.md).
