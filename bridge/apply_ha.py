import shutil, pathlib
root = pathlib.Path("alice_server")
shutil.copy("ha.py", root / "ha.py")
def sub(f, old, new):
    p = root / f; s = p.read_text(encoding="utf-8")
    if new in s: return
    assert old in s, f"{f}: не найдено: {old[:60]}"
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
sub("asr.py", 'if self._model is not None or self.cfg.engine == "openai":',
              'if self._model is not None or self.cfg.engine in ("openai", "ha"):')
sub("asr.py", '        if self.cfg.engine == "openai":\n            return self._transcribe_openai(pcm)',
              '        if self.cfg.engine == "ha":\n            from .ha import stt_sync\n            return stt_sync(pcm)\n'
              '        if self.cfg.engine == "openai":\n            return self._transcribe_openai(pcm)')
sub("tts.py", '        elif self.cfg.engine == "openai":',
              '        elif self.cfg.engine == "ha":\n            from .ha import tts_pcm\n            pcm, rate = await tts_pcm(text)\n'
              '        elif self.cfg.engine == "openai":')
sub("uniproxy.py", '        music_cmd = intents.match_music(text)\n', '        music_cmd = None  # HA\n')
sub("uniproxy.py",
    '                async for s in self.svc.dialog.stream(self.device_id, text):\n                    yield s\n',
    '                from .ha import converse\n                speech = await converse(self.device_id, text)\n'
    '                if speech:\n                    yield speech\n')
sub("uniproxy.py", 'yield "Извините, мой мозг сейчас недоступен."', 'yield "Home Assistant недоступен."')
sub("http_api.py", '@r.get("/generate_204")', '@r.api_route("/generate_204", methods=["GET", "HEAD"])')
print("OK: патч HA применён")
