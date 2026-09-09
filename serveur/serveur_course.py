"""Serveur MCP « course » : expose l'état, le solveur, le vérificateur, les règles et le journal
comme des outils standard, appelables par un agent Strands, par Claude Desktop, ou par un script de test.

Aucune logique métier ici : les outils appellent le code de solveur/ et outils/.
L'état vit dans un dossier (défaut : etat/ à la racine du projet) en fichiers JSON lisibles.

Lancer en local (stdio, pour Strands ou Claude Desktop) :
    python serveur/serveur_course.py
Lancer en HTTP (pour AgentCore ou un test à distance) :
    python serveur/serveur_course.py --http --port 8765

Règle absolue : ne jamais écrire sur la sortie standard (c'est le canal du protocole).
Tout ce qui imprime est redirigé vers stderr.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "solveur"))
sys.path.insert(0, str(RACINE / "outils"))

try:                                            # mcp 2.x
    from mcp.server.mcpserver import MCPServer  # noqa: E402
except ImportError:                             # mcp 1.x (celui que Strands installe)
    from mcp.server.fastmcp import FastMCP as MCPServer  # noqa: E402

import solveur as S  # noqa: E402
import verifier as V  # noqa: E402

ETAT = Path(os.environ.get("COURSE_ETAT", RACINE / "etat"))
ETAT.mkdir(parents=True, exist_ok=True)

mcp = MCPServer(
    name="course",
    instructions="Outils de planification des bénévoles d'une course de trail. Charger les données, "
                 "traduire un formulaire, résoudre, vérifier, lire le plan, gérer les règles et le journal. "
                 "Rien n'est envoyé aux bénévoles sans un appel explicite à publier() par l'organisateur.",
)


# ---------------------------------------------------------------------------
# État sur disque
# ---------------------------------------------------------------------------
def _lire(nom: str, defaut):
    f = ETAT / nom
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else defaut


def _ecrire(nom: str, valeur):
    (ETAT / nom).write_text(json.dumps(valeur, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _config():
    return _lire("config.json", {"dossier_donnees": str(RACINE / "data"), "fichier_benevoles": "", "fichier_postes": ""})


def _journal_ajouter(auteur: str, action: str, cible, justification: str, avant=None, apres=None) -> str:
    entrees = _lire("journal.json", [])
    e = {"id": f"J{len(entrees) + 1:04d}", "horodatage": datetime.now().isoformat(timespec="minutes"),
         "auteur": auteur, "action": action, "cible": cible, "justification": justification, "avant": avant, "apres": apres}
    entrees.append(e)
    _ecrire("journal.json", entrees)
    return e["id"]


def _regles():
    r = _lire("regles.json", None)
    if r is None:
        r = json.loads((RACINE / "serveur" / "regles_defaut.json").read_text(encoding="utf-8"))
        _ecrire("regles.json", r)
    return r


def _donnees():
    c = _config()
    fb = Path(c["fichier_benevoles"]) if c.get("fichier_benevoles") else None
    fp = Path(c["fichier_postes"]) if c.get("fichier_postes") else None
    return S.charger(Path(c["dossier_donnees"]), fb, fp)


def _plan_courant():
    return _lire("plan.json", None)


def _nom(b):
    return b["nom"]


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------
@mcp.tool()
def etat_resume() -> dict:
    """Où en est-on : données chargées, bénévoles, créneaux, statut du plan, dernières entrées du journal."""
    c = _config()
    try:
        postes, benevoles, _, _ = _donnees()
        donnees = {"creneaux": len(postes), "benevoles": len(benevoles), "fichier_benevoles": c.get("fichier_benevoles") or "data/benevoles.csv"}
    except Exception as e:  # noqa: BLE001
        donnees = {"erreur": str(e)}
    plan = _plan_courant()
    journal = _lire("journal.json", [])
    return {
        "dossier_donnees": c["dossier_donnees"], "donnees": donnees,
        "plan": None if not plan else {"version": plan.get("version"), "statut": plan.get("statut"), "calcule_le": plan.get("calcule_le"),
                                        "affectations": len(plan["affectations"]), "trous": len(plan["trous"]),
                                        "postes_sans_responsable": plan.get("postes_sans_responsable", [])},
        "regles_actives": sum(1 for r in _regles() if r["active"]),
        "journal_dernieres": journal[-5:],
    }


@mcp.tool()
def charger_donnees(dossier: str = "", fichier_benevoles: str = "", fichier_postes: str = "") -> dict:
    """Charge le jeu de données d'une course (postes.csv, benevoles.csv, trajets.csv, battements.csv).
    dossier : chemin du dossier (défaut : data/ du projet). fichier_benevoles : autre fichier bénévoles au même format,
    par exemple celui produit par traduire_formulaire. fichier_postes : autre fichier postes, par exemple celui produit par construire_postes."""
    c = _config()
    if dossier:
        c["dossier_donnees"] = str(Path(dossier).resolve())
    c["fichier_benevoles"] = str(Path(fichier_benevoles).resolve()) if fichier_benevoles else ""
    c["fichier_postes"] = str(Path(fichier_postes).resolve()) if fichier_postes else ""
    _ecrire("config.json", c)
    postes, benevoles, trajets, battements = _donnees()
    _journal_ajouter("outil:charger_donnees", "chargement", {"dossier": c["dossier_donnees"], "benevoles": c["fichier_benevoles"]}, "")
    return {"creneaux": len(postes), "benevoles": len(benevoles), "trajets": len(trajets),
            "premier_creneau": min(p["debut"] for p in postes), "dernier_creneau": max(p["fin"] for p in postes),
            "responsables_declares": sum(b["responsable"] for b in benevoles)}


@mcp.tool()
def lire_roadbook(chemin_pdf: str, pages: str, course: str, date_depart: str = "") -> dict:
    """Lit les pages d'un roadbook PDF (tableaux en image) avec un modèle qui voit, et rend la fiche de la course :
    points de passage, horaires du premier et du dernier coureur, barrières, services, accès, dossards, navettes, et une liste
    de doutes à faire relire à l'organisateur. pages : numéros séparés par des virgules. course : nom tel qu'il apparaît dans le roadbook.
    Environ 40 secondes. La fiche est enregistrée dans l'état ; l'organisateur la corrige avant construire_postes."""
    import subprocess
    sortie = ETAT / "course.json"
    cmd = [sys.executable, str(RACINE / "outils" / "lire_roadbook.py"), "--pdf", chemin_pdf, "--pages", pages, "--course", course, "--sortie", str(sortie)]
    if date_depart:
        cmd += ["--date", date_depart]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return {"erreur": r.stderr[-800:]}
    fiche = _lire("course.json", {})
    _journal_ajouter("outil:lire_roadbook", "extraction", {"pdf": chemin_pdf, "pages": pages}, f"{len(fiche.get('points_de_passage', []))} points de passage")
    return {"nom": fiche.get("nom"), "depart": fiche.get("depart"), "distance_km": fiche.get("distance_km"),
            "points_de_passage": [{"nom": p["nom"], "km": p["km"], "premier": p["premier"][11:16], "dernier": p["dernier"][11:16],
                                   "barriere": (p["barriere"] or "")[11:16] or None, "services": p["services"], "acces": p["acces"], "confiance": p["confiance"]}
                                  for p in fiche.get("points_de_passage", [])],
            "autres_courses": len(fiche.get("autres_courses_sur_les_memes_postes", [])),
            "retrait_dossards": fiche.get("retrait_dossards"), "navettes_coureurs": fiche.get("navettes_coureurs"),
            "doutes_a_relire": fiche.get("doutes", []), "fichier": str(sortie)}


@mcp.tool()
def corriger_course(champ: str, valeur: str, auteur: str = "orga", justification: str = "") -> dict:
    """Corrige la fiche de course lue, avant de construire les postes. champ : chemin pointé, par exemple
    « points_de_passage.1.services » ou « coureurs_max ». valeur : en JSON, par exemple ["ravitaillement","bus_abandon"] ou 450. Journalisé."""
    fiche = _lire("course.json", None)
    if fiche is None:
        return {"erreur": "aucune fiche de course : appeler lire_roadbook d'abord"}
    try:
        nouvelle = json.loads(valeur)
    except json.JSONDecodeError:
        nouvelle = valeur
    cible = fiche
    parties = champ.split(".")
    for part in parties[:-1]:
        cible = cible[int(part)] if isinstance(cible, list) else cible[part]
    dernier = parties[-1]
    cle = int(dernier) if isinstance(cible, list) else dernier
    avant = cible[cle] if (isinstance(cible, list) or cle in cible) else None
    cible[cle] = nouvelle
    _ecrire("course.json", fiche)
    jid = _journal_ajouter(auteur, "correction_course", {"champ": champ}, justification, avant, nouvelle)
    return {"champ": champ, "avant": avant, "apres": nouvelle, "journal": jid}


@mcp.tool()
def construire_postes(gabarit: str = "trail") -> dict:
    """Construit les postes et leurs créneaux à partir de la fiche de course de l'état et d'un gabarit (trail par défaut) :
    ravitaillements, pointages, barrières, arrivée, serre-files, dossards, navettes, PC, réserve volante, livraisons, rangement.
    Écrit le fichier postes et le rend actif pour le solveur."""
    import subprocess
    fiche = ETAT / "course.json"
    if not fiche.exists():
        return {"erreur": "aucune fiche de course : appeler lire_roadbook d'abord"}
    sortie = ETAT / "postes_construits.csv"
    r = subprocess.run([sys.executable, str(RACINE / "outils" / "construire_postes.py"), "--course", str(fiche),
                        "--gabarit", str(RACINE / "gabarits" / f"{gabarit}.json"), "--sortie", str(sortie)],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return {"erreur": r.stderr[-800:]}
    c = _config(); c["fichier_postes"] = str(sortie); _ecrire("config.json", c)
    postes, _, _, _ = _donnees()
    _journal_ajouter("outil:construire_postes", "construction_postes", {"gabarit": gabarit}, f"{len(postes)} créneaux")
    return {"creneaux": len(postes), "besoin_min": sum(p["min"] for p in postes), "besoin_ideal": sum(p["ideal"] for p in postes),
            "par_categorie": {cat: sum(1 for p in postes if p["categorie"] == cat) for cat in sorted({p["categorie"] for p in postes})},
            "fichier": str(sortie), "resume": r.stdout.splitlines()[0]}


@mcp.tool()
def traduire_formulaire(chemin_csv: str = "", lignes: str = "") -> dict:
    """Traduit le formulaire d'inscription (texte libre, 6 colonnes) en bénévoles structurés, avec un modèle de langage,
    puis construit le fichier bénévoles pour le solveur (fusion des doublons, binômes retrouvés par nom).
    Long : environ 10 secondes par ligne. lignes : ids séparés par des virgules pour n'en traduire que quelques-unes.
    Rend le nombre de décisions prises seul et les questions à poser à l'organisateur."""
    import subprocess
    chemin = chemin_csv or str(Path(_config()["dossier_donnees"]) / "formulaire_benevoles.csv")
    sortie_trad = ETAT / "benevoles_traduits.json"
    cmd = [sys.executable, str(RACINE / "outils" / "traduire_dispos.py"), "--sortie", str(sortie_trad),
           "--data", str(Path(chemin).parent)]
    cmd += ["--lignes", lignes] if lignes else ["--toutes"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return {"erreur": r.stderr[-800:]}
    sortie_csv = ETAT / "benevoles_depuis_formulaire.csv"
    r2 = subprocess.run([sys.executable, str(RACINE / "outils" / "pont.py"), "--traduits", str(sortie_trad),
                         "--formulaire", chemin, "--sortie", str(sortie_csv), "--journal", str(ETAT / "pont_decisions.json")],
                        capture_output=True, text=True, encoding="utf-8")
    if r2.returncode != 0:
        return {"erreur": r2.stderr[-800:]}
    dec = _lire("pont_decisions.json", {"decisions": [], "questions": []})
    c = _config(); c["fichier_benevoles"] = str(sortie_csv); _ecrire("config.json", c)
    _journal_ajouter("outil:traduire_formulaire", "traduction", {"formulaire": chemin}, f"{len(dec['decisions'])} décisions, {len(dec['questions'])} questions")
    return {"benevoles": sum(1 for _ in csv.DictReader(open(sortie_csv, encoding="utf-8"), delimiter=";")),
            "decisions_prises_seul": len(dec["decisions"]), "exemples_decisions": dec["decisions"][:8],
            "questions_pour_orga": len(dec["questions"]), "questions": dec["questions"][:25]}


@mcp.tool()
def resoudre(absents: list[str] | None = None, heure: str = "", respecter_plan_publie: bool = True) -> dict:
    """Calcule un plan d'affectation avec le solveur (OR-Tools). Rend un brouillon : score, trous, postes sans responsable.
    absents : ids de bénévoles qui ne viennent plus (jour J). heure : heure courante ISO (jour J) ; les créneaux terminés
    ne bougent plus. respecter_plan_publie : si un plan a été publié, minimiser les changements par rapport à lui."""
    postes, benevoles, trajets, battements = _donnees()
    absents = set(absents or [])
    benevoles = [b for b in benevoles if b["id"] not in absents]
    plan_fige = None
    publie = _lire("plan_publie.json", None)
    if publie and respecter_plan_publie:
        h = datetime.fromisoformat(heure) if heure else None
        P = {p["id"]: p for p in postes}
        plan_fige = {(a["benevole_id"], a["poste_id"]): ("en_poste" if h and P[a["poste_id"]]["debut"] <= h else "notifie")
                     for a in publie["affectations"] if a["benevole_id"] not in absents and a["poste_id"] in P}
        if h:
            termines = {p["id"] for p in postes if p["fin"] <= h}
            postes = [p for p in postes if p["id"] not in termines]
            plan_fige = {k: v for k, v in plan_fige.items() if k[1] not in termines}
    s, v, statut, relache = S.resoudre(postes, benevoles, trajets, battements, plan_fige=plan_fige)
    with redirect_stdout(io.StringIO()):
        plan = S.rapport(s, v, statut, relache, postes, benevoles, ETAT / "brouillon", plan_fige)
    ancien = _plan_courant()
    plan["version"] = (ancien.get("version", 0) + 1) if ancien else 1
    plan["statut"] = "brouillon"
    plan["absents"] = sorted(absents)
    plan["heure"] = heure
    if plan_fige:
        actuels = {(a["benevole_id"], a["poste_id"]) for a in plan["affectations"]}
        B = {b["id"]: b for b in benevoles}
        P = {p["id"]: p for p in postes}
        plan["ecarts"] = {
            "retraits": [{"benevole": B[b]["nom"] if b in B else b, "poste": P[p]["nom"], "etat": plan_fige[(b, p)]} for b, p in sorted(set(plan_fige) - actuels)],
            "ajouts": [{"benevole": B[b]["nom"], "poste": P[p]["nom"]} for b, p in sorted(actuels - set(plan_fige))],
        }
    _ecrire("plan.json", plan)
    _journal_ajouter("outil:resoudre", "calcul", {"version": plan["version"], "absents": sorted(absents), "heure": heure},
                     f"{plan['score']['statut']} {plan['score']['mode']}")
    P = {p["id"]: p for p in postes}
    return {
        "version": plan["version"], "statut_solveur": plan["score"]["statut"], "mode": plan["score"]["mode"], "temps_s": plan["score"]["temps_s"],
        "postes_sans_responsable": [f"{pid} {P[pid]['nom']}" for pid in plan["postes_sans_responsable"]],
        "personnes_sous_minimum": plan["score"]["personnes_sous_minimum"], "personnes_sous_ideal": plan["score"]["personnes_sous_ideal"],
        "trous": [{"poste": f"{t['poste_id']} {P[t['poste_id']]['nom']}", "manque": t["manque"], "eligibles": t["eligibles"], "exclus": t["refus"]} for t in plan["trous"]],
        "ecarts_au_plan_publie": plan.get("ecarts"),
        "rapport_complet": str(ETAT / "brouillon" / "rapport.txt"),
    }


@mcp.tool()
def verifier(max_alertes: int = 40) -> dict:
    """Relit le plan courant avec les règles actives (bloquantes et alertes). Les dérogations accordées sont signalées comme telles."""
    plan = _plan_courant()
    if not plan:
        return {"erreur": "aucun plan : appeler resoudre d'abord"}
    postes, benevoles, trajets, battements = _donnees()
    c = _config()
    dossier = Path(c["dossier_donnees"])
    course = json.loads((dossier / "course_marathon.json").read_text(encoding="utf-8")) if (dossier / "course_marathon.json").exists() else None
    traduits = V.charger_traduits(ETAT / "benevoles_traduits.json")
    tels = V.charger_telephones(dossier, Path(c["fichier_benevoles"]) if c.get("fichier_benevoles") else None)
    regles = {r["id"]: r for r in _regles()}
    for rid, r in regles.items():
        if rid == "B5": V.HEURE_LIMITE_MINEUR = r["parametres"].get("heure_limite_mineur", 22)
        if rid == "A4": V.JOURNEE_LONGUE_H = r["parametres"].get("journee_longue_h", 10)
    viols = V.verifier(plan, postes, benevoles, trajets, battements, traduits, tels, course)
    viols = [v for v in viols if regles.get(v["regle"], {}).get("active", True)]
    derogations = plan.get("derogations", [])
    for v in viols:
        v["derogee"] = any(d["regle"] == v["regle"] and d.get("poste") in (None, v["poste"]) and d.get("benevole") in (None, v["benevole"]) for d in derogations)
    bloquantes = [v for v in viols if v["gravite"] == "bloquante"]
    alertes = [v for v in viols if v["gravite"] == "alerte"]
    _ecrire("violations.json", viols)
    return {"bloquantes": len(bloquantes), "bloquantes_non_derogees": sum(not v["derogee"] for v in bloquantes),
            "alertes": len(alertes),
            "liste_bloquantes": [f"[{v['regle']}]{' (dérogée)' if v['derogee'] else ''} {v['message']}" for v in bloquantes],
            "liste_alertes": [f"[{v['regle']}] {v['message']}" for v in alertes[:max_alertes]],
            "alertes_par_regle": {rid: sum(v["regle"] == rid for v in alertes) for rid in sorted({v["regle"] for v in alertes})}}


@mcp.tool()
def plan_par_poste(poste_id: str = "") -> list[dict]:
    """Le plan courant vu par créneau : qui est où, avec le responsable marqué. poste_id pour un seul créneau."""
    plan = _plan_courant()
    if not plan:
        return [{"erreur": "aucun plan"}]
    postes, benevoles, _, _ = _donnees()
    B = {b["id"]: b for b in benevoles}
    out = []
    for p in postes:
        if poste_id and p["id"] != poste_id:
            continue
        eq = [a for a in plan["affectations"] if a["poste_id"] == p["id"]]
        out.append({"poste": p["id"], "nom": p["nom"], "site": p["site"], "debut": p["debut"].strftime("%a %H:%M"), "fin": p["fin"].strftime("%a %H:%M"),
                    "couverture": f"{sum(1 + a.get('accompagnants', 0) for a in eq)}/{p['min']}-{p['ideal']}",
                    "equipe": [("*" if a["role"] == "responsable" else "") + B[a["benevole_id"]]["nom"] + (f" +{a['accompagnants']}" if a.get("accompagnants") else "") for a in eq if a["benevole_id"] in B]})
    return out


@mcp.tool()
def plan_par_personne(benevole: str) -> dict:
    """L'agenda d'un bénévole dans le plan courant, par id (B012) ou par nom. Avec ses dispos, compétences et remarques."""
    plan = _plan_courant()
    postes, benevoles, _, _ = _donnees()
    P = {p["id"]: p for p in postes}
    cible = next((b for b in benevoles if b["id"] == benevole or benevole.lower() in b["nom"].lower()), None)
    if not cible:
        return {"erreur": f"aucun bénévole « {benevole} »"}
    trad = V.charger_traduits(ETAT / "benevoles_traduits.json").get(cible["id"], {})
    agenda = [a for a in (plan["affectations"] if plan else []) if a["benevole_id"] == cible["id"]]
    return {"id": cible["id"], "nom": cible["nom"], "age": cible["age"], "responsable": cible["responsable"], "editions": cible["editions_precedentes"],
            "dispos": cible["dispos"], "accepte_nuit": cible["accepte_nuit"], "accompagnants": cible["accompagnants"], "binome": cible["binome"],
            "competences": [k for k in ("PSC1_ou_samaritain", "permis_B", "vehicule", "vehicule_4x4", "apte_marche_montagne", "pratique_trail") if cible[k]],
            "agenda": [{"poste": a["poste_id"], "nom": P[a["poste_id"]]["nom"], "debut": P[a["poste_id"]]["debut"].strftime("%a %H:%M"),
                        "fin": P[a["poste_id"]]["fin"].strftime("%a %H:%M"), "role": a["role"]} for a in sorted(agenda, key=lambda a: P[a["poste_id"]]["debut"])],
            "remarques": trad.get("remarques", []), "questions": trad.get("questions", [])}


@mcp.tool()
def regles_lister() -> list[dict]:
    """Les règles du vérificateur, actives ou non, avec leurs paramètres. L'organisateur peut les modifier via regle_modifier."""
    return _regles()


@mcp.tool()
def regle_modifier(regle_id: str, auteur: str, justification: str, active: bool | None = None, parametres: dict | None = None) -> dict:
    """Active, désactive ou paramètre une règle (ex. heure_limite_mineur, journee_longue_h). Journalisé avec l'auteur et la raison."""
    regles = _regles()
    r = next((r for r in regles if r["id"] == regle_id), None)
    if not r:
        return {"erreur": f"règle {regle_id} inconnue"}
    avant = dict(r)
    if active is not None:
        r["active"] = active
    if parametres:
        r["parametres"].update(parametres)
    r["modifiee_le"] = datetime.now().isoformat(timespec="minutes")
    _ecrire("regles.json", regles)
    jid = _journal_ajouter(auteur, "regle_modifiee", {"regle": regle_id}, justification, avant, r)
    return {"regle": r, "journal": jid}


@mcp.tool()
def deroger(regle_id: str, auteur: str, justification: str, poste_id: str = "", benevole_id: str = "") -> dict:
    """Accorde une dérogation ponctuelle à une règle sur le plan courant (« mets Marc là quand même »). La règle reste, la dérogation est journalisée."""
    plan = _plan_courant()
    if not plan:
        return {"erreur": "aucun plan"}
    d = {"regle": regle_id, "poste": poste_id or None, "benevole": benevole_id or None, "auteur": auteur, "justification": justification}
    plan.setdefault("derogations", []).append(d)
    jid = _journal_ajouter(auteur, "derogation", d, justification)
    d["journal"] = jid
    _ecrire("plan.json", plan)
    return d


@mcp.tool()
def journaliser(auteur: str, action: str, justification: str, cible: str = "") -> str:
    """Ajoute une entrée au journal (qui, quoi, quand, pourquoi). Rend son identifiant."""
    return _journal_ajouter(auteur, action, cible or None, justification)


@mcp.tool()
def journal_lire(n: int = 20) -> list[dict]:
    """Les n dernières entrées du journal."""
    return _lire("journal.json", [])[-n:]


@mcp.tool()
def publier(auteur: str, justification: str = "") -> dict:
    """Publie le plan courant : il devient le plan de référence (figé), chaque affectation est marquée prévenue,
    et un message par bénévole est écrit dans etat/envoyes/ (envoi simulé). À n'appeler que sur décision explicite de l'organisateur."""
    plan = _plan_courant()
    if not plan:
        return {"erreur": "aucun plan"}
    postes, benevoles, _, _ = _donnees()
    P = {p["id"]: p for p in postes}
    B = {b["id"]: b for b in benevoles}
    plan["statut"] = "publie"
    plan["fige_le"] = datetime.now().isoformat(timespec="minutes")
    for a in plan["affectations"]:
        a["notifie"] = True
    _ecrire("plan_publie.json", plan)
    _ecrire("plan.json", plan)
    dossier = ETAT / "envoyes"
    dossier.mkdir(exist_ok=True)
    n = 0
    for bid in {a["benevole_id"] for a in plan["affectations"]}:
        if bid not in B:
            continue
        lignes = [f"Bonjour {B[bid]['nom'].split()[0]},", "", "Voici ton programme pour le SwissPeaks Marathon :"]
        for a in sorted((a for a in plan["affectations"] if a["benevole_id"] == bid), key=lambda a: P[a["poste_id"]]["debut"]):
            p = P[a["poste_id"]]
            lignes.append(f"- {p['debut']:%A %d %H:%M} à {p['fin']:%H:%M} : {p['nom']} ({p['site']})" + (" , tu es responsable du poste" if a["role"] == "responsable" else ""))
        lignes += ["", "Merci d'être là. Réponds à ce message si quelque chose ne va pas."]
        (dossier / f"{bid}.txt").write_text("\n".join(lignes), encoding="utf-8")
        n += 1
    jid = _journal_ajouter(auteur, "publication", {"version": plan["version"]}, justification or "plan publié")
    return {"version": plan["version"], "messages_ecrits": n, "dossier": str(dossier), "journal": jid}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--http", action="store_true")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    if args.http:
        try:
            mcp.settings.host = "127.0.0.1"
            mcp.settings.port = args.port
        except AttributeError:
            pass
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")
