"""Vérificateur de règles : relit un plan avec les règles du plan 02, en code pur.

Infaillible sur ce qu'il connaît (les règles écrites), aveugle au reste (c'est le
rôle du contradicteur). Rend une liste de violations {regle, gravite, poste, benevole, message}.

Lancer :
    python outils/verifier.py                       (plan par défaut : solveur/sortie/plan.json)
    python outils/verifier.py --plan autre.json --data data/
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "solveur"))
from solveur import charger, eligible, enchainement_possible, est_de_nuit, COMPETENCES  # noqa: E402

SITES_A_PIED = {"Taney", "Chalet de Blancsex"}
HEURE_LIMITE_MINEUR = 22
JOURNEE_LONGUE_H = 10


def charger_plan(chemin: Path) -> dict:
    return json.loads(chemin.read_text(encoding="utf-8"))


def charger_traduits(chemin: Path) -> dict:
    if not chemin.exists():
        return {}
    return {t["id"]: t for t in json.loads(chemin.read_text(encoding="utf-8"))}


def charger_telephones(dossier: Path, fichier: Path | None = None) -> dict:
    import csv
    with open(fichier or dossier / "benevoles.csv", encoding="utf-8", newline="") as f:
        return {b["benevole_id"]: re.sub(r"\D", "", b["telephone"]) for b in csv.DictReader(f, delimiter=";")}


def verifier(plan: dict, postes: list, benevoles: list, trajets: dict, battements: dict,
             traduits: dict | None = None, telephones: dict | None = None, course: dict | None = None) -> list[dict]:
    traduits = traduits or {}
    telephones = telephones or {}
    P = {p["id"]: p for p in postes}
    B = {b["id"]: b for b in benevoles}
    V: list[dict] = []

    def viol(regle, gravite, message, poste=None, benevole=None):
        V.append({"regle": regle, "gravite": gravite, "poste": poste, "benevole": benevole, "message": message})

    par_poste: dict[str, list[dict]] = defaultdict(list)
    par_benevole: dict[str, list[str]] = defaultdict(list)
    for a in plan["affectations"]:
        par_poste[a["poste_id"]].append(a)
        par_benevole[a["benevole_id"]].append(a["poste_id"])

    # ----- Bloquantes ------------------------------------------------------
    for p in postes:
        eq = par_poste.get(p["id"], [])
        couverture = sum(1 + a.get("accompagnants", 0) for a in eq)
        # B1 : poste sans responsable
        if p["responsable_requis"] and not any(a["role"] == "responsable" for a in eq):
            viol("B1", "bloquante", f"{p['nom']} : aucun responsable", p["id"])
        # B2 : sous le minimum
        if couverture < p["min"]:
            viol("B2", "bloquante", f"{p['nom']} : {couverture} personne(s) pour un minimum de {p['min']}", p["id"])
        # B5 bis : mineur sur un poste isolé sans adulte
        mineurs = [a for a in eq if B[a["benevole_id"]]["age"] < 18]
        adultes = [a for a in eq if B[a["benevole_id"]]["age"] >= 18]
        if mineurs and p["site"] in SITES_A_PIED and not adultes:
            viol("B5", "bloquante", f"{p['nom']} : mineur sans adulte sur un poste isolé", p["id"], mineurs[0]["benevole_id"])

    for bid, pids in par_benevole.items():
        b = B[bid]
        for pid in pids:
            p = P[pid]
            ok, raison = eligible(b, p)
            # B3 / B9 : hors dispo (dont le créneau qui passe minuit), refus de nuit
            if not ok and raison == "dispo":
                minuit = p["fin"].date() > p["debut"].date()
                viol("B9" if minuit else "B3", "bloquante",
                     f"{b['nom']} sur {p['nom']} : hors de sa disponibilité" + (" (le créneau passe minuit)" if minuit else ""), pid, bid)
            elif not ok and raison == "nuit":
                viol("B3", "bloquante", f"{b['nom']} sur {p['nom']} : refuse la nuit, créneau de nuit", pid, bid)
            # B6 : poste à pied sans aptitude montagne ; B7 : compétence exigée absente
            elif not ok:
                regle = "B6" if raison == "montagne" else "B7"
                viol(regle, "bloquante", f"{b['nom']} sur {p['nom']} : compétence manquante ({raison})", pid, bid)
            # B5 : mineur sur poste route, ou après 22h
            if b["age"] < 18:
                if p["categorie"] == "signaleur":
                    viol("B5", "bloquante", f"{b['nom']} ({b['age']} ans) : mineur sur un poste route ({p['nom']})", pid, bid)
                if p["fin"] > p["debut"].replace(hour=HEURE_LIMITE_MINEUR, minute=0):
                    viol("B5", "bloquante", f"{b['nom']} ({b['age']} ans) : mineur sur un créneau qui finit après {HEURE_LIMITE_MINEUR}h ({p['nom']})", pid, bid)
            # B8 : coureur de la course affecté pendant la course
            t = traduits.get(bid)
            if t and any(r["etiquette"] == "coureur" for r in t["remarques"]) and p["debut"].date() == datetime(2025, 9, 6).date():
                viol("B8", "bloquante", f"{b['nom']} court la course et est affecté samedi ({p['nom']})", pid, bid)
        # B4 : deux créneaux incompatibles pour la même personne
        for pa, pb in itertools.combinations(sorted(pids, key=lambda x: P[x]["debut"]), 2):
            a, c = P[pa], P[pb]
            if not (enchainement_possible(a, c, trajets, battements) or enchainement_possible(c, a, trajets, battements)):
                viol("B4", "bloquante", f"{b['nom']} : {a['nom']} puis {c['nom']} sont incompatibles (chevauchement ou trajet)", pb, bid)

    # ----- Alertes ---------------------------------------------------------
    for p in postes:
        eq = par_poste.get(p["id"], [])
        if not eq:
            continue
        couverture = sum(1 + a.get("accompagnants", 0) for a in eq)
        listes = [B[a["benevole_id"]] for a in eq]
        # A1 : que des débutants
        if all(b["editions_precedentes"] == 0 for b in listes):
            viol("A1", "alerte", f"{p['nom']} : personne sur ce créneau n'a déjà fait la course, prévoir un briefing ou y placer quelqu'un d'expérimenté", p["id"])
        # A5 : poste isolé sans véhicule dans l'équipe
        if p["site"] in SITES_A_PIED and not any(b["vehicule"] for b in listes):
            viol("A5", "alerte", f"{p['nom']} : personne n'a de véhicule dans l'équipe, navette à prévoir", p["id"])
        # A6 / A11 : accompagnants non listés, et poste tenu par une seule personne listée
        for a in eq:
            if a.get("accompagnants", 0):
                viol("A6", "alerte", f"{p['nom']} : {B[a['benevole_id']]['nom']} vient avec {a['accompagnants']} personne(s) non listée(s), prénoms à confirmer", p["id"], a["benevole_id"])
        if len(eq) == 1 and eq[0].get("accompagnants", 0) and p["min"] > 1:
            viol("A11", "alerte", f"{p['nom']} : une seule personne listée ({B[eq[0]['benevole_id']]['nom']}) et ses accompagnants anonymes, si elle se décommande le poste tombe", p["id"], eq[0]["benevole_id"])
        # A10 : idéal non atteint
        if p["min"] <= couverture < p["ideal"]:
            viol("A10", "alerte", f"{p['nom']} : {couverture}/{p['ideal']}, il manque {p['ideal'] - couverture} pour l'idéal", p["id"])
        # A9 : poste partagé avec une autre course, fenêtre trop courte
        if course:
            for autre in course.get("autres_courses_sur_les_memes_postes", []):
                if autre["poste"] == p["site"] and p["categorie"] == "ravitaillement":
                    dernier = datetime.fromisoformat(autre["dernier"])
                    derniers_du_site = max(q["fin"] for q in postes if q["site"] == p["site"] and q["categorie"] == "ravitaillement")
                    if derniers_du_site < dernier:
                        viol("A9", "alerte", f"{p['site']} : le dernier du {autre['course']} passe à {dernier:%H:%M}, le dernier créneau ferme à {derniers_du_site:%H:%M}", p["id"])
                    break

    for bid, pids in par_benevole.items():
        b = B[bid]
        # A2 : binôme non réuni
        if b["binome"] and b["binome"] in B and not set(pids) & set(par_benevole.get(b["binome"], [])):
            viol("A2", "alerte", f"{b['nom']} voulait être avec {B[b['binome']]['nom']}, ils ne partagent aucun créneau", None, bid)
        # A3 : rôle préféré ignoré pour un habitué
        if b["editions_precedentes"] >= 2 and b["roles_preferes"] and not any(P[x]["categorie"] in b["roles_preferes"] for x in pids):
            viol("A3", "alerte", f"{b['nom']} ({b['editions_precedentes']} éditions) n'est sur aucun de ses rôles préférés ({', '.join(b['roles_preferes'])})", None, bid)
        # A4 : journée longue
        par_jour: dict = defaultdict(float)
        for x in pids:
            par_jour[P[x]["debut"].date()] += (P[x]["fin"] - P[x]["debut"]).total_seconds() / 3600
        for jour, h in par_jour.items():
            if h > JOURNEE_LONGUE_H:
                viol("A4", "alerte", f"{b['nom']} : {h:.1f} h le {jour:%A}", None, bid)
        # A8 : remarques à relire pour les personnes affectées
        t = traduits.get(bid)
        if t:
            for r in t["remarques"]:
                if r["etiquette"] in ("physique", "animal", "relation", "identite", "logistique"):
                    viol("A8", "alerte", f"{b['nom']} : remarque [{r['etiquette']}] « {r['texte']} », à relire au regard de ses postes ({', '.join(pids)})", None, bid)
            for q in t["questions"]:
                viol("A8", "alerte", f"{b['nom']} : question restée ouverte, « {q} »", None, bid)

    # A7 : doublons probables (même téléphone, ou même nom normalisé)
    def cle(nom): return re.sub(r"[^a-z]", "", nom.lower().replace("é", "e").replace("è", "e"))
    vus_tel: dict[str, str] = {}
    vus_nom: dict[str, str] = {}
    for b in benevoles:
        tel = telephones.get(b["id"], "")
        if tel and tel in vus_tel:
            viol("A7", "alerte", f"{b['nom']} et {B[vus_tel[tel]]['nom']} ont le même téléphone : même personne ? Si oui, leurs postes se cumulent ({', '.join(par_benevole.get(b['id'], []) + par_benevole.get(vus_tel[tel], []))})", None, b["id"])
        elif tel:
            vus_tel[tel] = b["id"]
        k = cle(b["nom"])
        if k in vus_nom and vus_nom[k] != vus_tel.get(tel):
            viol("A7", "alerte", f"{b['nom']} et {B[vus_nom[k]]['nom']} : noms quasi identiques, doublon possible", None, b["id"])
        vus_nom.setdefault(k, b["id"])

    return V


def rapport(V: list[dict]) -> str:
    ordre = {"bloquante": 0, "alerte": 1}
    V = sorted(V, key=lambda v: (ordre[v["gravite"]], v["regle"], v["poste"] or "", v["benevole"] or ""))
    lignes = [f"{sum(v['gravite'] == 'bloquante' for v in V)} bloquante(s), {sum(v['gravite'] == 'alerte' for v in V)} alerte(s)", ""]
    for g in ("bloquante", "alerte"):
        lignes.append(g.upper() + "S")
        for v in [v for v in V if v["gravite"] == g]:
            lignes.append(f"  [{v['regle']}] {v['message']}")
        lignes.append("")
    return "\n".join(lignes)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ICI.parent / "data"))
    ap.add_argument("--plan", default=str(ICI.parent / "solveur" / "sortie" / "plan.json"))
    ap.add_argument("--traduits", default=str(ICI / "sortie" / "benevoles_traduits.json"))
    ap.add_argument("--sortie", default=str(ICI / "sortie" / "violations.json"))
    ap.add_argument("--benevoles", default="", help="fichier bénévoles utilisé pour le plan (défaut : data/benevoles.csv)")
    args = ap.parse_args()
    dossier = Path(args.data)
    postes, benevoles, trajets, battements = charger(dossier, Path(args.benevoles) if args.benevoles else None)
    course = json.loads((dossier / "course_marathon.json").read_text(encoding="utf-8"))
    V = verifier(charger_plan(Path(args.plan)), postes, benevoles, trajets, battements,
                 charger_traduits(Path(args.traduits)), charger_telephones(dossier, Path(args.benevoles) if args.benevoles else None), course)
    print(rapport(V))
    Path(args.sortie).parent.mkdir(parents=True, exist_ok=True)
    Path(args.sortie).write_text(json.dumps(V, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {args.sortie}")
