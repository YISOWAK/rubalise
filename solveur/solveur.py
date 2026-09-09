"""Solveur d'affectation des bénévoles. OR-Tools CP-SAT.

Lit le jeu de données (postes, bénévoles, trajets, battements), construit le
modèle selon les arbitrages du plan 07, résout, et écrit un plan + un rapport.

Lancer depuis le dossier du projet :
    python solveur/solveur.py            (jeu de données par défaut : data/)
    python solveur/solveur.py --data autre_dossier

Structure du fichier, dans l'ordre de lecture :
    1. chargement des données
    2. règles d'éligibilité (qui PEUT tenir quel créneau) : dispo, nuit, compétences
    3. paires de créneaux incompatibles (chevauchement + trajet + battements)
    4. le modèle : variables, contraintes dures, objectif
    5. résolution, avec relance en mode relâché si aucun plan n'existe
    6. rapport et écriture du plan
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from datetime import datetime, timedelta
from pathlib import Path

from ortools.sat.python import cp_model

# ---------------------------------------------------------------------------
# Les poids. Des taux de change entre niveaux, voir plan/07.
# ---------------------------------------------------------------------------
POIDS = {
    "personne_sous_minimum": 1000,   # par personne manquante sous l'effectif minimum
    "personne_sous_ideal": 10,       # par personne manquante sous l'effectif idéal
    "preference_respectee": 1,       # par affectation sur une catégorie préférée
    "binome_reuni": 2,               # par binôme placé sur le même créneau
    "quart_heure_au_dela": 1,        # par quart d'heure au-delà du seuil de charge (4 points par heure)
    "responsable_manquant": 10000,   # seulement en mode relâché, si le mode dur est infaisable
    "retrait_notifie": 20,           # jour J : retirer quelqu'un d'un créneau où il a été prévenu
    "retrait_en_poste": 100,         # jour J : retirer quelqu'un déjà en poste
    "ajout_jour_j": 10,              # jour J : toute nouvelle affectation = un message de plus à envoyer
}
SEUIL_CHARGE_HEURES = 8              # au-delà, chaque quart d'heure coûte
HEURE_DEBUT_NUIT = 21                # un créneau qui finit après 21h00 est un créneau de nuit

# Ce qu'un jeton de compétence dans postes.csv exige d'un bénévole.
# Les jetons absents d'ici (gilet, telephone, frontale, hygiene, informatique) sont
# de l'équipement ou du bon sens : ignorés par le solveur, rappelés dans la feuille de route.
COMPETENCES = {
    "PSC1": lambda b: b["PSC1_ou_samaritain"],
    "permis_B": lambda b: b["permis_B"],
    "vehicule": lambda b: b["vehicule"],
    "4x4": lambda b: b["vehicule_4x4"],
    "montagne": lambda b: b["apte_marche_montagne"],
    "trail": lambda b: b["pratique_trail"],
    "majeur": lambda b: b["age"] >= 18,
    "experience": lambda b: b["editions_precedentes"] >= 1,
    "controle_materiel": lambda b: b["editions_precedentes"] >= 1,
}
JOURS = {"2025-09-05": "dispo_vendredi", "2025-09-06": "dispo_samedi", "2025-09-07": "dispo_dimanche"}


# ---------------------------------------------------------------------------
# 1. Chargement
# ---------------------------------------------------------------------------
def lire_csv(chemin: Path) -> list[dict]:
    with open(chemin, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def vrai(v: str) -> bool:
    return str(v).strip().lower() in ("true", "1", "oui", "yes")


def charger(dossier: Path, fichier_benevoles: Path | None = None, fichier_postes: Path | None = None):
    postes = []
    for p in lire_csv(fichier_postes or dossier / "postes.csv"):
        postes.append({
            "id": p["poste_id"], "nom": p["nom"], "site": p["site"], "categorie": p["categorie"],
            "debut": datetime.fromisoformat(p["debut"]), "fin": datetime.fromisoformat(p["fin"]),
            "min": int(p["effectif_min"]), "ideal": int(p["effectif_ideal"]),
            "competences": [c for c in p["competences_requises"].split(",") if c],
            "responsable_requis": vrai(p["chef_de_poste_requis"]),
        })
    benevoles = []
    for b in lire_csv(fichier_benevoles or dossier / "benevoles.csv"):
        benevoles.append({
            "id": b["benevole_id"], "nom": f"{b['prenom']} {b['nom']}", "age": int(b["age"]),
            "editions_precedentes": int(b["editions_precedentes"]),
            "PSC1_ou_samaritain": vrai(b["PSC1_ou_samaritain"]), "permis_B": vrai(b["permis_B"]),
            "vehicule": vrai(b["vehicule"]), "vehicule_4x4": vrai(b["vehicule_4x4"]),
            "apte_marche_montagne": vrai(b["apte_marche_montagne"]), "pratique_trail": vrai(b["pratique_trail"]),
            "accepte_nuit": vrai(b["accepte_nuit"]), "responsable": vrai(b["accepte_chef_de_poste"]),
            "roles_preferes": [r for r in b["roles_preferes"].split(",") if r],
            "binome": b["binome_souhaite"], "accompagnants": int(b.get("accompagnants") or 0),
            "pas_avec": b.get("pas_avec", "") or "",
            "dispos": {jour: b[col] for jour, col in JOURS.items()},
        })
    trajets = {}
    for t in lire_csv(dossier / "trajets.csv"):
        trajets[(t["de"], t["vers"])] = int(t["minutes_voiture"]) + int(t["marche_supplementaire_min"])
    battements = {}
    for r in lire_csv(dossier / "battements.csv"):
        battements[r["categorie_poste"]] = (int(r["battement_depart_min"]), int(r["battement_arrivee_min"]))
    return postes, benevoles, trajets, battements


# ---------------------------------------------------------------------------
# 2. Éligibilité : qui PEUT tenir quel créneau. Tout ce qui est ici est dur.
# ---------------------------------------------------------------------------
def fenetres(b: dict) -> list[tuple[datetime, datetime]]:
    """Traduit '06:00-24:00' du samedi en un intervalle daté. '24:00' = minuit, le lendemain."""
    out = []
    for jour, texte in b["dispos"].items():
        for plage in filter(None, (s.strip() for s in texte.split(","))):
            d, f = plage.split("-")
            base = datetime.fromisoformat(jour)
            debut = base + timedelta(hours=int(d[:2]), minutes=int(d[3:]))
            fin = base + timedelta(hours=int(f[:2]), minutes=int(f[3:]))  # 24:00 devient bien 00:00 le lendemain
            out.append((debut, fin))
    out.sort()
    fusion = []
    for d, f in out:                       # « samedi jusqu'à minuit » + « dimanche dès minuit » = une seule plage
        if fusion and d <= fusion[-1][1]:
            fusion[-1] = (fusion[-1][0], max(fusion[-1][1], f))
        else:
            fusion.append((d, f))
    return fusion


def est_de_nuit(p: dict) -> bool:
    return p["fin"] > p["debut"].replace(hour=HEURE_DEBUT_NUIT, minute=0)


def eligible(b: dict, p: dict) -> tuple[bool, str]:
    """Rend (éligible, raison du refus). Créneau entier : la dispo doit couvrir tout le créneau."""
    if not any(d <= p["debut"] and f >= p["fin"] for d, f in fenetres(b)):
        return False, "dispo"
    if est_de_nuit(p) and not b["accepte_nuit"]:
        return False, "nuit"          # arbitrage 8 : le refus de la nuit est une dispo, donc dur
    if b["age"] < 18 and (p["categorie"] == "signaleur" or p["fin"] > p["debut"].replace(hour=22, minute=0)):
        return False, "mineur"        # règle B5 : pas de poste route, pas de créneau après 22h
    for jeton in p["competences"]:
        test = COMPETENCES.get(jeton)
        if test and not test(b):
            return False, jeton       # arbitrage 3 : compétence, majeur, montagne : dur
    return True, ""


# ---------------------------------------------------------------------------
# 3. Paires de créneaux incompatibles pour une même personne (arbitrage 2, dur)
#    A puis B est possible si : fin A + battement départ A + trajet + battement arrivée B <= début B
# ---------------------------------------------------------------------------
def enchainement_possible(a: dict, b: dict, trajets: dict, battements: dict) -> bool:
    dep_a = battements.get(a["categorie"], battements["defaut"])[0]
    arr_b = battements.get(b["categorie"], battements["defaut"])[1]
    route = 0 if a["site"] == b["site"] else trajets.get((a["site"], b["site"]), 10**6)
    return a["fin"] + timedelta(minutes=dep_a + route + arr_b) <= b["debut"]


def paires_incompatibles(postes: list[dict], trajets: dict, battements: dict) -> list[tuple[str, str]]:
    out = []
    for a, b in itertools.combinations(postes, 2):
        if not (enchainement_possible(a, b, trajets, battements) or enchainement_possible(b, a, trajets, battements)):
            out.append((a["id"], b["id"]))
    return out


# ---------------------------------------------------------------------------
# 4. Le modèle
# ---------------------------------------------------------------------------
def construire(postes, benevoles, trajets, battements, relache_responsable: bool = False, plan_fige: dict | None = None):
    """plan_fige : {(benevole_id, poste_id): "notifie" | "en_poste"} ; chaque écart coûte (voir POIDS)."""
    plan_fige = plan_fige or {}
    m = cp_model.CpModel()
    P = {p["id"]: p for p in postes}
    B = {b["id"]: b for b in benevoles}

    # Variables : une case par (bénévole, créneau) éligible. Les autres n'existent pas (= 0).
    x, refus = {}, {}
    for b in benevoles:
        for p in postes:
            ok, raison = eligible(b, p)
            if ok:
                x[(b["id"], p["id"])] = m.NewBoolVar(f"x_{b['id']}_{p['id']}")
            else:
                refus.setdefault(p["id"], {}).setdefault(raison, 0)
                refus[p["id"]][raison] += 1

    def cases_du_poste(pid):
        return [(bid, v) for (bid, pid2), v in x.items() if pid2 == pid]

    # Contrainte : jamais deux créneaux incompatibles pour la même personne (dur).
    for a, c in paires_incompatibles(postes, trajets, battements):
        for b in benevoles:
            if (b["id"], a) in x and (b["id"], c) in x:
                m.Add(x[(b["id"], a)] + x[(b["id"], c)] <= 1)

    # « Pas avec X » (dur) : jamais les deux sur le même créneau.
    for b in benevoles:
        autre = b["pas_avec"]
        if autre and autre in B and b["id"] < autre:
            for p in postes:
                if (b["id"], p["id"]) in x and (autre, p["id"]) in x:
                    m.Add(x[(b["id"], p["id"])] + x[(autre, p["id"])] <= 1)

    # Jour J : coût de chaque écart au plan figé (stabilité, plan 03).
    couts_changement = []
    for (bid, pid), etat in plan_fige.items():
        if (bid, pid) in x:   # sinon la personne est absente : retrait subi, pas pénalisé
            poids = POIDS["retrait_en_poste"] if etat == "en_poste" else POIDS["retrait_notifie"]
            couts_changement.append(poids * (1 - x[(bid, pid)]))
    if plan_fige:
        for (bid, pid), var in x.items():
            if (bid, pid) not in plan_fige:
                couts_changement.append(POIDS["ajout_jour_j"] * var)

    # Couverture, déficits, responsable.
    deficit_min, deficit_ideal, manque_resp = {}, {}, {}
    for p in postes:
        pid = p["id"]
        cases = cases_du_poste(pid)
        # Arbitrage 5 : un responsable qui vient accompagné compte pour 1 + N.
        couverture = sum(v * (1 + B[bid]["accompagnants"]) for bid, v in cases)
        personnes_listees = sum(v for _, v in cases)
        m.Add(personnes_listees <= p["ideal"])                       # on ne gaspille pas de monde

        deficit_min[pid] = m.NewIntVar(0, p["min"], f"dmin_{pid}")   # arbitrage 6 : souple
        m.Add(deficit_min[pid] >= p["min"] - couverture)
        deficit_ideal[pid] = m.NewIntVar(0, p["ideal"], f"dideal_{pid}")
        m.Add(deficit_ideal[pid] >= p["ideal"] - couverture)

        if p["responsable_requis"]:                                    # arbitrage 7 : dur, relâché seulement en secours
            responsables = [v for bid, v in cases if B[bid]["responsable"]]
            if relache_responsable:
                manque_resp[pid] = m.NewBoolVar(f"mresp_{pid}")
                m.Add(sum(responsables) + manque_resp[pid] >= 1)
            else:
                m.Add(sum(responsables) >= 1)

    # Charge par personne (arbitrage 9) : rien jusqu'au seuil, puis chaque quart d'heure coûte.
    depassement = {}
    for b in benevoles:
        quarts = sum(v * int((P[pid]["fin"] - P[pid]["debut"]).total_seconds() // 900)
                     for (bid, pid), v in x.items() if bid == b["id"])
        depassement[b["id"]] = m.NewIntVar(0, 24 * 4, f"over_{b['id']}")
        m.Add(depassement[b["id"]] >= quarts - SEUIL_CHARGE_HEURES * 4)

    # Préférences (souple, +1) et binômes (souple, +2).
    preferences = [v for (bid, pid), v in x.items() if P[pid]["categorie"] in B[bid]["roles_preferes"]]
    binomes = []
    for b in benevoles:
        autre = b["binome"]
        if autre and autre in B and B[autre]["binome"] == b["id"] and b["id"] < autre:
            for p in postes:
                if (b["id"], p["id"]) in x and (autre, p["id"]) in x:
                    y = m.NewBoolVar(f"bin_{b['id']}_{autre}_{p['id']}")
                    m.AddImplication(y, x[(b["id"], p["id"])])
                    m.AddImplication(y, x[(autre, p["id"])])
                    binomes.append(y)

    # L'objectif : on minimise les pénalités moins les bonus.
    m.Minimize(
        POIDS["personne_sous_minimum"] * sum(deficit_min.values())
        + POIDS["personne_sous_ideal"] * sum(deficit_ideal.values())
        + POIDS["quart_heure_au_dela"] * sum(depassement.values())
        + POIDS["responsable_manquant"] * sum(manque_resp.values())
        + sum(couts_changement)
        - POIDS["preference_respectee"] * sum(preferences)
        - POIDS["binome_reuni"] * sum(binomes)
    )
    return m, dict(x=x, deficit_min=deficit_min, deficit_ideal=deficit_ideal, manque_resp=manque_resp,
                   depassement=depassement, preferences=preferences, binomes=binomes, refus=refus)


# ---------------------------------------------------------------------------
# 5. Résolution
# ---------------------------------------------------------------------------
def resoudre(postes, benevoles, trajets, battements, temps_max_s: float = 10.0, plan_fige: dict | None = None):
    for relache in (False, True):
        m, v = construire(postes, benevoles, trajets, battements, relache_responsable=relache, plan_fige=plan_fige)
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = temps_max_s
        s.parameters.num_workers = 8
        s.parameters.random_seed = 0
        statut = s.Solve(m)
        if statut in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return s, v, statut, relache
    raise RuntimeError("Aucun plan possible, même en relâchant le responsable.")


# ---------------------------------------------------------------------------
# 6. Rapport
# ---------------------------------------------------------------------------
def rapport(s, v, statut, relache, postes, benevoles, sortie: Path, plan_fige: dict | None = None):
    P = {p["id"]: p for p in postes}
    B = {b["id"]: b for b in benevoles}
    val = s.Value
    affectations = [{"benevole_id": bid, "poste_id": pid,
                     "role": "responsable" if B[bid]["responsable"] and P[pid]["responsable_requis"] else "petite_main",
                     "accompagnants": B[bid]["accompagnants"]}
                    for (bid, pid), var in v["x"].items() if val(var)]
    # un seul responsable affiché par poste : le premier trouvé garde le rôle
    vus = set()
    for a in affectations:
        if a["role"] == "responsable":
            if a["poste_id"] in vus:
                a["role"] = "petite_main"
            vus.add(a["poste_id"])

    trous = [{"poste_id": pid, "manque": val(d), "eligibles": len([1 for (b, p) in v["x"] if p == pid]),
              "refus": v["refus"].get(pid, {})}
             for pid, d in v["deficit_min"].items() if val(d) > 0]
    sans_resp = [pid for pid, mr in v["manque_resp"].items() if val(mr)]

    score = {
        "statut": s.StatusName(statut), "mode": "relâché sur le responsable" if relache else "strict",
        "objectif": s.ObjectiveValue(),
        "personnes_sous_minimum": sum(val(d) for d in v["deficit_min"].values()),
        "personnes_sous_ideal": sum(val(d) for d in v["deficit_ideal"].values()),
        "preferences_respectees": sum(val(t) for t in v["preferences"]),
        "binomes_reunis": sum(val(t) for t in v["binomes"]),
        "quarts_heure_au_dela_du_seuil": sum(val(t) for t in v["depassement"].values()),
        "temps_s": round(s.WallTime(), 2),
    }

    lignes = [f"Statut : {score['statut']} ({score['mode']}), {score['temps_s']} s"]
    if sans_resp:
        lignes.append("")
        lignes.append("POSTES SANS RESPONSABLE (grave, à traiter en premier) :")
        lignes += [f"  {pid}  {P[pid]['nom']}" for pid in sans_resp]
    lignes += ["", f"Sous le minimum : {score['personnes_sous_minimum']} personne(s) manquante(s) sur {len(trous)} créneau(x)",
               f"Sous l'idéal : {score['personnes_sous_ideal']} | préférences respectées : {score['preferences_respectees']}"
               f" | binômes réunis : {score['binomes_reunis']} | quarts d'heure au-delà de {SEUIL_CHARGE_HEURES} h : {score['quarts_heure_au_dela_du_seuil']}"]
    if trous:
        lignes += ["", "Trous (créneau, manque, éligibles, pourquoi les autres sont exclus) :"]
        for t in trous:
            raisons = ", ".join(f"{k} {n}" for k, n in sorted(t["refus"].items(), key=lambda kv: -kv[1]))
            lignes.append(f"  {t['poste_id']:<4} {P[t['poste_id']]['nom'][:44]:<44} manque {t['manque']}  éligibles {t['eligibles']:>2}  exclus : {raisons}")
    lignes += ["", "Par créneau :"]
    for p in postes:
        eq = [a for a in affectations if a["poste_id"] == p["id"]]
        couv = sum(1 + a["accompagnants"] for a in eq)
        noms = ", ".join(("*" if a["role"] == "responsable" else "") + B[a["benevole_id"]]["nom"]
                         + (f" +{a['accompagnants']}" if a["accompagnants"] else "") for a in eq)
        lignes.append(f"  {p['id']:<4} {p['debut']:%a %H:%M}-{p['fin']:%H:%M} {p['nom'][:40]:<40} {couv}/{p['min']}-{p['ideal']}  {noms}")
    lignes += ["", "Par personne (les plus chargés d'abord) :"]
    charge = {}
    for a in affectations:
        p = P[a["poste_id"]]
        charge.setdefault(a["benevole_id"], []).append(p)
    for bid, ps in sorted(charge.items(), key=lambda kv: -sum((p["fin"] - p["debut"]).total_seconds() for p in kv[1]))[:15]:
        h = sum((p["fin"] - p["debut"]).total_seconds() for p in ps) / 3600
        lignes.append(f"  {B[bid]['nom']:<24} {h:>4.1f} h  " + " > ".join(f"{p['id']} {p['debut']:%H:%M}" for p in sorted(ps, key=lambda p: p['debut'])))
    lignes.append(f"  ... {len(benevoles) - len(charge)} bénévole(s) sans affectation")

    if plan_fige:
        actuels = {(a["benevole_id"], a["poste_id"]) for a in affectations}
        retires = sorted(set(plan_fige) - actuels)
        ajoutes = sorted(actuels - set(plan_fige))
        lignes += ["", f"Écarts au plan figé : {len(retires)} retrait(s), {len(ajoutes)} ajout(s)"]
        for bid, pid in retires:
            lignes.append(f"  - {B[bid]['nom'] if bid in B else bid:<24} quitte {pid} {P[pid]['nom'][:40]} ({plan_fige[(bid, pid)]})")
        for bid, pid in ajoutes:
            lignes.append(f"  + {B[bid]['nom']:<24} prend  {pid} {P[pid]['nom'][:40]}")
    texte = "\n".join(lignes)
    print(texte)
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "rapport.txt").write_text(texte, encoding="utf-8")
    plan = {"version": 1, "statut": "brouillon", "calcule_le": datetime.now().isoformat(timespec="minutes"),
            "score": score, "affectations": affectations, "trous": trous, "postes_sans_responsable": sans_resp,
            "plan_fige": bool(plan_fige)}
    (sortie / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ici = Path(__file__).resolve().parent
    ap.add_argument("--data", default=str(ici.parent / "data"))
    ap.add_argument("--sortie", default=str(ici / "sortie"))
    ap.add_argument("--benevoles", default="", help="autre fichier bénévoles (même format que data/benevoles.csv)")
    ap.add_argument("--postes", default="", help="autre fichier postes (ex. construit depuis le roadbook)")
    ap.add_argument("--plan-fige", default="", help="plan.json publié : le solveur minimise les écarts avec lui")
    ap.add_argument("--absents", default="", help="jour J : ids qui ne viennent plus, séparés par des virgules")
    ap.add_argument("--heure", default="", help="jour J : heure courante ISO ; les créneaux commencés sont 'en poste'")
    args = ap.parse_args()
    postes, benevoles, trajets, battements = charger(Path(args.data), Path(args.benevoles) if args.benevoles else None, Path(args.postes) if args.postes else None)
    absents = {a for a in args.absents.split(",") if a}
    benevoles = [b for b in benevoles if b["id"] not in absents]
    plan_fige = None
    if args.plan_fige:
        publie = json.loads(Path(args.plan_fige).read_text(encoding="utf-8"))
        heure = datetime.fromisoformat(args.heure) if args.heure else None
        P = {p["id"]: p for p in postes}
        plan_fige = {(a["benevole_id"], a["poste_id"]): ("en_poste" if heure and P[a["poste_id"]]["debut"] <= heure else "notifie")
                     for a in publie["affectations"] if a["benevole_id"] not in absents}
        if heure:
            # Les créneaux déjà terminés ne bougent plus : on les sort du problème.
            # Les créneaux en cours restent, pour pouvoir y ajouter du monde.
            termines = {p["id"] for p in postes if p["fin"] <= heure}
            postes = [p for p in postes if p["id"] not in termines]
            plan_fige = {k: v for k, v in plan_fige.items() if k[1] not in termines}
    s, v, statut, relache = resoudre(postes, benevoles, trajets, battements, plan_fige=plan_fige)
    rapport(s, v, statut, relache, postes, benevoles, Path(args.sortie), plan_fige)
