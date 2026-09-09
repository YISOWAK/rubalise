# Architecture

## Vue d'ensemble

```
Organisateur (chat texte, une seule interface)
        |
        v
+-----------------------------------------------------------+
| Agent orchestrateur (Strands)                              |
|  comprend la demande, appelle les outils, délègue aux      |
|  agents spécialisés, ne valide jamais seul                 |
|                                                           |
|  Agents spécialisés (Strands, "agents comme outils")       |
|   - Lecteur : roadbook, fichier bénévoles -> données       |
|   - Planificateur : prépare le problème, appelle le        |
|     solveur, explique le résultat                          |
|   - Contradicteur : relit avec les règles, modèle fort     |
|   - Rédacteur : feuilles de route, messages aux bénévoles  |
+-----------------------------------------------------------+
        |  MCP
        v
+-----------------------------------------------------------+
| Serveur MCP "course"                                       |
|   - solveur d'affectation (OR-Tools CP-SAT)                |
|   - état : course, postes, bénévoles, plan, règles         |
|   - journal (qui a décidé quoi, quand, pourquoi)           |
|   - vérificateur de règles (déterministe)                  |
+-----------------------------------------------------------+
        |
        v
  Stockage : fichiers JSON en local (v1) -> AgentCore Memory (v2)
  Jour J durable : Temporal (phase 2)
  Hébergement : AgentCore Runtime
  Traces : AgentCore Observability
```

## Pourquoi cette découpe

- **Le LLM ne calcule pas le planning.** Le solveur est un outil déterministe. Le LLM prépare les données, lit le résultat, explique. Résultat garanti, reproductible, et un jury technique le comprend en une phrase.
- **Les règles sont vérifiées deux fois.** Une fois par du code (le vérificateur, infaillible sur ce qu'il connaît), une fois par le contradicteur (qui attrape ce que le code ne connaît pas : un commentaire libre mal compris, une conséquence à trois heures). Les deux ensemble, c'est le motif « agent + garde-fou » que le barème récompense.
- **Tout passe par MCP.** Le solveur, l'état, le journal sont des outils standard. Un autre client (un autre agent, Claude Desktop, un script de test) peut les appeler. C'est aussi ce qui rend la suite d'évaluations facile.
- **L'humain valide.** L'orchestrateur produit des propositions. La validation est une action explicite de l'orga, journalisée.

## Les outils MCP

| Outil | Entrée | Sortie |
|---|---|---|
| `charger_course` | roadbook (JSON extrait par le lecteur) | postes avec fenêtres calculées |
| `charger_benevoles` | fichier CSV + contraintes extraites du texte libre | bénévoles structurés, liste des ambiguïtés |
| `resoudre` | postes, bénévoles, règles, plan figé (optionnel), poids | plan, trous, violations impossibles à éviter |
| `verifier` | plan, règles | liste des violations bloquantes et alertes |
| `journaliser` | événement, auteur, justification | identifiant |
| `lire_etat` / `ecrire_etat` | | état courant |
| `regles` | lister, ajouter, modifier, déroger | règles actives |

## Le solveur

OR-Tools CP-SAT. Variables booléennes « bénévole b sur créneau c ». Contraintes dures : disponibilité, majeur, montagne, PSC1, un responsable par poste, pas de chevauchement, enchaînement faisable (libération + battements + trajet). Objectif pondéré : couverture du minimum (poids très fort), responsable présent, couverture de l'idéal, préférences de rôle, binômes, et coût de changement par rapport au plan figé (jour J). Temps de calcul attendu : moins d'une seconde pour 75 personnes et 32 créneaux.

Le plan figé est le mécanisme de stabilité : au jour J, tout ce qui n'est pas cassé a un coût de changement élevé, ce qui force une réparation minimale.

## Le jour J, v1 puis v2

- **v1 (fichier)** : l'état est un JSON. Chaque message de l'orga déclenche la boucle : diff, impact, vérification, réparation minimale, proposition, journal. Suffisant pour la démo.
- **v2 (Temporal)** : le plan devient un workflow durable. La validation de l'orga est un signal, les désistements sont des événements, les horaires de fermeture des postes sont des timers. Le workflow survit au redémarrage et garde l'historique. À faire seulement quand la v1 tourne.

## Modèles

Via Amazon Bedrock, ce qui compte pour un jury AWS. Modèle fort pour le contradicteur et le planificateur, modèle rapide pour le lecteur et le rédacteur. Le choix exact se fait au moment du code, selon ce que Bedrock propose dans la région.

## Évaluation

Les 14 cas pièges du jeu de données deviennent des tests : on injecte le jeu, on lance le plan, on compte combien de pièges le vérificateur attrape, combien le contradicteur attrape en plus, et combien passent. Le score est dans le README. Deuxième suite : 10 événements de jour J (désistement, retard, orage, réassort) avec le nombre de personnes déplacées par réparation, qui doit rester petit.

## Ce qui va sur AgentCore

- **Runtime** : l'orchestrateur, déployé comme un agent hébergé, avec une URL de démo (le lien live compte dans le score).
- **Memory** : état et journal, à la place des fichiers JSON, si le temps le permet.
- **Gateway** : le serveur MCP, exposé proprement.
- **Observability** : traces des appels d'agents et d'outils, montrées 10 secondes dans la vidéo.

## Phasage jusqu'au 14 septembre (deadline 17h PT, soit le 15 à 2h Paris)

| Jours | Objectif | Résultat visible |
|---|---|---|
| 3 au 4 sept | Serveur MCP : état, solveur, vérificateur, sur le jeu de données | Un plan calculé en ligne de commande, les 14 pièges passés au vérificateur |
| 5 au 6 | Agents Strands : orchestrateur, lecteur, planificateur, contradicteur, rédacteur | Phases 1 à 3 jouables dans un terminal |
| 7 au 8 | Boucle du jour J v1, suite d'évaluations, compte AWS et Bedrock opérationnels | Phase 4 jouable, score d'évaluation |
| 9 au 10 | AgentCore Runtime et Observability, interface web minimale | Lien live |
| 11 | Temporal pour le jour J, si tout le reste tient | Workflow durable |
| 12 au 13 | Vidéo (5 min max, démo + pitch), README, diagramme, licence, billet builder.aws.com | Soumission complète en brouillon |
| 14 | Marge | Soumission finale |

## Risques

- **Compte AWS et accès Bedrock** : à faire dès maintenant, l'activation des modèles peut prendre du temps.
- **Trop de frameworks** : Strands, MCP, OR-Tools, AgentCore, et Temporal en option. Pas un de plus.
- **La vidéo** : 5 minutes, c'est court pour 4 phases. Phase 1 en 30 secondes, phases 2 et 4 sont les moments forts.
- **Le solveur qui dit « infaisable »** : c'est une fonctionnalité, pas un bug. L'agent doit savoir dire « il manque 6 personnes, voici où » plutôt que de forcer.
