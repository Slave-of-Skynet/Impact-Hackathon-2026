# LOCAL SYNTHETIC — #65 daily reading streak (2026-10-31)

Local Django dev server (`config.settings.dev`), disposable SQLite outside the repo, `seed_demo` (fictional
`@demo.local` accounts only). Mia's events were back-dated by script to Thursday, Friday and Saturday
(today = Saturday 31 Oct), Alex only Friday; the adult has no reading. Not evidence from the public host,
not tested on a real Android phone. Emoji show as boxes because the WSL Chromium has no emoji font.

| File | What it shows |
|---|---|
| `01-child-home-mobile-360.png` | Child mode, Mia: `3 zile consecutive`, week strip L–D with Thu–Sat read, today ringed, Sunday dashed |
| `02-child-home-mobile-390.png` | Same at 390 px |
| `03-child-home-mobile-430.png` | Same at 430 px |
| `04-parent-dashboard-mobile-390.png` | Guardian dashboard: own streak (`Începe seria ta de lectură!` + week), Mia compact `3 zile consecutive`, Alex carried `1 zi consecutivă` + `Mai poți continua seria azi!` |
| `05-child-report-desktop.png` | Guardian report for Mia at 1280 px |

No horizontal overflow at 360/390/430 (`scrollWidth <= innerWidth`).
