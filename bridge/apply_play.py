import pathlib
root = pathlib.Path("alice_server")
def sub(f, old, new):
    p = root / f; s = p.read_text(encoding="utf-8")
    if new in s: return
    assert old in s, f"{f}: не найдено: {old[:60]}"
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# app.py: общий помощник glagol + /_play и /_cmd
sub("app.py", '''    @app.post("/_say/{device_id}")''', '''    async def glagol(device_id: str, payload: dict) -> None:
        import json as _j, os as _o, ssl as _s, time as _t, uuid as _u
        import httpx as _h, websockets as _w
        ip = _o.environ.get("STATION_IP", "")
        async with _h.AsyncClient() as cl:
            tok = (await cl.get(f"http://127.0.0.1:{cfg.server.http_port}/quasar.yandex.net/glagol/token",
                                params={"device_id": device_id, "platform": "yandexmini"})).json()["token"]
        ctx = _s.SSLContext(_s.PROTOCOL_TLS_CLIENT); ctx.check_hostname = False; ctx.verify_mode = _s.CERT_NONE
        async with _w.connect(f"wss://{ip}:1961", ssl=ctx, open_timeout=5) as ws:
            await ws.send(_j.dumps({"conversationToken": tok, "id": str(_u.uuid4()),
                                    "sentTime": int(_t.time() * 1000), "payload": payload}))
            try:
                await ws.recv()
            except Exception:
                pass

    svc.pending_play = {}

    @app.post("/_play/{device_id}")
    async def play(device_id: str, body: dict):
        """Проиграть URL (mp3-поток/файл) на станции."""
        import uuid as _u
        key = _u.uuid4().hex[:8]
        svc.pending_play[key] = body
        await glagol(device_id, {"command": "sendText", "text": "включи поток " + key})
        return {"status": "ok"}

    @app.post("/_cmd/{device_id}")
    async def cmd(device_id: str, body: dict):
        """Команда плееру: {"command": "stop"|"play"|"next"|"prev"} или {"command": "setVolume", "volume": 0.4}."""
        await glagol(device_id, body)
        return {"status": "ok"}

    @app.post("/_say/{device_id}")''')

# uniproxy: «включи поток <key>» -> audio_play
sub("uniproxy.py", '''        m_rep = re.match(''', '''        m_play = re.match(r"^\\s*включи поток (\\w+)\\s*$", text, re.I)
        if m_play:
            item = getattr(self.svc, "pending_play", {}).pop(m_play.group(1), None)
            if item and item.get("url"):
                fmt = (item.get("format") or "MP3").upper()
                d = {"name": "audio_play", "sub_name": "music", "type": "client_action", "is_led_silent": True,
                     "payload": {"stream": {"id": m_play.group(1), "type": "Track", "url": item["url"], "format": fmt,
                                            "codec": "Mp3" if fmt == "MP3" else fmt.capitalize(), "offset_ms": 0},
                                 "metadata": {"title": item.get("title") or "Home Assistant", "subtitle": "",
                                              "hide_progress_bar": True},
                                 "callbacks": {}, "scenario_meta": {"owner": "music"},
                                 "background_mode": "Ducking", "screen_type": "Music", "provider_name": "",
                                 "set_pause": False, "playback_speed": 1}}
                log.info("Плеер: %s", item["url"])
                await self._speak_sentences(ref, request_id, seq, _aiter([]), [d], listen_on_question=False)
                return
        m_rep = re.match(''')
print("OK: плеер подключён")
