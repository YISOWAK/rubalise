# Le texte à lire, scène par scène

Anglais parlé, phrases entières, comme si tu expliquais à un collègue. Une ligne vide = un temps. Lis lentement.

Mots à articuler : **SwissPeaks** (pas « Swiss peak »), **Rubalise** (roo-bah-LEEZ), **roadbook**, **cut-off**, **contradictor** (con-tra-DIC-tor), **Strands**.

Tu n'enregistres l'écran que pour les scènes 3 et 4. Les scènes 1, 2 et 5 sont des images déjà prêtes dans `video/brut/`.

---

## Scène 1 · ta course · 35 s · fait

Images : les trois photos, dix secondes chacune. Prise 2 gardée.

---

## Scène 2 A · les deux documents · environ 67 s

Images : la page du roadbook, puis le tableau des points de passage en gros plan, puis le formulaire.

> So here's what the organizer starts with.
>
> The first thing is the roadbook. It's a PDF, and the page I care about
> is basically a screenshot of a spreadsheet.
> It lists every checkpoint, what time the fastest runner gets there,
> what time the slowest one does, and the cut-off time, after which you're out of the race.
>
> The second thing is the sign-up form.
> A hundred people filled it in, and they wrote in normal sentences.
>
> One guy is running the race himself, so he can only help on Friday evening.
> A woman is coming with three friends, and they'd like an aid station together.
> Another one says: put me at Taney, I love that place, I'm seventy-one and still fit.
>
> From those two files, one person has to work out who's where and at what time,
> over three days and fifty shifts.
>
> If they get it wrong, someone reaches an aid station at two in the morning
> and there's nobody there.

---

## Scène 2 B · comment ça marche · environ 85 s

Image : le schéma, que j'anime bloc par bloc au rythme de ta voix.

> So how do you go from that to a schedule?
>
> First you read the roadbook.
> That's one model call on the pages as images.
> It gives back the checkpoints, the times, the cut-offs,
> and a list of what it wasn't sure about, so the organizer can check.
>
> Then the form. One call per line, and what someone wrote becomes real fields.
>
> Then you build the schedule, and that part is not done by the model.
> Language models are bad at counting, and bad at respecting fifty constraints at the same time.
> So the plan comes from a constraint solver. It takes about ten seconds,
> and it can tell you why there wasn't a better answer.
>
> The agent running all of this is the orchestrator. It's a Strands agent.
> It talks to the organizer and it calls the tools.
>
> Then there's a second agent, and I call it the contradictor.
> It gets the finished plan without knowing how it was built,
> and it looks for problems that no rule describes.
> Someone working thirteen hours, or a checkpoint where one family does everything.
> It can't change anything, it just reports.
>
> And nothing is sent to the volunteers unless the organizer says yes.
> That check is in the code, not in the prompt.

Enregistre A et B dans deux fichiers, `video/voix/voix2a.m4a` et `voix2b.m4a`.

---

## Scène 3 · la course à l'écran · environ 55 s · **tu filmes**

Onglet **Course**, plan déjà calculé. Trois ronds verts (Morgins, Conche, Blancsex) et trois oranges (Taney, Grand Pré, Bouveret) : c'est normal, le rond résume le jour de la course.

Ordre des clics : **Blancsex** d'abord, un rond vert. Son planning s'ouvre et la barre du vendredi est rouge, c'est le 4x4 manquant. Le rond est vert parce qu'il résume le samedi, la barre rouge est la veille. Puis un créneau pour montrer l'équipe, puis « Toute la course » pour revenir.

> This is what comes out.
>
> Every checkpoint has a colour. Green if the team is complete,
> orange if it's a bit short, red if someone is missing.
>
> Underneath is the schedule, shift by shift, over three days.
> I click on a checkpoint and I only see its shifts.
> A shift tells me who's working, who's in charge, and what's missing and why.
>
> On this plan, one person is missing in the whole race.
> It's a four-by-four driver on Friday, and the agent explains why nobody else can do it.
>
> The contradictor had things to say too.
> One team leader brought three friends, and those three are doing most of the work
> at that checkpoint. Nobody had written a rule about that.

---

## Scène 4 · le jour J · environ 33 s · **tu filmes**

Le chat. Tu tapes le message, tu laisses tourner, l'attente se coupe au montage.

> And then there's race day, which is really the point.
>
> It's eleven in the morning and two volunteers aren't coming.
> I tell the agent, the way I'd tell a colleague.
>
> It finds who's affected and fixes the plan with as few changes as possible.
> Shifts that are already over don't move.
> People who are already at their post get flagged, because those you call yourself.
>
> And it asks before it sends anything.

---

## Scène 5 · la fin · environ 23 s

Image : le tableau des mesures, puis le lien du dépôt.

> Everything here is measured. The roadbook reading, the form,
> ten solver scenarios, the race-day repairs.
>
> It runs on Amazon Bedrock AgentCore, and the code is public.
> For a triathlon, it's another template file.
>
> Volunteers make races happen.
> The person who organizes them should have a decent tool.
