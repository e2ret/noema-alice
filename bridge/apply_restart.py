import pathlib
root = pathlib.Path("alice_server")
def sub(f, old, new, marker):
    p = root / f; s = p.read_text(encoding="utf-8")
    if marker in s: return
    assert old in s, f"{f}: не найдено: {old[:60]}"
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
sub("app.py", '''    svc.pending_play = {}
''', '''    svc.pending_play = {}

    @app.post("/_restart")
    async def restart():
        import subprocess as _sp
        # отдельный юнит systemd, чтобы перезапуск не убил сам себя вместе с ответом
        _sp.Popen(["systemd-run", "--on-active=1", "systemctl", "restart", "alice-ha"],
                  stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        return {"status": "restarting"}
''', '"/_restart"')
print("OK: перезапуск моста подключён")
