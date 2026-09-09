# Arbitrages du solveur

Un solveur de contraintes ne connaît que trois choses : des variables (les cases bénévole × créneau), des contraintes dures (interdictions absolues) et un objectif (un score à maximiser, où vivent les contraintes souples sous forme de pénalités). Chaque arbitrage ci-dessous revient à décider : dur, souple avec quel poids, ou hors solveur.

## Tranchés par défaut

| # | Arbitrage | Options | Choix | Ce que ça change |
|---|---|---|---|---|
| 1 | Unité d'affectation | créneau entier / heures propres (grille au quart d'heure) | créneau entier | Les postes longs sont coupés en créneaux de 4 à 5 h, chevauchement de 30 min. Une personne dispo sur une partie seulement d'un créneau n'y est pas éligible. Perte : « Julie de 12h à 15h30 ». Gain : modèle 15 fois plus petit, code 3 fois plus court. |
| 2 | Chevauchement et trajet | dur / souple | dur | Deux créneaux pour la même personne doivent respecter : fin A + battement départ + trajet + battement arrivée <= début B. Contrainte native CP-SAT (intervalles sans recouvrement) ou paires interdites précalculées. |
| 3 | Compétences exigées, majeur, montagne | dur / souple | dur | Sécurité. Un poste qui exige PSC1 ne reçoit qu'un PSC1. Si ça rend le plan infaisable, le trou apparaît via l'arbitrage 6, pas via une dérogation silencieuse. |
| 4 | Hiérarchie des poids | somme pondérée / résolution en étapes (lexicographique) | somme pondérée, magnitudes séparées | 1000 par personne manquante sous le minimum, 100 par responsable manquant, 10 par personne manquante sous l'idéal, 1 par préférence respectée. L'orga règle ces quatre chiffres. |
| 5 | Accompagnants anonymes | personnes fantômes / capacité du responsable | capacité | Dans la contrainte d'effectif, la case du responsable compte pour 1 + N. Simple, et l'agent demande les prénoms avant le jour J. |

## À trancher par l'orga (Antoine)

| # | Arbitrage | Options | Question de terrain |
|---|---|---|---|
| 6 | Effectif minimum | dur / souple à 1000 | Un ravito à 2 au lieu de 3, c'est un plan avec un trou à signaler, ou un non-plan ? Dur = le solveur dit « infaisable » sans rien d'autre. |
| 7 | Responsable manquant | dur / souple à 1000 | Même question pour le « trou grave ». |
| 8 | Refus de la nuit | dispo (dur) / préférence (souple) | Quand quelqu'un coche « pas la nuit », est-ce une limite ou un souhait négociable par un coup de fil ? |
| 9 | Charge par personne | plafond dur (3 créneaux ou 10 h) / pénalité souple / rien, le contradicteur signale | Sans rien, le solveur peut charger quelqu'un de très disponible 14 h d'affilée. Qu'est-ce qu'un bénévole raisonnable ? |

## Ce qui reste hors solveur

- La fatigue fine, l'équité entre bénévoles (« Marc fait toujours Blancsex ») : le contradicteur, pas le solveur.
- Les quantités de matériel et de nourriture.
- Le choix des créneaux eux-mêmes (découpe, fenêtres) : fait avant, par « Construire les postes ».

## Paramètres techniques

- Limite de temps : 10 secondes. Sur 75 × 32 le solveur finit bien avant.
- Déterminisme : graine fixée et nombre de threads fixé, pour que deux lancements donnent le même plan (utile pour les tests et pour la confiance de l'orga).
- Plan figé : chaque case qui change par rapport au plan publié coûte 20 si la personne était prévenue, 100 si elle est déjà en poste. C'est une ligne dans l'objectif.
