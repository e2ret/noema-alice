import pathlib
root = pathlib.Path("alice_server")
def sub(f, old, new, marker):
    p = root / f; s = p.read_text(encoding="utf-8")
    if marker in s: return
    assert old in s, f"{f}: не найдено: {old[:60]}"
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
sub("app.py", '''    svc.pending_play = {}
''', r'''    svc.pending_play = {}

    @app.get("/_config")
    async def get_config():
        from . import ha as _ha
        return {"tts": _ha.HA_TTS, "stt": _ha.HA_STT}

    @app.post("/_config")
    async def set_config(body: dict):
        import os as _o, re as _re
        from fastapi import HTTPException as _E
        from . import ha as _ha
        rx = {"tts": r"tts\.[a-z0-9_]+", "stt": r"stt\.[a-z0-9_]+"}
        names = {"tts": "HA_TTS", "stt": "HA_STT"}
        upd = {}
        for k in rx:
            if k in body:
                v = str(body[k])
                if not _re.fullmatch(rx[k], v):
                    raise _E(status_code=400, detail="bad " + k)
                upd[names[k]] = v
        path = _o.environ.get("HA_ENV_FILE", "ha.env")
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except OSError:
            lines = []
        for name, v in upd.items():
            setattr(_ha, name, v)  # ha.py читает их при каждом вызове, перезапуск не нужен
            for i, ln in enumerate(lines):
                if ln.startswith(name + "="):
                    lines[i] = name + "=" + v
                    break
            else:
                lines.append(name + "=" + v)
        if upd:
            open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        return {"tts": _ha.HA_TTS, "stt": _ha.HA_STT}
''', '"/_config"')
print("OK: настройки движков подключены")
