#!/usr/bin/env python3
"""Build the 2026-27 datapack. Premier League names from public season previews.
Other leagues: real 2026-27 clubs, generated depth squads + known stars.
Unofficial fan database — ratings estimated, no official logos."""

from __future__ import annotations

import json
import random
from pathlib import Path

from engine.ratings import compute_value

OUT = Path(__file__).with_name("world.json")

FIRST = [
    "Adam", "Alex", "Andrei", "Ben", "Carlos", "Daniel", "Diego", "Eli", "Felix",
    "Hugo", "Ivan", "Jonas", "Leo", "Marco", "Nico", "Oscar", "Pablo", "Rafa",
    "Sam", "Theo", "Victor", "Will", "Yuri", "Luca", "Mateo", "Noah", "Owen",
]
LAST = [
    "Hart", "Cole", "Varga", "Silva", "Kovacs", "Berg", "Nunez", "Petrov", "Walsh",
    "Sato", "Ibrahim", "Costa", "Nowak", "Larsen", "Moreau", "Keller", "Duarte",
    "Okafor", "Bianchi", "Novak", "Stefan", "Reeves", "Diaz", "Farrell",
]


def bd(year: int, rng: random.Random) -> str:
    return f"{year}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}"


def skills_from_ovr(ovr: float, pos: str) -> dict:
    rng = random.Random(int(ovr * 10) + len(pos))
    def j(base):
        return round(max(40, min(99, base + rng.uniform(-4, 4))), 1)
    if pos == "GK":
        return {"pace": j(ovr - 18), "passing": j(ovr - 8), "shooting": j(45), "dribbling": j(48), "defence": j(ovr - 6), "physical": j(ovr - 4), "gk": j(ovr)}
    if pos in ("CB", "LB", "RB"):
        return {"pace": j(ovr - 4), "passing": j(ovr - 8), "shooting": j(ovr - 16), "dribbling": j(ovr - 10), "defence": j(ovr + 1), "physical": j(ovr), "gk": j(28)}
    if pos in ("CDM", "CM"):
        return {"pace": j(ovr - 5), "passing": j(ovr + 1), "shooting": j(ovr - 8), "dribbling": j(ovr - 3), "defence": j(ovr - 4), "physical": j(ovr - 2), "gk": j(22)}
    if pos in ("CAM", "LM", "RM"):
        return {"pace": j(ovr - 1), "passing": j(ovr), "shooting": j(ovr - 4), "dribbling": j(ovr + 1), "defence": j(ovr - 14), "physical": j(ovr - 6), "gk": j(18)}
    return {"pace": j(ovr), "passing": j(ovr - 6), "shooting": j(ovr + 1), "dribbling": j(ovr), "defence": j(ovr - 18), "physical": j(ovr - 3), "gk": j(16)}


def P(pid, first, last, ovr, pos, nation, club_id, born, pot=None, foot="right", h=182):
    roles = [{"code": pos, "mult": 1.0}]
    extra = {
        "ST": ["LW", "RW"], "LW": ["ST", "LM"], "RW": ["ST", "RM"],
        "CAM": ["CM", "LW"], "CM": ["CDM", "CAM"], "CDM": ["CM", "CB"],
        "CB": ["CDM"], "LB": ["LM", "CB"], "RB": ["RM", "CB"],
        "LM": ["LW", "CM"], "RM": ["RW", "CM"],
    }
    for e in extra.get(pos, []):
        roles.append({"code": e, "mult": 0.86})
    age_year = int(born[:4])
    age = 2026 - age_year
    pot = pot or min(99.0, ovr + (8 if age < 23 else 3 if age < 27 else 0))
    return {
        "id": pid,
        "first_name": first,
        "last_name": last,
        "birthdate": born,
        "nation": nation,
        "height_cm": h,
        "foot": foot,
        "roles": roles,
        "overall": float(ovr),
        "potential": float(pot),
        "club_id": club_id,
        "condition": 88.0,
        "form": 6.6,
        "adaptation": 76.0,
        "injury": None,
        "value": compute_value(float(ovr), max(17, age)),
        "season_stats": {"apps": 0, "goals": 0, "assists": 0},
        "skills": skills_from_ovr(float(ovr), pos),
        "retired": False,
    }


# club_id 1-20 Premier League
PL_SQUADS = {
    1: [  # Arsenal
        ("David", "Raya", 86, "GK", "Spain", "1995-08-15", "right", 183),
        ("Kepa", "Arrizabalaga", 78, "GK", "Spain", "1994-10-03", "right", 186),
        ("William", "Saliba", 88, "CB", "France", "2001-03-24", "right", 192),
        ("Gabriel", "Magalhaes", 86, "CB", "Brazil", "1997-12-19", "left", 190),
        ("Jurrien", "Timber", 83, "RB", "Netherlands", "2001-06-17", "right", 179),
        ("Ben", "White", 82, "RB", "England", "1997-10-08", "right", 186),
        ("Riccardo", "Calafiori", 82, "LB", "Italy", "2002-05-19", "left", 188),
        ("Piero", "Hincapie", 81, "CB", "Ecuador", "2002-01-09", "left", 184),
        ("Declan", "Rice", 88, "CDM", "England", "1999-01-14", "right", 185),
        ("Martin", "Odegaard", 87, "CAM", "Norway", "1998-12-17", "left", 178),
        ("Bruno", "Guimaraes", 86, "CM", "Brazil", "1997-11-16", "right", 182),
        ("Martin", "Zubimendi", 84, "CDM", "Spain", "1999-02-02", "right", 181),
        ("Eberechi", "Eze", 85, "CAM", "England", "1998-06-29", "right", 178),
        ("Bukayo", "Saka", 89, "RW", "England", "2001-09-05", "left", 178),
        ("Gabriel", "Martinelli", 84, "LW", "Brazil", "2001-06-18", "right", 178),
        ("Viktor", "Gyokeres", 87, "ST", "Sweden", "1998-06-04", "right", 187),
        ("Kai", "Havertz", 84, "ST", "Germany", "1999-06-11", "left", 193),
        ("Noni", "Madueke", 80, "RW", "England", "2002-03-10", "left", 182),
        ("Ethan", "Nwaneri", 76, "CAM", "England", "2007-03-30", "left", 176),
        ("Myles", "Lewis-Skelly", 75, "LB", "England", "2006-09-26", "left", 178),
    ],
    2: [  # Aston Villa
        ("Emiliano", "Martinez", 86, "GK", "Argentina", "1992-09-02", "right", 195),
        ("Ezri", "Konsa", 81, "CB", "England", "1997-10-23", "right", 183),
        ("Pau", "Torres", 80, "CB", "Spain", "1997-01-16", "left", 191),
        ("Matty", "Cash", 79, "RB", "Poland", "1997-08-07", "right", 185),
        ("Ian", "Maatsen", 78, "LB", "Netherlands", "2002-03-16", "left", 178),
        ("John", "McGinn", 82, "CM", "Scotland", "1994-10-18", "left", 178),
        ("Amadou", "Onana", 81, "CDM", "Belgium", "2001-08-16", "right", 195),
        ("Boubacar", "Kamara", 80, "CDM", "France", "1999-11-23", "right", 184),
        ("Youri", "Tielemans", 81, "CM", "Belgium", "1997-05-07", "right", 176),
        ("Ollie", "Watkins", 84, "ST", "England", "1995-12-30", "right", 180),
        ("Morgan", "Rogers", 82, "LW", "England", "2002-07-26", "right", 187),
        ("Alejandro", "Garnacho", 81, "LW", "Argentina", "2004-07-01", "right", 180),
        ("Leon", "Bailey", 80, "RW", "Jamaica", "1997-08-09", "left", 178),
        ("Tammy", "Abraham", 78, "ST", "England", "1997-10-02", "right", 194),
        ("Victor", "Lindelof", 78, "CB", "Sweden", "1994-07-17", "right", 187),
        ("Emiliano", "Buendia", 77, "CAM", "Argentina", "1996-12-25", "right", 172),
    ],
    3: [  # Bournemouth
        ("Djordje", "Petrovic", 78, "GK", "Serbia", "1999-10-08", "right", 194),
        ("Illia", "Zabarnyi", 80, "CB", "Ukraine", "2002-09-01", "right", 189),
        ("Marcos", "Senesi", 78, "CB", "Argentina", "1997-05-10", "left", 185),
        ("Adrien", "Truffert", 77, "LB", "France", "2001-11-20", "left", 176),
        ("Adam", "Smith", 75, "RB", "England", "1991-04-29", "right", 180),
        ("Lewis", "Cook", 77, "CM", "England", "1997-02-03", "right", 175),
        ("Alex", "Scott", 77, "CM", "England", "2003-08-21", "right", 178),
        ("Marcus", "Tavernier", 79, "LM", "England", "1999-03-22", "right", 178),
        ("Justin", "Kluivert", 80, "LW", "Netherlands", "1999-05-05", "right", 171),
        ("Evanilson", "Evanilson", 80, "ST", "Brazil", "1999-10-06", "right", 183),
        ("Antoine", "Semenyo", 79, "RW", "Ghana", "2000-01-07", "right", 185),
        ("Tyler", "Adams", 78, "CDM", "USA", "1999-02-14", "right", 175),
        ("David", "Brooks", 76, "RW", "Wales", "1997-07-08", "left", 173),
        ("Ryan", "Christie", 76, "CM", "Scotland", "1995-02-22", "left", 178),
    ],
    4: [  # Brentford
        ("Caoimhin", "Kelleher", 78, "GK", "Ireland", "1998-11-23", "right", 188),
        ("Nathan", "Collins", 79, "CB", "Ireland", "2001-04-30", "right", 193),
        ("Ethan", "Pinnock", 77, "CB", "Jamaica", "1993-05-29", "left", 194),
        ("Rico", "Henry", 76, "LB", "England", "1997-07-08", "left", 170),
        ("Mikkel", "Damsgaard", 79, "CAM", "Denmark", "2000-07-03", "right", 180),
        ("Christian", "Norgaard", 78, "CDM", "Denmark", "1994-03-10", "right", 187),
        ("Mathias", "Jensen", 77, "CM", "Denmark", "1996-01-01", "right", 180),
        ("Kevin", "Schade", 78, "LW", "Germany", "2001-11-27", "right", 183),
        ("Bryan", "Mbeumo", 84, "RW", "Cameroon", "1999-08-07", "left", 171),
        ("Yoane", "Wissa", 80, "ST", "DR Congo", "1996-09-03", "right", 176),
        ("Igor", "Thiago", 78, "ST", "Brazil", "2001-06-26", "right", 188),
        ("Keane", "Lewis-Potter", 76, "LW", "England", "2001-02-22", "right", 170),
        ("Sepp", "van den Berg", 76, "CB", "Netherlands", "2001-12-20", "right", 189),
    ],
    5: [  # Brighton
        ("Bart", "Verbruggen", 80, "GK", "Netherlands", "2002-08-18", "right", 194),
        ("Lewis", "Dunk", 80, "CB", "England", "1991-11-21", "right", 192),
        ("Jan", "Paul van Hecke", 78, "CB", "Netherlands", "2000-06-08", "right", 189),
        ("Pervis", "Estupinan", 80, "LB", "Ecuador", "1998-01-21", "left", 175),
        ("Tariq", "Lamptey", 76, "RB", "Ghana", "2000-09-30", "right", 163),
        ("Carlos", "Baleba", 80, "CDM", "Cameroon", "2004-01-03", "left", 179),
        ("Billy", "Gilmour", 77, "CM", "Scotland", "2001-06-11", "right", 170),
        ("Kaoru", "Mitoma", 83, "LW", "Japan", "1997-05-20", "right", 178),
        ("Yankuba", "Minteh", 79, "RW", "Gambia", "2004-07-22", "left", 180),
        ("Joao", "Pedro", 81, "ST", "Brazil", "2001-09-26", "right", 182),
        ("Georginio", "Rutter", 78, "ST", "France", "2002-04-20", "left", 182),
        ("Evan", "Ferguson", 77, "ST", "Ireland", "2004-10-19", "right", 183),
        ("Mats", "Wieffer", 77, "CM", "Netherlands", "1999-11-16", "right", 188),
        ("Ferdi", "Kadioglu", 78, "LB", "Turkey", "1999-10-07", "right", 174),
    ],
    6: [  # Chelsea
        ("Robert", "Sanchez", 79, "GK", "Spain", "1997-11-18", "right", 197),
        ("Levi", "Colwill", 82, "CB", "England", "2003-02-26", "left", 187),
        ("Wesley", "Fofana", 81, "CB", "France", "2000-12-17", "right", 186),
        ("Reece", "James", 83, "RB", "England", "1999-12-08", "right", 182),
        ("Malo", "Gusto", 80, "RB", "France", "2003-05-19", "right", 178),
        ("Marc", "Cucurella", 80, "LB", "Spain", "1998-07-22", "left", 174),
        ("Moises", "Caicedo", 86, "CDM", "Ecuador", "2001-11-02", "right", 178),
        ("Enzo", "Fernandez", 84, "CM", "Argentina", "2001-01-17", "right", 178),
        ("Cole", "Palmer", 88, "CAM", "England", "2002-05-06", "left", 189),
        ("Pedro", "Neto", 82, "RW", "Portugal", "2000-03-09", "left", 174),
        ("Nicolas", "Jackson", 80, "ST", "Senegal", "2001-06-20", "right", 186),
        ("Liam", "Delap", 79, "ST", "England", "2003-02-08", "right", 186),
        ("Estevao", "Willian", 78, "RW", "Brazil", "2007-04-24", "left", 176),
        ("Romeo", "Lavia", 78, "CDM", "Belgium", "2004-01-06", "right", 181),
        ("Tosin", "Adarabioyo", 78, "CB", "England", "1997-09-24", "right", 196),
        ("Jamie", "Gittens", 77, "LW", "England", "2004-08-08", "right", 175),
    ],
    7: [  # Coventry
        ("Ben", "Wilson", 72, "GK", "England", "1992-08-09", "right", 186),
        ("Bobby", "Thomas", 73, "CB", "England", "2001-01-30", "right", 186),
        ("Liam", "Kitching", 72, "CB", "England", "1999-10-25", "left", 191),
        ("Milan", "van Ewijk", 74, "RB", "Netherlands", "2000-09-08", "right", 175),
        ("Jay", "Dasilva", 73, "LB", "England", "1998-04-22", "left", 170),
        ("Jack", "Rudoni", 75, "CM", "England", "2001-06-14", "right", 186),
        ("Matt", "Grimes", 74, "CM", "England", "1995-07-15", "left", 178),
        ("Gustavo", "Hamer", 76, "CM", "Netherlands", "1997-06-24", "right", 169),
        ("Haji", "Wright", 75, "ST", "USA", "1998-03-27", "right", 191),
        ("Ellis", "Simms", 73, "ST", "England", "2001-01-05", "right", 191),
        ("Ephraim", "Mason-Clark", 73, "LW", "England", "1999-12-25", "right", 178),
        ("Frank", "Onyeka", 73, "CDM", "Nigeria", "1998-01-01", "right", 183),
        ("Brandon", "Thomas-Asante", 72, "ST", "England", "1998-12-29", "right", 175),
    ],
    8: [  # Crystal Palace
        ("Dean", "Henderson", 80, "GK", "England", "1997-03-12", "right", 188),
        ("Marc", "Guehi", 82, "CB", "England", "2000-07-13", "right", 182),
        ("Maxence", "Lacroix", 80, "CB", "France", "2000-04-06", "right", 190),
        ("Daniel", "Munoz", 80, "RB", "Colombia", "1996-05-26", "right", 180),
        ("Tyrick", "Mitchell", 78, "LB", "England", "1999-09-01", "left", 175),
        ("Adam", "Wharton", 81, "CM", "England", "2004-02-06", "left", 182),
        ("Eberechi", "Eze", 85, "CAM", "England", "1998-06-29", "right", 178),
        ("Ismaila", "Sarr", 80, "RW", "Senegal", "1998-02-25", "right", 185),
        ("Jean-Philippe", "Mateta", 81, "ST", "France", "1997-06-28", "right", 192),
        ("Eddie", "Nketiah", 76, "ST", "England", "1999-05-30", "right", 180),
        ("Daichi", "Kamada", 77, "CAM", "Japan", "1996-08-05", "right", 184),
        ("Jefferson", "Lerma", 76, "CDM", "Colombia", "1994-10-25", "right", 179),
        ("Cheick", "Doucoure", 77, "CDM", "Mali", "2000-01-08", "right", 180),
        ("Daniel", "Kamada", 76, "CM", "Japan", "1996-08-05", "right", 184),
    ],
    9: [  # Everton
        ("Jordan", "Pickford", 84, "GK", "England", "1994-03-07", "left", 185),
        ("Jarrad", "Branthwaite", 82, "CB", "England", "2002-06-27", "left", 195),
        ("James", "Tarkowski", 79, "CB", "England", "1992-11-19", "right", 185),
        ("Vitalii", "Mykolenko", 77, "LB", "Ukraine", "1999-05-29", "left", 180),
        ("Jake", "O'Brien", 76, "RB", "Ireland", "2001-05-15", "right", 197),
        ("Idrissa", "Gueye", 78, "CDM", "Senegal", "1989-09-26", "right", 174),
        ("James", "Garner", 77, "CM", "England", "2001-03-13", "right", 182),
        ("Iliman", "Ndiaye", 79, "LW", "Senegal", "2000-03-06", "right", 180),
        ("Beto", "Beto", 76, "ST", "Portugal", "1998-01-31", "right", 194),
        ("Dominic", "Calvert-Lewin", 77, "ST", "England", "1997-03-16", "right", 187),
        ("Dwight", "McNeil", 77, "LW", "England", "1999-11-22", "left", 183),
        ("Abdoulaye", "Doucoure", 76, "CM", "Mali", "1993-01-01", "right", 184),
        ("Michael", "Keane", 75, "CB", "England", "1993-01-11", "right", 191),
    ],
    10: [  # Fulham
        ("Bernd", "Leno", 82, "GK", "Germany", "1992-03-04", "right", 190),
        ("Joachim", "Andersen", 80, "CB", "Denmark", "1996-05-31", "right", 192),
        ("Calvin", "Bassey", 78, "CB", "Nigeria", "1999-12-31", "left", 185),
        ("Antonee", "Robinson", 81, "LB", "USA", "1997-08-08", "left", 183),
        ("Kenny", "Tete", 76, "RB", "Netherlands", "1995-10-09", "right", 180),
        ("Sander", "Berge", 78, "CM", "Norway", "1998-02-14", "right", 195),
        ("Alex", "Iwobi", 79, "LW", "Nigeria", "1996-05-17", "right", 180),
        ("Emile", "Smith Rowe", 79, "CAM", "England", "2000-07-28", "right", 182),
        ("Raul", "Jimenez", 78, "ST", "Mexico", "1991-05-05", "right", 190),
        ("Rodrigo", "Muniz", 77, "ST", "Brazil", "2001-05-04", "right", 186),
        ("Andreas", "Pereira", 77, "CAM", "Brazil", "1996-01-01", "right", 178),
        ("Timothy", "Castagne", 76, "RB", "Belgium", "1995-12-05", "right", 185),
        ("Harry", "Wilson", 76, "RW", "Wales", "1997-03-22", "left", 173),
    ],
    11: [  # Hull
        ("Jack", "Butland", 74, "GK", "England", "1993-03-10", "right", 196),
        ("Alfie", "Jones", 72, "CB", "England", "1997-10-14", "right", 191),
        ("Sean", "McLoughlin", 71, "CB", "Ireland", "1996-11-13", "left", 191),
        ("Lewie", "Coyle", 71, "RB", "England", "1995-10-15", "right", 173),
        ("Ryan", "Giles", 72, "LB", "England", "2000-01-26", "left", 180),
        ("Gustavo", "Puerta", 73, "CM", "Colombia", "2003-07-23", "right", 172),
        ("Regan", "Slater", 72, "CM", "England", "1999-09-11", "right", 173),
        ("Oli", "McBurnie", 74, "ST", "Scotland", "1996-06-04", "right", 188),
        ("Liam", "Millar", 73, "LW", "Canada", "1999-09-27", "right", 176),
        ("Mohamed", "Belloumi", 73, "RW", "Algeria", "2002-06-01", "left", 175),
        ("Joe", "Gelhardt", 72, "ST", "England", "2002-05-04", "left", 179),
        ("Matt", "Crooks", 71, "CM", "England", "1994-01-20", "right", 191),
    ],
    12: [  # Ipswich
        ("Arijanet", "Muric", 75, "GK", "Kosovo", "1998-11-07", "right", 198),
        ("Dara", "O'Shea", 75, "CB", "Ireland", "1999-04-04", "right", 189),
        ("Jacob", "Greaves", 75, "CB", "England", "2000-09-12", "left", 187),
        ("Leif", "Davis", 76, "LB", "England", "1999-12-28", "left", 166),
        ("Axel", "Tuanzebe", 74, "CB", "DR Congo", "1997-11-14", "right", 186),
        ("Sam", "Morsy", 74, "CDM", "Egypt", "1991-09-10", "right", 175),
        ("Kalvin", "Phillips", 76, "CDM", "England", "1995-12-02", "right", 178),
        ("Omari", "Hutchinson", 75, "RW", "Jamaica", "2003-10-30", "left", 174),
        ("Liam", "Delap", 79, "ST", "England", "2003-02-08", "right", 186),
        ("Jack", "Clarke", 75, "LW", "England", "2000-11-23", "right", 181),
        ("Sammie", "Szmodics", 74, "CAM", "Ireland", "1995-09-24", "right", 168),
        ("Wes", "Burns", 73, "RW", "Wales", "1994-11-23", "right", 173),
    ],
    13: [  # Leeds
        ("Illan", "Meslier", 76, "GK", "France", "2000-03-02", "left", 196),
        ("Joe", "Rodon", 77, "CB", "Wales", "1997-10-22", "right", 193),
        ("Pascal", "Struijk", 76, "CB", "Netherlands", "1999-08-11", "left", 190),
        ("Junior", "Firpo", 75, "LB", "Dominican Republic", "1996-08-10", "left", 184),
        ("Jayden", "Bogle", 75, "RB", "England", "2000-07-27", "right", 178),
        ("Ethan", "Ampadu", 78, "CDM", "Wales", "2000-09-14", "right", 182),
        ("Ao", "Tanaka", 76, "CM", "Japan", "1998-09-10", "right", 180),
        ("Brenden", "Aaronson", 76, "CAM", "USA", "2000-10-22", "right", 178),
        ("Wilfried", "Gnonto", 77, "RW", "Italy", "2003-11-05", "right", 170),
        ("Daniel", "James", 76, "RW", "Wales", "1997-11-10", "right", 171),
        ("Joel", "Piroe", 77, "ST", "Netherlands", "1999-08-02", "left", 185),
        ("Patrick", "Bamford", 74, "ST", "England", "1993-09-05", "left", 185),
        ("Manor", "Solomon", 76, "LW", "Israel", "1999-07-24", "right", 170),
    ],
    14: [  # Liverpool
        ("Alisson", "Becker", 89, "GK", "Brazil", "1992-10-02", "right", 193),
        ("Virgil", "van Dijk", 89, "CB", "Netherlands", "1991-07-08", "right", 195),
        ("Ibrahima", "Konate", 85, "CB", "France", "1999-05-25", "right", 194),
        ("Andy", "Robertson", 83, "LB", "Scotland", "1994-03-11", "left", 178),
        ("Trent", "Alexander-Arnold", 86, "RB", "England", "1998-10-07", "right", 175),
        ("Ryan", "Gravenberch", 84, "CM", "Netherlands", "2002-05-16", "right", 190),
        ("Alexis", "Mac Allister", 86, "CM", "Argentina", "1998-12-24", "right", 176),
        ("Dominik", "Szoboszlai", 85, "CAM", "Hungary", "2000-10-25", "right", 186),
        ("Florian", "Wirtz", 89, "CAM", "Germany", "2003-05-03", "right", 177),
        ("Mohamed", "Salah", 89, "RW", "Egypt", "1992-06-15", "left", 175),
        ("Cody", "Gakpo", 84, "LW", "Netherlands", "1999-05-07", "right", 193),
        ("Luis", "Diaz", 85, "LW", "Colombia", "1997-01-13", "right", 180),
        ("Alexander", "Isak", 88, "ST", "Sweden", "1999-09-21", "right", 192),
        ("Darwin", "Nunez", 82, "ST", "Uruguay", "1999-06-24", "right", 187),
        ("Curtis", "Jones", 80, "CM", "England", "2001-01-30", "right", 185),
        ("Conor", "Bradley", 77, "RB", "Northern Ireland", "2003-07-09", "right", 173),
    ],
    15: [  # Man City
        ("Ederson", "Moraes", 87, "GK", "Brazil", "1993-08-17", "left", 188),
        ("Ruben", "Dias", 88, "CB", "Portugal", "1997-05-14", "right", 187),
        ("Josko", "Gvardiol", 86, "CB", "Croatia", "2002-01-23", "left", 185),
        ("John", "Stones", 84, "CB", "England", "1994-05-28", "right", 188),
        ("Rico", "Lewis", 79, "RB", "England", "2004-11-21", "right", 169),
        ("Josko", "Gvardiol", 86, "LB", "Croatia", "2002-01-23", "left", 185),
        ("Rodri", "Hernandez", 90, "CDM", "Spain", "1996-06-22", "right", 191),
        ("Bernardo", "Silva", 87, "CM", "Portugal", "1994-08-10", "left", 173),
        ("Phil", "Foden", 88, "CAM", "England", "2000-05-28", "left", 171),
        ("Jeremy", "Doku", 84, "LW", "Belgium", "2002-05-27", "right", 173),
        ("Savinho", "Savio", 83, "RW", "Brazil", "2004-04-10", "left", 176),
        ("Erling", "Haaland", 91, "ST", "Norway", "2000-07-21", "left", 195),
        ("Omar", "Marmoush", 84, "ST", "Egypt", "1999-02-07", "right", 177),
        ("Nico", "Gonzalez", 81, "CM", "Argentina", "2002-01-06", "left", 186),
        ("Mateo", "Kovacic", 82, "CM", "Croatia", "1994-05-06", "right", 177),
        ("Ilkay", "Gundogan", 82, "CM", "Germany", "1990-10-24", "right", 180),
    ],
    16: [  # Man Utd
        ("Andre", "Onana", 82, "GK", "Cameroon", "1996-04-02", "right", 190),
        ("Lisandro", "Martinez", 84, "CB", "Argentina", "1998-01-18", "left", 175),
        ("Matthijs", "de Ligt", 84, "CB", "Netherlands", "1999-08-12", "right", 187),
        ("Leny", "Yoro", 80, "CB", "France", "2005-11-13", "right", 190),
        ("Diogo", "Dalot", 80, "RB", "Portugal", "1999-03-18", "right", 183),
        ("Noussair", "Mazraoui", 80, "RB", "Morocco", "1997-11-14", "right", 183),
        ("Patrick", "Dorgu", 76, "LB", "Denmark", "2004-10-26", "left", 185),
        ("Bruno", "Fernandes", 87, "CAM", "Portugal", "1994-09-08", "right", 179),
        ("Kobbie", "Mainoo", 81, "CM", "England", "2005-04-19", "right", 180),
        ("Manuel", "Ugarte", 80, "CDM", "Uruguay", "2001-04-11", "right", 182),
        ("Amad", "Diallo", 81, "RW", "Ivory Coast", "2002-07-11", "left", 173),
        ("Bryan", "Mbeumo", 84, "RW", "Cameroon", "1999-08-07", "left", 171),
        ("Matheus", "Cunha", 83, "ST", "Brazil", "1999-05-27", "right", 183),
        ("Benjamin", "Sesko", 82, "ST", "Slovenia", "2003-05-31", "right", 195),
        ("Alejandro", "Garnacho", 81, "LW", "Argentina", "2004-07-01", "right", 180),
        ("Casemiro", "Casemiro", 81, "CDM", "Brazil", "1992-02-23", "right", 185),
    ],
    17: [  # Newcastle
        ("Nick", "Pope", 82, "GK", "England", "1992-04-19", "right", 191),
        ("Sven", "Botman", 82, "CB", "Netherlands", "2000-01-12", "left", 193),
        ("Dan", "Burn", 78, "CB", "England", "1992-05-09", "left", 201),
        ("Tino", "Livramento", 80, "RB", "England", "2002-11-12", "right", 182),
        ("Lewis", "Hall", 78, "LB", "England", "2004-09-08", "left", 179),
        ("Bruno", "Guimaraes", 86, "CM", "Brazil", "1997-11-16", "right", 182),
        ("Sandro", "Tonali", 84, "CM", "Italy", "2000-05-08", "right", 181),
        ("Joelinton", "Joelinton", 81, "CM", "Brazil", "1996-08-14", "right", 186),
        ("Anthony", "Gordon", 83, "LW", "England", "2001-02-24", "right", 183),
        ("Jacob", "Murphy", 78, "RW", "England", "1995-02-24", "right", 173),
        ("Alexander", "Isak", 88, "ST", "Sweden", "1999-09-21", "right", 192),
        ("Harvey", "Barnes", 79, "LW", "England", "1997-12-09", "right", 174),
        ("Fabian", "Schar", 78, "CB", "Switzerland", "1991-12-20", "right", 186),
        ("Lewis", "Miley", 75, "CM", "England", "2006-05-01", "right", 185),
    ],
    18: [  # Nottingham Forest
        ("Matz", "Sels", 81, "GK", "Belgium", "1992-02-26", "right", 188),
        ("Murillo", "Murillo", 81, "CB", "Brazil", "2002-07-04", "left", 184),
        ("Nikola", "Milenkovic", 80, "CB", "Serbia", "1997-10-12", "right", 195),
        ("Ola", "Aina", 78, "RB", "Nigeria", "1996-10-08", "right", 184),
        ("Neco", "Williams", 76, "LB", "Wales", "2001-04-13", "right", 177),
        ("Morgan", "Gibbs-White", 82, "CAM", "England", "2000-01-27", "right", 171),
        ("Elliot", "Anderson", 78, "CM", "England", "2002-11-06", "right", 179),
        ("Ibrahim", "Sangare", 78, "CDM", "Ivory Coast", "1997-12-02", "right", 191),
        ("Callum", "Hudson-Odoi", 79, "LW", "England", "2000-11-07", "right", 182),
        ("Anthony", "Elanga", 78, "RW", "Sweden", "2002-04-27", "right", 178),
        ("Chris", "Wood", 80, "ST", "New Zealand", "1991-12-07", "right", 191),
        ("Taiwo", "Awoniyi", 76, "ST", "Nigeria", "1997-08-12", "right", 183),
        ("Nicolas", "Dominguez", 76, "CM", "Argentina", "1998-06-29", "right", 179),
    ],
    19: [  # Sunderland
        ("Anthony", "Patterson", 74, "GK", "England", "2000-05-10", "right", 189),
        ("Dan", "Ballard", 74, "CB", "Northern Ireland", "1999-09-22", "right", 187),
        ("Trai", "Hume", 74, "RB", "Northern Ireland", "2002-03-18", "right", 180),
        ("Dennis", "Cirkin", 73, "LB", "England", "2002-03-06", "left", 182),
        ("Dan", "Neil", 74, "CM", "England", "2001-11-06", "right", 176),
        ("Jobe", "Bellingham", 76, "CM", "England", "2005-09-23", "right", 191),
        ("Romaine", "Mundle", 73, "LW", "England", "2003-04-24", "right", 178),
        ("Eliezer", "Mayenda", 74, "ST", "Spain", "2005-05-08", "right", 180),
        ("Wilson", "Isidor", 74, "ST", "France", "2000-08-27", "right", 186),
        ("Patrick", "Roberts", 74, "RW", "England", "1997-02-05", "left", 167),
        ("Chris", "Rigg", 72, "CAM", "England", "2007-06-18", "right", 177),
        ("Luke", "O'Nien", 72, "CB", "England", "1994-11-21", "right", 174),
    ],
    20: [  # Spurs
        ("Guglielmo", "Vicario", 84, "GK", "Italy", "1996-10-07", "right", 194),
        ("Cristian", "Romero", 85, "CB", "Argentina", "1998-04-27", "right", 185),
        ("Micky", "van de Ven", 84, "CB", "Netherlands", "2001-04-19", "left", 193),
        ("Pedro", "Porro", 82, "RB", "Spain", "1999-09-13", "right", 173),
        ("Destiny", "Udogie", 81, "LB", "Italy", "2002-11-28", "left", 188),
        ("Yves", "Bissouma", 79, "CDM", "Mali", "1996-08-30", "right", 182),
        ("Pape", "Matar Sarr", 80, "CM", "Senegal", "2002-09-14", "right", 185),
        ("James", "Maddison", 83, "CAM", "England", "1996-11-23", "right", 175),
        ("Dejan", "Kulusevski", 83, "RW", "Sweden", "2000-04-25", "left", 186),
        ("Brennan", "Johnson", 80, "RW", "Wales", "2001-05-23", "right", 179),
        ("Son", "Heung-min", 86, "LW", "South Korea", "1992-07-08", "right", 183),
        ("Dominic", "Solanke", 81, "ST", "England", "1997-09-14", "right", 187),
        ("Xavi", "Simons", 84, "CAM", "Netherlands", "2003-04-21", "right", 179),
        ("Archie", "Gray", 76, "CM", "England", "2006-03-12", "right", 187),
        ("Rodrigo", "Bentancur", 80, "CM", "Uruguay", "1997-06-25", "right", 187),
    ],
}

PL_CLUBS = [
    (1, "Arsenal", "ARS", "Emirates Stadium", 88, 145_000_000),
    (2, "Aston Villa", "AVL", "Villa Park", 82, 70_000_000),
    (3, "Bournemouth", "BOU", "Vitality Stadium", 76, 35_000_000),
    (4, "Brentford", "BRE", "Gtech Community Stadium", 77, 32_000_000),
    (5, "Brighton & Hove Albion", "BHA", "Amex Stadium", 79, 48_000_000),
    (6, "Chelsea", "CHE", "Stamford Bridge", 85, 120_000_000),
    (7, "Coventry City", "COV", "CBS Arena", 70, 18_000_000),
    (8, "Crystal Palace", "CRY", "Selhurst Park", 78, 40_000_000),
    (9, "Everton", "EVE", "Hill Dickinson Stadium", 76, 28_000_000),
    (10, "Fulham", "FUL", "Craven Cottage", 76, 30_000_000),
    (11, "Hull City", "HUL", "MKM Stadium", 69, 16_000_000),
    (12, "Ipswich Town", "IPS", "Portman Road", 72, 20_000_000),
    (13, "Leeds United", "LEE", "Elland Road", 75, 28_000_000),
    (14, "Liverpool", "LIV", "Anfield", 90, 130_000_000),
    (15, "Manchester City", "MCI", "Etihad Stadium", 92, 160_000_000),
    (16, "Manchester United", "MUN", "Old Trafford", 84, 110_000_000),
    (17, "Newcastle United", "NEW", "St James' Park", 83, 85_000_000),
    (18, "Nottingham Forest", "NFO", "City Ground", 78, 42_000_000),
    (19, "Sunderland", "SUN", "Stadium of Light", 73, 22_000_000),
    (20, "Tottenham Hotspur", "TOT", "Tottenham Hotspur Stadium", 84, 95_000_000),
]

LA_LIGA = [
    (21, "Real Madrid", "RMA", "Santiago Bernabeu", 93),
    (22, "Barcelona", "BAR", "Spotify Camp Nou", 92),
    (23, "Atletico Madrid", "ATM", "Riyadh Air Metropolitano", 86),
    (24, "Athletic Club", "ATH", "San Mames", 80),
    (25, "Real Sociedad", "RSO", "Reale Arena", 79),
    (26, "Villarreal", "VIL", "Estadio de la Ceramica", 80),
    (27, "Real Betis", "BET", "La Cartuja", 78),
    (28, "Sevilla", "SEV", "Ramon Sanchez-Pizjuan", 77),
    (29, "Valencia", "VAL", "Mestalla", 75),
    (30, "Celta Vigo", "CEL", "Balaidos", 75),
    (31, "Osasuna", "OSA", "El Sadar", 74),
    (32, "Rayo Vallecano", "RAY", "Vallecas", 73),
    (33, "Getafe", "GET", "Coliseum", 73),
    (34, "Espanyol", "ESP", "RCDE Stadium", 73),
    (35, "Alaves", "ALA", "Mendizorrotza", 72),
    (36, "Levante", "LEV", "Ciutat de Valencia", 71),
    (37, "Elche", "ELC", "Martinez Valero", 70),
    (38, "Deportivo La Coruna", "DEP", "Riazor", 71),
    (39, "Racing Santander", "RAC", "El Sardinero", 70),
    (40, "Malaga", "MAL", "La Rosaleda", 70),
]

SERIE_A = [
    (41, "Inter", "INT", "San Siro", 88),
    (42, "Napoli", "NAP", "Diego Armando Maradona", 86),
    (43, "AC Milan", "MIL", "San Siro", 85),
    (44, "Juventus", "JUV", "Allianz Stadium", 84),
    (45, "Atalanta", "ATA", "Gewiss Stadium", 83),
    (46, "Roma", "ROM", "Stadio Olimpico", 82),
    (47, "Lazio", "LAZ", "Stadio Olimpico", 80),
    (48, "Fiorentina", "FIO", "Artemio Franchi", 79),
    (49, "Bologna", "BOL", "Renato Dall'Ara", 78),
    (50, "Como", "COM", "Giuseppe Sinigaglia", 76),
    (51, "Torino", "TOR", "Olimpico Grande Torino", 76),
    (52, "Udinese", "UDI", "Bluenergy Stadium", 74),
    (53, "Genoa", "GEN", "Luigi Ferraris", 73),
    (54, "Sassuolo", "SAS", "Mapei Stadium", 73),
    (55, "Cagliari", "CAG", "Unipol Domus", 72),
    (56, "Parma", "PAR", "Ennio Tardini", 72),
    (57, "Lecce", "LEC", "Via del Mare", 71),
    (58, "Venezia", "VEN", "Pier Luigi Penzo", 70),
    (59, "Frosinone", "FRO", "Benito Stirpe", 69),
    (60, "Monza", "MON", "U-Power Stadium", 70),
]

BUNDES = [
    (61, "Bayern Munich", "BAY", "Allianz Arena", 93),
    (62, "Borussia Dortmund", "BVB", "Signal Iduna Park", 86),
    (63, "Bayer Leverkusen", "LEV", "BayArena", 85),
    (64, "RB Leipzig", "RBL", "Red Bull Arena", 83),
    (65, "VfB Stuttgart", "STU", "MHP Arena", 80),
    (66, "Eintracht Frankfurt", "SGE", "Deutsche Bank Park", 80),
    (67, "Borussia Monchengladbach", "BMG", "Borussia-Park", 77),
    (68, "SC Freiburg", "SCF", "Europa-Park Stadion", 76),
    (69, "Werder Bremen", "SVW", "Weserstadion", 75),
    (70, "TSG Hoffenheim", "TSG", "PreZero Arena", 75),
    (71, "1. FC Koln", "KOE", "RheinEnergieStadion", 74),
    (72, "1. FSV Mainz 05", "M05", "Mewa Arena", 74),
    (73, "FC Augsburg", "FCA", "WWK Arena", 73),
    (74, "Union Berlin", "FCU", "Stadion An der Alten Forsterei", 73),
    (75, "Hamburger SV", "HSV", "Volksparkstadion", 74),
    (76, "Schalke 04", "S04", "Veltins-Arena", 73),
    (77, "SC Paderborn", "SCP", "Home Deluxe Arena", 70),
    (78, "SV Elversberg", "ELV", "Waldstadion an der Kaiserlinde", 69),
]

LIGUE1 = [
    (79, "Paris Saint-Germain", "PSG", "Parc des Princes", 93),
    (80, "Marseille", "OM", "Orange Velodrome", 84),
    (81, "Monaco", "ASM", "Stade Louis II", 83),
    (82, "Lille", "LIL", "Stade Pierre-Mauroy", 82),
    (83, "Lyon", "OL", "Groupama Stadium", 81),
    (84, "Lens", "RCL", "Stade Bollaert-Delelis", 80),
    (85, "Nice", "NIC", "Allianz Riviera", 79),
    (86, "Rennes", "REN", "Roazhon Park", 78),
    (87, "Strasbourg", "RCS", "Stade de la Meinau", 77),
    (88, "Brest", "SBR", "Stade Francis-Le Ble", 75),
    (89, "Toulouse", "TFC", "Stadium de Toulouse", 74),
    (90, "Lorient", "FCL", "Stade du Moustoir", 73),
    (91, "Paris FC", "PFC", "Stade Jean-Bouin", 73),
    (92, "Le Havre", "HAC", "Stade Oceane", 72),
    (93, "Angers", "ANG", "Stade Raymond-Kopa", 71),
    (94, "Auxerre", "AJA", "Stade Abbe-Deschamps", 71),
    (95, "Troyes", "EST", "Stade de l'Aube", 70),
    (96, "Le Mans", "LEM", "Stade Marie-Marvingt", 69),
]

EGYPT = [
    (97, "Al Ahly", "AHL", "Cairo International Stadium", 82),
    (98, "Zamalek", "ZAM", "Cairo International Stadium", 78),
    (99, "Pyramids", "PYR", "30 June Stadium", 77),
    (100, "Al Masry", "MAS", "Borg El Arab Stadium", 73),
    (101, "Ceramica Cleopatra", "CLE", "Osman Ahmed Osman Stadium", 72),
    (102, "National Bank", "NBE", "Petrosport Stadium", 71),
    (103, "Petrojet", "PET", "Cairo Military Sports Complex", 70),
    (104, "Zed FC", "ZED", "Cairo International Stadium", 70),
    (105, "ENPPI", "ENP", "Petrosport Stadium", 70),
    (106, "Smouha", "SMO", "Alexandria Stadium", 69),
    (107, "El Gouna", "GOU", "El Gouna Stadium", 68),
    (108, "Ismaily", "ISM", "Ismailia Stadium", 69),
    (109, "Ghazl El Mahalla", "GMH", "El Mahalla Stadium", 67),
    (110, "Haras El Hodoud", "HAR", "Haras El Hodoud Stadium", 67),
    (111, "Pharco", "PHA", "Borg El Arab Stadium", 68),
    (112, "Modern Sport", "MOD", "Al Salam Stadium", 69),
]

ZAMBIA = [
    (113, "Power Dynamos", "POW", "Arthur Davies Stadium", 74),
    (114, "Red Arrows", "ARR", "Nkoloma Stadium", 73),
    (115, "ZESCO United", "ZES", "Levy Mwanawasa Stadium", 73),
    (116, "Nkana", "NKA", "Nkana Stadium", 72),
    (117, "Zanaco", "ZAN", "Sunset Stadium", 71),
    (118, "Kabwe Warriors", "KAB", "Godfrey Chitalu Stadium", 70),
    (119, "Nchanga Rangers", "NCH", "Nchanga Stadium", 70),
    (120, "Green Eagles", "GEA", "Choma Independence Stadium", 69),
    (121, "Mufulira Wanderers", "MUW", "Shinde Stadium", 69),
    (122, "Maestro United", "MUZ", "Nakambala Stadium", 69),
    (123, "Green Buffaloes", "BUF", "Woodlands Stadium", 68),
    (124, "NAPSA Stars", "NAP", "Woodlands Stadium", 67),
    (125, "Konkola Blades", "KON", "Konkola Stadium", 67),
    (126, "Kansanshi Dynamos", "KAN", "Kansanshi Stadium", 66),
    (127, "Nkwazi", "NKW", "Edwin Imboela Stadium", 66),
    (128, "Mutondo Stars", "MUT", "Arthur Davies Stadium", 65),
]
SA_PSL = [
    (129, "Orlando Pirates", "PIR", "Orlando Stadium", 78),
    (130, "Mamelodi Sundowns", "SUN", "Loftus Versfeld", 80),
    (131, "Kaizer Chiefs", "CHI", "FNB Stadium", 76),
    (132, "AmaZulu", "AMZ", "Moses Mabhida Stadium", 72),
    (133, "Sekhukhune United", "SEK", "Peter Mokaba Stadium", 71),
    (134, "Golden Arrows", "GAR", "King Zwelithini Stadium", 70),
    (135, "Stellenbosch", "STE", "Danie Craven Stadium", 70),
    (136, "TS Galaxy", "TSG", "Mbombela Stadium", 69),
    (137, "Durban City", "DUR", "Chatsworth Stadium", 69),
    (138, "Polokwane City", "POL", "Peter Mokaba Stadium", 68),
    (139, "Richards Bay", "RCB", "Richards Bay Stadium", 67),
    (140, "Chippa United", "CHP", "Buffalo City Stadium", 67),
    (141, "Siwelele", "SIW", "Dr Petrus Molemela Stadium", 66),
    (142, "Marumo Gallants", "MAR", "Dr Petrus Molemela Stadium", 66),
    (143, "Milford", "MIL", "Chatsworth Stadium", 65),
    (144, "Kruger United", "KRU", "Mbombela Stadium", 64),
]
BOTOLA = [
    (145, "Wydad AC", "WAC", "Mohammed V Stadium", 77),
    (146, "Raja CA", "RCA", "Mohammed V Stadium", 76),
    (147, "AS FAR", "FAR", "Prince Moulay Abdellah Stadium", 75),
    (148, "RS Berkane", "RSB", "Berkane Municipal Stadium", 74),
    (149, "MAS Fez", "MAS", "Fez Stadium", 73),
    (150, "FUS Rabat", "FUS", "Moulay Hassan Stadium", 71),
    (151, "IR Tanger", "IRT", "Ibn Batouta Stadium", 70),
    (152, "Hassania Agadir", "HUS", "Adrar Stadium", 69),
    (153, "Difaâ El Jadida", "DHJ", "Ben M'Hamed El Abdi Stadium", 68),
    (154, "KAC Marrakech", "KAC", "Marrakesh Stadium", 68),
    (155, "COD Meknès", "COD", "Honneur Stadium", 67),
    (156, "RCA Zemamra", "ZEM", "Ahmed Choukri Stadium", 66),
    (157, "UTS Rabat", "UTS", "Al Medina Stadium", 66),
    (158, "Olympique Dcheira", "ODC", "Adrar Stadium", 65),
    (159, "US Yacoub El Mansour", "USY", "Rabat Olympic Stadium", 65),
    (160, "OC Safi", "OCS", "El Massira Stadium", 64),
]
NPFL = [
    (161, "Enyimba", "ENY", "Enyimba International Stadium", 73),
    (162, "Rangers International", "ENU", "Nnamdi Azikiwe Stadium", 72),
    (163, "Remo Stars", "REM", "Remo Stars Stadium", 72),
    (164, "Rivers United", "RIV", "Yakubu Gowon Stadium", 71),
    (165, "Kano Pillars", "KANP", "Sani Abacha Stadium", 70),
    (166, "Shooting Stars", "3SC", "Lekan Salami Stadium", 69),
    (167, "Plateau United", "PLA", "Rwang Pam Stadium", 69),
    (168, "Akwa United", "AKW", "Godswill Akpabio Stadium", 68),
    (169, "Bendel Insurance", "BEN", "Samuel Ogbemudia Stadium", 68),
    (170, "Kwara United", "KWA", "Ilorin Township Stadium", 67),
    (171, "Heartland", "HEA", "Dan Anyiam Stadium", 67),
    (172, "Sunshine Stars", "SUNN", "Akure Township Stadium", 66),
    (173, "Lobi Stars", "LOB", "Aper Aku Stadium", 66),
    (174, "Niger Tornadoes", "NIG", "Minna Township Stadium", 65),
    (175, "Abia Warriors", "ABI", "Umuahia Township Stadium", 65),
    (176, "Katsina United", "KAT", "Muhammadu Dikko Stadium", 64),
]
GHANA = [
    (177, "Asante Kotoko", "KOT", "Baba Yara Stadium", 73),
    (178, "Accra Hearts of Oak", "HEA", "Accra Sports Stadium", 72),
    (179, "Medeama", "MED", "TNA Park", 70),
    (180, "Bechem United", "BEC", "Nana Gyeabour Stadium", 69),
    (181, "Aduana Stars", "ADU", "Agyeman Badu Stadium", 69),
    (182, "Dreams FC", "DRE", "Dawu Park", 68),
    (183, "Samartex", "SAM", "Samartex Park", 68),
    (184, "Berekum Chelsea", "BER", "Berekum Sports Stadium", 67),
    (185, "Great Olympics", "OLY", "Accra Sports Stadium", 67),
    (186, "Legon Cities", "LEG", "El Wak Stadium", 66),
    (187, "Karela United", "KAR", "Crosby Awuah Memorial Park", 66),
    (188, "Bibiani Gold Stars", "BIB", "Dun's Park", 65),
    (189, "Nations FC", "NAT", "Dr Kwame Kyei Sports Complex", 65),
    (190, "Nsoatreman", "NSO", "Nana Agyemang Stadium", 64),
    (191, "Vision FC", "VIS", "El Wak Stadium", 64),
    (192, "Young Apostles", "YAP", "Tema Sports Stadium", 63),
]
TUNISIA = [
    (193, "Espérance de Tunis", "EST", "Hammadi Agrebi Stadium", 78),
    (194, "Étoile du Sahel", "ESS", "Olympique de Sousse", 75),
    (195, "Club Africain", "CA", "Hammadi Agrebi Stadium", 74),
    (196, "CS Sfaxien", "CSS", "Taieb Mhiri Stadium", 73),
    (197, "US Monastir", "USM", "Mustapha Ben Jannet Stadium", 71),
    (198, "Stade Tunisien", "ST", "Chedly Zouiten Stadium", 69),
    (199, "CA Bizertin", "CAB", "15 October Stadium", 68),
    (200, "US Ben Guerdane", "USBG", "7 March Stadium", 67),
    (201, "Olympique Béja", "OB", "Boujemaa Kmiti Stadium", 66),
    (202, "ES Métlaoui", "ESM", "Metlaoui Municipal Stadium", 65),
    (203, "AS Soliman", "ASS", "Soliman Municipal Stadium", 65),
    (204, "AS Gabès", "ASG", "Gabès Municipal Stadium", 64),
    (205, "JS El Omrane", "JSO", "Chedly Zouiten Stadium", 64),
    (206, "ES Zarzis", "ESZ", "Zarzis Municipal Stadium", 63),
    (207, "EGS Gafsa", "EGS", "Gafsa Olympic Stadium", 63),
    (208, "US Tataouine", "UST", "Tataouine Municipal Stadium", 62),
]

ERED = [
    (209, "PSV", "PSV", "Philips Stadion", 84),
    (210, "Ajax", "AJA", "Johan Cruijff Arena", 83),
    (211, "Feyenoord", "FEY", "De Kuip", 82),
    (212, "AZ", "AZ", "AFAS Stadion", 78),
    (213, "Twente", "TWE", "De Grolsch Veste", 75),
    (214, "Utrecht", "UTR", "Stadion Galgenwaard", 74),
    (215, "Go Ahead Eagles", "GAE", "De Adelaarshorst", 72),
    (216, "NEC", "NEC", "Goffertstadion", 71),
    (217, "Groningen", "GRO", "Euroborg", 70),
    (218, "Heerenveen", "HEE", "Abe Lenstra Stadion", 70),
    (219, "Sparta Rotterdam", "SPA", "Sparta Stadion", 69),
    (220, "Fortuna Sittard", "FOR", "Fortuna Sittard Stadion", 68),
    (221, "Excelsior", "EXC", "Woudestein", 67),
    (222, "PEC Zwolle", "ZWO", "MAC³PARK Stadion", 67),
    (223, "Telstar", "TEL", "BUKO Stadion", 65),
    (224, "ADO Den Haag", "ADO", "Bingoal Stadion", 68),
    (225, "Willem II", "WIL", "Koning Willem II Stadion", 67),
    (226, "Cambuur", "CAM", "Kooi Stadion", 66),
]
PORT = [
    (227, "Benfica", "BEN", "Estádio da Luz", 84),
    (228, "Porto", "POR", "Estádio do Dragão", 83),
    (229, "Sporting CP", "SCP", "José Alvalade", 84),
    (230, "Braga", "BRA", "Estádio Municipal de Braga", 76),
    (231, "Vitória Guimarães", "VGU", "D. Afonso Henriques", 73),
    (232, "Famalicão", "FAM", "Estádio Municipal 22 de Junho", 70),
    (233, "Moreirense", "MOR", "Parque de Jogos Comendador", 69),
    (234, "Casa Pia", "CAS", "Estádio Pina Manique", 68),
    (235, "Rio Ave", "RAV", "Estádio dos Arcos", 68),
    (236, "Estoril", "EST", "António Coimbra da Mota", 67),
    (237, "Arouca", "ARO", "Estádio Municipal de Arouca", 66),
    (238, "Gil Vicente", "GIL", "Estádio Cidade de Barcelos", 66),
    (239, "Nacional", "NAC", "Estádio da Madeira", 65),
    (240, "Estrela Amadora", "ESTA", "Estádio José Gomes", 65),
    (241, "AVS", "AVS", "Estádio do CD Aves", 64),
    (242, "Santa Clara", "SCL", "Estádio de São Miguel", 67),
    (243, "Alverca", "ALV", "Complexo Desportivo", 63),
    (244, "Tondela", "TON", "Estádio João Cardoso", 63),
]
BELG = [
    (245, "Club Brugge", "CLU", "Jan Breydel Stadium", 80),
    (246, "Union SG", "USG", "Joseph Marien Stadium", 78),
    (247, "Anderlecht", "AND", "Lotto Park", 77),
    (248, "Genk", "GNK", "Cegeka Arena", 76),
    (249, "Gent", "GNT", "Planet Group Arena", 74),
    (250, "Antwerp", "ANT", "Bosuilstadion", 73),
    (251, "Standard Liège", "STD", "Maurice Dufrasne", 72),
    (252, "Mechelen", "MEC", "Achter de Kazerne", 70),
    (253, "Charleroi", "CHA", "Stade du Pays de Charleroi", 70),
    (254, "Westerlo", "WES", "Het Kuipje", 68),
    (255, "OH Leuven", "OHL", "Den Dreef", 67),
    (256, "Cercle Brugge", "CER", "Jan Breydel Stadium", 67),
    (257, "Sint-Truiden", "STV", "Stayen", 66),
    (258, "Kortrijk", "KVK", "Guldensporen Stadion", 65),
    (259, "Zulte Waregem", "ZUL", "Regenboogstadion", 65),
    (260, "Beveren", "BEV", "Freethiel Stadion", 64),
]

STARS = {
    21: [("Thibaut", "Courtois", 89, "GK", "Belgium"), ("Antonio", "Rudiger", 86, "CB", "Germany"),
         ("Jude", "Bellingham", 90, "CAM", "England"), ("Vinicius", "Junior", 90, "LW", "Brazil"),
         ("Kylian", "Mbappe", 91, "ST", "France"), ("Federico", "Valverde", 88, "CM", "Uruguay"),
         ("Rodrygo", "Goes", 86, "RW", "Brazil"), ("Eduardo", "Camavinga", 84, "CM", "France")],
    22: [("Marc-Andre", "ter Stegen", 87, "GK", "Germany"), ("Pau", "Cubarsi", 84, "CB", "Spain"),
         ("Pedri", "Gonzalez", 88, "CM", "Spain"), ("Lamine", "Yamal", 90, "RW", "Spain"),
         ("Raphinha", "Dias", 87, "LW", "Brazil"), ("Robert", "Lewandowski", 86, "ST", "Poland"),
         ("Frenkie", "de Jong", 86, "CM", "Netherlands"), ("Gavi", "Paez", 83, "CM", "Spain")],
    23: [("Jan", "Oblak", 88, "GK", "Slovenia"), ("Julian", "Alvarez", 87, "ST", "Argentina"),
         ("Antoine", "Griezmann", 84, "CAM", "France"), ("Rodrigo", "De Paul", 82, "CM", "Argentina")],
    41: [("Yann", "Sommer", 85, "GK", "Switzerland"), ("Lautaro", "Martinez", 88, "ST", "Argentina"),
         ("Nicolo", "Barella", 87, "CM", "Italy"), ("Marcus", "Thuram", 84, "ST", "France")],
    42: [("Khvicha", "Kvaratskhelia", 87, "LW", "Georgia"), ("Scott", "McTominay", 83, "CM", "Scotland")],
    43: [("Mike", "Maignan", 87, "GK", "France"), ("Rafael", "Leao", 86, "LW", "Portugal"),
         ("Christian", "Pulisic", 84, "RW", "USA")],
    44: [("Kenan", "Yildiz", 82, "LW", "Turkey"), ("Dusan", "Vlahovic", 83, "ST", "Serbia")],
    61: [("Manuel", "Neuer", 86, "GK", "Germany"), ("Harry", "Kane", 90, "ST", "England"),
         ("Jamal", "Musiala", 89, "CAM", "Germany"), ("Michael", "Olise", 86, "RW", "France"),
         ("Alphonso", "Davies", 85, "LB", "Canada"), ("Joshua", "Kimmich", 87, "CM", "Germany")],
    62: [("Serhou", "Guirassy", 85, "ST", "Guinea"), ("Julian", "Brandt", 83, "CAM", "Germany")],
}


def fill_squad(club_id: int, rep: int, nation: str, start_id: int, existing: list) -> list:
    rng = random.Random(club_id * 99 + 7)
    have = {r[3] if len(r) > 3 else "" for r in existing}
    need = [("GK", 2), ("CB", 3), ("LB", 2), ("RB", 2), ("CDM", 2), ("CM", 3), ("CAM", 1), ("LW", 2), ("RW", 2), ("ST", 2)]
    out = []
    pid = start_id
    counts = {}
    for p in existing:
        counts[p[3]] = counts.get(p[3], 0) + 1
    for pos, n in need:
        while counts.get(pos, 0) < n:
            ovr = max(62, min(84, int(rng.gauss(rep - 12, 4))))
            first, last = rng.choice(FIRST), rng.choice(LAST)
            year = rng.randint(1994, 2007)
            out.append((first, last, ovr, pos, nation, f"{year}-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}", rng.choice(["right", "left"]), rng.randint(174, 196)))
            counts[pos] = counts.get(pos, 0) + 1
            pid += 1
    return out


def round_robin(club_ids: list[int], league_id: int, start: str, fid0: int):
    """Double RR, one matchday ≈ midweek/weekend spacing from start date."""
    from datetime import date, timedelta
    y, m, d = (int(x) for x in start.split("-"))
    day0 = date(y, m, d)
    ids = list(club_ids)
    if len(ids) % 2:
        ids.append(-1)
    n = len(ids)
    rounds = []
    rot = ids[:]
    for _ in range(n - 1):
        pairs = []
        for i in range(n // 2):
            a, b = rot[i], rot[-1 - i]
            if a != -1 and b != -1:
                pairs.append((a, b))
        rounds.append(pairs)
        rot = [rot[0]] + [rot[-1]] + rot[1:-1]
    fixtures = []
    fid = fid0
    md = 0
    for extra in (False, True):
        for pairs in rounds:
            md += 1
            dt = day0 + timedelta(days=(md - 1) * 7)
            for i, (a, b) in enumerate(pairs):
                flip = ((md + i) % 2 == 1)
                home, away = (b, a) if flip else (a, b)
                if extra:
                    home, away = away, home
                fixtures.append({
                    "id": fid,
                    "league_id": league_id,
                    "week": md,
                    "date": dt.isoformat(),
                    "home_id": home,
                    "away_id": away,
                    "played": False,
                })
                fid += 1
    return fixtures, fid


def main():
    clubs = []
    stadiums = []
    players = []
    pid = 1

    def add_club(cid, name, short, stad, rep, budget, league_id, nation):
        clubs.append({
            "id": cid, "name": name, "short": short, "league_id": league_id,
            "nation": nation, "stadium": stad, "reputation": rep, "budget": budget,
            "academy": max(3, rep // 12), "style": "balanced", "formation": "4-3-3",
        })
        stadiums.append({"id": cid, "name": stad, "club_id": cid})

    for cid, name, short, stad, rep, bud in PL_CLUBS:
        add_club(cid, name, short, stad, rep, bud, 1, "England")
        for row in PL_SQUADS.get(cid, []):
            first, last, ovr, pos, nat, born, foot, h = row
            players.append(P(pid, first, last, ovr, pos, nat, cid, born, foot=foot, h=h))
            pid += 1
        extra = fill_squad(cid, rep, "England", pid, PL_SQUADS.get(cid, []))
        for row in extra:
            first, last, ovr, pos, nat, born, foot, h = row
            players.append(P(pid, first, last, ovr, pos, nat, cid, born, foot=foot, h=h))
            pid += 1

    def pack_league(rows, league_id, nation, default_nat):
        nonlocal pid
        for item in rows:
            cid, name, short, stad, rep = item
            add_club(cid, name, short, stad, rep, int(8_000_000 * (rep / 70)), league_id, nation)
            stars = STARS.get(cid, [])
            built = []
            for s in stars:
                first, last, ovr, pos, nat = s
                year = 2000 - int((ovr - 70) / 3)
                players.append(P(pid, first, last, ovr, pos, nat, cid, bd(year, random.Random(pid))))
                built.append((first, last, ovr, pos, nat))
                pid += 1
            extra = fill_squad(cid, rep, default_nat, pid, [(s[0], s[1], s[2], s[3], s[4]) for s in stars])
            for row in extra:
                first, last, ovr, pos, nat, born, foot, h = row
                players.append(P(pid, first, last, ovr, pos, nat, cid, born, foot=foot, h=h))
                pid += 1

    pack_league(LA_LIGA, 2, "Spain", "Spain")
    pack_league(SERIE_A, 3, "Italy", "Italy")
    pack_league(BUNDES, 4, "Germany", "Germany")
    pack_league(LIGUE1, 5, "France", "France")
    pack_league(EGYPT, 6, "Egypt", "Egypt")
    pack_league(ZAMBIA, 7, "Zambia", "Zambia")
    pack_league(SA_PSL, 8, "South Africa", "South Africa")
    pack_league(BOTOLA, 9, "Morocco", "Morocco")
    pack_league(NPFL, 10, "Nigeria", "Nigeria")
    pack_league(GHANA, 11, "Ghana", "Ghana")
    pack_league(TUNISIA, 12, "Tunisia", "Tunisia")
    pack_league(ERED, 13, "Netherlands", "Netherlands")
    pack_league(PORT, 14, "Portugal", "Portugal")
    pack_league(BELG, 15, "Belgium", "Belgium")

    fixtures = []
    fid = 1
    for lid, cids, start in (
        (1, list(range(1, 21)), "2026-08-21"),
        (2, list(range(21, 41)), "2026-08-15"),
        (3, list(range(41, 61)), "2026-08-22"),
        (4, list(range(61, 79)), "2026-08-28"),
        (5, list(range(79, 97)), "2026-08-21"),
        (6, list(range(97, 113)), "2026-09-11"),
        (7, list(range(113, 129)), "2026-08-22"),
        (8, list(range(129, 145)), "2026-08-15"),
        (9, list(range(145, 161)), "2026-09-12"),
        (10, list(range(161, 177)), "2026-09-07"),
        (11, list(range(177, 193)), "2026-09-14"),
        (12, list(range(193, 209)), "2026-08-16"),
        (13, list(range(209, 227)), "2026-08-07"),
        (14, list(range(227, 245)), "2026-08-09"),
        (15, list(range(245, 261)), "2026-08-01"),
    ):
        fx, fid = round_robin(cids, lid, start, fid)
        fixtures.extend(fx)

    world = {
        "meta": {
            "name": "Gaffer 2026-27",
            "season": "2026-27",
            "season_start_year": 2026,
            "current_date": "2026-08-14",
            "version": "0.1",
            "disclaimer": "Unofficial fan simulation. Squads and ratings estimated from public 2026-27 previews. Not affiliated with any league or club.",
        },
        "leagues": [
            {"id": 1, "name": "Premier League", "nation": "England", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 2, "name": "La Liga", "nation": "Spain", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 3, "name": "Serie A", "nation": "Italy", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 4, "name": "Bundesliga", "nation": "Germany", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 5, "name": "Ligue 1", "nation": "France", "tier": 1, "promoted": 0, "relegated": 2},
            {"id": 6, "name": "Egyptian Premier League", "nation": "Egypt", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 7, "name": "Zambia Super League", "nation": "Zambia", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 8, "name": "South African Premiership", "nation": "South Africa", "tier": 1, "promoted": 0, "relegated": 2},
            {"id": 9, "name": "Botola Pro", "nation": "Morocco", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 10, "name": "NPFL", "nation": "Nigeria", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 11, "name": "Ghana Premier League", "nation": "Ghana", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 12, "name": "Tunisian Ligue 1", "nation": "Tunisia", "tier": 1, "promoted": 0, "relegated": 2},
            {"id": 13, "name": "Eredivisie", "nation": "Netherlands", "tier": 1, "promoted": 0, "relegated": 2},
            {"id": 14, "name": "Primeira Liga", "nation": "Portugal", "tier": 1, "promoted": 0, "relegated": 3},
            {"id": 15, "name": "Belgian Pro League", "nation": "Belgium", "tier": 1, "promoted": 0, "relegated": 2},
        ],
        "clubs": clubs,
        "stadiums": stadiums,
        "players": players,
        "fixtures": fixtures,
        "results": [],
        "news": [],
    }
    OUT.write_text(json.dumps(world), encoding="utf-8")
    print(f"Wrote {OUT} clubs={len(clubs)} players={len(players)} fixtures={len(fixtures)}")


if __name__ == "__main__":
    main()
