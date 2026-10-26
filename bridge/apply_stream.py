import pathlib
root = pathlib.Path("alice_server")
def sub(f, old, new):
    p = root / f; s = p.read_text(encoding="utf-8")
    if new in s: return
    assert old in s, f"{f}: не найдено: {old[:60]}"
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

# прокси для интернет-радио: убирает ICY-метаданные, редиректы и https
sub("app.py", '''    svc.pending_play = {}''', '''    svc.pending_play = {}

    @app.get("/_stream")
    async def stream(u: str):
        import httpx as _h
        from fastapi.responses import StreamingResponse
        cl = _h.AsyncClient(follow_redirects=True, timeout=_h.Timeout(10, read=None))
        r = await cl.send(cl.build_request("GET", u, headers={"User-Agent": "VLC/3.0.20", "Icy-MetaData": "0"}),
                          stream=True)
        ctype = r.headers.get("content-type", "audio/mpeg").split(";")[0].strip()
        if not ctype.startswith("audio") or "icy" in ctype:
            ctype = "audio/mpeg"

        async def body():
            try:
                async for chunk in r.aiter_raw():
                    yield chunk
            finally:
                await r.aclose()
                await cl.aclose()
        return StreamingResponse(body(), media_type=ctype)''')

sub("uniproxy.py", '''                fmt = (item.get("format") or "MP3").upper()''', '''                fmt = (item.get("format") or "MP3").upper()
                if not re.match(r"https?://(10\\.|192\\.168\\.|172\\.(1[6-9]|2\\d|3[01])\\.|127\\.|homeassistant)", item["url"]):
                    import os as _o, urllib.parse as _up
                    item["url"] = _o.environ.get("BRIDGE_URL", "http://192.168.1.49") + "/_stream?u=" + _up.quote(item["url"], safe="")''')
print("OK: прокси радио подключён")
