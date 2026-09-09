# La vidéo : 5 minutes maximum, démo + pitch

Règle du concours : démo qui marche + pitch (problème, pour qui, pourquoi ça compte). Slides, captures d'écran et voix off suffisent, pas besoin d'être à l'image. Le jury note Technical Implementation, Impact, Creativity, Presentation, Strands usage.

## Découpage (4 min 45 s)

| Temps | Ce qu'on voit | Ce qu'on dit (voix off) |
|---|---|---|
| 0:00 - 0:30 | Une page du roadbook SwissPeaks (le tableau en image), puis un Google Form avec des réponses en texte libre, puis un fil WhatsApp | « Sur chaque trail, une personne passe ses soirées à faire ça : 75 bénévoles, 50 créneaux, un PDF fait d'images et un formulaire où les gens écrivent ce qu'ils veulent. Un trou dans un créneau, c'est un coureur seul sur une route la nuit. Les grandes courses achètent des plateformes. Les petites ont Excel et de la bonne volonté. » |
| 0:30 - 0:50 | Le schéma d'architecture, 15 secondes fixes | « Rubalise, c'est un agent Strands qui parle à l'organisateur, un serveur d'outils MCP, un solveur de contraintes, et un second agent, le contradicteur, qui relit tout avec un regard neuf. Le modèle ne calcule jamais le planning ; il lit, traduit, explique. » |
| 0:50 - 1:35 | Terminal : « Voici le roadbook, pages 14, 18, 22 à 24, course Marathon ». Tableau des points de passage avec les doutes. « Conche a bien un bus d'abandon, ajoute-le ». « Construis les postes ». | « Phase 1 : il lit le PDF comme on le lirait, ligne par ligne, et dit ce dont il n'est pas sûr. L'organisateur corrige en français. Un gabarit transforme la fiche en 60 créneaux : ravitos, serre-files, dossards, PC course. » |
| 1:35 - 2:35 | Deux lignes du formulaire à l'écran (« je cours le Marathon mais je peux aider vendredi », « samedi toute la journée, je viens avec mes 3 potes ») puis leur traduction. Puis « Calcule un plan » : postes sans responsable, trous avec la raison, remarques du contradicteur. | « Phase 2 : chaque ligne devient des champs fermés que le solveur comprend ; 74 sur 75 justes. Le solveur rend un plan optimal en cinq secondes, et surtout il nomme les trous : il manque un 4x4 vendredi, il manque des trailers avec PSC1 pour les serre-files. Puis le contradicteur : une mineure déclarée responsable, une livraison vide qui bloque quatre postes. Aucune règle ne le disait. » |
| 2:35 - 3:05 | « Accorde la dérogation, Sandra confirme » : le garde-fou demande confirmation, on tape oui. « Publie le plan » : confirmation, 73 messages écrits, journal. | « Rien ne part sans l'organisateur. La confirmation est dans le code, pas dans le prompt. Chaque décision est journalisée avec son auteur et sa raison. » |
| 3:05 - 4:05 | « Il est 11h, Marc et Fabien ne viennent pas. » L'agent liste qui est touché, recalcule, montre les mouvements personne par personne, « Lucas est déjà en poste, à prévenir en direct », ce qui reste cassé, et demande s'il doit publier. | « Le jour J, c'est là que ça compte. Le plan publié est un engagement : chaque changement coûte, plus cher si la personne est déjà en poste. Le solveur répare avec le moins de mouvements possible, les créneaux terminés ne bougent pas, et l'agent dit ce qu'il ne peut pas résoudre. » |
| 4:05 - 4:30 | Tableau des résultats mesurés, puis 8 secondes de traces AgentCore Observability | « Tout est mesuré : la traduction, la lecture du roadbook, dix scénarios de solveur. L'agent est hébergé sur AgentCore. » |
| 4:30 - 4:45 | Le schéma, avec « trail.json » surligné, puis le mot fin | « Un triathlon, c'est un autre fichier de gabarit. Et après la course, l'agent relit le journal et propose ce qu'il faut changer l'an prochain. Les bénévoles font tourner les courses ; celui qui les organise mérite un outil. » |

## Messages à taper pendant l'enregistrement (mode interactif)

1. Où en est-on ?
2. Voici le roadbook : ../sources-privees/roadbook-2025.pdf, pages 14,18,22,23,24, course « Marathon (46 km, départ Morgins) », départ le 2025-09-06.
3. Le Chalet de Conche a bien un bus d'abandon, ajoute-le. Ensuite construis les postes.
4. Traduis le formulaire des bénévoles.
5. Calcule un plan.
6. Pour le Grand Pré du soir on tiendra à 2, Sandra me l'a confirmé : accorde la dérogation.
7. Oui, vas-y.
8. Publie le plan, on l'a validé en réunion.
9. Oui, publie.
10. Il est 11h, Marc Saudan et Fabien Carraux ne viennent pas. On fait quoi ?

Les étapes 2 et 4 prennent 40 s et 10 min : on les enregistre à part et on coupe au montage. Police du terminal à 18 pt minimum, fenêtre 1280 × 720, thème clair.

## À préparer

- 3 captures : page du roadbook, formulaire, fil WhatsApp (flouté ou inventé).
- Le schéma en PNG (docs/architecture.svg).
- Le tableau des résultats en une image.
- 8 secondes de traces AgentCore Observability dans la console.
- Enregistrement : OBS ou l'enregistreur Windows (Win + Alt + R), voix off avec le micro du casque, montage dans Clipchamp (fourni avec Windows).
