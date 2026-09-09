"""Étape 1 : un solveur jouet. Trois bénévoles, deux créneaux.

Objectif pédagogique : voir les trois briques d'un solveur de contraintes
(variables, contraintes, objectif) sur un cas qu'on peut vérifier de tête.

Lancer :  python etape1_jouet.py
Prérequis : pip install ortools
"""
from ortools.sat.python import cp_model

# ---------------------------------------------------------------------------
# Les données d'entrée. Volontairement minuscules.
# ---------------------------------------------------------------------------
benevoles = {
    # nom : (dispo_matin, dispo_soir, est_responsable, creneau_prefere)
    "Marc":  (True,  True,  True,  "ravito_matin"),
    "Julie": (True,  False, False, "ravito_matin"),
    "Lea":   (True,  True,  False, "arrivee_soir"),
}

creneaux = {
    # id : (effectif_min, responsable_requis)
    "ravito_matin": (2, True),
    "arrivee_soir": (2, False),
}

# Quelle colonne de dispo correspond à quel créneau (index dans le tuple ci-dessus)
colonne_dispo = {"ravito_matin": 0, "arrivee_soir": 1}

# ---------------------------------------------------------------------------
# Brique 1 : les variables. Une case à cocher par (bénévole, créneau).
# ---------------------------------------------------------------------------
model = cp_model.CpModel()

x = {}  # x[(b, c)] vaut 1 si le bénévole b est affecté au créneau c
for b in benevoles:
    for c in creneaux:
        x[(b, c)] = model.NewBoolVar(f"x_{b}_{c}")

# ---------------------------------------------------------------------------
# Brique 2 : les contraintes. Des phrases vraies sur la grille.
# ---------------------------------------------------------------------------

# Contrainte A (à compléter) : un bénévole ne peut pas être coché sur un créneau
# où il n'est pas disponible.
# Indice : pour chaque (b, c), si benevoles[b][colonne_dispo[c]] est False,
# alors la case doit valoir 0. En CP-SAT, "la case vaut 0" s'écrit model.Add(x[(b, c)] == 0).
for b, (dispo_matin, dispo_soir, est_resp, prefere) in benevoles.items():
    for c in creneaux:
        # TODO 1 : écrire la contrainte de disponibilité ici
        pass

# Contrainte B : chaque créneau atteint son effectif minimum.
# sum(...) fait la somme des cases de la colonne c. La phrase dit : somme >= minimum.
for c, (effectif_min, resp_requis) in creneaux.items():
    model.Add(sum(x[(b, c)] for b in benevoles) >= effectif_min)

# Contrainte C : si le créneau exige un responsable, au moins une case cochée
# dans la colonne appartient à un responsable.
for c, (effectif_min, resp_requis) in creneaux.items():
    if resp_requis:
        model.Add(sum(x[(b, c)] for b in benevoles if benevoles[b][2]) >= 1)

# ---------------------------------------------------------------------------
# Brique 3 : l'objectif. Un score que le solveur doit rendre maximal.
# ---------------------------------------------------------------------------
# Ici : 1 point par bénévole placé sur son créneau préféré.
# TODO 2 : construire la liste `termes` des cases qui rapportent un point,
# puis appeler model.Maximize(sum(termes)).
# Indice : la case x[(b, c)] rapporte un point si c == benevoles[b][3].
termes = []
# ... à compléter ...
model.Maximize(sum(termes))

# ---------------------------------------------------------------------------
# On lance le solveur et on lit la grille.
# ---------------------------------------------------------------------------
solver = cp_model.CpSolver()
statut = solver.Solve(model)

if statut in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print("Statut :", solver.StatusName(statut), "| score :", solver.ObjectiveValue())
    print()
    print("Vue par créneau")
    for c in creneaux:
        equipe = [b for b in benevoles if solver.Value(x[(b, c)]) == 1]
        print(f"  {c:<14} {', '.join(equipe)}")
    print()
    print("Vue par personne")
    for b in benevoles:
        agenda = [c for c in creneaux if solver.Value(x[(b, c)]) == 1]
        print(f"  {b:<6} {', '.join(agenda) or '(libre)'}")
else:
    print("Infaisable : les contraintes se contredisent.", solver.StatusName(statut))

# ---------------------------------------------------------------------------
# Questions à se poser une fois que ça tourne :
#  1. Retire Léa. Que dit le solveur ? Pourquoi ?
#  2. Mets l'effectif minimum du soir à 3. Que se passe-t-il ?
#  3. Le solveur a-t-il mis Marc sur les deux créneaux ? Qu'est-ce qui l'empêcherait
#     de mettre quelqu'un sur deux créneaux qui se chevauchent ? (rien, pour l'instant)
# ---------------------------------------------------------------------------
