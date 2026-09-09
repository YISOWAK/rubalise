"""Construire les postes : une fiche de course (JSON, lue dans le roadbook ou corrigée par l'orga)
+ un gabarit (trail.json) -> postes.csv, au format que le solveur lit.

Tout est déterministe. Le gabarit dit ce qu'est un trail ; la fiche dit cette course-là.
Un autre type d'événement = un autre gabarit, même code.

Lancer :
    python outils/construire_postes.py --course data/course_marathon.json --sortie data/postes_construits.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def borne(expr: str, refs: dict) -> datetime:
    """'premier-60' -> refs['premier'] moins 60 min. 'veille 13:00' / 'lendemain 14:00' -> jour relatif."""
    expr = expr.strip()
    if expr.startswith("veille ") or expr.startswith("lendemain "):
        mot, heure = expr.split()
        jour = refs["jour_course"] + timedelta(days=-1 if mot == "veille" else 1)
        h, m = heure.split(":")
        return jour.replace(hour=int(h), minute=int(m))
    for sep in ("+", "-"):
        if sep in expr:
            nom, minutes = expr.split(sep)
            return refs[nom] + timedelta(minutes=int(minutes) * (1 if sep == "+" else -1))
    return refs[expr]


def a_pied(point: dict, gabarit: dict) -> bool:
    texte = (point.get("acces") or "").lower()
    return any(mot in texte for mot in gabarit["acces_a_pied_si"])


def decouper(postes: list[dict], regle: dict) -> list[dict]:
    out = []
    for p in postes:
        duree = int((p["fin"] - p["debut"]).total_seconds() // 60)
        if duree <= regle["max_minutes"]:
            out.append(p)
            continue
        n = math.ceil(duree / regle["cible_minutes"])
        bornes = [p["debut"] + timedelta(minutes=round(duree * k / n / 15) * 15) for k in range(n + 1)]
        for k in range(n):
            q = dict(p)
            q["id"] = f"{p['id']}{'abcdef'[k]}"
            q["nom"] = f"{p['nom']}, créneau {k + 1}/{n}"
            q["debut"] = bornes[k]
            q["fin"] = bornes[k + 1] + timedelta(minutes=regle["chevauchement_minutes"]) if k < n - 1 else p["fin"]
            out.append(q)
    return out


def construire(course: dict, gabarit: dict) -> list[dict]:
    marges = gabarit["marges_minutes"]
    depart = dt(course["depart"]["date_heure"])
    jour = depart.replace(hour=0, minute=0)
    points = course["points_de_passage"]
    arrivee = next((p for p in points if "arrivee" in p["services"]), points[-1])
    dernier_arrivee = dt(arrivee["dernier"])
    postes: list[dict] = []
    n = 0

    def ajouter(cat, nom, site, debut, fin, mini, ideal, resp, comp, origine, notes=""):
        nonlocal n
        n += 1
        postes.append({"id": f"P{n:02d}", "nom": nom, "site": site, "categorie": cat, "debut": debut, "fin": fin,
                       "min": mini, "ideal": ideal, "responsable_requis": resp, "competences": list(comp), "origine": origine, "notes": notes})

    # Fenêtre de chaque point : union avec les autres courses qui y passent
    for p in points:
        premier, dernier = dt(p["premier"]), dt(p["dernier"])
        autres = [a for a in course.get("autres_courses_sur_les_memes_postes", []) if a["poste"] == p["nom"]]
        for a in autres:
            premier, dernier = min(premier, dt(a["premier"])), max(dernier, dt(a["dernier"]))
        refs = {"premier": premier, "dernier": dernier, "barriere": dt(p["barriere"]) if p.get("barriere") else dernier, "jour_course": jour}
        pied = a_pied(p, gabarit)
        note = ("Partagé avec " + ", ".join(a["course"] for a in autres) + ". " if autres else "") + (p.get("acces") or "")
        for service in p["services"]:
            for g in gabarit["par_service"].get(service, []):
                debut = borne(g["debut"], refs) if "debut" in g else premier - timedelta(minutes=marges["avant_premier"])
                fin = borne(g["fin"], refs) if "fin" in g else refs["barriere" if p.get("barriere") else "dernier"] + timedelta(minutes=marges["apres_dernier"])
                if service == "depart" and p["km"] == 0:
                    debut, fin = depart - timedelta(minutes=90), depart + timedelta(minutes=30)
                    if g["categorie"] == "signaleur":
                        debut, fin = depart - timedelta(minutes=30), depart + timedelta(minutes=45)
                comp = list(g["competences"]) + ([gabarit["competence_si_acces_a_pied"]] if pied and g["categorie"] in ("ravitaillement", "pointage", "controle") else [])
                ajouter(g["categorie"], g["nom"].format(lieu=p["nom"]), p["nom"], debut, fin, g["min"], g["ideal"], g["responsable"], comp, "roadbook", note)

    # Postes fixes
    ravitos = [p for p in points if "ravitaillement" in p["services"]]
    premier_a_pied = next((p for p in points if a_pied(p, gabarit)), None)
    sites_fixes = {"arrivee": arrivee["nom"], "premier_ravito": ravitos[0]["nom"] if ravitos else arrivee["nom"],
                   "premier_a_pied": premier_a_pied["nom"] if premier_a_pied else arrivee["nom"]}
    refs = {"depart": depart, "dernier_arrivee": dernier_arrivee, "jour_course": jour}
    for g in gabarit["postes_fixes"]:
        if g.get("si") == "a_pied" and not premier_a_pied:
            continue
        src = g.get("source")
        if src == "retrait_dossards":
            for r in course.get("retrait_dossards", []):
                rr = dict(refs, debut=dt(r["debut"]), fin=dt(r["fin"]))
                ajouter(g["categorie"], g["nom"].format(lieu=r["lieu"]), r["lieu"].split(",")[0], borne(g["debut"], rr), borne(g["fin"], rr), g["min"], g["ideal"], g["responsable"], g["competences"], "roadbook")
        elif src == "navettes_coureurs":
            for nav in course.get("navettes_coureurs", []):
                rr = dict(refs, depart=dt(nav["depart"]))
                lieu = nav["trajet"].split(" vers ")[0].split("(")[0].strip()
                ajouter(g["categorie"], g["nom"].format(lieu=f"{dt(nav['depart']):%a %H:%M}"), lieu, borne(g["debut"], rr), borne(g["fin"], rr), g["min"], g["ideal"], g["responsable"], g["competences"], "roadbook", nav["trajet"])
        elif src == "segments":
            # un serre-file par tronçon entre ravitos, tronçons courts (< 10 km) regroupés avec le suivant
            bornes_seg = [p for p in points if p["km"] == 0] + ravitos + ([arrivee] if arrivee not in ravitos else [])
            bornes_seg = sorted({p["nom"]: p for p in bornes_seg}.values(), key=lambda p: p["km"])
            i = 0
            while i < len(bornes_seg) - 1:
                a, b = bornes_seg[i], bornes_seg[i + 1]
                j = i + 1
                while b["km"] - a["km"] < 10 and j < len(bornes_seg) - 1:
                    j += 1; b = bornes_seg[j]
                seg = f"{a['nom']} vers {b['nom']}"
                debut, fin = dt(a["dernier"]), dt(b["dernier"]) + timedelta(minutes=30)
                ajouter(g["categorie"], g["nom"].format(segment=seg), a["nom"], debut, fin, g["min"], g["ideal"], g["responsable"], g["competences"], "gabarit", "suit le dernier coureur, débalise, remonte au PC")
                i = j
        else:
            site = sites_fixes[g["site"]]
            ajouter(g["categorie"], g["nom"], site, borne(g["debut"], refs), borne(g["fin"], refs), g["min"], g["ideal"], g["responsable"], g["competences"], "gabarit")

    # Les sites doivent porter le nom exact des points de passage (la matrice de trajets s'y réfère).
    connus = [p["nom"] for p in points]
    def normaliser(site: str) -> str:
        mots = {m for m in site.lower().replace("(", " ").replace(")", " ").replace(",", " ").split() if len(m) > 3}
        for nom in connus:
            if mots & {m for m in nom.lower().split() if len(m) > 3}:
                return nom
        return site
    for p in postes:
        p["site"] = normaliser(p["site"])

    postes.sort(key=lambda p: (p["debut"], p["site"]))
    for k, p in enumerate(postes, 1):
        p["id"] = f"P{k:02d}"
    return decouper(postes, gabarit["decoupe"])


def ecrire_csv(postes: list[dict], chemin: Path):
    with open(chemin, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["poste_id", "nom", "site", "categorie", "debut", "fin", "effectif_min", "effectif_ideal", "competences_requises", "chef_de_poste_requis", "notes", "origine"])
        for p in postes:
            w.writerow([p["id"], p["nom"], p["site"], p["categorie"], p["debut"].strftime("%Y-%m-%dT%H:%M:%S"), p["fin"].strftime("%Y-%m-%dT%H:%M:%S"),
                        p["min"], p["ideal"], ",".join(p["competences"]), p["responsable_requis"], p["notes"], p["origine"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--course", required=True)
    ap.add_argument("--gabarit", default=str(RACINE / "gabarits" / "trail.json"))
    ap.add_argument("--sortie", required=True)
    args = ap.parse_args()
    course = json.loads(Path(args.course).read_text(encoding="utf-8"))
    gabarit = json.loads(Path(args.gabarit).read_text(encoding="utf-8"))
    postes = construire(course, gabarit)
    ecrire_csv(postes, Path(args.sortie))
    print(f"{len(postes)} créneaux construits depuis {len(course['points_de_passage'])} points de passage, besoin {sum(p['min'] for p in postes)} (min) à {sum(p['ideal'] for p in postes)} (idéal)")
    for p in postes:
        print(f"  {p['id']:<5} {p['debut']:%a %H:%M}-{p['fin']:%a %H:%M} {p['nom'][:52]:<52} {p['site'][:18]:<18} {p['min']}-{p['ideal']} {'R' if p['responsable_requis'] else ' '} {','.join(p['competences'])}")
    print(f"-> {args.sortie}")


if __name__ == "__main__":
    main()
