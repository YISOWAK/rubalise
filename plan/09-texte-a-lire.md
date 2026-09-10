# Le texte à lire, scène par scène

Une ligne = un souffle. Marque un temps à chaque ligne vide. Lis lentement, plus lentement que ça ne te paraît naturel : à l'écran ça passe bien.

Mots à articuler : **SwissPeaks** (pas « Swiss peak »), **Rubalise** (roo-bah-LEEZ), **roadbook**, **cut-off**, **contradictor** (con-tra-DIC-tor), **Strands**.

Tu n'enregistres l'écran que pour les scènes 3 et 4. Les scènes 1, 2 et 5 sont des images que j'ai déjà préparées dans `video/brut/`.

---

## Scène 1 · ta course · 35 s · fait

Images : les trois photos, dix secondes chacune. Prise 2 gardée.

---

## Scène 2 A · les deux documents · environ 65 s

Images (je les enchaîne) : la page du roadbook en entier, puis le tableau des points de passage en gros plan, puis le formulaire.

> Two documents land on that person's desk.
>
> The first one is the roadbook.
> The part they need is a photograph of a table.
> Every checkpoint of the race. The hour the first runner is expected.
> The hour the last one is.
> And the hour after which the mountain closes behind them.
>
> The second one is the sign-up form.
> A hundred people, writing in their own words.
>
> One of them is running the race himself, and offers Friday evening instead.
> One is coming with three friends, and wants an aid station for the four of them.
> One writes: put me at Taney, I love that place. I'm seventy-one, still fit.
>
> None of that is data. It's paper, and it's people.
>
> And out of it, one person has to say who stands where, and at what hour,
> across three days and fifty shifts.
>
> Get it wrong, and at two in the morning
> a runner comes down a mountain road to an empty aid station.
>
> Those are the evenings I wanted to give back.

---

## Scène 2 B · comment ça marche · environ 70 s

Image : le schéma, que j'anime bloc par bloc au rythme de ta voix. Tu n'as rien à filmer.

> So how do you turn that into a schedule?
>
> You start by reading the roadbook the way a person would.
> One model call on the pages, and it comes back with the checkpoints, the hours, the cut-offs,
> and an honest list of what it couldn't make out.
>
> Then the form.
> One call per line, and what a volunteer wrote in his own words
> becomes fields the program can reason about.
>
> And then you have to build the thing.
> This is where I stopped trusting the model.
> A language model is bad at counting, and worse at holding fifty constraints at once.
> So the plan comes from a constraint solver. Ten seconds.
> And it tells you not just the answer, but why there was no better one.
>
> The agent around all of this is the orchestrator.
> It talks to the organizer, and it calls those tools.
>
> And there's a second agent. I call it the contradictor.
> It reads the finished plan with no memory of how it was made,
> and it looks for what no rule covers.
> A thirteen-hour day. A post held up by one family.
> It changes nothing. It just says what it sees.
>
> Nothing is ever sent without the organizer.
> That confirmation lives in the code, not in the prompt.

Enregistre A et B dans deux fichiers, `video/voix/voix2a.m4a` et `voix2b.m4a`. Plus court à refaire si une phrase tombe mal.

---

## Scène 3 · la course à l'écran · environ 50 s · **tu filmes**

Onglet **Course**, plan déjà calculé. Tu cliques un point de la frise, puis un créneau, puis « Toute la course ».

> Here is what comes out.
>
> Every checkpoint, with the state of its team.
> Green when it's complete. Orange when it's a bit short. Red when someone is missing.
>
> Underneath, the schedule itself, shift by shift, over three days.
> I click on a checkpoint, and only its shifts remain.
> A shift tells you who is there, who leads it, and what is missing, with the reason.
>
> On the whole race, one person is missing.
> A four-by-four driver on Friday, and the agent tells you why nobody else can take it.
>
> The contradictor had things to say too.
> A post leader whose three companions are carrying the entire post.
> A thirteen-hour day.
> Nobody had written a rule for either of those.

---

## Scène 4 · le jour J · environ 40 s · **tu filmes**

Le chat. Tu tapes le message, tu laisses tourner, l'attente se coupe au montage.

> Now, race day. This is the part that matters.
>
> It's eleven in the morning, and two volunteers are not coming.
> I tell the agent, the way I'd tell a colleague.
>
> It finds who is affected, and repairs the plan with as few moves as it can.
> Shifts already finished never move.
> People already standing at a post are flagged: those you call yourself.
>
> And it asks before it publishes anything.

---

## Scène 5 · la fin · environ 25 s

Image : le tableau des mesures, puis le lien du dépôt.

> All of this is measured.
> The roadbook reading, the form, ten solver scenarios, the race-day repairs.
>
> It runs on Amazon Bedrock AgentCore, and the code is public.
> A triathlon is just another template file.
>
> Volunteers make races happen.
> The person who organizes them deserves a tool.
