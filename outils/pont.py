"""Pont entre la traduction (sortie du modèle) et le solveur.

Entrée : outils/sortie/benevoles_traduits.json (une entrée par ligne du formulaire)
         data/formulaire_benevoles.csv (pour le nom et le téléphone)
Sortie : data/benevoles_depuis_formulaire.csv, au format que le solveur lit,
         plus la liste des décisions prises et des questions restantes.

Ce que fait le pont, en code pur :
  1. fusionne les doublons (même téléphone) : un seul bénévole, dispos et compétences réunies
  2. retrouve les binômes et les « pas avec » par leur nom, ou pose la question
  3. traduit les champs « inconnu » en hypothèses prudentes, et les note
  4. écrit le CSV pour le solveur

Lancer : python outils/pont.py
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).resolve().parent
AGE_INCONNU = 30          # hypothèse prudente pour le solveur ; le vérificateur alerte si le poste exige d'être majeur
AGE_MINEUR = 17


def normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFKD", texte or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z ]", " ", texte.lower()).strip()


def retrouver(nom_cherche: str, annuaire: dict[str, str], soi: str) -> tuple[str | None, str]:
    """Rend (id trouvé, explication). annuaire : nom normalisé -> id."""
    if not nom_cherche:
        return None, ""
    n = normaliser(nom_cherche)
    exacts = [i for nom, i in annuaire.items() if nom == n and i != soi]
    if len(exacts) == 1:
        return exacts[0], "nom complet"
    mots = n.split()
    candidats = {i for nom, i in annuaire.items() if i != soi and all(m in nom.split() for m in mots)}
    if len(candidats) == 1:
        return candidats.pop(), "prénom seul, une seule personne de ce prénom"
    if not candidats:
        return None, f"« {nom_cherche} » n'est dans aucune ligne du formulaire"
    return None, f"« {nom_cherche} » peut être {len(candidats)} personnes, à préciser"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traduits", default=str(ICI / "sortie" / "benevoles_traduits.json"))
    ap.add_argument("--formulaire", default=str(ICI.parent / "data" / "formulaire_benevoles.csv"))
    ap.add_argument("--sortie", default=str(ICI.parent / "data" / "benevoles_depuis_formulaire.csv"))
    ap.add_argument("--journal", default=str(ICI / "sortie" / "pont_decisions.json"))
    args = ap.parse_args()

    traduits = json.loads(Path(args.traduits).read_text(encoding="utf-8"))
    with open(args.formulaire, encoding="utf-8", newline="") as f:
        formulaire = {l["_id_verite"]: l for l in csv.DictReader(f, delimiter=";")}
    decisions, questions = [], []

    # 1. Doublons par téléphone : on fusionne dans la première ligne rencontrée.
    par_tel: dict[str, list[dict]] = defaultdict(list)
    for t in traduits:
        tel = re.sub(r"\D", "", formulaire[t["id"]]["Téléphone"])
        par_tel[tel or t["id"]].append(t)
    fusionnes = []
    for tel, groupe in par_tel.items():
        base = groupe[0]
        for autre in groupe[1:]:
            vus = {(d["jour"], d["debut"], d["fin"]) for d in base["disponibilites"]}
            base["disponibilites"] += [d for d in autre["disponibilites"] if (d["jour"], d["debut"], d["fin"]) not in vus]
            base["competences"] = sorted(set(base["competences"]) | set(autre["competences"]))
            base["roles_preferes"] = sorted(set(base["roles_preferes"]) | set(autre["roles_preferes"]))
            if base["niveau"] == "inconnu": base["niveau"] = autre["niveau"]
            if base["accepte_nuit"] is None: base["accepte_nuit"] = autre["accepte_nuit"]
            elif autre["accepte_nuit"] is False: base["accepte_nuit"] = False
            base["accompagnants"] = max(base["accompagnants"], autre["accompagnants"])
            base["remarques"] += autre["remarques"]
            decisions.append(f"{base['nom']} et {autre['nom']} ont le même téléphone : fusionnés en une seule personne ({base['id']})")
            questions.append(f"{base['nom']} / {autre['nom']} : bien la même personne ? Dispos réunies : "
                             + ", ".join(f"{d['jour']} {d['debut']}-{d['fin']}" for d in base["disponibilites"]))
        fusionnes.append(base)

    # 2. Annuaire pour retrouver les binômes et les « pas avec ».
    annuaire = {normaliser(t["nom"]): t["id"] for t in fusionnes}
    lignes = []
    for t in fusionnes:
        binome, pourquoi = retrouver(t["binome_nom"], annuaire, t["id"])
        if t["binome_nom"] and binome:
            decisions.append(f"{t['nom']} : binôme « {t['binome_nom']} » = {binome} ({pourquoi})")
        elif t["binome_nom"]:
            questions.append(f"{t['nom']} veut être avec {pourquoi}")
        pas_avec, pourquoi2 = retrouver(t["pas_avec_nom"], annuaire, t["id"])
        if t["pas_avec_nom"] and not pas_avec:
            questions.append(f"{t['nom']} ne veut pas être avec {pourquoi2}")

        # 3. Hypothèses prudentes pour les champs inconnus, chacune notée.
        if t["majeur"] is None:
            age = AGE_INCONNU
            if any(r in ("signaleur", "serre_file") for r in t["roles_preferes"]):
                questions.append(f"{t['nom']} : âge non indiqué, demande un poste route ; confirmer qu'il ou elle est majeur(e)")
        else:
            age = AGE_INCONNU if t["majeur"] else AGE_MINEUR
        nuit = True if t["accepte_nuit"] is None else t["accepte_nuit"]
        if t["accepte_nuit"] is None:
            decisions.append(f"{t['nom']} : rien dit sur la nuit, considéré comme disponible le soir (à confirmer si affecté tard)")
        dispos = {"vendredi": [], "samedi": [], "dimanche": []}
        for d in t["disponibilites"]:
            dispos[d["jour"]].append(f"{d['debut']}-{d['fin']}")
        comp = set(t["competences"])
        prenom, *reste = t["nom"].split(" ", 1)
        lignes.append({
            "benevole_id": t["id"], "prenom": prenom, "nom": reste[0] if reste else "", "age": age,
            "commune": "", "email": "", "telephone": formulaire[t["id"]]["Téléphone"],
            "dispo_vendredi": ",".join(dispos["vendredi"]), "dispo_samedi": ",".join(dispos["samedi"]), "dispo_dimanche": ",".join(dispos["dimanche"]),
            "editions_precedentes": t.get("editions_precedentes") or 0,
            "PSC1_ou_samaritain": "psc1" in comp, "permis_B": "permis" in comp,
            "vehicule": "vehicule" in comp or "4x4" in comp, "vehicule_4x4": "4x4" in comp,
            "apte_marche_montagne": "montagne" in comp, "pratique_trail": "trail" in comp,
            "langues": "", "roles_preferes": ",".join(t["roles_preferes"]),
            "accepte_nuit": nuit, "accepte_chef_de_poste": t["niveau"] == "responsable",
            "binome_souhaite": binome or "", "pas_avec": pas_avec or "",
            "accompagnants": t["accompagnants"],
            "contraintes": " | ".join(r["texte"] for r in t["remarques"] if r["etiquette"] == "physique"),
            "commentaire_libre": formulaire[t["id"]]["Remarques"],
        })
        questions += [f"{t['nom']} : {q}" for q in t["questions"]]

    with open(args.sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(lignes)
    Path(args.journal).write_text(json.dumps({"decisions": decisions, "questions": questions}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{len(traduits)} lignes traduites -> {len(lignes)} bénévoles pour le solveur ({len(traduits) - len(lignes)} fusion(s))")
    print(f"{len(decisions)} décision(s) prises seul, {len(questions)} question(s) pour l'orga")
    print("\nDécisions (extrait) :")
    for d in decisions[:12]: print("  -", d)
    print("\nQuestions pour l'orga (extrait) :")
    for q in questions[:15]: print("  ?", q)
    print(f"\n-> {args.sortie}\n-> {args.journal}")


if __name__ == "__main__":
    main()
