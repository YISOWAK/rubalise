# La vidéo : 5 minutes maximum, visite du site en anglais

Règle du concours : une démo qui marche et un pitch (le problème, pour qui, pourquoi ça compte). Écran enregistré et voix off suffisent, pas besoin d'être à l'image. Tout le dossier doit être en anglais ou traduit, donc voix off en anglais. Le jury note Technical Implementation, Impact, Creativity, Presentation, Strands usage. Pas de soutenance : le jury juge sur la vidéo, le texte et le dépôt, et n'est même pas obligé de tester le lien.

Ordre du récit : d'abord ta course, ensuite **les deux documents que l'organisateur a vraiment entre les mains** et ce qu'il doit en faire, ensuite seulement comment la machine répond à ce besoin, et enfin la démonstration. Personne ne comprend une architecture avant d'avoir vu le problème.

## Le déroulé

| Temps | À l'écran | Voix off (anglais) |
|---|---|---|
| 0:00 - 0:35 | Trois photos, dix secondes chacune, dans `video/brut/` : la ligne de départ à Morgins, l'arche Finisher, la médaille. Fondu de l'une à l'autre | **Enregistré (prise 2).** Last September I ran the SwissPeaks Marathon. It was forty-six kilometers in the Swiss Alps and it took me around eight and a half hours. And honestly, I remember the volunteers as much as the trail. Everything was so well organized, and I keep thinking that someone put a lot of effort and time into making my race go well, almost for free. So I built an agent to help that person. I called it Rubalise, after the tape that marks the trail. |
| 0:35 - 1:25 | Onglet **Notre course**. Tu montres d'abord la page du roadbook, tu la laisses trois secondes, puis tu descends sur le formulaire et ses réponses en texte libre | Let me show you what that person actually works with. This is the official roadbook of the race. It's a PDF, and everything that matters is a picture of a table: each checkpoint, the kilometer, when the first runner arrives, when the last one does, and the cut-off time after which runners are stopped. And this is the sign-up form. A hundred people wrote whatever they wanted. Saturday all day, but I'm running the race myself. I'll come with three friends. Anything except night. Out of those two documents, one person has to produce a schedule: who is where, at what time, over three days and fifty shifts. And if one shift ends up empty, a runner is alone on a mountain road at night. That is the job I wanted to help with. |
| 1:25 - 2:25 | Onglet **How it works**, le schéma. Tu suis à la souris, dans l'ordre du texte : les deux outils LLM, le solveur, l'orchestrateur, le contradicteur | So what do you need for that? First, something to read the PDF. That's this tool: one model call, and it returns a strict form, plus a list of what it wasn't sure about. Second, something to turn free text into data: one model call per line, filling closed fields. Then you need to build the schedule itself. And that is not a job for a language model: it is bad at counting, and bad at holding fifty constraints at once. So the plan comes from a constraint solver, in under ten seconds. The model never decides who goes where. Around them, the orchestrator: a Strands agent that talks to the organizer and calls those tools. And on the right, a second agent, the contradictor. It re-reads every plan with a blank context and a stronger model, looking for what no rule covers. It changes nothing, it just reports. And nothing goes out without the organizer saying yes. That confirmation is in the code, not in the prompt. |
| 2:25 - 3:15 | Onglet **Course**, plan déjà calculé. Tu cliques un point de la frise (Taney), puis un créneau, puis « Toute la course » | Here is the result. The timeline shows every checkpoint with its status: green when the team is complete, orange when it is a bit short, red when someone is missing. Below, the schedule, shift by shift, over three days. I click a checkpoint, and only its shifts remain. A shift shows its team, who leads it, and what is missing, with the reason. On the whole race, one person is missing: a four-by-four driver on Friday, and the agent says why nobody else can do it. The contradictor had remarks of its own: a post leader whose three companions carry the entire post, and a thirteen-hour day. No rule said either of those. |
| 3:15 - 4:10 | Le chat. Tu tapes le message du jour J, l'attente se coupe au montage, la réponse s'affiche, la frise se met à jour | Now, race day. It's eleven in the morning, and two volunteers are not coming. I tell the agent, in plain language. It lists who is affected, repairs the plan with as few moves as possible, and explains each move. Shifts already finished never move. People already on site are flagged: those you warn in person. The timeline updates. And it asks before publishing anything. |
| 4:10 - 4:40 | Retour sur **How it works**, tableau « What was measured », puis le lien du dépôt | Everything here is measured: the roadbook reading, the form translation, ten solver scenarios, the race-day repairs. The agents run on Amazon Bedrock AgentCore. The code and the data are public. And a triathlon is just another template file. Volunteers make races happen. The person who organizes them deserves a tool. |

Autour de 4 min 40. Si une scène est trop longue à dire, coupe des phrases, personne ne vérifie le mot à mot.

Ne dis pas que tu as organisé des courses : Devpost vérifie le rôle du gagnant et le README dit que tu as couru celle-là. Le vrai est plus fort.

## Le message à taper (scène 5)

1. Il est 11h. Deux personnes du ravitaillement du Grand Pre, creneau 11:00-16:00, ne viennent pas. Prendre les noms sur l'ecran avant de filmer : le responsable et une autre.
2. Facultatif, si tu veux montrer le garde-fou à l'écran : « Oui, publie le plan corrigé. » L'agent demande confirmation, tu réponds « oui ».

## Ce que tu enregistres, ce que je monte

- **Toi** : les voix, une par scène, dans `video/brut/` sous les noms voix2.m4a à voix6.m4a (la scène 1 est faite). Et trois clips d'écran : scènes 2, 4 et 5, sous les noms scene2.mp4, scene4.mp4, scene5.mp4.
- **Moi** : la scène 1 (les photos), la scène 3 (le schéma, animé à partir de `docs/architecture.png`) et la scène 6 (le tableau des mesures). Puis le montage complet : coupes, calage des voix, fondus, export 1080p.

## Avant d'enregistrer l'écran

- Chrome, fenêtre en plein écran 1920 × 1080, zoom de la page à 110 ou 125 % pour que le texte reste lisible sur YouTube.
- Ouvre le lien de démo (`web/lien_demo.txt`), lance **Calculer le plan**, attends la minute et demie : l'onglet Course doit être vert avant la première seconde de film.
- Ouvre une fois chaque onglet pour que tout soit chargé. Une session s'endort après 15 minutes sans message : enchaîne, ou renvoie un message avant de filmer.
- Ferme les autres fenêtres et coupe les notifications (Paramètres > Système > Notifications > Ne pas déranger).

## Pendant

- Win + Alt + R lance l'enregistreur de Windows sur la fenêtre active. Tu n'as pas besoin de parler : la voix vient après.
- Pour la scène 5, tape le message, laisse tourner, attends la réponse : la minute d'attente se coupera au montage.
- Va lentement à la souris, deux fois plus lentement que d'habitude. Ce qui semble lent en direct est normal en vidéo.
