# Agents for Humans: from a Strands agent on my laptop to AgentCore and a live cockpit

*Published on the AWS Builder Center on 13 September 2026: https://builder.aws.com/content/3JHRH1HmBbwSgUDwB07Uppohqp6/agents-for-humans-from-a-strands-agent-on-my-laptop-to-agentcore-and-a-live-cockpit*

The first two posts about Rubalise, my Agents for Humans entry, were about design: a model that reads and explains but never plans, and a second agent that only disagrees. This one is about the plumbing: how the agent went from a terminal on my laptop to a hosted runtime with a web page in front of it, what broke on the way, and what it costs to run.

## On the laptop: an agent, a tool server, and tests that cost nothing

Locally, Rubalise is a Strands `Agent` connected through `MCPClient` to my own MCP server over stdio. The server exposes sixteen tools: read the roadbook, correct the race sheet, build the shifts from a template, translate the sign-up form, solve, verify, show the plan by post or by person, list and change rules, grant a derogation, write and read the journal, publish. The server keeps all state in a directory of JSON files; the agents keep nothing in their memory.

This split paid for itself immediately. Every tool runs without a model, so the solver, the checker, the shift builder and the MCP protocol itself have tests that run in seconds and cost nothing. A scripted demo replays the whole conversation with automatic confirmations, which is how I checked that a change to a prompt did not break the flow. The two steps that do call a model, roadbook reading and form translation, are measured against ground truth on the generated dataset, and cached line by line so that a rerun only pays for what changed.

## Hosting on Amazon Bedrock AgentCore Runtime

The hosted version is the same code behind a `BedrockAgentCoreApp` entrypoint. The runtime gives each organizer a session; inside the session I start the MCP server as a subprocess and the orchestrator talks to it exactly as on my laptop. State goes to a per-session directory under `/tmp`.

Two practical things I learned:

- **CodeZip, not containers.** I had no Docker on the machine, so I deployed with the CodeZip build. The first archive was 169 MB because it dragged the roadbook PDF, the GPS track and an unused tools package; moving the heavy files out and trimming dependencies brought it to 108 MB. Worth checking before the first deploy.
- **Sessions sleep.** After about fifteen minutes without a message, a session is gone and so is its `/tmp`. That is fine for a conversation and a problem for a shared demo link: a plan computed for a colleague has vanished by the time they open it. The honest fix for the hackathon was to say so on the page and make recomputing a one-click action. The real fix is durable state, which is on the list.

## The web page in front of it

A chat alone does not convince anyone who runs a race. So the demo page is a cockpit: a timeline of the checkpoints coloured by staffing, the schedule by site, the detail of a shift with its team, its gaps and the closest candidates, a way to report from a post, and the chat with the agent on the right. To draw it, the hosted app answers a special `{"action": "etat"}` payload with the whole session state: race sheet, shifts with teams, plan, violations, journal, rules.

Between the page and the runtime sits a small Lambda relay. Three things bit me there:

- **The Lambda function URL returned 403 no matter what.** The account had a block on public function URLs that I could not lift from the CLI, so I put an HTTP API from API Gateway in front of the function instead.
- **The 30-second limit.** A full plan takes 60 to 90 seconds (solve, verify, contradictor). The relay now works in two steps: `POST /invoke` starts the job and invokes the function again asynchronously, the job writes its result to S3, and the page polls `GET /result` every three seconds. The S3 objects expire after two days.
- **Retries that look like failures.** The default boto3 read timeout is 60 seconds with retries; on a busy session the first attempt timed out and the retry made the agent do the work twice. One long timeout and no retries fixed it.

Bedrock quotas were the other constant. Translating a hundred form lines is a hundred calls; with the default quota they run sequentially with a backoff, and the cache means an interrupted run resumes where it stopped. The Claude 5 models were not available on the account, so everything runs on the 4.6 generation: Sonnet for the orchestrator, Opus for the contradictor and the extraction steps.

## The video, made by scripts too

The demo video is five minutes, and I built it the way I built everything else. The voice-over is Amazon Polly, synthesized one sentence at a time so that the duration of each file gives the exact timing of each subtitle. The screen scenes are Chrome driven by Playwright on the live cockpit, with a small injected cursor so that viewers can follow the clicks, and each click scheduled at the second the voice mentions it. Still images get slow zooms from ffmpeg, and ffmpeg assembles the whole thing with burned-in subtitles. The race-day scene picks two names from the plan the agent actually produced during the recording, so the message the viewer sees typed is true for that plan.

## What it costs

A full plan, with the checker and the contradictor, is roughly 15 cents of Bedrock. Translating the form once is a few cents per ten lines. The relay and the page cost nothing at this scale. The expensive thing is not the compute; it is the organizer's evening, and that is the thing the agent gives back.

Code, data and design notes: github.com/YISOWAK/rubalise. The race is real; the volunteers are synthetic.
