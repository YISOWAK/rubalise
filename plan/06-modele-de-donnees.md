# Modèle de données et contrats des outils

Tout ce que les agents savent vit dans l'état, en JSON lisible. Six objets. Les champs sont en français, comme le reste du projet, pour que l'orga puisse ouvrir un fichier et le comprendre.

## Choix tranchés par défaut (à contester si besoin)

1. Le roadbook n'est extrait que pour ce qui sert aux postes : points de passage, horaires, barrières, services, accès, retrait des dossards, navettes. Pas le règlement ni le matériel obligatoire.
2. L'orga corrige l'extraction en une fois, sous forme de tableau, avant qu'on construise les postes.
3. L'envoi des messages est simulé : un fichier par bénévole dans un dossier `envoyes/`, et une ligne dans le journal.
4. Une affectation porte sur un créneau entier (version simple). Les postes longs sont coupés en créneaux de 4 à 5 heures qui se chevauchent de 30 minutes.
5. Le niveau « responsable » est déclaré par l'orga. L'agent le suggère quand il voit quelqu'un avec plusieurs éditions et rien de déclaré.
6. Un responsable qui amène des personnes non listées compte pour lui plus N petites mains anonymes sur son poste. Leurs prénoms sont demandés avant le jour J.

## 1. Course

```json
{
  "nom": "SwissPeaks Marathon",
  "date": "2025-09-06",
  "depart": {"lieu": "Morgins", "heure": "2025-09-06T09:00"},
  "arrivee": {"lieu": "Le Bouveret"},
  "coureurs": 500,
  "points_de_passage": [
    {"nom": "Taney", "km": 25, "altitude": 1416,
     "premier": "2025-09-06T11:45", "dernier": "2025-09-06T16:15", "barriere": null,
     "services": ["ravitaillement"],
     "acces": "a_pied", "acces_note": "parking à Le Flon puis 400 m D+, 60 min"}
  ],
  "autres_courses": [
    {"nom": "SwissPeaks 70", "poste": "Taney", "premier": "2025-09-06T10:45", "dernier": "2025-09-06T17:30"}
  ],
  "dossards": [{"lieu": "Le Bouveret", "debut": "2025-09-05T15:00", "fin": "2025-09-05T19:00"}],
  "navettes": [{"trajet": "Le Bouveret vers Morgins", "depart": "2025-09-06T07:00"}],
  "source": "roadbook 2025 p.23-25, corrigé par l'orga le 2026-09-04"
}
```

Écrit par « Lire le roadbook », corrigé par l'orga. Lu par « Construire les postes ».

## 2. Poste (un créneau à pourvoir)

```json
{
  "id": "S11",
  "nom": "Ravitaillement Taney, matin",
  "site": "Taney",
  "categorie": "ravitaillement",
  "debut": "2025-09-06T09:45",
  "fin": "2025-09-06T14:00",
  "effectif_min": 3,
  "effectif_ideal": 5,
  "responsable_requis": true,
  "competences_requises": ["montagne"],
  "majeur_requis": false,
  "acces": "a_pied",
  "notes": "Premier SP70 10h45, premier Marathon 11h45",
  "origine": "roadbook"
}
```

`origine` vaut `roadbook` (déduit d'un point de passage), `gabarit` (ajouté par le gabarit trail : signaleurs, PC, réserve volante) ou `orga` (ajouté à la main). Écrit par « Construire les postes » et par l'orga. Lu par tout le monde.

Les catégories viennent du gabarit trail : dossards, depart, ravitaillement, controle, signaleur, serre_file, arrivee, restauration, secours, logistique, livraison, parking, pc_course, reserve_volante, navette, rangement.

## 3. Bénévole

```json
{
  "id": "B012",
  "prenom": "Marc", "nom": "Favre", "telephone": "+41 79 ...",
  "majeur": true,
  "niveau": "responsable",
  "editions": 4,
  "disponibilites": [
    {"debut": "2025-09-06T06:00", "fin": "2025-09-06T12:00"},
    {"debut": "2025-09-06T14:00", "fin": "2025-09-07T00:00"}
  ],
  "competences": ["psc1", "permis", "vehicule", "montagne"],
  "roles_preferes": ["ravitaillement"],
  "poste_souhaite": "Chalet de Blancsex",
  "accepte_nuit": true,
  "binome": "B013",
  "accompagnants": 3,
  "contraintes": [
    {"type": "indisponible", "detail": "récupérer les enfants 12h-14h", "source": "texte libre", "confiance": 0.9},
    {"type": "physique", "detail": "pas de station debout prolongée", "source": "texte libre", "confiance": 0.8}
  ],
  "commentaire_brut": "Dispo samedi sauf entre midi et 14h (enfants). Je prends Blancsex comme d'hab avec mes 3 potes.",
  "ambiguites": ["« mes 3 potes » : non listés, prénoms à demander"]
}
```

Les champs structurés sont produits par « Traduire les dispos » à partir du fichier et du texte libre ; `commentaire_brut` est conservé tel quel pour que le contradicteur puisse relire la source. `niveau` est déclaré par l'orga (`responsable` ou `petite_main`), suggéré par l'agent sinon.

Fichier d'entrée attendu (6 colonnes, texte libre partout sauf le nom) : prénom et nom, téléphone, quand je suis libre, ce que je sais faire, ce que je voudrais faire, remarques.

## 4. Règle

```json
{
  "id": "R05",
  "type": "bloquante",
  "enonce": "Un mineur n'est jamais seul sur un poste signaleur ni sur un poste isolé",
  "test": "mineur_seul_sur_poste_route_ou_isole",
  "parametres": {},
  "active": true,
  "origine": "defaut",
  "modifiee_le": null
}
```

```json
{
  "id": "R21",
  "type": "bloquante",
  "enonce": "À Blancsex, au moins deux personnes PSC1 sur chaque créneau",
  "test": "effectif_competence_minimum",
  "parametres": {"site": "Chalet de Blancsex", "competence": "psc1", "minimum": 2},
  "active": true,
  "origine": "orga",
  "modifiee_le": "2026-09-05T10:12"
}
```

`enonce` est ce que l'orga lit. `test` est le nom d'une vérification codée, avec ses paramètres. Ajouter une règle depuis le chat, c'est choisir un test existant et remplir ses paramètres ; si aucun test ne correspond, l'agent le dit et la règle devient une alerte que seul le contradicteur peut relire. Les battements par catégorie et les poids du solveur vivent aussi ici, comme paramètres.

## 5. Plan

```json
{
  "version": 3,
  "statut": "publie",
  "calcule_le": "2026-09-05T11:40",
  "fige_le": "2026-09-05T18:02",
  "affectations": [
    {"benevole_id": "B012", "poste_id": "S08", "role": "responsable", "notifie": true},
    {"benevole_id": "anonyme:B012:1", "poste_id": "S08", "role": "petite_main", "notifie": false}
  ],
  "trous": [
    {"poste_id": "S17", "manque": 1, "raison": "aucun profil PSC1 + montagne disponible après 14h"}
  ],
  "violations": [
    {"regle_id": "R21", "poste_id": "S09", "gravite": "bloquante", "derogee": true, "derogation_id": "J0042"}
  ],
  "score": {"couverture_min": 0.97, "couverture_ideal": 0.71, "preferences": 0.64}
}
```

`statut` suit brouillon, valide, publie, fige. Une fois `fige_le` posé, toute affectation avec `notifie: true` a un coût de changement élevé dans le solveur. Écrit par le solveur, par « Envoyer » (fige) et par l'orga (dérogations).

## 6. Journal

```json
{
  "id": "J0042",
  "horodatage": "2026-09-05T11:52",
  "auteur": "orga",
  "action": "derogation",
  "cible": {"regle_id": "R21", "poste_id": "S09"},
  "justification": "Léa a son PSC1 depuis mardi, pas encore dans le fichier",
  "avant": null,
  "apres": null
}
```

Auteurs possibles : orga, orchestrateur, contradicteur, ou le nom d'un outil. Actions : extraction, correction, calcul, verification, remarque, derogation, regle_ajoutee, regle_modifiee, validation, envoi, evenement_jour_j, reparation. Le journal ne s'efface jamais.

## Contrats des outils

| Outil | Reçoit | Rend | Écrit dans l'état |
|---|---|---|---|
| `lire_roadbook` | chemin du PDF, pages | Course (brouillon) + niveau de confiance par champ | Course |
| `construire_postes` | Course, gabarit trail, battements | liste de Postes | Postes |
| `traduire_dispos` | une ligne du fichier | Bénévole structuré + ambiguïtés | Bénévoles |
| `resoudre` | Postes, Bénévoles, Règles, plan figé (optionnel), poids | Plan (brouillon), trous, contraintes impossibles | Plan |
| `verifier` | Plan, Règles | violations bloquantes et alertes | rien |
| `regles` | lister / ajouter / modifier / déroger | Règles à jour | Règles, Journal |
| `feuilles_de_route` | Plan, Postes, Bénévoles, trajets | un texte par bénévole | rien |
| `envoyer` | feuilles de route validées | accusés (simulés) | Plan (fige, notifie), Journal |
| `journaliser` | auteur, action, cible, justification | id | Journal |

Le contradicteur n'a pas d'outil d'écriture. Il reçoit un Plan ou une proposition, lit l'état, rend une liste de remarques `{gravite, cible, texte}`.

## Ce que le gabarit trail contient

Un fichier de configuration, pas du code :

- pour chaque service d'un point de passage (ravitaillement, barrière, bus abandon, arrivée), les postes à créer, avec effectifs, compétences, responsable requis, marge avant le premier coureur et après le dernier ;
- les postes hors parcours à proposer systématiquement : dossards, départ, signaleurs, PC course, réserve volante, livraison, rangement ;
- la durée maximale d'un créneau avant découpe, et le chevauchement de relève ;
- les battements par catégorie.

Un gabarit « triathlon » ou « festival » serait un autre fichier du même format.
