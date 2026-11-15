"""CapCut Agent — Claude ekranni ko'rib, sichqoncha va klaviatura bilan CapCut'ni boshqaradi.

Koordinatalar: screenshot() qaytargan rasm piksellarida (rasm kattalashtirilmaydi/kichraytirilmaydi
qo'shimcha). Dastur ichkarida haqiqiy ekran koordinatasiga o'zi o'giradi.
"""
import io
import os
import subprocess
import sys
import time
from typing import Optional

from mcp.server.fastmcp import FastMCP, Image

mcp = FastMCP("capcut-agent")

MAX_W = 1400  # Claude'ga yuboriladigan rasm kengligi (piksel)

_state = {"scale": 1.0, "origin": (0, 0), "last_size": None}  # rasm -> ekran: ekran = origin + rasm*scale


def _dpi_aware():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


_dpi_aware()


def _pag():
    # mouseinfo tkinter topilmasa butun jarayonni o'chiradi (exe'da xavfli) - bo'sh modul bilan almashtiramiz
    if "mouseinfo" not in sys.modules:
        import types
        sys.modules["mouseinfo"] = types.ModuleType("mouseinfo")
    import pyautogui  # kech import: displeysiz muhitda modul yuklanishi buzilmasin
    pyautogui.FAILSAFE = True   # sichqonchani ekran burchagiga olib borsangiz - avariya to'xtatish
    pyautogui.PAUSE = 0.08
    return pyautogui


def _to_screen(x: float, y: float) -> tuple[int, int]:
    ox, oy = _state["origin"]
    s = _state["scale"]
    return int(round(ox + x * s)), int(round(oy + y * s))


def _grab(region: Optional[dict] = None):
    import mss
    from PIL import Image as PILImage
    with mss.mss() as sct:
        mon = region or sct.monitors[1]
        shot = sct.grab(mon)
        img = PILImage.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    return img, (mon["left"], mon["top"])


def _encode(img, origin) -> Image:
    w, h = img.size
    scale = 1.0
    if w > MAX_W:
        scale = w / MAX_W
        img = img.resize((MAX_W, int(h / scale)))
    _state["scale"] = scale
    _state["origin"] = origin
    _state["last_size"] = img.size
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return Image(data=buf.getvalue(), format="png")


# ---------------------------------------------------------------- ko'rish

@mcp.tool()
def screenshot() -> Image:
    """Butun ekranning rasmi. Keyingi click/drag koordinatalari shu rasm piksellarida."""
    img, origin = _grab()
    return _encode(img, origin)


@mcp.tool()
def zoom(x: int, y: int, width: int = 500, height: int = 300) -> Image:
    """Ekranning bir qismini yirik ko'rsatadi (kichik tugma/yozuvlarni o'qish uchun).
    (x, y) - oxirgi screenshot rasmidagi chap-yuqori burchak. Keyingi koordinatalar shu zoom rasmiga tegishli."""
    sx, sy = _to_screen(x, y)
    s = _state["scale"]
    reg = {"left": sx, "top": sy, "width": int(width * s), "height": int(height * s)}
    img, origin = _grab(reg)
    w, h = img.size
    k = max(1, min(3, MAX_W // max(w, 1)))
    if k > 1:
        img = img.resize((w * k, h * k))
    _state["scale"] = 1.0 / k if k > 1 else 1.0
    _state["origin"] = origin
    import io as _io
    buf = _io.BytesIO(); img.save(buf, format="PNG")
    return Image(data=buf.getvalue(), format="png")


@mcp.tool()
def screen_info() -> dict:
    """Ekran o'lchami va oxirgi rasm masshtabi."""
    p = _pag()
    return {"screen": list(p.size()), "last_image_size": _state["last_size"], "scale": _state["scale"]}


# ---------------------------------------------------------------- sichqoncha

@mcp.tool()
def click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    """Bosish. button: left|right|middle. clicks=2 - ikki marta bosish."""
    sx, sy = _to_screen(x, y)
    _pag().click(sx, sy, clicks=clicks, button=button)
    return f"click ({x},{y}) -> ekran ({sx},{sy})"


@mcp.tool()
def move(x: int, y: int) -> str:
    """Sichqonchani ko'chiradi (hover uchun, masalan tooltip)."""
    sx, sy = _to_screen(x, y)
    _pag().moveTo(sx, sy, duration=0.15)
    return "ok"


@mcp.tool()
def drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.6) -> str:
    """Sudrash: (x1,y1) dan (x2,y2) ga (timeline'da klipni surish, chetini cho'zish, slayder)."""
    p = _pag()
    a = _to_screen(x1, y1); b = _to_screen(x2, y2)
    p.moveTo(*a, duration=0.15)
    p.mouseDown()
    p.moveTo(*b, duration=duration)
    p.mouseUp()
    return f"drag {a} -> {b}"


@mcp.tool()
def scroll(x: int, y: int, amount: int, horizontal: bool = False) -> str:
    """Aylantirish. amount>0 yuqoriga/o'ngga, <0 pastga/chapga."""
    p = _pag()
    sx, sy = _to_screen(x, y)
    p.moveTo(sx, sy)
    (p.hscroll if horizontal else p.scroll)(amount)
    return "ok"


# ---------------------------------------------------------------- klaviatura

@mcp.tool()
def type_text(text: str, via_clipboard: bool = True) -> str:
    """Matn yozadi. O'zbekcha/Unicode harflar uchun via_clipboard=True (Ctrl+V orqali) ishonchliroq."""
    p = _pag()
    if via_clipboard:
        import pyperclip
        old = None
        try:
            old = pyperclip.paste()
        except Exception:
            pass
        pyperclip.copy(text)
        time.sleep(0.05)
        p.hotkey("ctrl", "v")
        time.sleep(0.1)
        if old is not None:
            try:
                pyperclip.copy(old)
            except Exception:
                pass
    else:
        p.write(text, interval=0.02)
    return f"yozildi: {len(text)} belgi"


@mcp.tool()
def hotkey(keys: list[str]) -> str:
    """Tugmalar kombinatsiyasi, masalan ["ctrl","b"] yoki ["ctrl","shift","z"]."""
    _pag().hotkey(*keys)
    return "+".join(keys)


@mcp.tool()
def press(key: str, times: int = 1) -> str:
    """Bitta tugma: space, enter, delete, left, right, home, end, esc, f2 ..."""
    _pag().press(key, presses=times, interval=0.05)
    return f"{key} x{times}"


@mcp.tool()
def wait(seconds: float = 1.0) -> str:
    """Kutish (eksport, yuklanish, animatsiya tugashi uchun)."""
    time.sleep(min(max(seconds, 0), 60))
    return f"{seconds}s kutildi"


# ---------------------------------------------------------------- CapCut oynasi

def _capcut_windows():
    if sys.platform != "win32":
        return []
    import pygetwindow as gw
    return [w for w in gw.getAllWindows() if w.title and "capcut" in w.title.lower()]


@mcp.tool()
def focus_capcut() -> str:
    """CapCut oynasini oldinga chiqaradi va kattalashtiradi."""
    ws = _capcut_windows()
    if not ws:
        return "CapCut oynasi topilmadi. open_capcut ni chaqiring."
    w = ws[0]
    try:
        if w.isMinimized:
            w.restore()
        w.activate()
        time.sleep(0.4)
        if not w.isMaximized:
            w.maximize()
    except Exception as e:
        return f"Fokus xatosi: {e}"
    return f"Fokus: {w.title}"


@mcp.tool()
def open_capcut() -> str:
    """CapCut'ni ishga tushiradi (odatiy joylardan qidiradi)."""
    la = os.environ.get("LOCALAPPDATA", "")
    cands = [os.path.join(la, "CapCut", "Apps", "CapCut.exe")]
    apps = os.path.join(la, "CapCut", "Apps")
    if os.path.isdir(apps):
        for d in sorted(os.listdir(apps), reverse=True):
            cands.append(os.path.join(apps, d, "CapCut.exe"))
    for c in cands:
        if os.path.isfile(c):
            subprocess.Popen([c])
            return f"Ishga tushirildi: {c}. 5-10 soniya kuting, so'ng screenshot oling."
    return "CapCut.exe topilmadi. Start menyudan qo'lda oching yoki yo'lini ayting."


SHORTCUTS = """CapCut (kompyuter) tez-tugmalari — versiyaga qarab farq qilishi mumkin; shubha bo'lsa menyuda tekshiring:
Space            - pleyer: o'ynatish/to'xtatish
Ctrl+B           - klipni qizil chiziq (playhead) joyida bo'lish
Delete           - tanlangan klipni o'chirish
Ctrl+Z / Ctrl+Shift+Z - bekor qilish / qaytarish
Ctrl+C / Ctrl+V / Ctrl+X - nusxa / qo'yish / kesish
Ctrl+E           - eksport
Ctrl+I           - media import
Q / W            - playhead'gacha chap / o'ng tomonni kesib tashlash
Left / Right     - playhead'ni 1 kadrga surish
Ctrl+= / Ctrl+-  - timeline'ni yaqinlashtirish / uzoqlashtirish
M                - marker qo'yish
Ish tartibi: screenshot -> kerakli joyni zoom -> click/drag -> screenshot bilan natijani tekshirish."""


@mcp.tool()
def capcut_shortcuts() -> str:
    """CapCut'ning asosiy tez-tugmalari ro'yxati."""
    return SHORTCUTS


def main():
    mcp.run()


if __name__ == "__main__":
    main()
