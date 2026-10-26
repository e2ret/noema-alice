# 8. Интеграция NOEMA Alice в Home Assistant

Интеграция `noema_alice` добавляется через интерфейс HA, сама находит колонку на мосту и создаёт устройство с сущностью `media_player.alisa`. Через неё работают `tts.speak`, медиабраузер, радио, пауза и громкость. YAML и `rest_command` не нужны.

## 1. Установка

Положите папку [custom_components/noema_alice](../custom_components/noema_alice) в `/config/custom_components/` на HA (Samba, Studio Code Server или File editor):

```text
/config/custom_components/noema_alice/
├── __init__.py
├── config_flow.py
├── const.py
├── manifest.json
├── media_player.py
└── translations/
    ├── en.json
    └── ru.json
```

Перезапустите HA.

## 2. Добавление

**Настройки → Устройства и службы → Добавить интеграцию → NOEMA Alice.** Мастер спросит адрес моста (`http://192.168.1.49`) и имя колонки («Алиса»). Затем запросит у моста `/_status` и возьмёт `device_id` подключённой колонки сам; если колонок несколько, предложит выбрать.

Ошибки мастера:

- «Мост не отвечает» — не запущена служба `alice-ha` или неверный адрес.
- «Колонка не подключена» — мост работает, но колонка к нему ещё не переподключилась. Подождите 30 секунд.

ID сущности (`media_player.alisa`) — автоматическая транслитерация имени «Алиса». Если задать другое имя, ID изменится.

## 3. Проверка

```yaml
action: tts.speak
target:
  entity_id: tts.piper
data:
  media_player_entity_id: media_player.alisa
  message: "Плеер подключён"
```

```yaml
action: media_player.volume_set
target:
  entity_id: media_player.alisa
data:
  volume_level: 0.3
```

Сущность становится «недоступной», когда колонка не подключена к мосту: интеграция раз в 10 секунд проверяет `/_status`.

### Сообщение через `play_media` (формат интеграции AlexxIT)

Старые автоматизации с `media_content_type: dialog` работают без правок. Допустимые типы: `dialog`, `text`, `tts`.

```yaml
action: media_player.play_media
target:
  entity_id: media_player.alisa
data:
  media_content_type: dialog
  media_content_id: Принтер закончил печать
  extra:
    volume_level: 0.2
```

`extra.volume_level` необязателен. Громкость колонки меняется на время сообщения, затем возвращается к значению, которое последним задавали через HA (`volume_set` или предыдущее сообщение). Если громкость через HA ещё ни разу не задавалась, прежнее значение неизвестно, и после сообщения остаётся новая. Момент конца речи мост не знает, поэтому возврат происходит по таймеру, пропорциональному длине текста.

## 4. Карточка радио

Подходит `custom:mini-media-player` с `entity: media_player.alisa` и кнопками `type: music`, где `id` — ссылка на поток (http или https, с ICY или без). `media_player.media_play` только снимает с паузы: если ничего не запущено, звука не будет.

## Как устроена интеграция

| Файл | Что делает |
| --- | --- |
| `manifest.json` | описание, `config_flow: true` |
| `config_flow.py` | мастер: адрес моста, имя, поиск колонки через `/_status` |
| `media_player.py` | сущность: `play_media` → `/_play`, пауза, стоп, громкость → `/_cmd` |
| `__init__.py` | подключает платформу `media_player` |
| `translations/` | тексты мастера на русском и английском |

TTS и файлы из медиабраузера HA превращаются в ссылку (`media_source` → URL), которую мост отдаёт колонке.

Дальше: [9. Изоляция от интернета](09-isolation.md).
