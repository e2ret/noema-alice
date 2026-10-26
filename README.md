# NOEMA Alice

[![Translate](https://img.shields.io/badge/Translate-To_Your_Language-red)](https://translate.google.com/translate?sl=auto&u=https://github.com/e2ret/noema-alice)

Яндекс Станция Мини как **полностью локальный** голосовой спутник Home Assistant. Аналог ESP32 с ESPHome: колонка используется только как железо (микрофоны, динамик и слово активации «Алиса» работают прямо на ней), а вся обработка речи и ответы идут у вас дома. Облако Яндекса не нужно.

- **Голос:** «Алиса, …» → Vosk → встроенный Assist HA → Piper. Без LLM.
- **Информер:** `tts.speak` на `media_player.alisa`.
- **Плеер:** файлы и TTS из HA, интернет-радио через прокси моста, громкость, пауза.
- **Управление мостом:** датчики «Мост» и «Колонка на связи», кнопка «Перезапустить мост», выбор движков речи (TTS и STT) прямо в HA.
- **Приватность:** интернет колонке закрыт, облако Яндекса заменено мостом в вашем контейнере.

> **Отказ от ответственности.** Неофициальный проект, не связан с Яндексом. Он даёт root-доступ к вашей колонке и отключает обновления. Всё на ваш риск: колонку можно «окирпичить», гарантия теряется. Делайте только со своим устройством.

## Как это работает

```
Станция Мини  (root, /etc/hosts → мост)
   │  uniproxy (protobuf по WSS :443), HTTP quasar/* :80/:443
   ▼
Мост alice-ha = quasard + патчи   (LXC на Proxmox)
   │  REST: /api/stt/stt.vosk → /api/conversation/process → /api/tts_get_url (tts.piper)
   ▼
Home Assistant
   └─ интеграция noema_alice → media_player.alisa → мост /_play /_cmd → glagol колонки :1961
```

Колонка сама распознаёт слово «Алиса» и шлёт звук на мост по протоколу Яндекса. Мост переводит его в запросы к REST API HA и возвращает ответ. В обратную сторону HA управляет колонкой через мост и её локальный API glagol. Подробности: [docs/architecture.md](docs/architecture.md).

## Что понадобится

Колонку не нужно разбирать. Весь процесс занимает 2–3 часа.

| Что | Пример | Зачем |
| --- | --- | --- |
| Станция Мини 1-го поколения | YNDX-0004, platform `yandexmini` | уши и рот помощника |
| Сервер для моста | LXC на Proxmox, Ubuntu 24.04, 192.168.1.49 | стенд для root, затем мост |
| Home Assistant | 192.168.1.111:8123 | Assist, STT, TTS |
| `stt.vosk` и `tts.piper` в HA | — | распознавание и синтез |
| Роутер с DHCP | IP колонки закреплён, 192.168.1.102 | временная подмена DNS, закрытие интернета |
| Машина с VPN (по необходимости) | — | скачать прошивку, если сервер недоступен из РФ |

Адреса в документации — примеры, подставьте свои. Device ID колонки (`<DEVICE_ID>`) мост показывает в `GET /_status`.

> **Внимание.** Колонка будет сброшена к заводским настройкам и заново привязана к аккаунту. Сброс кнопками в будущем стирает root, тогда всё повторяется с [части 2](docs/02-root.md).

## Порядок установки

1. [Контейнер на Proxmox](docs/01-container.md)
2. [Root на колонке через lite-kit](docs/02-root.md)
3. [Отключение обновлений и SSH](docs/03-ota-ssh.md)
4. [Мост quasard → Home Assistant](docs/04-bridge.md)
5. [Перенаправление колонки на мост](docs/05-redirect.md)
6. [Служба systemd](docs/06-service.md)
7. [Информер, плеер и прокси радио](docs/07-player.md)
8. [Интеграция в Home Assistant](docs/08-ha-integration.md)
9. [Изоляция колонки от интернета](docs/09-isolation.md)

Потом: [обслуживание и диагностика](docs/10-maintenance.md).

## Что в репозитории

```
bridge/               файлы моста: ha.py, патчи apply_*.py, config.toml, systemd-юнит, пример ha.env
station/              файлы для колонки: hosts, автозапуск SSH
custom_components/    интеграция HA noema_alice (config flow, media_player, ru/en)
docs/                 пошаговая инструкция и справка
CLAUDE.md             контекст проекта для Claude Code
```

## Благодарности

Проект стоит на плечах других:

- **[hackalice.me](https://hackalice.me/)** — вики Yandex Station Extended: root, SSH, отключение обновлений, голосовой тракт. Отличный проект, с него стоит начинать, если хотите понять, как всё устроено.
- [krevetkqqq/lite-kit](https://github.com/krevetkqqq/lite-kit) — локальный стенд для получения root по DNS.
- [Marker284/yandex-station-extended](https://github.com/Marker284/yandex-station-extended) — скрипт отключения OTA и dropbear.
- [amirilivice/quasard](https://github.com/amirilivice/quasard) — эмулятор бэкенда Алисы, на его основе сделан мост.

## Лицензия

MIT, см. [LICENSE](LICENSE). Сторонние проекты из списка выше распространяются на условиях своих лицензий.
