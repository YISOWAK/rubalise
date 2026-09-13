# Agents for Humans: why my volunteer-planning agent never computes the plan

*Draft for builder.aws.com. First person, the author's voice. The title must keep "Agents for Humans".*

Last September I ran the SwissPeaks Marathon, 46 km in the Swiss Alps, in a bit more than eight hours. What I remember as much as the trail are the volunteers: someone at every aid station, on every road crossing, at the finish until the last runner. And someone, before the race, had put each of them at the right place at the right hour.

That someone works with two documents. The first is the roadbook, a PDF where the useful page is a picture of a spreadsheet: checkpoints, the hour the fastest runner arrives, the hour the slowest one does, and the cut-off after which you are out of the race. The second is the sign-up form, where a hundred people wrote in their own words: "I'm running the race myself but I can help on Friday evening", "I'm coming with three friends, we'd like an aid station together", "put me at Taney, I love that place, I'm 71 and still fit". From that, one person has to say who stands where, over three days and fifty shifts. Big races buy a platform for this. Small races have Excel and goodwill.

For the Agents for Humans hackathon I built Rubalise for that person. It runs on Strands Agents, an MCP tool server, OR-Tools and Claude on Amazon Bedrock, and it is deployed on Amazon Bedrock AgentCore. The design decision that shaped everything else: the language model never computes the schedule.

## The temptation, and why I resisted it

The obvious first version is to hand the model the volunteers and the shifts and ask for a schedule. I did not even try, for three reasons I could already see. A language model is bad at counting. It is worse at holding fifty constraints at the same time: availabilities that must cover the whole shift, night refusals, minors who cannot hold a road crossing or work after 22:00, skills like a 4x4 or a first-aid certificate, travel time between two mountain sites with a buffer at each end. And when it fails, it cannot tell you *why* there was no better answer, which is precisely what the organizer needs when someone is missing.

So the model does three jobs, and only three: it reads, it translates, it explains.

**It reads the roadbook the way a person would.** The PDF pages are rendered as images and sent to Claude with a closed JSON schema: checkpoints, kilometre, times, cut-offs, services, access notes, plus a list of doubts. One call. On the SwissPeaks roadbook it returned the six checkpoints with exact kilometres, altitudes, times and cut-offs, and flagged two small service icons it had confused. The organizer corrects those in plain language.

**It translates the form, one line at a time.** Each free-text answer becomes fields the solver understands: availability windows per day, skills from a closed vocabulary, adult or minor, night accepted or not, who they want to work with, who they refuse to work with, how many unlisted companions they bring. Free-text remarks that do not fit are kept and tagged (physical, material, animal, runner, relationship, logistics) for the second agent. Because the output is a closed schema, I could measure it: on 100 generated lines with known ground truth, availability is right on 99, skills on 100, night refusals on 99, companions, leader status and pairs on 100. The one availability "error" is the volunteer who wrote that he runs the race on Saturday: the model removed his Saturday, and it was right to.

**It explains.** Which brings us to the solver.

## The solver does the planning

The plan comes from OR-Tools CP-SAT. The model is a boolean grid, volunteer by shift. Hard constraints: availability must cover the whole shift, night refusal is an availability, minors are excluded from road posts and late shifts, required skills, and pairs of shifts that cannot be chained by the same person once you add travel time and buffers. Soft goals with weights: a person below the minimum staffing costs 1,000, below the ideal 10, a preference respected earns 1, a pair reunited earns 2, every quarter of an hour beyond eight hours of work costs 1. A shift without a leader is a hard constraint first; if the model is infeasible, the solver reruns with that constraint relaxed and reports the posts left without a leader.

On 50 shifts and 99 volunteers it returns a feasible plan in about ten seconds. And when it cannot fill a shift, it does something a language model cannot: it counts. "Friday 4x4 supply run to the isolated aid stations: one person missing. 91 volunteers are not free at that time, 6 have no 4x4, 1 has no licence." Then it names who is closest, meaning the people who miss on exactly one criterion: "Fabien Bender, Simon Rey-Bellet and Charlotte Pittet are free and licensed, they only lack the car. Lend one of them a 4x4." That is a phone call, not a spreadsheet exercise.

## Where Strands comes in

The orchestrator is a Strands `Agent` on Claude Sonnet 4.6, with the tools exposed by an MCP server: read the roadbook, correct the sheet, build the shifts from a template, translate the form, solve, verify, show the plan by post or by person, manage rules, grant derogations, write the journal, publish. During preparation the order of the steps is known, and the agent just runs them and talks to the organizer in between. On race day the order is unknown ("it's 11:00, two people from Le Grand Pré aren't coming") and the agent reasons: who is affected, re-solve against the published plan, explain each move, ask before publishing.

The tools are plain Python and run without any model, so the whole chain has tests that cost nothing. The agent adds the conversation, the judgment about what to call next, and the explanations in the organizer's language.

## What I would tell another builder

Give the model the jobs where it is good, reading and translating messy human input into a closed form, and explaining a result back. Give the counting to something that counts. Then measure every model step against ground truth, which closed schemas make possible. The result is an agent that is useful precisely because it knows what it does not do.

Code, data and design notes: github.com/YISOWAK/rubalise. The race is real; the volunteers are synthetic, because real volunteer data cannot be published.
