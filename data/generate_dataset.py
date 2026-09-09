"""Génère le jeu de données de démo pour l'agent de coordination des bénévoles.

Course de référence : SwissPeaks Marathon 2025 (46 km, 2 480 m D+), départ Morgins
le samedi 6 septembre 2025 à 09h00, arrivée Le Bouveret. Les points de passage,
altitudes, distances, horaires du premier et du dernier coureur et barrières
horaires viennent du roadbook coureurs officiel 2025 (pages 23 et 24).

Tout le reste (postes hors ravitaillements, effectifs, bénévoles, disponibilités,
compétences, cas pièges) est synthétique et généré ici de façon reproductible.

Usage : python generate_dataset.py   (écrit les fichiers dans le dossier courant)
"""
from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta

random.seed(2025)

RACE_DAY = "2025-09-06"          # samedi
DAY_BEFORE = "2025-09-05"        # vendredi
DAY_AFTER = "2025-09-07"         # dimanche


def t(day: str, hhmm: str) -> str:
    return f"{day}T{hhmm}:00"


def shift(day: str, hhmm: str, minutes: int) -> str:
    base = datetime.fromisoformat(t(day, hhmm)) + timedelta(minutes=minutes)
    return base.strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------------------
# 1. La course : données réelles du roadbook
# ---------------------------------------------------------------------------
course = {
    "evenement": "SwissPeaks Trail 2025",
    "course": "SwissPeaks Marathon",
    "source": "Roadbook coureurs 2025 (FR), pages 23 et 24, édité par l'organisation",
    "distance_km": 46,
    "denivele_positif_m": 2483,
    "denivele_negatif_m": 3453,
    "depart": {"lieu": "Morgins", "date_heure": t(RACE_DAY, "09:00")},
    "arrivee": {"lieu": "Le Bouveret, quai Bussien"},
    "coureurs_max": 500,
    "temps_max": "14:00",
    "premier_estime": "04:30",
    "retrait_dossards": [
        {"lieu": "Le Bouveret, quai Bussien", "debut": t(DAY_BEFORE, "15:00"), "fin": t(DAY_BEFORE, "19:00")},
        {"lieu": "Morgins, route de France 33 (tennis)", "debut": t(RACE_DAY, "07:30"), "fin": t(RACE_DAY, "08:30")},
    ],
    "navettes_coureurs": [
        {"trajet": "Le Bouveret (parking voitures) vers Morgins", "depart": t(DAY_BEFORE, "17:00")},
        {"trajet": "Le Bouveret (parking voitures) vers Morgins", "depart": t(RACE_DAY, "07:00")},
    ],
    "points_de_passage": [
        # nom, altitude, km cumulé, D+ cumulé, D- cumulé, 1er coureur, dernier coureur, barrière, services
        {"nom": "Morgins", "altitude_m": 1342, "km": 0, "dplus_cumul": 0, "dmoins_cumul": 0,
         "premier": t(RACE_DAY, "09:00"), "dernier": t(RACE_DAY, "09:00"), "barriere": None,
         "services": ["depart"], "assistance_perso": False, "acces": "route, village"},
        {"nom": "Chalet de Conche", "altitude_m": 1693, "km": 6, "dplus_cumul": 475, "dmoins_cumul": 124,
         "premier": t(RACE_DAY, "09:45"), "dernier": t(RACE_DAY, "10:45"), "barriere": None,
         "services": ["ravitaillement", "bus_abandon"], "assistance_perso": True, "acces": "route d'alpage"},
        {"nom": "Chalet de Blancsex", "altitude_m": 1500, "km": 19, "dplus_cumul": 1286, "dmoins_cumul": 1128,
         "premier": t(RACE_DAY, "11:00"), "dernier": t(RACE_DAY, "14:00"), "barriere": t(RACE_DAY, "14:00"),
         "services": ["ravitaillement", "bus_abandon", "barriere_horaire"], "assistance_perso": True,
         "acces": "parking puis accès à pied (assistance), véhicules organisation seulement"},
        {"nom": "Taney", "altitude_m": 1416, "km": 25, "dplus_cumul": 1716, "dmoins_cumul": 1644,
         "premier": t(RACE_DAY, "11:45"), "dernier": t(RACE_DAY, "16:15"), "barriere": None,
         "services": ["ravitaillement"], "assistance_perso": True,
         "acces": "accès voiture interdit : parking obligatoire à Le Flon puis taxi payant ou montée à pied (400 m D+)"},
        {"nom": "Le Grand Pré", "altitude_m": 903, "km": 35, "dplus_cumul": 2268, "dmoins_cumul": 2707,
         "premier": t(RACE_DAY, "12:45"), "dernier": t(RACE_DAY, "20:00"), "barriere": None,
         "services": ["ravitaillement"], "assistance_perso": True, "acces": "route"},
        {"nom": "Le Bouveret", "altitude_m": 372, "km": 46, "dplus_cumul": 2483, "dmoins_cumul": 3453,
         "premier": t(RACE_DAY, "13:30"), "dernier": t(RACE_DAY, "23:00"), "barriere": t(RACE_DAY, "23:00"),
         "services": ["arrivee", "barriere_horaire", "repas_chaud", "sac_suiveur", "point_de_secours", "douche", "massage"],
         "assistance_perso": False, "acces": "village, quai Bussien"},
    ],
    # Le SP70 (73 km, départ Val d'Illiez 05h00 le même jour) partage plusieurs postes avec le Marathon.
    # Horaires du roadbook page 25. Utile pour dimensionner les postes partagés.
    "autres_courses_sur_les_memes_postes": [
        {"course": "SwissPeaks 70", "poste": "Morgins", "km": 26.8, "premier": t(RACE_DAY, "08:00"), "dernier": t(RACE_DAY, "11:00"), "barriere": t(RACE_DAY, "11:00")},
        {"course": "SwissPeaks 70", "poste": "Chalet de Conche", "km": 32.8, "premier": t(RACE_DAY, "08:45"), "dernier": t(RACE_DAY, "12:30"), "barriere": None},
        {"course": "SwissPeaks 70", "poste": "Chalet de Blancsex", "km": 45.8, "premier": t(RACE_DAY, "10:00"), "dernier": t(RACE_DAY, "15:30"), "barriere": t(RACE_DAY, "15:30")},
        {"course": "SwissPeaks 70", "poste": "Taney", "km": 51.7, "premier": t(RACE_DAY, "10:45"), "dernier": t(RACE_DAY, "17:30"), "barriere": None},
        {"course": "SwissPeaks 70", "poste": "Le Grand Pré", "km": 61.4, "premier": t(RACE_DAY, "12:00"), "dernier": t(RACE_DAY, "20:45"), "barriere": None},
        {"course": "SwissPeaks 70", "poste": "Le Bouveret", "km": 72.5, "premier": t(RACE_DAY, "13:00"), "dernier": t(RACE_DAY, "23:30"), "barriere": t(RACE_DAY, "23:30")},
    ],
}

# ---------------------------------------------------------------------------
# 2. Les sites et les temps de trajet (estimations, en voiture, hors course)
# ---------------------------------------------------------------------------
sites = [
    {"site": "Le Bouveret", "type": "village", "acces_vehicule": True, "notes": "Arrivée, dossards, parking Bellossy, quai Bussien"},
    {"site": "Morgins", "type": "village", "acces_vehicule": True, "notes": "Départ, dossards au tennis (route de France 33)"},
    {"site": "Chalet de Conche", "type": "alpage", "acces_vehicule": True, "notes": "Route d'alpage, véhicule conseillé"},
    {"site": "Chalet de Blancsex", "type": "alpage", "acces_vehicule": False, "notes": "Parking en contrebas puis 20 à 30 min à pied ; 4x4 organisation pour le matériel"},
    {"site": "Taney", "type": "alpage", "acces_vehicule": False, "notes": "Parking à Le Flon puis 400 m D+ à pied (1h) ou taxi"},
    {"site": "Le Grand Pré", "type": "hameau", "acces_vehicule": True, "notes": "Route"},
]

trajets = [
    ("Le Bouveret", "Morgins", 45),
    ("Le Bouveret", "Chalet de Conche", 55),
    ("Le Bouveret", "Chalet de Blancsex", 40),   # jusqu'au parking, puis marche
    ("Le Bouveret", "Taney", 25),                # jusqu'au parking Le Flon, puis 60 min à pied
    ("Le Bouveret", "Le Grand Pré", 15),
    ("Morgins", "Chalet de Conche", 15),
    ("Morgins", "Chalet de Blancsex", 50),
    ("Morgins", "Taney", 60),
    ("Morgins", "Le Grand Pré", 40),
    ("Chalet de Conche", "Chalet de Blancsex", 55),
    ("Chalet de Blancsex", "Taney", 35),
    ("Taney", "Le Grand Pré", 20),
    ("Chalet de Blancsex", "Le Grand Pré", 35),
    ("Chalet de Conche", "Taney", 65),
    ("Chalet de Conche", "Le Grand Pré", 50),
]
marche_supplementaire = {"Chalet de Blancsex": 25, "Taney": 60}

# ---------------------------------------------------------------------------
# 3. Les postes et leurs créneaux
#    Règle de calcul : un ravitaillement ouvre 60 min avant le premier coureur
#    (montage) et ferme 30 min après le dernier coureur ou la barrière (démontage).
#    Quand un poste sert aussi au SP70, la fenêtre est l'union des deux courses.
# ---------------------------------------------------------------------------
postes: list[dict] = []


def add(poste_id, nom, site, categorie, debut, fin, mini, ideal, competences="", chef_requis=False, notes="", origine="roadbook"):
    postes.append({
        "poste_id": poste_id, "nom": nom, "site": site, "categorie": categorie,
        "debut": debut, "fin": fin, "effectif_min": mini, "effectif_ideal": ideal,
        "competences_requises": competences, "chef_de_poste_requis": chef_requis,
        "notes": notes, "origine": origine,
    })


# Vendredi 5 septembre
add("V01", "Retrait des dossards Marathon", "Le Bouveret", "dossards", t(DAY_BEFORE, "14:30"), t(DAY_BEFORE, "19:15"), 4, 6,
    "controle_materiel", True, "Contrôle pièce d'identité et matériel obligatoire, remise du bracelet")
add("V02", "Accueil navette coureurs 17h00", "Le Bouveret", "navette", t(DAY_BEFORE, "16:30"), t(DAY_BEFORE, "17:15"), 1, 2,
    "", False, "Vérification des réservations au parking voitures")
add("V03", "Préparation logistique ravitos (chargement)", "Le Bouveret", "logistique", t(DAY_BEFORE, "13:00"), t(DAY_BEFORE, "17:00"), 3, 5,
    "permis_B", False, "Chargement des camionnettes : tables, eau, boissons, barres", origine="hypothese")

add("V04", "Livraison des postes isolés (Blancsex, Taney) en 4x4", "Chalet de Blancsex", "logistique", t(DAY_BEFORE, "13:00"), t(DAY_BEFORE, "18:00"), 2, 3,
    "permis_B,4x4,montagne", False, "Eau, tables, matériel sec déposés la veille au chalet ; le frais monte le matin avec l'équipe", origine="hypothese")

# Samedi matin, départ
add("S00", "Livraison du frais aux postes accessibles (Conche, Grand Pré)", "Chalet de Conche", "logistique", t(RACE_DAY, "06:00"), t(RACE_DAY, "09:00"), 2, 2,
    "permis_B", False, "Camionnette : Conche avant 07h45, puis Grand Pré", origine="hypothese")
add("S26", "Réserve volante au PC (véhicule chargé)", "Le Bouveret", "reserve_volante", t(RACE_DAY, "08:00"), t(RACE_DAY, "23:00"), 2, 3,
    "permis_B,vehicule", False, "Sans poste fixe. Réassort eau, remplacement, transport d'un bénévole. Idéalement un 4x4 et une personne apte montagne. Deux créneaux conseillés.", origine="hypothese")
add("S01", "Accueil navette coureurs 07h00", "Le Bouveret", "navette", t(RACE_DAY, "06:30"), t(RACE_DAY, "07:15"), 1, 2)
add("S02", "Retrait des dossards Marathon (Morgins)", "Morgins", "dossards", t(RACE_DAY, "07:00"), t(RACE_DAY, "08:45"), 3, 5,
    "controle_materiel", True, "Tennis, route de France 33")
add("S03", "Zone de départ (sas, consignes, sacs)", "Morgins", "depart", t(RACE_DAY, "07:30"), t(RACE_DAY, "09:30"), 4, 6,
    "", True, "Gestion du sas, dépose des sacs 15 min avant le départ", origine="hypothese")
add("S04", "Signaleurs traversée de route au départ", "Morgins", "signaleur", t(RACE_DAY, "08:30"), t(RACE_DAY, "09:45"), 2, 3,
    "majeur,gilet", False, "Route cantonale à la sortie du village, 2 côtés", origine="hypothese")
add("S05", "Ravitaillement Morgins (SP70) + départ Marathon", "Morgins", "ravitaillement", t(RACE_DAY, "07:00"), t(RACE_DAY, "11:30"), 4, 6,
    "", True, "Ravito du SP70 (premier 08h00, barrière 11h00) au même endroit que le départ du Marathon")

# Samedi, postes de parcours
add("S06", "Ravitaillement Chalet de Conche", "Chalet de Conche", "ravitaillement", t(RACE_DAY, "07:45"), t(RACE_DAY, "13:00"), 4, 6,
    "", True, "Premier SP70 08h45, dernier Marathon 10h45, dernier SP70 12h30. Bus abandon sur place.")
add("S07", "Chef de poste + pointage Chalet de Conche", "Chalet de Conche", "pointage", t(RACE_DAY, "07:45"), t(RACE_DAY, "13:00"), 1, 2,
    "experience,telephone", False, "Pointage manuel de secours, liaison PC course", origine="hypothese")
add("S08", "Ravitaillement Chalet de Blancsex, créneau matin", "Chalet de Blancsex", "ravitaillement", t(RACE_DAY, "09:00"), t(RACE_DAY, "12:30"), 4, 6,
    "montagne", True, "Accès à pied depuis le parking (25 min). Premier SP70 10h00, premier Marathon 11h00.")
add("S09", "Ravitaillement Chalet de Blancsex, créneau après-midi", "Chalet de Blancsex", "ravitaillement", t(RACE_DAY, "12:00"), t(RACE_DAY, "16:00"), 4, 6,
    "montagne", True, "Barrière Marathon 14h00, barrière SP70 15h30. Gestion des abandons et du bus.")
add("S10", "Barrière horaire et abandons Blancsex", "Chalet de Blancsex", "controle", t(RACE_DAY, "13:00"), t(RACE_DAY, "16:00"), 2, 2,
    "experience,montagne,telephone", False, "Invalidation des dossards, récupération des puces, comptage bus")
add("S11", "Ravitaillement Taney, créneau matin", "Taney", "ravitaillement", t(RACE_DAY, "09:45"), t(RACE_DAY, "14:00"), 3, 5,
    "montagne", True, "Montée à pied 400 m D+ depuis Le Flon (1h) ou taxi. Premier SP70 10h45, premier Marathon 11h45.")
add("S12", "Ravitaillement Taney, créneau après-midi", "Taney", "ravitaillement", t(RACE_DAY, "13:30"), t(RACE_DAY, "18:00"), 3, 5,
    "montagne", True, "Dernier Marathon 16h15, dernier SP70 17h30")
add("S13", "Ravitaillement Le Grand Pré, créneau 1", "Le Grand Pré", "ravitaillement", t(RACE_DAY, "11:00"), t(RACE_DAY, "16:00"), 4, 6,
    "", True, "Premier SP70 12h00, premier Marathon 12h45")
add("S14", "Ravitaillement Le Grand Pré, créneau 2", "Le Grand Pré", "ravitaillement", t(RACE_DAY, "15:30"), t(RACE_DAY, "21:15"), 4, 6,
    "", True, "Dernier Marathon 20h00, dernier SP70 20h45, nuit à partir de 20h00 : frontales")
add("S15", "Signaleurs traversée de route Le Grand Pré", "Le Grand Pré", "signaleur", t(RACE_DAY, "11:30"), t(RACE_DAY, "21:00"), 2, 4,
    "majeur,gilet", False, "Traversée de la route, 2 personnes en permanence, relève à 16h00", origine="hypothese")
add("S16", "Serre-file Morgins vers Blancsex", "Chalet de Conche", "serre_file", t(RACE_DAY, "09:00"), t(RACE_DAY, "14:30"), 2, 2,
    "trail,montagne,telephone,PSC1", False, "Partent derrière le dernier coureur, débalisent, signalent au PC", origine="hypothese")
add("S17", "Serre-file Blancsex vers Bouveret", "Chalet de Blancsex", "serre_file", t(RACE_DAY, "14:00"), t(RACE_DAY, "23:30"), 2, 2,
    "trail,montagne,telephone,PSC1,frontale", False, "Section de nuit possible après Le Grand Pré", origine="hypothese")

# Samedi, arrivée au Bouveret
add("S18", "Arrivée : ligne, médailles et bracelets, créneau 1", "Le Bouveret", "arrivee", t(RACE_DAY, "12:00"), t(RACE_DAY, "18:00"), 4, 6,
    "", True, "Premier SP70 13h00, premier Marathon 13h30")
add("S19", "Arrivée : ligne, médailles et bracelets, créneau 2", "Le Bouveret", "arrivee", t(RACE_DAY, "17:30"), t(DAY_AFTER, "00:15"), 4, 6,
    "", True, "Barrière Marathon 23h00, barrière SP70 23h30")
add("S20", "Repas chaud finishers", "Le Bouveret", "restauration", t(RACE_DAY, "12:30"), t(RACE_DAY, "23:30"), 4, 8,
    "hygiene", False, "Deux services conseillés : 12h30-18h00 et 17h30-23h30", origine="hypothese")
add("S21", "Sacs suiveurs et consigne", "Le Bouveret", "logistique", t(RACE_DAY, "12:30"), t(RACE_DAY, "23:30"), 2, 3,
    "", False, "Restitution des sacs sur présentation du dossard")
add("S22", "Assistance point de secours (aide aux secouristes)", "Le Bouveret", "secours", t(RACE_DAY, "13:00"), t(RACE_DAY, "23:30"), 2, 3,
    "PSC1", False, "Les soins sont assurés par les samaritains, les bénévoles orientent et accompagnent")
add("S23", "Signaleurs traversée quai Bussien", "Le Bouveret", "signaleur", t(RACE_DAY, "12:30"), t(RACE_DAY, "23:15"), 2, 4,
    "majeur,gilet", False, "Relève conseillée à 18h00", origine="hypothese")
add("S24", "Parking Bellossy et navettes", "Le Bouveret", "parking", t(RACE_DAY, "06:00"), t(RACE_DAY, "20:00"), 2, 4,
    "gilet", False, "Orientation des véhicules, 2 créneaux conseillés", origine="hypothese")
add("S25", "PC course : standard téléphonique et suivi live", "Le Bouveret", "pc_course", t(RACE_DAY, "08:00"), t(DAY_AFTER, "00:00"), 2, 3,
    "experience,informatique", True, "Réception des pointages, appels des chefs de poste, suivi des abandons", origine="hypothese")

# Dimanche
add("D01", "Démontage et rangement du matériel", "Le Bouveret", "logistique", t(DAY_AFTER, "14:00"), t(DAY_AFTER, "18:00"), 4, 8,
    "", False, "Après le Semi-Marathon du dimanche", origine="hypothese")

# Découpe des postes trop longs en créneaux (règle du plan : au-delà de 6 h, on coupe
# en créneaux d'environ 5 h qui se chevauchent de 30 min pour la relève).
def decouper(postes, max_minutes=360, cible_minutes=300, chevauchement=30):
    import math
    out = []
    for p in postes:
        d, f = datetime.fromisoformat(p["debut"]), datetime.fromisoformat(p["fin"])
        duree = int((f - d).total_seconds() // 60)
        if duree <= max_minutes:
            out.append(p); continue
        n = math.ceil(duree / cible_minutes)
        bornes = [d + timedelta(minutes=round(duree * k / n / 15) * 15) for k in range(n + 1)]
        for k in range(n):
            q = dict(p)
            q["poste_id"] = f"{p['poste_id']}{'abcdef'[k]}"
            q["nom"] = f"{p['nom']}, créneau {k + 1}/{n}"
            q["debut"] = bornes[k].strftime("%Y-%m-%dT%H:%M:%S")
            fin_k = bornes[k + 1] + timedelta(minutes=chevauchement) if k < n - 1 else f
            q["fin"] = fin_k.strftime("%Y-%m-%dT%H:%M:%S")
            out.append(q)
    return out


postes = decouper(postes)

# ---------------------------------------------------------------------------
# 4. Les bénévoles synthétiques
# ---------------------------------------------------------------------------
PRENOMS = ["Julie", "Marc", "Sophie", "Nicolas", "Laura", "Thomas", "Camille", "David", "Emma", "Yann",
           "Léa", "Fabien", "Anne", "Cédric", "Marion", "Loïc", "Chloé", "Steve", "Aurélie", "Jonas",
           "Manon", "Vincent", "Sarah", "Kevin", "Elodie", "Sébastien", "Nadia", "Grégory", "Isabelle", "Mathieu",
           "Sandra", "Bastien", "Céline", "Pascal", "Jessica", "Olivier", "Valérie", "Alexandre", "Nathalie", "Romain",
           "Florence", "Christophe", "Mélanie", "Jérôme", "Stéphanie", "Pierre-Alain", "Corinne", "Raphaël", "Sylvie", "Damien",
           "Anaïs", "Frédéric", "Josiane", "Michel", "Claudine", "Gérard", "Lucie", "Hugo", "Noémie", "Arnaud",
           "Maëlle", "Simon", "Justine", "Benoît", "Océane", "Lucas", "Amélie", "Guillaume", "Charlotte", "Xavier",
           "Inès", "Killian", "Zoé", "Théo", "Margaux"]
NOMS = ["Favre", "Bochatay", "Vuadens", "Carraux", "Défago", "Rey-Bellet", "Grenon", "Mariétan", "Roch", "Clerc",
        "Derivaz", "Curdy", "Bressoud", "Vannay", "Fornay", "Trombert", "Perrin", "Gex-Fabry", "Berrut", "Dubosson",
        "Chevalley", "Pittet", "Monnay", "Pellaud", "Gross", "Rouiller", "Michellod", "Bonvin", "Gay-Balmaz", "Zufferey",
        "Salamin", "Barman", "Cornut", "Morisod", "Rappaz", "Saudan", "Lattion", "Bender", "Praz", "Fellay"]
COMMUNES = ["Le Bouveret", "Port-Valais", "Vouvry", "Vionnaz", "Monthey", "Collombey", "Saint-Gingolph", "Morgins",
            "Troistorrents", "Val-d'Illiez", "Champéry", "Aigle", "Villeneuve", "Évian (FR)", "Thonon (FR)", "Martigny"]
LANGUES_OPTIONS = ["FR", "FR,EN", "FR,DE", "FR,DE,EN", "DE,EN", "FR,IT"]
ROLES = ["ravitaillement", "dossards", "signaleur", "arrivee", "logistique", "serre_file", "pc_course", "restauration", "parking", "pointage"]

DISPOS_TYPES = [
    # (vendredi, samedi, dimanche) sous forme de plages "HH:MM-HH:MM" ou "" ; "24:00" = minuit ;
    # une plage du dimanche qui commence à 00:00 prolonge celle du samedi (jusqu'à 1h du matin)
    ("", "06:00-24:00", ""),
    ("", "06:00-24:00", ""),
    ("", "06:00-24:00", "13:00-18:00"),
    ("14:00-19:30", "06:00-24:00", ""),
    ("13:00-19:00", "06:00-24:00", "13:00-18:00"),
    ("", "06:00-24:00", "00:00-01:00,13:00-18:00"),
    ("", "12:00-24:00", "00:00-01:00"),
    ("", "07:00-14:00", ""),
    ("", "12:00-24:00", ""),
    ("", "06:00-13:00", "13:00-18:00"),
    ("13:00-19:30", "", "13:00-18:00"),
    ("", "08:00-18:00", ""),
    ("", "15:00-24:00", "00:00-01:00"),
    ("", "06:00-12:00", ""),
    ("", "10:00-20:00", ""),
    ("13:00-19:30", "06:00-24:00", ""),
]


def make_volunteer(i: int) -> dict:
    prenom = PRENOMS[i % len(PRENOMS)]
    nom = random.choice(NOMS)
    age = random.choice([17, 19, 22, 24, 27, 29, 31, 34, 36, 38, 41, 43, 45, 48, 52, 55, 58, 61, 64, 67, 71])
    ven, sam, dim = random.choice(DISPOS_TYPES)
    editions = random.choice([0, 0, 0, 1, 1, 2, 3, 5, 8])
    permis = age >= 18 and random.random() < 0.88
    vehicule = permis and random.random() < 0.85
    return {
        "benevole_id": f"B{i:03d}",
        "prenom": prenom, "nom": nom, "age": age,
        "commune": random.choice(COMMUNES),
        "email": f"{prenom.lower().replace('ï','i').replace('é','e').replace('è','e').replace('ë','e').replace('-','')}.{nom.lower().replace(' ','').replace('-','')}@example.org",
        "telephone": f"+41 79 {random.randint(100,999)} {random.randint(10,99)} {random.randint(10,99)}",
        "dispo_vendredi": ven, "dispo_samedi": sam, "dispo_dimanche": dim,
        "editions_precedentes": editions,
        "PSC1_ou_samaritain": random.random() < 0.38,
        "permis_B": permis,
        "vehicule": vehicule,
        "vehicule_4x4": vehicule and random.random() < 0.25,
        "apte_marche_montagne": random.random() < (0.8 if age < 60 else 0.35),
        "pratique_trail": random.random() < 0.5,
        "langues": random.choice(LANGUES_OPTIONS),
        "roles_preferes": ",".join(sorted(random.sample(ROLES, random.choice([1, 2, 3])))),
        "accepte_nuit": random.random() < 0.7,
        "accepte_chef_de_poste": (editions >= 2 and random.random() < 0.7) or (editions == 1 and random.random() < 0.25),
        "binome_souhaite": "",
        "accompagnants": 0,
        "contraintes": "",
        "commentaire_libre": "",
    }


NB_BENEVOLES = 100
benevoles = [make_volunteer(i) for i in range(1, NB_BENEVOLES + 1)]

# Pas deux vrais homonymes dans le jeu (les doublons volontaires sont ajoutés plus bas, exprès)
_vus = set()
for b in benevoles:
    while (b["prenom"], b["nom"]) in _vus:
        b["nom"] = NOMS[(NOMS.index(b["nom"]) + 1) % len(NOMS)]
    _vus.add((b["prenom"], b["nom"]))

# Quelques commentaires libres réalistes (comme sur un formulaire d'inscription)
commentaires = [
    "Je peux apporter mon barnum 3x3 si besoin.",
    "Disponible mais je dois récupérer mes enfants à 17h.",
    "Déjà fait Blancsex l'an dernier, je connais le poste.",
    "Pas de station debout prolongée (genou).",
    "Je parle allemand, utile pour les coureurs suisses alémaniques.",
    "Je viens en train, pas de voiture.",
    "OK pour la nuit si on me ramène au Bouveret après.",
    "Je préfère être avec des gens que je connais.",
    "Première fois, mettez-moi où vous voulez.",
    "J'ai un chien, est-ce que je peux le prendre au ravito ?",
]
for b in random.sample(benevoles, 18):
    c = random.choice(commentaires)
    if "enfants" in c and b["age"] < 28:
        c = "Première fois, mettez-moi où vous voulez."
    b["commentaire_libre"] = c

# Quelques responsables viennent avec des personnes non listées
_n = [3, 2, 2, 3]
for b in [b for b in benevoles if b["accepte_chef_de_poste"]][:4]:
    b["accompagnants"] = _n.pop(0)
    b["commentaire_libre"] = f"Je viens avec {b['accompagnants']} personnes, on prend un ravito ensemble."

# Binômes cohérents
pairs = [(4, 5), (12, 13), (30, 31)]
for a, c in pairs:
    benevoles[a]["binome_souhaite"] = benevoles[c]["benevole_id"]
    benevoles[c]["binome_souhaite"] = benevoles[a]["benevole_id"]
    benevoles[c]["dispo_vendredi"], benevoles[c]["dispo_samedi"], benevoles[c]["dispo_dimanche"] = (
        benevoles[a]["dispo_vendredi"], benevoles[a]["dispo_samedi"], benevoles[a]["dispo_dimanche"])

# ---------------------------------------------------------------------------
# 5. Les cas pièges (pour l'agent contradicteur)
# ---------------------------------------------------------------------------
cas_pieges = []


def piege(idx: int, titre: str, attendu: str, **changes):
    b = benevoles[idx]
    b.update(changes)
    cas_pieges.append({"benevole_id": b["benevole_id"], "nom": f"{b['prenom']} {b['nom']}", "titre": titre, "ce_que_l_agent_doit_detecter": attendu})


piege(40, "Binôme souhaité incompatible", "B041 veut être avec B042 mais leurs disponibilités du samedi ne se recouvrent pas",
      binome_souhaite="B042", dispo_samedi="06:00-12:00")
benevoles[41].update(binome_souhaite="B041", dispo_samedi="15:00-24:00")

piege(43, "Mineur", "17 ans : pas de poste signaleur seul sur route, pas de créneau après 22h00, pas de serre-file",
      age=17, permis_B=False, vehicule=False, vehicule_4x4=False, roles_preferes="signaleur,serre_file", accepte_nuit=True)

piege(45, "Dit être partout mais ne peut pas monter", "Souhaite Taney ou Blancsex mais 71 ans et non apte marche montagne : accès Taney = 400 m D+ à pied",
      age=71, apte_marche_montagne=False, roles_preferes="ravitaillement", commentaire_libre="Mettez-moi à Taney, j'adore cet endroit.")

piege(47, "Disponibilité partielle sur le créneau", "Dispo samedi 06:00-13:00 seulement : ne couvre aucun créneau d'arrivée ni de Grand Pré en entier",
      dispo_samedi="06:00-13:00", roles_preferes="arrivee")

piege(49, "Doublon d'inscription", "B050 et B051 sont la même personne (même téléphone, orthographe différente du prénom)",
      prenom="Pierre-Alain", nom="Défago", telephone="+41 79 512 44 18", email="pa.defago@example.org")
benevoles[50].update(prenom="Pierre Alain", nom="Defago", telephone="+41 79 512 44 18", email="pierrealain.defago@example.org")
cas_pieges[-1]["benevole_id"] = "B050,B051"

piege(52, "Bénévole aussi coureur du Marathon", "Inscrit comme coureur du Marathon (dossard 312) : indisponible samedi de 07h00 à son arrivée, ne peut tenir que vendredi ou dimanche",
      commentaire_libre="Je cours le Marathon (dossard 312) mais je peux aider le vendredi soir et le dimanche.", dispo_samedi="06:00-24:00")

piege(54, "Trajet impossible entre deux postes", "Si affecté à la navette 07h00 au Bouveret puis aux dossards à Morgins 07h30 : 45 min de route, impossible",
      roles_preferes="navette,dossards", dispo_samedi="06:00-12:00", vehicule=True, permis_B=True)

piege(56, "Sans véhicule sur un poste isolé", "Vient en train, pas de voiture : ne peut pas rejoindre Chalet de Conche à 07h45 sans covoiturage organisé",
      permis_B=False, vehicule=False, vehicule_4x4=False, roles_preferes="ravitaillement", dispo_samedi="06:00-24:00",
      commentaire_libre="Je viens en train, pas de voiture.")

piege(58, "Refuse la nuit mais seule dispo tardive", "Dispo 15:00-24:00 mais accepte_nuit = non : ne peut pas tenir Grand Pré créneau 2 ni l'arrivée après 20h00 sans accord explicite",
      dispo_samedi="15:00-24:00", accepte_nuit=False)

piege(60, "Contrainte médicale incompatible avec le poste préféré", "Genou : pas de station debout prolongée, incompatible avec signaleur 9h30 d'affilée",
      contraintes="pas de station debout prolongée", roles_preferes="signaleur", commentaire_libre="Pas de station debout prolongée (genou).")

piege(62, "Chef de poste sans expérience", "Se propose chef de poste avec 0 édition précédente : à valider par l'organisateur, pas automatique",
      editions_precedentes=0, accepte_chef_de_poste=True, roles_preferes="ravitaillement")

# Piège structurel (pas lié à un bénévole) : pénurie de PSC1
cas_pieges.append({"benevole_id": "", "nom": "", "titre": "Pénurie de PSC1 sur les serre-files",
                   "ce_que_l_agent_doit_detecter": "Les deux postes serre-file demandent PSC1 + trail + montagne : vérifier qu'il existe assez de profils, sinon alerter l'organisateur au lieu d'affecter sans PSC1"})
cas_pieges.append({"benevole_id": "", "nom": "", "titre": "Postes partagés avec le SP70",
                   "ce_que_l_agent_doit_detecter": "Blancsex, Taney, Grand Pré et Bouveret reçoivent les deux courses : la fenêtre du poste est l'union des deux, pas seulement celle du Marathon"})
cas_pieges.append({"benevole_id": "", "nom": "", "titre": "Créneau qui dépasse minuit",
                   "ce_que_l_agent_doit_detecter": "L'arrivée créneau 2 finit à 00:15 le dimanche : les disponibilités 'jusqu'à 24:00' du samedi ne couvrent pas la fin"})

# ---------------------------------------------------------------------------
# 6. Écriture des fichiers
# ---------------------------------------------------------------------------
with open("course_marathon.json", "w", encoding="utf-8") as f:
    json.dump(course, f, ensure_ascii=False, indent=2)


def write_csv(name: str, rows: list[dict]):
    with open(name, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)


write_csv("sites.csv", sites)
write_csv("trajets.csv", [{"de": a, "vers": b, "minutes_voiture": m,
                           "marche_supplementaire_min": marche_supplementaire.get(b, 0)} for a, b, m in trajets]
          + [{"de": b, "vers": a, "minutes_voiture": m, "marche_supplementaire_min": marche_supplementaire.get(a, 0)} for a, b, m in trajets])
write_csv("postes.csv", postes)
write_csv("benevoles.csv", benevoles)

# ---------------------------------------------------------------------------
# 6 bis. Le formulaire tel que les gens le remplissent : 6 colonnes, texte libre.
#        C'est l'entrée réelle du produit ; benevoles.csv est la vérité pour tester la traduction.
# ---------------------------------------------------------------------------
_rf = random.Random(7)


def _plage(txt):
    if not txt:
        return ""
    if "," in txt:
        return " et ".join(_plage(x) for x in txt.split(","))
    if txt == "00:00-01:00":
        return _rf.choice(["jusqu'à 1h du matin", "je peux rester jusqu'à 1h", "encore une heure après minuit"])
    d, f = txt.split("-")
    h = lambda x: ("minuit" if x == "24:00" else (x[:2].lstrip("0") or "0") + "h" + ("" if x[3:] == "00" else x[3:]))
    if txt == "06:00-24:00":
        return _rf.choice(["toute la journée", "du matin jusqu'à minuit", "dispo toute la journée et le soir", "toute la journée"])
    return _rf.choice([f"de {h(d)} à {h(f)}", f"{h(d)}-{h(f)}", f"entre {h(d)} et {h(f)}"])


def _dispos(b):
    morceaux = []
    for jour, cle in (("vendredi", "dispo_vendredi"), ("samedi", "dispo_samedi"), ("dimanche", "dispo_dimanche")):
        if b[cle]:
            morceaux.append(f"{jour} {_plage(b[cle])}")
    if not morceaux:
        return _rf.choice(["pas dispo finalement", "à confirmer"])
    if b["benevole_id"] == "B053":
        return "Je cours le Marathon samedi (dossard 312) mais je peux aider le vendredi soir et le dimanche après-midi"
    return _rf.choice([", ".join(morceaux), " et ".join(morceaux), "Je suis libre " + ", ".join(morceaux)])


def _sait_faire(b):
    c = []
    if b["PSC1_ou_samaritain"]: c.append(_rf.choice(["j'ai le PSC1", "samaritain", "formation premiers secours à jour"]))
    if b["permis_B"]: c.append("permis")
    if b["vehicule_4x4"]: c.append(_rf.choice(["j'ai un 4x4", "pick-up 4x4 dispo"]))
    elif b["vehicule"]: c.append(_rf.choice(["j'ai une voiture", "véhiculé"]))
    if b["apte_marche_montagne"]: c.append(_rf.choice(["je marche bien en montagne", "ok pour monter à pied aux postes isolés", "randonneur"]))
    if b["pratique_trail"]: c.append(_rf.choice(["je fais du trail", "trailer (plusieurs ultras)"]))
    if b["langues"] != "FR": c.append("langues : " + b["langues"].replace("DE", "allemand").replace("EN", "anglais").replace("IT", "italien").replace("FR,", ""))
    if b["editions_precedentes"]: c.append(_rf.choice([f"{b['editions_precedentes']} édition(s) comme bénévole", f"déjà bénévole {b['editions_precedentes']} fois", "j'ai déjà fait les ravitos"]))
    return ", ".join(c) if c else _rf.choice(["rien de spécial", "", "je suis motivé !"])


_ROLES = {"ravitaillement": "ravito", "dossards": "les dossards", "signaleur": "signaleur sur la route", "arrivee": "l'arrivée",
          "logistique": "la logistique", "serre_file": "serre-file", "pc_course": "le PC course", "restauration": "le repas",
          "parking": "le parking", "pointage": "le pointage"}


def _veut_faire(b, par_id):
    c = [_rf.choice(["plutôt ", "", "idéalement "]) + " ou ".join(_ROLES.get(r, r) for r in b["roles_preferes"].split(","))]
    if b["binome_souhaite"] and b["binome_souhaite"] in par_id:
        a = par_id[b["binome_souhaite"]]
        c.append(_rf.choice([f"avec {a['prenom']} {a['nom']}", f"je veux être avec {a['prenom']} {a['nom']} svp", f"même poste que {a['prenom']}"]))
    if not b["accepte_nuit"]: c.append(_rf.choice(["pas la nuit", "pas après 20h", "je ne fais pas la nuit"]))
    if b["accepte_chef_de_poste"]: c.append(_rf.choice(["je peux tenir un poste", "ok pour être responsable de poste", "chef de poste si besoin"]))
    return ", ".join(c)


def _remarques(b):
    c = []
    if b["commentaire_libre"]: c.append(b["commentaire_libre"])
    if b["contraintes"] and b["contraintes"] not in (b["commentaire_libre"] or ""): c.append(b["contraintes"])
    if b["age"] < 18: c.append(f"j'ai {b['age']} ans")
    elif b["age"] >= 65 and _rf.random() < 0.7: c.append(f"{b['age']} ans, encore en forme")
    return " ".join(c)


par_id = {b["benevole_id"]: b for b in benevoles}
formulaire = [{
    "Prénom et nom": f"{b['prenom']} {b['nom']}",
    "Téléphone": b["telephone"],
    "Quand je suis libre": _dispos(b),
    "Ce que je sais faire": _sait_faire(b),
    "Ce que je voudrais faire": _veut_faire(b, par_id),
    "Remarques": _remarques(b),
    "_id_verite": b["benevole_id"],
} for b in benevoles]
write_csv("formulaire_benevoles.csv", formulaire)
write_csv("cas_pieges.csv", cas_pieges)

total_min = sum(p["effectif_min"] for p in postes)
total_ideal = sum(p["effectif_ideal"] for p in postes)
print(f"{len(postes)} postes, besoin cumulé {total_min} (min) à {total_ideal} (idéal) affectations-créneaux")
print(f"{len(benevoles)} bénévoles, {len(cas_pieges)} cas pièges")
print("PSC1 :", sum(b['PSC1_ou_samaritain'] for b in benevoles),
      "| aptes montagne :", sum(b['apte_marche_montagne'] for b in benevoles),
      "| véhicule :", sum(b['vehicule'] for b in benevoles),
      "| dispo samedi :", sum(1 for b in benevoles if b['dispo_samedi']))
