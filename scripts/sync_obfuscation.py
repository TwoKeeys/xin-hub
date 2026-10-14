#!/usr/bin/env python3
"""Refresh the reversible encoded Luau loader from the source repository (public or private)."""
import base64
import hashlib
import os
from pathlib import Path
from urllib.request import Request, urlopen

SOURCE = "https://api.github.com/repos/TwoKeeys/MyRobloxScript/contents/main.lua?ref=main"
KEY = bytes([173,47,209,86,18,144,231,59,122,5,197,66,240,31,109,154,83,212,37,168,14,95,201,74,132,23,184,55,226,101,11,146])
OUT = Path("main.lua")

def build(source: bytes) -> str:
    digest = hashlib.sha256(source).hexdigest()
    encoded = base64.b64encode(bytes(value ^ KEY[i % len(KEY)] for i, value in enumerate(source))).decode("ascii")
    chunks = [f'"{encoded[i:i+160]}"' for i in range(0, len(encoded), 160)]
    return (
        "-- Encoded Lua loader; reversible encoding, not secure encryption.\n"
        f"-- Source SHA256: {digest}\n"
        "local _data = table.concat({\n" + ",\n".join(chunks) + "\n})\n"
        'local _alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"\n'
        "local _lookup = {}\n"
        "for i = 1, #_alphabet do _lookup[string.byte(_alphabet, i)] = i - 1 end\n"
        "local _key = {" + ",".join(str(x) for x in KEY) + "}\n"
        "local _output, _n = {}, 0\n"
        "local _byte, _char, _bxor = string.byte, string.char, bit32.bxor\n"
        "for i = 1, #_data, 4 do\n"
        "    local a, b, c, d = _byte(_data, i, i + 3)\n"
        "    local x, y = _lookup[a], _lookup[b]\n"
        "    local z, w = _lookup[c] or 0, _lookup[d] or 0\n"
        "    _n = _n + 1; _output[_n] = _char(_bxor(x * 4 + math.floor(y / 16), _key[((_n - 1) % #_key) + 1]))\n"
        "    if c ~= 61 then\n"
        "        _n = _n + 1; _output[_n] = _char(_bxor((y % 16) * 16 + math.floor(z / 4), _key[((_n - 1) % #_key) + 1]))\n"
        "        if d ~= 61 then\n"
        "            _n = _n + 1; _output[_n] = _char(_bxor((z % 4) * 64 + w, _key[((_n - 1) % #_key) + 1]))\n"
        "        end\n"
        "    end\n"
        "end\n"
        "local _fn, _err = loadstring(table.concat(_output))\n"
        'if not _fn then error("Unable to compile decoded script: " .. tostring(_err)) end\n'
        "return _fn()\n"
    )

def main() -> None:
    token = os.environ.get("SOURCE_REPO_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing SOURCE_REPO_TOKEN secret; configure it in xin-hub Actions secrets")
    req = Request(SOURCE, headers={
        "User-Agent": "xin-hub-automatic-encoder",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json",
    })
    with urlopen(req, timeout=45) as response:
        source = response.read()
    if len(source) < 1000:
        raise RuntimeError("Source script unexpectedly small; refusing to overwrite")
    result = build(source)
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != result:
        OUT.write_text(result, encoding="utf-8")
        print(f"Updated {OUT}: {len(source)} source bytes")
    else:
        print("Source unchanged; no update necessary")

if __name__ == "__main__":
    main()
