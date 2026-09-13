# La soumission : ce qu'il reste à faire, et les textes à coller

Date limite : lundi 14 septembre 2026, 17h00 heure du Pacifique, soit **mardi 15 septembre 02h00 à Paris**. Nous sommes dimanche 13 : vise lundi en fin d'après-midi, pas lundi minuit.

## Dans l'ordre

1. **YouTube : fait le 13 septembre.** https://youtu.be/r-ERVq44WSE, en public, notifications aux abonnés désactivées, remix interdits, mention « contenu synthétique » (la voix). Lien mis dans le README.
2. **Devpost : soumis le 13 septembre (5 étapes sur 5).** Modifiable jusqu'à la date limite pour ajouter les liens des billets. Nom, accroche, texte long, 13 tags, liens dépôt, démo et vidéo, galerie de 4 images avec légendes, piste Good Neighbor Agents, schéma d'architecture, instructions de test. Reste : confirmer l'AWS Builder ID (mis : antoine.krycho@gmail.com), cocher les conditions et cliquer « Submit project ». On peut encore modifier après soumission jusqu'à la date limite, par exemple pour ajouter les liens des billets.
3. **Les billets de blog bonus**, 0,2 point chacun, trois au maximum. Profil Builder Center créé le 13 septembre (@yisowak) ; le site impose un délai de quelques minutes avant le premier article. Trois brouillons sont dans `docs/blog/`. Ils sont écrits à la première personne avec ce qu'on a vraiment fait ; relis-les, change ce qui ne sonne pas comme toi, et publie-les sur builder.aws.com avec ton Builder ID, **avant la date limite**. Le titre doit contenir « Agents for Humans ». Après publication, colle les liens dans la soumission Devpost.
4. **Laisse la démo en ligne jusqu'au 8 octobre**, fin du jugement. Le jury n'est pas obligé de la tester, mais s'il le fait, il faut qu'elle réponde. Un plan complet coûte environ 15 centimes, l'alerte de budget est en place.

## YouTube

**Titre**

```
Rubalise, an AI agent that plans trail-race volunteers | AWS Agents for Humans hackathon
```

**Description**

```
Rubalise helps the person who assigns volunteers on a trail race: a hundred volunteers, fifty shifts, a roadbook PDF made of images, and a sign-up form where people write in plain sentences.

Built for the AWS Agents for Humans hackathon (Good Neighbor Agents track) with Strands Agents, an MCP tool server, OR-Tools CP-SAT and Claude on Amazon Bedrock, and deployed on Amazon Bedrock AgentCore Runtime.

The model reads, translates and explains. It never computes the schedule: a constraint solver does, in ten seconds, and it says why there was no better answer. A second agent, the contradictor, rereads every plan with a blank context and reports what no written rule covers. Nothing is sent to volunteers unless the organizer says yes, and that check lives in the code, not in the prompt.

Demonstrated on the SwissPeaks Marathon 2025 (46 km, Swiss Alps), a race I ran. The organizer's screen is in French; the narration is in English.

Code, data and design notes: https://github.com/YISOWAK/rubalise

0:00 Why I built it
0:26 The organizer's two documents
1:18 How it works
2:26 The race, post by post
3:16 The contradictor
3:36 Race day
4:00 Measured results
```

## Devpost

**Project name** : Rubalise

**Tagline** (une ligne)

```
An agent that plans trail-race volunteers, and never guesses the schedule.
```

**Track** : Good Neighbor Agents

**Built with** (mots-clés)

```
python, strands-agents, amazon-bedrock, claude, amazon-bedrock-agentcore, model-context-protocol, or-tools, aws-lambda, amazon-api-gateway, amazon-s3, amazon-polly, playwright, ffmpeg
```

**Links** : le dépôt `https://github.com/YISOWAK/rubalise`, la vidéo YouTube, et le lien de démo qui est dans `web/lien_demo.txt` (avec sa clé, c'est voulu : la clé n'ouvre que cette page).

**About the project** (le champ long, il accepte le Markdown)

```
## Inspiration

Last September I ran the SwissPeaks Marathon: 46 km and 2,483 m of climb in the Swiss Alps, eight and a half hours. I remember the volunteers as much as the trail. Someone had put each of them at the right place at the right hour, and that someone works with a roadbook PDF made of images, a sign-up form where a hundred people write whatever they want, and a WhatsApp group, on their evenings. Big races buy a platform. Small races have Excel and goodwill. Rubalise is for them. The name is the striped tape that marks the trail.

## What it does

The organizer drops the roadbook and the sign-up form in a chat. The agent reads the PDF pages as images and returns a closed race sheet (checkpoints, first and last runner, cut-offs) with a list of what it was not sure about. It translates every free-text line of the form into fields a solver understands, keeping the remarks tagged. A template turns the race into 50 shifts. A constraint solver assigns 99 volunteers under hard rules (availability, night refusals, minors, skills, travel between sites) and weighted goals (minimum staffing, preferences, pairs, workload). A deterministic checker lists violations. A second agent, the contradictor, rereads the plan with a blank context and reports what no rule describes: a post leader whose three unlisted companions carry the whole post, a thirteen-hour day.

When someone is missing, the agent does not stop at "no". It names who is closest and what to change: three people are free and licensed, they only lack a 4x4.

Nothing reaches the volunteers unless the organizer explicitly confirms. Publishing, waiving a rule and changing a rule go through a gate that lives in the code, not in the prompt. On race day, the published plan is a commitment: every change has a cost, higher for people already on site, and the solver repairs with the fewest moves. Finished shifts never move.

A web cockpit shows the race post by post: a timeline of checkpoints coloured by staffing, the schedule by site, the detail of a shift with its team and its gaps, and the chat with the agent.

## How we built it

Two Strands agents: the orchestrator (Claude Sonnet 4.6) holds the conversation and calls the tools, in a known order during preparation and freely on race day; the contradictor (Claude Opus 4.6) only reads and reports. The tools are exposed by an MCP server (16 tools: read roadbook, translate form, build shifts, solve, verify, rules, derogations, journal, publish) and are testable without any model. The solver is OR-Tools CP-SAT. Everything the agents know lives in a JSON state per session, not in their memory.

Hosting: Amazon Bedrock AgentCore Runtime (CodeZip, Python 3.12), the MCP server running inside the session. The cockpit is a single HTML page behind a Lambda relay and an HTTP API; because a plan takes longer than the API's 30-second limit, the relay starts the job, stores the result in S3 and the page polls.

## Challenges we ran into

Making the language model useful without letting it plan: it is bad at counting and at holding fifty constraints at once, so every model step fills a closed JSON schema that code validates, and every step is measured against ground truth. Keeping a published plan stable on race day, which meant a second objective in the solver with change costs. Making the human gate real when the agent is hosted: it executes only if the organizer's own message contains an explicit confirmation. And the usual: Bedrock quotas, a blocked Lambda function URL, a 30-second API limit, sessions that sleep.

## Accomplishments that we're proud of

Form translation: 99 out of 100 lines right, and the one difference is the runner whose Saturday the model correctly removed. Roadbook: all six checkpoints exact. A full plan in ten seconds with the reason for every gap and the nearest candidates named. Race day: five no-shows repaired in half a second with one removal and six additions. The contradictor finding, unprompted, the post held up by one family.

## What we learned

A solver plus a language model that reads and explains beats a language model that plans. A second agent with a blank context catches what the first one cannot see, because it did not build the plan. And a guard in a prompt is not a guard; a guard in the code is.

## What's next

Volunteer briefs written by the model for each person, a post-race review that reads the journal and proposes next year's rules, durable state across sessions, and other event templates (a triathlon is another template file, not another program).
```

**Testing instructions** (si le formulaire a un champ à part, sinon c'est dans le README)

```
Open the demo link (no login). Click "Calculer le plan" and wait 60 to 90 seconds: the timeline turns green, orange or red. Click "Chalet de Blancsex" to filter its shifts, then the red Friday bar: the panel names who is missing, why, and who is closest. Click the chip "Jour J : deux absents au Grand Pré" to see a race-day repair; the agent asks before publishing. The "How it works" tab is in English. A session sleeps after 15 idle minutes: reload and compute again if the timeline is grey.
```
