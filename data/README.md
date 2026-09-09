# Jeu de données de démo : bénévoles du SwissPeaks Marathon 2025

Course de référence : **SwissPeaks Marathon**, 46 km et 2 483 m D+, départ à Morgins le samedi 6 septembre 2025 à 09h00, arrivée au Bouveret (quai Bussien). 500 coureurs, 14 h de temps maximum.

## Ce qui est réel

| Fichier | Contenu | Source |
|---|---|---|
| `course_marathon.json` | Points de passage, altitudes, km, D+ et D- cumulés, heure du premier et du dernier coureur, barrières horaires, services (ravito, bus abandon, secours), retrait des dossards, navettes. Contient aussi les horaires du SwissPeaks 70 sur les postes partagés. | Roadbook coureurs 2025, pages 23 à 25 (`source/*.png`) |
| `parcours.gpx` | Trace du parcours (lat, lon, altitude), 1 point tous les 15 m environ | Enregistrement GPS d'un coureur, nettoyé |
| `parcours_profil.csv` | Profil tous les 100 m : km, altitude, D+ et D- cumulés, coordonnées | Dérivé de la trace |
| `points_de_passage_geo.csv` | Coordonnées GPS de chaque poste, retrouvées sur la trace. L'écart d'altitude avec le roadbook est inférieur à 10 m partout. | Trace + roadbook |
| `passages_reference.csv` | Heures de passage réelles d'un coureur du peloton à chaque poste, comparées à la fenêtre premier / dernier du roadbook. Ce coureur passe partout entre 46 % et 61 % de la fenêtre : il sert de « coureur médian » pour simuler le flux. | Trace |

Les fichiers bruts (roadbook PDF complet, enregistrement GPS avec fréquence cardiaque) sont conservés hors du projet, dans `../sources-privees/`, et ne sont pas publiés. `source/` ne garde que les rendus des pages du roadbook utilisées.

## Ce qui est synthétique

| Fichier | Contenu |
|---|---|
| `postes.csv` | 32 postes ou créneaux sur trois jours (vendredi dossards, samedi course, dimanche démontage), avec fenêtre horaire, effectif minimum et idéal, compétences requises, besoin d'un chef de poste. La colonne `origine` distingue les postes tirés du roadbook (`roadbook`) de ceux ajoutés par hypothèse d'organisation (`hypothese` : signaleurs, serre-files, parking, PC course, logistique). |
| `sites.csv` | Les six sites et leur accessibilité en véhicule. |
| `trajets.csv` | Temps de trajet estimés en voiture entre les sites, plus la marche d'approche pour Blancsex (25 min) et Taney (60 min, 400 m D+). Estimation de démo : dans le produit, cette matrice est fournie par l'organisateur. |
| `battements.csv` | Par catégorie de poste, le temps pour se libérer (passer la main, ranger, monter en voiture) et le temps pour être opérationnel à l'arrivée. Un enchaînement A puis B vaut : libération à A + battement de départ + trajet + battement d'arrivée. |
| `benevoles.csv` | 75 bénévoles fictifs : disponibilités par jour, éditions précédentes, PSC1, permis, véhicule, aptitude montagne, langues, rôles préférés, nuit acceptée, binôme souhaité, contraintes, commentaire libre tel qu'on le lit sur un formulaire. Noms, courriels et téléphones inventés. |
| `cas_pieges.csv` | 14 situations que l'agent contradicteur doit détecter avant validation : binôme incompatible, mineur, doublon, bénévole qui court la course, trajet impossible entre deux postes, dispo qui ne couvre pas le créneau, créneau qui passe minuit, postes partagés avec le SP70, etc. |

## Règles de calcul des fenêtres de postes

- Un ravitaillement ouvre 60 minutes avant le premier coureur attendu (montage) et ferme 30 minutes après le dernier coureur ou la barrière horaire (démontage).
- Quand un poste sert aussi au SwissPeaks 70 (Morgins, Conche, Blancsex, Taney, Grand Pré, Bouveret), la fenêtre est l'union des deux courses.
- Les postes de plus de 5 heures sont coupés en deux créneaux qui se chevauchent de 30 minutes pour la relève.

## Regénérer

```bash
python generate_dataset.py
python build_gpx_derivatives.py
```

Le premier script est déterministe (graine fixée). Le second a besoin de la trace brute dans `source/`.

## Volumes

- 32 postes, besoin cumulé de 89 (minimum) à 140 (idéal) affectations.
- 75 bénévoles, dont 71 disponibles le samedi, 25 avec PSC1, 49 aptes à la marche en montagne, 45 avec véhicule.
- Le jeu est volontairement tendu : il n'y a pas assez de monde pour l'effectif idéal partout, l'agent doit arbitrer et le dire.
