# Gaffer

Unofficial 2026–27 football season manager. Fan simulation.

Premier League squads use publicly listed 2026–27 names. Ratings are estimates.
La Liga, Serie A and Bundesliga use real 2026–27 club lists with mixed known stars and generated depth players.
Not affiliated with any league, club or other game.

## Termux

```bash
termux-setup-storage
cd ~/storage/shared
unzip Gaffer.zip
cd Gaffer
python run.py
```

Open `http://127.0.0.1:8765` in the phone browser.

Python 3.10+ only. No pip packages.

## Play

1. Pick a Premier League club.
2. Game plan — formation, style, tap cards to change the XI.
3. Matchday — play the next fixture.
4. Table / schedule — league picture.

XI strength is overall × natural position × fitness × form. Your best two outfield players carry extra weight. Sit them and the number drops more than sitting a squad man.

## Saves

Club page → Save writes `saves/career1.json`.

## GitHub then Railway

On the phone (Termux) after unzip:

```bash
pkg install git
cd ~/storage/shared/Download/Gaffer
git init
git add .
git commit -m "Gaffer"
```

On GitHub: New repository named `Gaffer` (do not add a README on the website). Then:

```bash
git remote add origin https://github.com/YOUR_USER/Gaffer.git
git branch -M main
git push -u origin main
```

Railway: New project → Deploy from GitHub → pick `Gaffer`.  
Start command is already in `Procfile`: `web: python run.py`  
It uses `$PORT`. Add a volume mounted at `/app/saves` if you want rooms to survive restarts.
