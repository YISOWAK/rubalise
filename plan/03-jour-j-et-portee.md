# Jour J : portée de l'agent, stabilité, supervision

## Trois niveaux d'action

| L'agent fait seul | L'agent propose (avec justification, validation humaine) | L'agent ne fait jamais |
|---|---|---|
| Surveiller l'état : heure, pointages, messages reçus | Tout changement d'affectation | Décider de la sécurité de la course (arrêt, neutralisation, barrières) |
| Recalculer un plan en interne | Tout message envoyé à un bénévole | Contacter quelqu'un hors de la liste des bénévoles |
| Rédiger des brouillons de messages | Toute dérogation à une règle | Modifier une règle sans demande de l'orga |
| Tenir le journal (qui, quoi, quand, pourquoi) | L'ajout d'une nouvelle règle dictée par l'orga (il la reformule, l'orga confirme) | Envoyer quoi que ce soit sans validation |
| Répondre aux questions de l'orga (« qui est à Taney ? ») | | |

## La boucle du jour J

Pas de catalogue d'événements. Un état (course, postes, plan, bénévoles, journal) et une boucle, déclenchée par tout message de l'orga ou par l'horloge :

1. Qu'est-ce qui a changé ? (une personne absente, un horaire décalé, une consigne du directeur de course, une info météo)
2. Qui et quels postes sont touchés, maintenant et dans les prochaines heures ?
3. Est-ce qu'une règle bloquante est violée ? Si non, on note et on ne propose rien.
4. Si oui, quelle est la réparation qui déplace le moins de personnes ?
5. Proposer : ce qui change, pourquoi, et les messages prêts à partir. L'orga valide, corrige ou refuse.
6. Journaliser.

Exemples qui passent dans la même boucle : « Julie ne vient pas », « le dernier coureur a 40 minutes de retard sur Blancsex », « le directeur de course neutralise la section Taney à cause de l'orage », « il manque de l'eau au Grand Pré », « Marc est arrivé avec 5 personnes au lieu de 3 ».

## Stabilité : ne pas réoptimiser en permanence

Un plan publié est un engagement : chaque bénévole a reçu sa feuille de route et s'est organisé. Déplacer quelqu'un a un coût.

Règles :

- L'agent ne propose un changement que si une règle bloquante est violée, si l'orga le demande, ou si le gain est important et tient en une phrase (« en déplaçant Léa, Taney retrouve un PSC1 pour l'après-midi »).
- Jamais de proposition du type « il existe un plan un peu meilleur ».
- Réparation minimale : on fige tout ce qui n'est pas cassé avant de relancer le solveur. Coût de changement élevé sur les personnes déjà notifiées, très élevé sur celles déjà en poste.
- Une seule proposition à la fois par incident. Pas de flux continu.
- Pas de nombre maximum de propositions en dur : ça dépend trop de la course. Le seuil de « gain important » est un poids que l'orga ressent et règle.

## Temps entre deux postes

Un enchaînement A puis B n'est valable que si : heure de libération à A + battement de départ + trajet A vers B + battement d'arrivée <= heure de prise de poste à B.

- **Trajet** : porte à porte, donné par l'orga d'expérience (voiture, plus marche d'approche pour les postes isolés). Sans cette matrice, l'agent la demande ; il ne l'invente pas.
- **Battement de départ** : passer la main, ranger, monter en voiture. Réglage par type de poste (ravito : 15 min, signaleur : 5 min).
- **Battement d'arrivée** : se garer, trouver le responsable, se mettre au courant. Réglage par type de poste (10 min par défaut).

Les battements vivent dans le fichier de règles, modifiables par l'orga.

## Règles modifiables par l'orga

Les règles (bloquantes, alertes, effectifs, compétences par poste) vivent dans un fichier lisible, pas dans le code. Depuis le chat, l'orga peut :

- ajouter une règle (« à Blancsex, toujours deux PSC1 ») : l'agent la reformule, l'orga confirme, elle s'applique au prochain calcul ;
- assouplir ou retirer une règle ;
- demander la liste des règles actives et la raison de chacune ;
- déroger ponctuellement (« mets Marc là quand même ») : la règle reste, la dérogation est journalisée.

C'est ce mécanisme qui permet de passer d'un trail à un autre type d'événement sans toucher au code : on change le catalogue de postes et les règles.

## Supervision

Deux niveaux, pas un :

- **Le contradicteur (agent, modèle fort).** Relit chaque proposition avant qu'elle atteigne l'orga : règles, conséquences à deux ou trois heures, ce que le planificateur a pu oublier. Il peut renvoyer la proposition au planificateur.
- **L'orga (humain).** Valide, corrige ou refuse. Rien ne part sans lui.

Un « superviseur qui dit continue » automatique n'est acceptable que pour la routine (rien de cassé, aucun message à envoyer). Pour tout changement, deux agents qui se valident entre eux ne remplacent pas un humain qui regarde.

## À découvrir en construisant

- Quels événements reviennent vraiment : on ajustera les exemples de la boucle après les premiers tests.
- Le bon seuil de « gain important » pour proposer un changement hors incident.
- La forme des messages aux bénévoles : ton, longueur, ce qu'il faut toujours y mettre (où, quand, avec qui, comment y aller, qui appeler).
