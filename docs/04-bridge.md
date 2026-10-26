# 4. Мост quasard → Home Assistant

Колонка говорит только на протоколе Яндекса (uniproxy), поэтому нужен переводчик. [quasard](https://github.com/amirilivice/quasard) эмулирует облако Алисы. Патчи из каталога [bridge/](../bridge) заменяют его распознавание, «мозг» и синтез на REST API HA: `stt.vosk` → встроенный Assist → `tts.piper`. Torch, GPU и LLM не нужны.

## 1. Установка quasard без тяжёлых зависимостей

В контейнере:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
cd ~ && git clone https://github.com/amirilivice/quasard && cd quasard
grep -v -E 'gigaam|omegaconf' requirements.txt > req.txt
uv venv -p 3.12 .venv
uv pip install -p .venv -r req.txt
```

## 2. Файлы моста

Скопируйте каталог `bridge/` этого репозитория в контейнер и разложите файлы по местам:

```bash
# на вашем компьютере
scp -r bridge root@192.168.1.49:/root/bridge

# в контейнере
cd ~/quasard
cp ../bridge/ha.py ../bridge/apply_*.py ../bridge/config.toml .
cp ../bridge/ha.env.example ha.env
chmod 600 ha.env
```

Файлы и назначение:

| Файл | Что делает |
| --- | --- |
| `ha.py` | REST-клиент HA: `stt_sync`, `converse`, `tts_pcm` |
| `apply_ha.py` | подключает `ha.py` к quasard, отключает Яндекс Музыку |
| `apply_say.py` | информер `/_say` ([часть 7](07-player.md)) |
| `apply_play.py` | плеер `/_play`, `/_cmd` ([часть 7](07-player.md)) |
| `apply_stream.py` | прокси радио `/_stream` ([часть 7](07-player.md)) |
| `config.toml` | порты 443 и 80, сертификаты lite-kit, `engine = "ha"` |
| `ha.env.example` | переменные окружения |
| `alice-ha.service` | systemd-юнит ([часть 6](06-service.md)) |

## 3. Патч quasard → HA

```bash
cd ~/quasard
.venv/bin/python apply_ha.py
sed -i 's|@r.get("/generate_204")|@r.api_route("/generate_204", methods=["GET", "HEAD"])|' alice_server/http_api.py
```

Патч идемпотентный: уже применённые правки он пропускает. Вторая команда чинит `HEAD /generate_204`, который колонка шлёт для проверки сети.

## 4. Токен и настройки

1. В HA: профиль → **Безопасность** → **Долгосрочные токены доступа** → создать.
2. Откройте `~/quasard/ha.env` в `nano` и впишите токен в `HA_TOKEN`. Вставка через `sed` может оставить его пустым.
3. Проверьте остальные значения:

| Переменная | Значение |
| --- | --- |
| `HA_URL` | адрес HA **с портом 8123**, например `http://192.168.1.111:8123` |
| `HA_TOKEN` | долгосрочный токен |
| `HA_STT` / `HA_TTS` | `stt.vosk` / `tts.piper` |
| `HA_LANG` | `ru` |
| `HA_AGENT` | необязательно: ID агента Assist (по умолчанию — агент по умолчанию) |
| `STATION_IP` | IP колонки |
| `BRIDGE_URL` | адрес моста, например `http://192.168.1.49` |

Токен не публикуйте и не коммитьте. В DEBUG-логах моста видны OAuth-токен Яндекса и токен HA.

Сертификат стенда lite-kit покрывает `uniproxy.alice.yandex.net`, `quasar.yandex.net` и другие домены Алисы, колонка ему доверяет. Поэтому `~/lite-kit` удалять нельзя.

## 5. Проверка связи с HA (до подключения колонки)

```bash
set -a; . ./ha.env; set +a
.venv/bin/python -c "import asyncio; from alice_server import ha; print(asyncio.run(ha.converse('test','который час')))"
.venv/bin/python -c "import asyncio; from alice_server import ha; p,r=asyncio.run(ha.tts_pcm('проверка связи')); print(len(p), r)"
```

Должны вывестись время и число сэмплов с частотой 48000. Ошибка `All connection attempts failed` значит, что в `HA_URL` нет порта 8123.

Дальше: [5. Перенаправление колонки](05-redirect.md).
