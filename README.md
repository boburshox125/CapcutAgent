# CapCut Agent

Claude (Claude Desktop) orqali CapCut kompyuter versiyasini sichqoncha va klaviatura bilan boshqaradigan MCP dasturi.
Claude ekranni ko'radi (screenshot), keyin bosadi, sudraydi, yozadi, tez-tugma bosadi.

## O'rnatish (Windows)
1. **Releases** bo'limidan `CapCutAgent.exe` ni yuklang (yoki Actions → Build exe → Artifacts).
2. `CapCutAgent.exe` ni ikki marta bosing - u Claude Desktop config'iga o'zini yozadi.
   (Windows "noma'lum dastur" desa: More info → Run anyway.)
3. Claude Desktop'ni to'liq yoping va qayta oching.
4. Claude'ga: "capcut-agent orqali CapCut'ni och, yangi loyiha yarat, ..." deb vazifa bering.

## Muhim
- Ishlayotganda sichqoncha/klaviaturaga tegmang.
- Avariya to'xtatish: sichqonchani ekranning chap-yuqori burchagiga olib boring.
- CapCut'ni to'liq ekranda (maximize) ishlating, ekran masshtabi 100–150% bo'lsin.

## Toollar
screenshot, zoom, screen_info, click, move, drag, scroll, type_text, hotkey, press, wait,
focus_capcut, open_capcut, capcut_shortcuts

## Qo'lda ishga tushirish (dasturchilar uchun)
pip install -r requirements.txt && python -m capcut_agent --install
