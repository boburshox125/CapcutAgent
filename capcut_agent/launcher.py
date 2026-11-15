"""CapCutAgent.exe kirish nuqtasi.

- Ikki marta bosilsa (konsol bor)  -> Claude Desktop'ga o'zini ro'yxatdan o'tkazadi (o'rnatish).
- Claude Desktop ishga tushirsa    -> MCP server sifatida ishlaydi (stdio).
- --install / --serve bilan majburan tanlash mumkin.
"""
import json
import os
import sys


def config_path() -> str:
    if sys.platform == "win32":
        return os.path.join(os.environ["APPDATA"], "Claude", "claude_desktop_config.json")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    return os.path.expanduser("~/.config/Claude/claude_desktop_config.json")


def self_command() -> tuple[str, list]:
    if getattr(sys, "frozen", False):
        return sys.executable, ["--serve"]
    return sys.executable, ["-m", "capcut_agent", "--serve"]


def install(path: str | None = None) -> str:
    path = path or config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cfg = {}
    if os.path.exists(path):
        raw = open(path, encoding="utf-8").read().strip()
        if raw:
            try:
                cfg = json.loads(raw)
            except json.JSONDecodeError:
                raise SystemExit(f"Config buzilgan (JSON emas): {path}. Uni tekshiring.")
        with open(path + ".bak", "w", encoding="utf-8") as f:
            f.write(raw)
    cmd, args = self_command()
    cfg.setdefault("mcpServers", {})["capcut-agent"] = {"command": cmd, "args": args}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return path


def main():
    argv = sys.argv[1:]
    if "--install" in argv or (not argv and sys.stdin is not None and sys.stdin.isatty()):
        p = install()
        print("CapCut Agent o'rnatildi.")
        print(f"Config yangilandi: {p}")
        print("\nENDI: Claude Desktop'ni to'liq yoping (trey ikonkasidan ham) va qayta oching.")
        print("Keyin Claude'ga yozing: \"capcut-agent orqali CapCut'ni och va ekranni ko'rsat\".")
        print("\nAvariya to'xtatish: sichqonchani ekranning chap-yuqori burchagiga olib boring.")
        try:
            input("\nEnter bosing...")
        except EOFError:
            pass
        return
    from capcut_agent.server import main as serve
    serve()


if __name__ == "__main__":
    main()
