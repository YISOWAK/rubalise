# La vidéo : 5 minutes maximum, visite du site en anglais

Règle du concours : une démo qui marche et un pitch (le problème, pour qui, pourquoi ça compte). Écran enregistré et voix off suffisent, pas besoin d'être à l'image. Tout le dossier doit être en anglais ou traduit, donc voix off en anglais. Le jury note Technical Implementation, Impact, Creativity, Presentation, Strands usage. Pas de soutenance : le jury juge sur la vidéo, le texte et le dépôt, et n'est même pas obligé de tester le lien.

Principe : tu fais visiter le site, en commençant par le schéma, et tu termines par une vraie interaction avec l'agent. Six scènes, 4 min 30 environ. Ce que tu vois à gauche, ce que tu dis à droite.

## Le déroulé

| Temps | À l'écran | Voix off (anglais) |
|---|---|---|
| 0:00 - 0:30 | Onglet **How it works**, en haut, sans bouger | On every trail race, someone spends their evenings doing this. A hundred volunteers, fifty shifts, a PDF made of images, and a form where people write whatever they want. One gap in one shift means a runner alone on a road at night. Big races buy a platform. Small races have Excel and good will. This is Rubalise. |
| 0:30 - 1:30 | Le schéma. Tu suis les blocs à la souris, dans l'ordre du texte : Organizer, Orchestrator, Tools, Contradictor, State | Here is how it works. The organizer, at the top, talks to the agent in the chat. Nothing goes out without them. The orchestrator is a Strands agent: an LLM that loops over tools. During preparation, the order of the steps is known, so it just runs them. On race day, the order is unknown, so it reasons. The tools are exposed by an MCP server: read the roadbook, translate the form, build the posts, solve, check the rules, log every decision. Only two of them use a model. The plan itself comes from a constraint solver, OR-Tools, never from the LLM. On the right, the contradictor: a second agent, with a blank context and a stronger model. It reviews every plan with the rules and common sense, and reports what the code cannot see. It changes nothing. And everything the agents know lives in this state, on disk, not in their memory. |
| 1:30 - 2:15 | Onglet **Notre course**. Tu descends lentement : fiche, points de passage, profil, page du roadbook, formulaire et traduction, règles, journal | The organizer's screen is in French: the race is in Switzerland. It is a real race, the SwissPeaks Marathon, forty-six kilometers, and I ran it last year. The agent read the official roadbook, page by page, as images, and produced this race sheet: checkpoints, cut-off times, first and last runner. It flagged what it was not sure about. Below, the volunteer form: free text, and its translation into closed fields the solver understands. Ninety-nine lines out of a hundred are right. Then the rules, which the organizer edits from the chat, and the log: who decided what, when, and why. |
| 2:15 - 3:15 | Onglet **Course**, plan déjà calculé. Tu cliques un point de la frise (Taney), puis un créneau, puis « Toute la course » | This is the race, post by post. The timeline shows each checkpoint with its status: green when the team is complete, orange when it is a bit short, red when someone is missing. Below, the schedule, shift by shift, over three days. I click a checkpoint: only its shifts remain. A shift shows its team, who leads it, and what is missing, with the reason. On the whole race, one person is missing: a four-by-four driver on Friday, and nobody else can do it. The contradictor had remarks too: a post leader whose three companions carry the whole post, a thirteen-hour day. No rule said that. |
| 3:15 - 4:15 | Le chat. Tu tapes le message du jour J, l'attente se coupe au montage, la réponse s'affiche, la frise se met à jour | Now, race day. It is eleven o'clock, and two volunteers are not coming. I tell the agent, in plain language. It lists who is affected, repairs the plan with as few moves as possible, and explains each move. Shifts already finished never move. People already on site are flagged: warn them in person. The timeline updates. And it asks before publishing. That confirmation is in the code, not in the prompt. Publishing, waiving a rule, changing a rule: all of it goes through the organizer. |
| 4:15 - 4:45 | Retour sur **How it works**, tableau « What was measured », puis le lien du dépôt | Everything is measured: the translation, the roadbook reading, ten solver scenarios, the race-day repairs. The agents run on Amazon Bedrock AgentCore. The code and the data are public. A triathlon is just another template file. Volunteers make races happen. The person who organizes them deserves a tool. |

Environ 580 mots : à un rythme posé, 4 min 30. Si une scène est trop longue à dire, coupe des phrases, personne ne vérifie le mot à mot.

## Le message à taper (scène 5)

1. Il est 11h, Emma Morisod et Sandra Rappaz ne viennent pas. On fait quoi ?
2. Facultatif, si tu veux montrer le garde-fou à l'écran : « Oui, publie le plan corrigé. » L'agent demande confirmation, tu réponds « oui ».

## Avant d'enregistrer

- Chrome, fenêtre en plein écran 1920 × 1080, zoom de la page à 110 ou 125 % pour que le texte reste lisible sur YouTube.
- Ouvre le lien de démo (`web/lien_demo.txt`), lance **Calculer le plan**, attends la minute et demie : l'onglet Course doit être vert avant la première seconde de film.
- Ouvre une fois chaque onglet pour que tout soit chargé. Une session s'endort après 15 minutes sans message : enchaîne, ou renvoie un message avant de filmer.
- Ferme les autres fenêtres et les notifications (Windows : Paramètres > Système > Notifications > Ne pas déranger).

## Pendant

- Win + Alt + R lance l'enregistreur de Windows sur la fenêtre active. Tu n'as pas besoin de parler : la voix vient après.
- Enregistre les scènes dans l'ordre du tableau, en un ou plusieurs clips. Pour la scène 5, tape le message, laisse tourner, attends la réponse : la minute d'attente se coupera au montage.
- Va lentement à la souris, deux fois plus lentement que d'habitude. Ce qui semble lent en direct est normal en vidéo.

## Montage

- Clipchamp (fourni avec Windows 11) : importe les clips, mets-les dans l'ordre, coupe les temps morts et l'attente de l'agent.
- Voix off : dans Clipchamp, « Enregistrer et créer » > « Audio », tu lis la colonne de droite scène par scène, tu recommences une scène autant de fois que tu veux.
- Exporte en MP4 1080p, envoie sur YouTube en **public** (exigé par le règlement), et colle le lien dans le formulaire Devpost.

## À préparer

- Rien d'autre que le site : le schéma en anglais est dans l'onglet How it works, et en PNG dans `docs/architecture.png` si tu veux l'afficher en plein écran dans la scène 2.
