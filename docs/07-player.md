# 7. Информер, плеер и прокси радио

Колонка игнорирует звук, который мост присылает без её запроса. Поэтому мост через локальный API колонки glagol (порт 1961) отправляет ей текстовую команду, колонка пересылает её мосту как обычный запрос, и мост отвечает нужным звуком или командой плееру. Механизм описан в [architecture.md](architecture.md#управление-колонкой-из-ha-glagol).

## Установка патчей

Пять патчей применяются по порядку в `~/quasard`:

| Патч | Добавляет |
| --- | --- |
| [apply_say.py](../bridge/apply_say.py) | информер `/_say` |
| [apply_play.py](../bridge/apply_play.py) | плеер `/_play`, `/_cmd` и функцию `glagol()` |
| [apply_stream.py](../bridge/apply_stream.py) | прокси радио `/_stream` |
| [apply_restart.py](../bridge/apply_restart.py) | перезапуск моста `/_restart` |
| [apply_config.py](../bridge/apply_config.py) | смена движков речи `/_config` |

```bash
cd ~/quasard
.venv/bin/python apply_say.py
.venv/bin/python apply_play.py
.venv/bin/python apply_stream.py
.venv/bin/python apply_restart.py
.venv/bin/python apply_config.py
systemctl restart alice-ha
```

Каждый скрипт можно запускать повторно, уже применённые правки он пропускает.

## API моста (порт 80)

| Метод | Тело | Действие |
| --- | --- | --- |
| `POST /_say/<device_id>` | `{"text": "…"}` | озвучить текст (команда «повтори за мной …») |
| `POST /_play/<device_id>` | `{"url": "…", "title": "…"}` | проиграть URL (команда «включи поток <ключ>» → `audio_play`) |
| `POST /_cmd/<device_id>` | `{"command": "stop"/"play"/"next"/"prev"}` или `{"command": "setVolume", "volume": 0.4}` | управление плеером через glagol |
| `GET /_stream?u=<url>` | — | прокси внешнего потока без ICY |
| `GET /_status` | — | подключённые колонки (`connections`) |
| `POST /_restart` | — | перезапуск службы `alice-ha` (колонка переподключится примерно через 30 с) |
| `GET /_config` | — | текущие движки: `{"tts": "tts.piper", "stt": "stt.vosk"}` |
| `POST /_config` | `{"tts": "tts.silero"}` и/или `{"stt": "stt.vosk"}` | сменить движок без перезапуска, значение сохраняется в `ha.env` |

Адреса моста без пароля, как и остальные: доступны всем в локальной сети. Не открывайте порт 80 моста наружу.

Внешние адреса (не `10.x`, `192.168.x`, `172.16–31.x`, `127.x` и не `homeassistant`) мост заворачивает в `/_stream` сам. Для этого в `ha.env` должен быть задан `BRIDGE_URL`.

## Проверка

```bash
curl http://192.168.1.49/_status
curl -X POST http://192.168.1.49/_say/<DEVICE_ID> -H 'Content-Type: application/json' -d '{"text":"проверка"}'
```

Колонка должна произнести «проверка». Ответ `ok` без звука значит, что не применён `apply_say.py` или пуст `STATION_IP`.

Дальше: [8. Интеграция в HA](08-ha-integration.md).
