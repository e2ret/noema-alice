import pathlib
root = pathlib.Path("alice_server")
def sub(f, old, new):
    p = root / f; s = p.read_text(encoding="utf-8")
    if new in s: return
    assert old in s, f"{f}: не найдено: {old[:60]}"
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# /_say: через glagol (sendText «повтори за мной ...»), станция сама отправит TextInput
sub("app.py",
'''        sess = next(iter(conns))
        ogg = await svc.tts.synth(body.get("text", ""))
        await sess.stream_tts("", ogg)
        return {"status": "ok"}''',
'''        import json as _j, os as _o, ssl as _s, time as _t, uuid as _u
        import httpx as _h, websockets as _w
        ip = _o.environ.get("STATION_IP", "")
        async with _h.AsyncClient() as cl:
            tok = (await cl.get(f"http://127.0.0.1:{cfg.server.http_port}/quasar.yandex.net/glagol/token",
                                params={"device_id": device_id, "platform": "yandexmini"})).json()["token"]
        ctx = _s.SSLContext(_s.PROTOCOL_TLS_CLIENT); ctx.check_hostname = False; ctx.verify_mode = _s.CERT_NONE
        async with _w.connect(f"wss://{ip}:1961", ssl=ctx, open_timeout=5) as ws:
            await ws.send(_j.dumps({"conversationToken": tok, "id": str(_u.uuid4()), "sentTime": int(_t.time() * 1000),
                                    "payload": {"command": "sendText", "text": "повтори за мной " + body.get("text", "")}}))
            try:
                await ws.recv()
            except Exception:
                pass
        return {"status": "ok"}''')

# «повтори за мной X» — говорим X сами, без HA
sub("uniproxy.py",
'''        intent = intents.match(text)
''',
'''        m_rep = re.match(r"^\\s*повтори за мной[\\s,:]+(.+)$", text, re.I | re.S)
        if m_rep:
            await self._speak_sentences(ref, request_id, seq, _aiter([m_rep.group(1)]), [], listen_on_question=False)
            return
        intent = intents.match(text)
''')
print("OK: информер подключён")
