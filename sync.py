import os
import hashlib
import datetime as dt

import pronotepy
from pronotepy.ent import educonnect

URL = "https://0590143k.index-education.net/pronote/eleve.html"
JOURS_AVANT = 7
JOURS_APRES = 45


def esc(texte):
    return (
        str(texte)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def fmt(d):
    return d.strftime("%Y%m%dT%H%M%S")


def lecons_vers_ics(lecons):
    lignes = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//pronote-calendrier//FR",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:Emploi du temps",
        "X-WR-TIMEZONE:Europe/Paris",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]
    for l in lecons:
        matiere = l.subject.name if l.subject else "Cours"
        titre = ("ANNULÉ - " if l.canceled else "") + matiere
        uid = hashlib.sha1(f"{l.id}{l.start}".encode()).hexdigest() + "@pronote-calendrier"
        lignes += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{fmt(l.start)}",
            f"DTEND:{fmt(l.end)}",
            f"SUMMARY:{esc(titre)}",
        ]
        if l.classroom:
            lignes.append(f"LOCATION:{esc(l.classroom)}")
        if l.status:
            lignes.append(f"DESCRIPTION:{esc(l.status)}")
        lignes.append("END:VEVENT")
    lignes.append("END:VCALENDAR")
    return "\r\n".join(lignes) + "\r\n"


def main():
    client = pronotepy.Client(
        URL,
        username=os.environ["PRONOTE_USER"],
        password=os.environ["PRONOTE_PASS"],
        ent=educonnect,
    )
    if not client.logged_in:
        raise SystemExit("Connexion à Pronote impossible")

    aujourdhui = dt.date.today()
    lecons = client.lessons(
        aujourdhui - dt.timedelta(days=JOURS_AVANT),
        aujourdhui + dt.timedelta(days=JOURS_APRES),
    )
    lecons = sorted(lecons, key=lambda l: l.start)

    with open("edt.ics", "w", encoding="utf-8", newline="") as f:
        f.write(lecons_vers_ics(lecons))
    print(f"{len(lecons)} cours exportés dans edt.ics")


if __name__ == "__main__":
    main()
