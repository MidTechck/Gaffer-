# Gaffer

Football manager you run in a browser. Season 2026–27 datapack. Not affiliated with any league, club, or other game.

## Play on a phone (Termux)

```bash
pkg install git python
git clone https://github.com/MidTechck/Gaffer-.git
cd Gaffer-
python run.py
```

Open `http://127.0.0.1:8765`

Same Wi-Fi: other devices use `http://YOUR_PHONE_IP:8765`

Python 3.10+. No pip packages.

## Season rules

- Year 1: league + domestic cups only. No UCL / Europa / Conference / CAF.
- After the season: 1st–5th → UCL, 6th → Europa, 7th–8th → Conference. One club, one ticket.
- Africa: top 2 per league → CAF from year 2.

## Railway

New project → Deploy from GitHub → `MidTechck/Gaffer-`  
Procfile: `web: python run.py` (uses `$PORT`)  
Add a volume at `/app/saves` if rooms should survive restarts.
