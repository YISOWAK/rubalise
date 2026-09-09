"""Outil « Traduire les dispos » : une ligne de formulaire en texte libre -> les champs
fermés que le solveur comprend, plus des remarques étiquetées pour le contradicteur.

Le modèle ne parle jamais au solveur : il remplit un formulaire à vocabulaire fermé
(schéma JSON strict), et c'est du code qui vérifie et range le résultat.

Lancer :
    python outils/traduire_dispos.py --lignes B044,B046,B053      (quelques lignes)
    python outils/traduire_dispos.py --toutes                      (les 75)
    python outils/traduire_dispos.py --toutes --evaluer            (compare à la vérité de benevoles.csv)

Modèle : Claude sur Amazon Bedrock. Opus 5 n'est pas ouvert sur ce compte AWS
(« not available for this account »), on utilise le meilleur disponible, Opus 4.6.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import time
from anthropic import AnthropicBedrock, RateLimitError

MODELE = "us.anthropic.claude-opus-4-6-v1"
REGION = "us-east-1"

CATEGORIES = ["dossards", "depart", "ravitaillement", "controle", "signaleur", "serre_file", "arrivee",
              "restauration", "secours", "logistique", "livraison", "parking", "pc_course", "reserve_volante",
              "navette", "rangement", "pointage"]
COMPETENCES = ["psc1", "permis", "vehicule", "4x4", "montagne", "trail"]
ETIQUETTES = ["physique", "materiel", "animal", "coureur", "relation", "logistique", "identite", "autre"]

# Le vocabulaire fermé. additionalProperties false partout : le modèle ne peut rien inventer.
SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["disponibilites", "competences", "majeur", "niveau", "editions_precedentes", "roles_preferes", "accepte_nuit",
                 "binome_nom", "pas_avec_nom", "groupe_taille", "accompagnants", "remarques", "questions", "confiance"],
    "properties": {
        "disponibilites": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["jour", "debut", "fin"],
            "properties": {"jour": {"type": "string", "enum": ["vendredi", "samedi", "dimanche"]},
                           "debut": {"type": "string", "description": "HH:MM"},
                           "fin": {"type": "string", "description": "HH:MM, 24:00 pour minuit"}}}},
        "competences": {"type": "array", "items": {"type": "string", "enum": COMPETENCES}},
        "majeur": {"type": ["boolean", "null"], "description": "null si l'âge n'est pas dit"},
        "niveau": {"type": "string", "enum": ["responsable", "petite_main", "inconnu"]},
        "editions_precedentes": {"type": ["integer", "null"], "description": "nombre d'éditions déjà faites comme bénévole, null si rien n'est dit"},
        "roles_preferes": {"type": "array", "items": {"type": "string", "enum": CATEGORIES}},
        "accepte_nuit": {"type": ["boolean", "null"], "description": "false si la personne refuse la nuit, null si rien n'est dit"},
        "binome_nom": {"type": ["string", "null"], "description": "nom de la personne avec qui elle veut être, tel qu'écrit"},
        "pas_avec_nom": {"type": ["string", "null"]},
        "groupe_taille": {"type": ["integer", "null"], "description": "si elle vient en groupe qui veut rester ensemble"},
        "accompagnants": {"type": "integer", "description": "personnes non inscrites qu'elle amène, 0 sinon"},
        "remarques": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["etiquette", "texte"],
            "properties": {"etiquette": {"type": "string", "enum": ETIQUETTES}, "texte": {"type": "string"}}}},
        "questions": {"type": "array", "items": {"type": "string"}, "description": "ce qu'il faut demander à l'orga"},
        "confiance": {"type": "number", "description": "entre 0 et 1"},
    },
}

SYSTEME = f"""Tu traduis une ligne de formulaire d'inscription bénévole (texte libre, français, souvent bâclé) en champs structurés pour un planificateur de course de trail. Tu remplis uniquement le formulaire fermé fourni.

L'événement : SwissPeaks Marathon 2025. Vendredi 5 septembre (retrait des dossards l'après-midi), samedi 6 septembre (la course : départ 09h00, dernier coureur attendu vers 23h00, arrivée ouverte jusqu'à 00h15 dimanche), dimanche 7 septembre (rangement l'après-midi).

Règles de traduction :
- Disponibilités : une plage par jour cité. « toute la journée » = 06:00-24:00. « le matin » = 06:00-13:00. « l'après-midi » = 13:00-18:00. « le soir » = 17:00-24:00. « jusqu'à minuit » = fin 24:00. Ne jamais inventer un jour non cité.
- Quelqu'un qui COURT la course n'est pas disponible le samedi, quoi qu'il dise d'autre : aucune plage le samedi, et une remarque « coureur ».
- Compétences, seulement ce qui est dit : psc1 (PSC1, samaritain, premiers secours), permis, vehicule (voiture, véhiculé, 4x4 implique aussi vehicule), 4x4, montagne (marche en montagne, randonneur, ok pour monter à pied), trail (fait du trail, ultras).
- majeur : true seulement si l'âge dit est >= 18 ou si un indice fort l'établit (enfants, éditions précédentes en tant qu'adulte ne suffit pas), false si l'âge dit est < 18, null sinon.
- editions_precedentes : le nombre d'éditions déjà faites comme bénévole si la personne le dit (« déjà bénévole 3 fois », « 2 éditions »), 0 si elle dit que c'est sa première fois, null sinon. Ne le répète pas en remarque.
- niveau : « responsable » si la personne se propose pour tenir ou être chef d'un poste ; « petite_main » si elle dit explicitement vouloir juste aider ; « inconnu » sinon. Le nombre d'éditions ne suffit pas.
- roles_preferes : dans la liste fermée. ravito -> ravitaillement, arrivée -> arrivee, repas -> restauration, PC -> pc_course, dossards -> dossards, signaleur -> signaleur, serre-file -> serre_file, parking -> parking, logistique -> logistique, pointage -> pointage.
- accepte_nuit : false seulement si la personne écrit « pas la nuit », « pas après 20h » ou équivalent ; true seulement si elle dit explicitement être ok la nuit ; null sinon. Une plage horaire qui s'arrête tôt n'est PAS un refus de la nuit, et « jusqu'à minuit » n'est PAS une acceptation explicite.
- binome_nom : la personne nommée avec qui elle veut être, telle qu'écrite. pas_avec_nom : l'inverse.
- accompagnants : « je viens avec 3 personnes » = 3, seulement si ces personnes ne semblent pas inscrites elles-mêmes.
- remarques : tout ce qui ne rentre dans aucun champ mais que l'organisateur doit voir, avec l'étiquette : physique (genou, station debout, âge avancé), materiel (barnum, matériel prêté), animal (chien), coureur (participe à la course), relation (veut ou ne veut pas être avec quelqu'un, au-delà du binôme), logistique (vient en train, pas de voiture, doit partir à telle heure), identite (doute sur l'identité, doublon possible), autre.
- questions : ce qu'il faut demander à l'organisateur pour lever un doute (prénoms des accompagnants, quelle personne exactement, âge non dit alors qu'elle veut être signaleur...). Ne pose pas de question quand tout est clair.
- confiance : 1 si tout est explicite, plus bas si tu as dû interpréter.
Ne devine jamais un champ absent : null ou liste vide, et une question si ça compte."""


def client():
    return AnthropicBedrock(aws_region=REGION, max_retries=8)  # Bedrock renvoie des 429 en rafale : on réessaie avec attente


def traduire(ligne: dict, cl=None) -> dict:
    """Une ligne du formulaire -> dict conforme au SCHEMA."""
    cl = cl or client()
    contenu = "\n".join(f"{k} : {v}" for k, v in ligne.items() if not k.startswith("_") and v)
    r = cl.messages.create(
        model=MODELE, max_tokens=2000, system=SYSTEME,
        messages=[{"role": "user", "content": f"Ligne du formulaire :\n{contenu}"}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    )
    return json.loads(r.content[0].text)


# ---------------------------------------------------------------------------
# Évaluation contre benevoles.csv (la vérité qui a servi à générer le formulaire)
# ---------------------------------------------------------------------------
def vrai(v): return str(v).lower() == "true"


def verite_de(b: dict) -> dict:
    comp = {k for k, col in [("psc1", "PSC1_ou_samaritain"), ("permis", "permis_B"), ("vehicule", "vehicule"),
                             ("4x4", "vehicule_4x4"), ("montagne", "apte_marche_montagne"), ("trail", "pratique_trail")] if vrai(b[col])}
    dispos = {j: b[c] for j, c in [("vendredi", "dispo_vendredi"), ("samedi", "dispo_samedi"), ("dimanche", "dispo_dimanche")] if b[c]}
    return {"competences": comp, "dispos": dispos, "accepte_nuit": vrai(b["accepte_nuit"]),
            "accompagnants": int(b.get("accompagnants") or 0), "binome": b["binome_souhaite"],
            "responsable": vrai(b["accepte_chef_de_poste"]), "majeur": int(b["age"]) >= 18}


def comparer(sortie: dict, verite: dict) -> dict:
    d_sortie = {}
    for d in sortie["disponibilites"]:                      # plusieurs plages le même jour : on les concatène, triées
        d_sortie.setdefault(d["jour"], []).append(f"{d['debut']}-{d['fin']}")
    d_sortie = {j: ",".join(sorted(v)) for j, v in d_sortie.items()}
    d_verite = {j: ",".join(sorted(v.split(","))) for j, v in verite["dispos"].items()}
    return {
        "dispos": d_sortie == d_verite,
        "competences": set(sortie["competences"]) == verite["competences"],
        "nuit": (sortie["accepte_nuit"] is False) == (not verite["accepte_nuit"]),
        "accompagnants": sortie["accompagnants"] == verite["accompagnants"],
        "responsable": (sortie["niveau"] == "responsable") == verite["responsable"],
        "binome": bool(sortie["binome_nom"]) == bool(verite["binome"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ici = Path(__file__).resolve().parent.parent
    ap.add_argument("--data", default=str(ici / "data"))
    ap.add_argument("--lignes", default="", help="ids séparés par des virgules, ex. B044,B053")
    ap.add_argument("--toutes", action="store_true")
    ap.add_argument("--evaluer", action="store_true")
    ap.add_argument("--forcer", action="store_true", help="retraduire même les lignes déjà dans la sortie")
    ap.add_argument("--sortie", default=str(ici / "outils" / "sortie" / "benevoles_traduits.json"))
    args = ap.parse_args()

    with open(Path(args.data) / "formulaire_benevoles.csv", encoding="utf-8", newline="") as f:
        formulaire = list(csv.DictReader(f, delimiter=";"))
    with open(Path(args.data) / "benevoles.csv", encoding="utf-8", newline="") as f:
        verite = {b["benevole_id"]: b for b in csv.DictReader(f, delimiter=";")}
    voulus = set(args.lignes.split(",")) if args.lignes else None
    lignes = [l for l in formulaire if args.toutes or (voulus and l["_id_verite"] in voulus)]
    if not lignes:
        sys.exit("Aucune ligne sélectionnée : --lignes B001,B002 ou --toutes")

    cl = client()
    deja = {}
    if Path(args.sortie).exists():
        deja = {s["id"]: s for s in json.loads(Path(args.sortie).read_text(encoding="utf-8"))}
    if args.forcer or args.lignes:                       # on retraduit les lignes demandées, on garde les autres
        for l in lignes:
            deja.pop(l["_id_verite"], None)
    sorties = []
    for l in lignes:
        bid = l["_id_verite"]
        if bid in deja:
            sorties.append(deja[bid]); continue
        s = traduire(l, cl); s["id"] = bid; s["nom"] = l["Prénom et nom"]
        sorties.append(s)
        deja[bid] = s
        Path(args.sortie).parent.mkdir(parents=True, exist_ok=True)
        Path(args.sortie).write_text(json.dumps(list(deja.values()), ensure_ascii=False, indent=2), encoding="utf-8")

    resultats = []
    scores = {}
    for l, s in zip(lignes, sorties):
        bid = l["_id_verite"]
        s["id"] = bid
        s["nom"] = l["Prénom et nom"]
        resultats.append(s)
        print(f"\n== {bid} {l['Prénom et nom']}  (confiance {s['confiance']})")
        print("   dispos :", ", ".join(f"{d['jour']} {d['debut']}-{d['fin']}" for d in s["disponibilites"]) or "aucune")
        print("   compétences :", ", ".join(s["competences"]) or "aucune", "| majeur :", s["majeur"], "| niveau :", s["niveau"],
              "| nuit :", s["accepte_nuit"], "| accompagnants :", s["accompagnants"])
        if s["roles_preferes"]: print("   rôles :", ", ".join(s["roles_preferes"]))
        if s["binome_nom"] or s["pas_avec_nom"] or s["groupe_taille"]:
            print("   binôme :", s["binome_nom"], "| pas avec :", s["pas_avec_nom"], "| groupe :", s["groupe_taille"])
        for r in s["remarques"]: print(f"   remarque [{r['etiquette']}] {r['texte']}")
        for q in s["questions"]: print(f"   question -> orga : {q}")
        if args.evaluer:
            c = comparer(s, verite_de(verite[bid]))
            for k, ok in c.items():
                scores.setdefault(k, [0, 0]); scores[k][0] += ok; scores[k][1] += 1
            faux = [k for k, ok in c.items() if not ok]
            if faux: print("   écarts avec la vérité :", ", ".join(faux))

    Path(args.sortie).parent.mkdir(parents=True, exist_ok=True)
    Path(args.sortie).write_text(json.dumps(resultats, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.evaluer:
        print("\nScore par champ (lignes justes / lignes) :")
        for k, (ok, n) in scores.items():
            print(f"  {k:<14} {ok}/{n}")
    print(f"\n{len(resultats)} ligne(s) traduite(s) -> {args.sortie}")


if __name__ == "__main__":
    main()
