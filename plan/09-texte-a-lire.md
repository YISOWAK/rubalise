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
> The agent running all of this is the orchestrator.
> It's built with Strands, the open-source agent SDK from AWS.
> It talks to the organizer and it calls the tools.
>
> Then there's a second agent, and I call it the contradictor.
> It gets the finished plan without knowing how it was built,
> and it looks for problems that no rule describes.
> It can't change anything, it just reports.
>
> And nothing is sent to the volunteers unless the organizer says yes.
> That check is in the code, not in the prompt.

Enregistre A et B dans deux fichiers, `video/voix/voix2a.m4a` et `voix2b.m4a`.

---

## Scène 3 · la course à l'écran · environ 65 s · **tu filmes**

Onglet **Course**, plan déjà calculé. Trois ronds verts (Morgins, Conche, Blancsex) et trois oranges (Taney, Grand Pré, Bouveret) : c'est normal, le rond résume le jour de la course.

Ordre des clics : **Blancsex**, un rond vert. Son planning s'ouvre et la barre du vendredi est rouge. Tu cliques cette barre rouge, le panneau s'ouvre à droite. Puis « Toute la course » pour revenir.

Le contradicteur ne parle pas dans ce panneau, il parle dans la conversation. C'est la scène suivante.

> This is what comes out.
>
> Every checkpoint has a colour. Green means the team is complete,
> orange means it's a bit short, and red means someone is missing.
>
> Underneath is the schedule, shift by shift, over three days.
> If I click on a checkpoint, I only see its shifts.
>
> This one is green, because the colour is about race day.
> But the day before, there's a red shift.
> It's a supply run in a four-by-four, to the two aid stations you can't reach by road.
>
> I click on it, and the agent tells me it's one person short,
> and that only one volunteer out of a hundred can actually take it.
>
> And then it tells me what I can do about that.
> Three people are free and have a licence, they just don't have the right car.
> Lend one of them a four-by-four, and the shift is covered.
>
> It doesn't only tell me no. It tells me what to change.

---

## Scène 3 bis · le contradicteur · environ 25 s · **tu filmes**

La conversation à droite, après « Calculer le plan ». Tu fais défiler jusqu'à sa relecture.

> That panel is a checker, and a checker only knows the rules somebody wrote down.
>
> So there's a second agent that reads the finished plan and looks for the rest.
> Here it noticed that one team leader is bringing three friends,
> and those three are doing most of the work at that checkpoint.
> If she cancels, the post is empty.
>
> Nobody had written a rule about that.

---

## Scène 4 · le jour J · environ 33 s · **tu filmes**

Le chat. Tu tapes le message, tu laisses tourner, l'attente se coupe au montage.

**Avant de filmer, lis les noms sur l'écran.** Le solveur ne rend pas exactement le même plan à chaque calcul, donc ne recopie pas des noms au hasard. Clique sur **Le Grand Pré**, ouvre le créneau **11:00-16:00** du ravitaillement : l'équipe y est à 4, juste au minimum. Prends le **responsable** (marqué comme tel) et **une autre personne du même créneau**, et mets ces deux noms dans ton message.

Sur le plan que j'ai sous la main, ce serait Cédric Pellaud, responsable, et Marion Perrin. Retirer ces deux-là fait tomber le poste de 4 à 2, sous le minimum, et lui enlève son responsable : l'agent a un vrai problème à résoudre, et ça se voit sur la frise.

Le message à taper :

> Il est 11h. Cédric Pellaud et Marion Perrin, au ravitaillement du Grand Pré, viennent d'appeler, ils ne viennent pas. On fait quoi ?

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
