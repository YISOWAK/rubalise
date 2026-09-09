"""Batterie de scénarios : on met le solveur à l'épreuve et on mesure comment il réagit.

Un solveur ne s'entraîne pas ; on le teste. Chaque scénario part du jeu SwissPeaks,
change une chose (moins de monde, une compétence qui disparaît, des absents le jour J),
et on note : statut, trous, écarts au plan publié, temps.

Lancer : python solveur/scenarios.py      -> solveur/sortie/scenarios.md
"""
from __future__ import annotations

import copy
import io
import random
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from solveur import charger, resoudre, rapport  # noqa: E402

DATA = ICI.parent / "data"
SORTIE = ICI / "sortie" / "scenarios"


def mesurer(nom, postes, benevoles, trajets, battements, plan_fige=None, heure=None):
    if heure:
        termines = {p["id"] for p in postes if p["fin"] <= heure}
        postes = [p for p in postes if p["id"] not in termines]
        if plan_fige:
            plan_fige = {k: v for k, v in plan_fige.items() if k[1] not in termines}
    t = time.time()
    s, v, statut, relache = resoudre(postes, benevoles, trajets, battements, plan_fige=plan_fige)
    duree = time.time() - t
    dossier = SORTIE / "".join(c if c.isalnum() else "_" for c in nom)[:40]
    with redirect_stdout(io.StringIO()):
        plan = rapport(s, v, statut, relache, postes, benevoles, dossier, plan_fige)
    val = s.Value
    ligne = {
        "scenario": nom, "statut": plan["score"]["statut"] + (" (relâché)" if relache else ""),
        "sans_responsable": len(plan["postes_sans_responsable"]),
        "sous_min": plan["score"]["personnes_sous_minimum"], "creneaux_troues": len(plan["trous"]),
        "sous_ideal": plan["score"]["personnes_sous_ideal"], "temps_s": round(duree, 1),
        "retraits": "", "ajouts": "",
    }
    if plan_fige:
        actuels = {(a["benevole_id"], a["poste_id"]) for a in plan["affectations"]}
        ligne["retraits"] = len(set(plan_fige) - actuels)
        ligne["ajouts"] = len(actuels - set(plan_fige))
    return ligne, plan


def figer(plan, postes, heure=None, absents=()):
    P = {p["id"]: p for p in postes}
    return {(a["benevole_id"], a["poste_id"]): ("en_poste" if heure and P[a["poste_id"]]["debut"] <= heure else "notifie")
            for a in plan["affectations"] if a["benevole_id"] not in absents}


def main():
    postes, benevoles, trajets, battements = charger(DATA)
    rng = random.Random(42)
    lignes = []

    # 0. Référence
    l, plan_base = mesurer("0 référence", postes, benevoles, trajets, battements)
    lignes.append(l)

    # 1. Moins de monde : 55 bénévoles au lieu de 75
    moins = rng.sample(benevoles, 55)
    lignes.append(mesurer("1 55 bénévoles au lieu de 75", postes, moins, trajets, battements)[0])

    # 2. Encore moins : 40
    lignes.append(mesurer("2 40 bénévoles", postes, rng.sample(benevoles, 40), trajets, battements)[0])

    # 3. Plus aucun PSC1
    sans_psc1 = copy.deepcopy(benevoles)
    for b in sans_psc1: b["PSC1_ou_samaritain"] = False
    lignes.append(mesurer("3 aucun PSC1", postes, sans_psc1, trajets, battements)[0])

    # 4. Tout le monde refuse la nuit
    sans_nuit = copy.deepcopy(benevoles)
    for b in sans_nuit: b["accepte_nuit"] = False
    lignes.append(mesurer("4 tout le monde refuse la nuit", postes, sans_nuit, trajets, battements)[0])

    # 5. Deux fois plus de coureurs : effectifs min et idéal x1.5 sur les ravitos et l'arrivée
    gros = copy.deepcopy(postes)
    for p in gros:
        if p["categorie"] in ("ravitaillement", "arrivee", "restauration"):
            p["min"] = round(p["min"] * 1.5); p["ideal"] = round(p["ideal"] * 1.5)
    lignes.append(mesurer("5 course plus grosse (effectifs x1,5)", gros, benevoles, trajets, battements)[0])

    # 6. Jour J, 6h30 : 5 désistements avant le départ (dont un responsable)
    resp = [b["id"] for b in benevoles if b["responsable"]][:1]
    absents = set(resp + [b["id"] for b in rng.sample(benevoles, 6) if b["id"] not in resp][:4])
    h = datetime(2025, 9, 6, 6, 30)
    pf = figer(plan_base, postes, h, absents)
    lignes.append(mesurer("6 jour J 6h30, 5 absents", postes, [b for b in benevoles if b["id"] not in absents], trajets, battements, pf, h)[0])

    # 7. Jour J, 11h : 2 absents (les deux responsables qui viennent accompagnés)
    absents = {"B001", "B011"}
    h = datetime(2025, 9, 6, 11, 0)
    pf = figer(plan_base, postes, h, absents)
    lignes.append(mesurer("7 jour J 11h, 2 responsables absents", postes, [b for b in benevoles if b["id"] not in absents], trajets, battements, pf, h)[0])

    # 8. Jour J, 13h : le dernier coureur a 45 min de retard à Blancsex, les créneaux de l'après-midi y sont prolongés
    retard = copy.deepcopy(postes)
    for p in retard:
        if p["site"] == "Chalet de Blancsex" and p["debut"].hour >= 12:
            p["fin"] += timedelta(minutes=45)
    h = datetime(2025, 9, 6, 13, 0)
    pf = figer(plan_base, retard, h)
    lignes.append(mesurer("8 jour J 13h, Blancsex prolongé de 45 min", retard, benevoles, trajets, battements, pf, h)[0])

    # 9. Jour J, 15h : orage, le directeur ferme Taney après-midi et demande 3 personnes de plus à Grand Pré
    orage = copy.deepcopy(postes)
    for p in orage:
        if p["id"] == "S12": p["min"] = 0; p["ideal"] = 0
        if p["id"] == "S14": p["min"] += 3; p["ideal"] += 3
    h = datetime(2025, 9, 6, 15, 0)
    pf = figer(plan_base, orage, h)
    lignes.append(mesurer("9 jour J 15h, orage : Taney fermé, +3 au Grand Pré", orage, benevoles, trajets, battements, pf, h)[0])

    # Tableau
    cols = ["scenario", "statut", "sans_responsable", "sous_min", "creneaux_troues", "sous_ideal", "retraits", "ajouts", "temps_s"]
    titres = ["Scénario", "Statut", "Sans resp.", "Sous min", "Créneaux troués", "Sous idéal", "Retraits", "Ajouts", "Temps (s)"]
    md = ["| " + " | ".join(titres) + " |", "|" + "---|" * len(cols)]
    for l in lignes:
        md.append("| " + " | ".join(str(l[c]) for c in cols) + " |")
    texte = "# Scénarios du solveur\n\nJeu SwissPeaks Marathon, 50 créneaux, 75 bénévoles sauf mention. Les scénarios 6 à 9 partent du plan de référence publié et mesurent combien de personnes bougent.\n\n" + "\n".join(md) + "\n"
    (ICI / "sortie" / "scenarios.md").write_text(texte, encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    main()
