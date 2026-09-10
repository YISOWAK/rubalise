# Le texte à lire, scène par scène

Une ligne = un souffle. Marque un temps à chaque ligne vide. Lis lentement, plus lentement que ça ne te paraît naturel : à l'écran ça passe bien.

Quelques mots à articuler : **SwissPeaks** (pas « Swiss peak »), **Rubalise** (roo-bah-LEEZ), **roadbook**, **cut-off**, **contradictor** (con-tra-DIC-tor), **Strands**.

---

## Scène 1 — ta course · fait, prise 2 gardée

---

## Scène 2 A — les documents · environ 50 s

À l'écran : onglet **Notre course**. La page du roadbook trois secondes, puis tu descends sur le formulaire et ses réponses.

> Let me show you what that person actually works with.
>
> This is the official roadbook of the race.
> It's a PDF, and everything that matters is a picture of a table.
> Each checkpoint. The kilometer. When the first runner arrives, when the last one does.
> And the cut-off time, after which runners are stopped.
>
> And this is the sign-up form.
> A hundred people wrote whatever they wanted.
> "Saturday all day, but I'm running the race myself."
> "I'll come with three friends."
> "Anything except night."
>
> Out of those two documents, one person has to build a schedule.
> Who is where, at what time, over three days and fifty shifts.
> And if one shift ends up empty, a runner is alone on a mountain road at night.
>
> That is the job I wanted to help with.

---

## Scène 2 B — comment ça marche · environ 60 s

À l'écran : onglet **How it works**, le schéma. Tu suis à la souris, dans l'ordre du texte. Je peux aussi l'animer moi-même si tu préfères ne pas filmer.

> So, what do you need for that?
>
> First, something to read the PDF.
> That's this tool. One model call, and it returns a strict form.
> Plus a list of what it wasn't sure about, for the organizer to check.
>
> Second, something to turn free text into data.
> That's this one. One call per line, filling closed fields.
>
> Then you need to build the schedule itself.
> And that is not a job for a language model.
> A language model is bad at counting, and bad at holding fifty constraints at once.
> So the plan comes from a constraint solver. Ten seconds.
> The model never decides who goes where.
>
> Around them, the orchestrator.
> A Strands agent that talks to the organizer and calls those tools.
>
> And on the right, a second agent. I call it the contradictor.
> It reads every plan with a blank context and a stronger model,
> looking for what no rule covers.
> It changes nothing. It just tells the organizer what it sees.
>
> And nothing goes out without the organizer saying yes.
> That confirmation is in the code, not in the prompt.

Enregistre A et B dans deux fichiers séparés, `video/voix/voix2a.m4a` et `voix2b.m4a`. Plus court à refaire si une phrase tombe mal.

---

## Scène 3 — la course à l'écran · environ 50 s

À l'écran : onglet **Course**, plan déjà calculé. Tu cliques un point de la frise, puis un créneau, puis « Toute la course ».

> Here is the result.
> The timeline shows every checkpoint with its status.
> Green when the team is complete. Orange when it's a bit short. Red when someone is missing.
>
> Below, the schedule. Shift by shift, over three days.
> I click a checkpoint, and only its shifts remain.
> A shift shows its team, who leads it, and what is missing, with the reason.
>
> On the whole race, one person is missing.
> A four-by-four driver on Friday, and the agent says why nobody else can do it.
>
> The contradictor had remarks of its own.
> A post leader whose three companions carry the entire post. A thirteen-hour day.
> No rule said either of those.

---

## Scène 4 — le jour J · environ 55 s

À l'écran : le chat. Tu tapes le message, tu laisses tourner, l'attente se coupe au montage.

> Now, race day.
> It's eleven in the morning, and two volunteers are not coming.
> I tell the agent, in plain language.
>
> It lists who is affected.
> It repairs the plan with as few moves as possible, and explains each move.
> Shifts already finished never move.
> People already on site are flagged: those you warn in person.
>
> The timeline updates.
> And it asks before publishing anything.

---

## Scène 5 — la fin · environ 30 s

À l'écran : retour sur **How it works**, tableau des mesures, puis le lien du dépôt.

> Everything here is measured.
> The roadbook reading, the form translation, ten solver scenarios, the race-day repairs.
>
> The agents run on Amazon Bedrock AgentCore.
> The code and the data are public.
> And a triathlon is just another template file.
>
> Volunteers make races happen.
> The person who organizes them deserves a tool.
