# Agents for Humans: the second agent whose only job is to disagree

*Draft for builder.aws.com. First person, the author's voice. The title must keep "Agents for Humans".*

Rubalise, my entry for the Agents for Humans hackathon, plans the volunteers of a trail race: it reads the roadbook, translates the sign-up form, and lets a constraint solver build the schedule. This post is about what happens *after* the plan exists, because that is where most of the risk is. A schedule that satisfies every written rule can still be a bad schedule.

## Two verifications, because rules are never complete

The first check is code. A deterministic verifier runs nine blocking rules and eleven alerts over the plan: a shift below its minimum, a post without a leader, a minor on a road crossing or after 22:00, a runner of the race assigned during the race, two sign-ups with the same phone number, a team with nobody who has done a previous edition, an isolated post with no vehicle in the team, and so on. It is fast, exact, and it only knows what somebody wrote down.

The second check is a Strands `Agent` I call the contradictor. It runs on Claude Opus 4.6, a stronger model than the orchestrator, and it is built to be as independent as possible from the agent that made the plan:

- **Blank context.** It does not see the conversation, the orchestrator's reasoning, or the corrections the organizer made. It gets the finished plan, the volunteers with their free-text remarks, the rules, and nothing else.
- **Read-only tools.** It can look at the plan by post and by person, at the rules and at the journal. It cannot modify anything.
- **A fixed output.** Findings ranked by severity, each with the people and shifts involved and a suggested move. It reports to the orchestrator, which relays to the organizer. It never talks to the organizer directly.
- **Automatic.** It runs after every plan, without being asked.

Why the blank context matters: an agent that built a plan will defend it. It has already reasoned its way to every assignment and will read the plan through that reasoning. A second agent that only sees the result reads it the way a colleague would the next morning.

## What it found without being told to look

On the SwissPeaks Marathon dataset, with no instruction other than "review this plan against the rules and the volunteers' remarks", the contradictor came back with:

- A post leader at the bib pick-up who wrote that she comes with three friends. The solver counted the four of them, so the shift is staffed. The contradictor noticed that three of the four are unlisted, unnamed people. If she cancels, the post falls.
- A volunteer who is the only named person on the evening standby team, again with anonymous companions.
- A volunteer with a thirteen-hour day: two shifts the solver considered compatible, with travel in between, that add up to a day nobody should work.
- A hand-over between two posts by 4x4 that is legal by the travel matrix and unrealistic in practice.

None of these breaks a written rule. All four are things the organizer would want to know. The rules file now has an entry for the thirteen-hour day, because the organizer can add rules from the chat; the others stay in the contradictor's territory.

## The gate is in the code, not in the prompt

Three actions have consequences outside the system: publishing the plan to volunteers, waiving a rule for one shift, and changing a rule. For these, the agent proposes and the organizer decides. I wanted that to be a property of the program, not a sentence in the system prompt, because a sentence in a prompt is a request, not a guarantee.

In the terminal, the tool itself asks for confirmation before doing anything. In the hosted version on AgentCore, there is no terminal, so the gate works in two steps: the first time the agent calls `publier`, the tool refuses and records that a confirmation is pending; it only executes if the organizer's *next message*, the human's own text, contains an explicit yes. The agent cannot confirm on the organizer's behalf, because the check reads the message the human typed, not the agent's arguments to the tool. Every decision, with its author and its reason, goes to an append-only journal.

## Race day: a published plan is a commitment

Preparation and race day are different problems. Before publication, the solver is free to move anyone. After, every change has a human cost: someone rearranges their weekend, someone drives to the wrong place. So the race-day solver has a second objective. Removing a person from a shift they were notified of costs 20; removing someone already standing at their post costs 100; adding a shift to someone on race day costs 10. Shifts that are already finished are frozen. The solver looks for the repair with the fewest moves, and the agent explains each one: who moves, from where, to where, and whether that person must be called in person because they are already on site.

Five no-shows announced at 06:30 against the published plan: one removal, six additions, half a second, no shift below its minimum. A storm at 15:00 that closes one aid station and needs three more people at another: six removals, three additions, and one post left without a leader, reported as such rather than hidden.

## What I would tell another builder

Write the rules you can write, and check them with code. Then give a second agent, with a blank context and read-only tools, the job of disagreeing. And when an action has consequences for real people, put the confirmation in the code path, where the model cannot talk its way around it.

Code and design notes: github.com/YISOWAK/rubalise.
