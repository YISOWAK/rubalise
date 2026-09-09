# Les étapes, et qui les fait

Légende : **code** = déterministe, testable sans LLM. **LLM 1 passe** = un prompt, une réponse structurée, pas de boucle. **agent** = un LLM qui boucle avec des outils parce que le nombre d'étapes n'est pas connu d'avance. **conversation** = l'orga et l'orchestrateur, dans le chat. **humain** = validation explicite.

## Phase 1 : les entrées

| # | Étape | Qui | Entrée | Sortie | Note |
|---|---|---|---|---|---|
| 1.1 | Lire le roadbook | LLM 1 passe | PDF (pages images) | points de passage, horaires 1er/dernier, barrières, services, accès | Le PDF est en images, il faut un modèle qui lit. On n'extrait que ce qui sert aux postes. |
| 1.2 | Faire relire l'extraction | conversation | 1.1 | 1.1 corrigé | Une seule fois, sous forme de tableau. « Conche n'a pas de bus cette année. » |
| 1.3 | Déduire les postes | code | 1.2 + gabarit trail | liste des postes avec catégorie, compétences, effectif min/idéal | Le gabarit dit « un ravito = 1 responsable + 3 à 5 petites mains ». |
| 1.4 | Calculer les fenêtres | code | 1.3 + horaires | postes avec début/fin, créneaux coupés si > 5 h | Union des courses sur un poste partagé. |
| 1.5 | Lire le fichier de dispos | code | CSV | lignes brutes | Colonnes fixes : nom, téléphone, dispos texte, compétences, souhaits, remarques. |
| 1.6 | Traduire les textes libres | LLM 1 passe, ligne par ligne | une ligne | dispos structurées, contraintes, préférences, niveau de confiance | « Samedi sauf 12h-14h, je peux monter à pied » devient deux plages et un drapeau montagne. |
| 1.7 | Lister les ambiguïtés | code + conversation | 1.6 | questions à l'orga | Tout ce qui a un niveau de confiance bas. |
| 1.8 | Ajouter ce que l'orga sait | conversation | phrases de l'orga | contraintes, personnes non listées | « Marc vient avec 3 potes, il prend Blancsex. » |

## Phase 2 : le plan

| # | Étape | Qui | Entrée | Sortie | Note |
|---|---|---|---|---|---|
| 2.1 | Affecter | code (solveur) | postes, bénévoles, règles, poids | plan, trous, contraintes impossibles | OR-Tools CP-SAT. |
| 2.2 | Vérifier les règles | code | plan, règles | violations bloquantes, alertes | Infaillible sur les règles écrites. |
| 2.3 | Relire avec un regard neuf | agent contradicteur | plan, règles, données, commentaires libres | remarques que le code ne voit pas | Contexte vierge, modèle fort. |
| 2.4 | Expliquer | LLM 1 passe | plan, 2.2, 2.3 | texte : ce qui est couvert, ce qui manque, pourquoi | C'est ce que l'orga lit. |
| 2.5 | Arbitrer | conversation + humain | remarques | dérogations, nouvelles règles, corrections | Chaque décision journalisée. |
| 2.6 | Recalculer si besoin | code | 2.5 | plan v2 | Boucle 2.1 à 2.5 jusqu'à validation. |

## Phase 3 : la publication

| # | Étape | Qui | Entrée | Sortie | Note |
|---|---|---|---|---|---|
| 3.1 | Feuilles de route | LLM 1 passe | plan validé, trajets | une par bénévole : où, quand, avec qui, comment y aller, qui appeler | Ton et longueur à fixer. |
| 3.2 | Valider l'envoi | humain | 3.1 | ok | Rien ne part sans. |
| 3.3 | Envoyer | code | 3.1 | messages envoyés (simulés pour le hackathon) | Un fichier par personne, ou un canal réel plus tard. |
| 3.4 | Figer le plan | code | plan | plan publié, horodaté | À partir de là, changer a un coût. |

## Phase 4 : le jour J

| # | Étape | Qui | Entrée | Sortie | Note |
|---|---|---|---|---|---|
| 4.1 | Comprendre l'événement | agent orchestrateur | message de l'orga, état | qui est touché, quand, quelle règle casse | Pas de catalogue d'événements. |
| 4.2 | Décider quoi faire | agent orchestrateur | 4.1 | rien / question / recalcul | Il peut choisir de ne rien proposer. |
| 4.3 | Recalculer avec plan figé | code | plan figé, changement | réparation minimale | Coût de changement élevé sur les gens prévenus. |
| 4.4 | Relire la proposition | agent contradicteur | proposition | remarques | Même agent que 2.3. |
| 4.5 | Proposer | LLM 1 passe | 4.3, 4.4 | texte : ce qui change, pourquoi, messages prêts | |
| 4.6 | Valider | humain | 4.5 | ok / non / autre | |
| 4.7 | Envoyer et journaliser | code | | | |

## Ce qui en sort

Deux agents :

- **L'orchestrateur** : tient la conversation avec l'orga, appelle les outils dans l'ordre pour les phases 1 à 3 (où l'ordre est connu), et boucle librement pour la phase 4 (où il ne l'est pas).
- **Le contradicteur** : reçoit un plan ou une proposition, relit, rend des remarques. Jamais d'écriture.

Tout le reste, ce sont des outils : du code, ou un prompt en une passe emballé dans une fonction.

## Questions ouvertes

1. Roadbook : tout extraire ou seulement ce qui sert aux postes ? Proposition : seulement les postes.
2. Corrections de l'extraction : en une fois ou au fil de l'eau ? Proposition : en une fois.
3. Envoi des messages : simulé ou réel ? Proposition : simulé pour le hackathon.
