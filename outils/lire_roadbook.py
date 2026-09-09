"""Outil « Lire le roadbook » : des pages de PDF (souvent des images) -> la fiche de course en JSON fermé.

Le roadbook d'une course est un document de communication, pas une base de données : tableaux
en image, icônes pour les services, horaires du premier et du dernier coureur. Un modèle qui voit
les pages remplit le format « course » que le reste de la chaîne comprend. Un niveau de confiance
par point de passage permet à l'organisateur de relire vite ce qui est douteux.

Lancer :
    python outils/lire_roadbook.py --pdf "chemin.pdf" --pages 23,24,25 --course "Marathon"
    python outils/lire_roadbook.py --pdf ... --pages ... --course Marathon --evaluer data/course_marathon.json
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

import fitz  # PyMuPDF
from anthropic import AnthropicBedrock, RateLimitError

MODELE = "us.anthropic.claude-opus-4-6-v1"
REGION = "us-east-1"

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["nom", "date", "distance_km", "denivele_positif_m", "depart", "arrivee", "coureurs_max", "temps_max",
                 "points_de_passage", "autres_courses_sur_les_memes_postes", "retrait_dossards", "navettes_coureurs", "doutes"],
    "properties": {
        "nom": {"type": "string"},
        "date": {"type": "string", "description": "AAAA-MM-JJ du départ"},
        "distance_km": {"type": "number"},
        "denivele_positif_m": {"type": "integer"},
        "depart": {"type": "object", "additionalProperties": False, "required": ["lieu", "date_heure"],
                   "properties": {"lieu": {"type": "string"}, "date_heure": {"type": "string", "description": "ISO AAAA-MM-JJTHH:MM"}}},
        "arrivee": {"type": "object", "additionalProperties": False, "required": ["lieu"], "properties": {"lieu": {"type": "string"}}},
        "coureurs_max": {"type": ["integer", "null"]},
        "temps_max": {"type": ["string", "null"], "description": "HH:MM"},
        "points_de_passage": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["nom", "altitude_m", "km", "premier", "dernier", "barriere", "services", "assistance_perso", "acces", "confiance"],
            "properties": {
                "nom": {"type": "string"}, "altitude_m": {"type": ["integer", "null"]}, "km": {"type": "number"},
                "premier": {"type": "string", "description": "ISO, heure de passage du premier coureur"},
                "dernier": {"type": "string", "description": "ISO, heure de passage du dernier coureur"},
                "barriere": {"type": ["string", "null"], "description": "ISO si barrière horaire, sinon null"},
                "services": {"type": "array", "items": {"type": "string", "enum": ["depart", "arrivee", "ravitaillement", "bus_abandon", "barriere_horaire",
                                                                                     "repas_chaud", "sac_suiveur", "point_de_secours", "douche", "massage", "lits"]}},
                "assistance_perso": {"type": "boolean"},
                "acces": {"type": "string", "description": "ce que le roadbook dit de l'accès (route, à pied, parking obligatoire...)"},
                "confiance": {"type": "number", "description": "0 à 1"}}}},
        "autres_courses_sur_les_memes_postes": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["course", "poste", "premier", "dernier", "barriere"],
            "properties": {"course": {"type": "string"}, "poste": {"type": "string"}, "premier": {"type": "string"}, "dernier": {"type": "string"},
                           "barriere": {"type": ["string", "null"]}}}},
        "retrait_dossards": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["lieu", "debut", "fin"],
            "properties": {"lieu": {"type": "string"}, "debut": {"type": "string"}, "fin": {"type": "string"}}}},
        "navettes_coureurs": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["trajet", "depart"],
            "properties": {"trajet": {"type": "string"}, "depart": {"type": "string"}}}},
        "doutes": {"type": "array", "items": {"type": "string"}, "description": "ce que l'organisateur doit vérifier"},
    },
}

SYSTEME = """Tu lis les pages d'un roadbook de course de trail et tu remplis la fiche de la course demandée, et seulement celle-là, dans le format fermé fourni.

Ce qui compte pour planifier les bénévoles : chaque point de passage (nom, altitude, km), l'heure du premier et du dernier coureur, la barrière horaire s'il y en a une, les services présents (les icônes : couverts = ravitaillement, bus = bus d'abandon, panneau STOP = barrière horaire, marmite = repas chaud, sac = sac suiveur, croix = point de secours, douche, massage, lit), si l'assistance personnelle est autorisée (astérisque), et ce que le roadbook dit de l'accès (voiture interdite, parking obligatoire, montée à pied).

Règles :
- Les points de passage sont EXACTEMENT les lignes du tableau « Lieu de passage » de la course demandée, ni plus ni moins. Le profil dessiné (courbe d'altitude) ne sert qu'à confirmer ; les sommets et cols nommés dessus ne sont pas des points de passage. Une page qui décrit une autre course (autre distance, autre départ) ne fournit que des horaires pour autres_courses_sur_les_memes_postes.
- Les icônes, de gauche à droite dans le tableau, ont chacune un sens précis donné par la légende : ne confonds pas le bus (bus d'abandon) avec la valise (sac suiveur). Le repas chaud est une marmite fumante.
- Les horaires sont écrits « 01-09h45 » : le chiffre avant le tiret est le jour de course (01 = le jour du départ). Convertis en ISO avec la date du départ.
- Si la même page décrit plusieurs courses, ne prends que la course demandée. Si d'autres courses passent par les mêmes postes le même jour et que leurs horaires sont visibles sur d'autres pages fournies, remplis autres_courses_sur_les_memes_postes.
- N'invente rien : un champ absent vaut null ou liste vide, et tu le signales dans doutes. Une valeur difficile à lire baisse la confiance du point de passage.
- Le retrait des dossards et les navettes coureurs ne concernent que la course demandée."""


def pages_en_images(pdf: Path, pages: list[int], dpi: int = 220) -> list[bytes]:
    d = fitz.open(pdf)
    out = []
    for n in pages:
        pix = d[n - 1].get_pixmap(dpi=dpi)
        out.append(pix.tobytes("png"))
    return out


def lire(pdf: Path, pages: list[int], course: str, date_indice: str = "") -> dict:
    cl = AnthropicBedrock(aws_region=REGION, max_retries=8)
    contenu = []
    for n, png in zip(pages, pages_en_images(pdf, pages)):
        contenu.append({"type": "text", "text": f"Page {n} du roadbook :"})
        contenu.append({"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(png).decode()}})
    contenu.append({"type": "text", "text": f"Course demandée : « {course} ».{' Indice de date : ' + date_indice if date_indice else ''} Remplis la fiche."})
    for tentative in range(6):
        try:
            r = cl.messages.create(model=MODELE, max_tokens=6000, system=SYSTEME,
                                   messages=[{"role": "user", "content": contenu}],
                                   output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
            return json.loads(r.content[0].text)
        except RateLimitError:
            time.sleep(20 * (tentative + 1))
    raise RuntimeError("quota Bedrock dépassé")


def evaluer(sortie: dict, verite: dict) -> list[str]:
    """Compare point par point avec une fiche de référence. Rend les écarts."""
    ecarts = []
    V = {p["nom"].lower(): p for p in verite["points_de_passage"]}
    for p in sortie["points_de_passage"]:
        v = V.get(p["nom"].lower())
        if not v:
            ecarts.append(f"{p['nom']} : absent de la référence (ou nom différent)")
            continue
        for champ in ("km", "altitude_m", "premier", "dernier", "barriere"):
            a, b = p.get(champ), v.get(champ)
            if isinstance(a, str) and isinstance(b, str):
                a, b = a[:16], b[:16]
            if a != b:
                ecarts.append(f"{p['nom']} / {champ} : lu {a!r}, référence {b!r}")
        if set(p["services"]) != set(v["services"]):
            ecarts.append(f"{p['nom']} / services : lu {sorted(p['services'])}, référence {sorted(v['services'])}")
    manquants = set(V) - {p["nom"].lower() for p in sortie["points_de_passage"]}
    ecarts += [f"{m} : non lu" for m in manquants]
    return ecarts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--pages", required=True, help="numéros de pages, ex. 23,24,25")
    ap.add_argument("--course", required=True)
    ap.add_argument("--date", default="", help="indice : date du départ si le roadbook ne la donne pas clairement")
    ap.add_argument("--sortie", default=str(Path(__file__).resolve().parent / "sortie" / "course_lue.json"))
    ap.add_argument("--evaluer", default="", help="fiche de référence JSON pour compter les écarts")
    args = ap.parse_args()
    pages = [int(x) for x in args.pages.split(",")]
    t = time.time()
    fiche = lire(Path(args.pdf), pages, args.course, args.date)
    Path(args.sortie).parent.mkdir(parents=True, exist_ok=True)
    Path(args.sortie).write_text(json.dumps(fiche, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{fiche['nom']} : {fiche['distance_km']} km, {fiche['denivele_positif_m']} m D+, départ {fiche['depart']['lieu']} {fiche['depart']['date_heure']}, "
          f"{len(fiche['points_de_passage'])} points de passage, lu en {time.time() - t:.0f} s")
    for p in fiche["points_de_passage"]:
        print(f"  km {p['km']:>4}  {p['nom']:<20} {p['altitude_m']} m  {p['premier'][11:16]} -> {p['dernier'][11:16]}"
              f"  barrière {p['barriere'][11:16] if p['barriere'] else '-'}  {', '.join(p['services'])}  (confiance {p['confiance']})")
    print(f"  autres courses : {len(fiche['autres_courses_sur_les_memes_postes'])} passages | dossards : {len(fiche['retrait_dossards'])} | navettes : {len(fiche['navettes_coureurs'])}")
    for d in fiche["doutes"]:
        print("  doute :", d)
    if args.evaluer:
        ecarts = evaluer(fiche, json.loads(Path(args.evaluer).read_text(encoding="utf-8")))
        print(f"\nÉcarts avec la référence : {len(ecarts)}")
        for e in ecarts:
            print("  -", e)
    print(f"-> {args.sortie}")


if __name__ == "__main__":
    main()
