"""Le texte de la voix off, scène par scène. Une entrée = un sous-titre.

Chaque phrase est un couple (texte lu, texte affiché). Quand ils sont identiques, une seule chaîne suffit.
Le texte lu peut tricher sur l'orthographe pour la prononciation ; le sous-titre garde la bonne.
"""

SCENES = {
    "s1": [
        "Last September I ran the SwissPeaks Marathon.",
        "Forty-six kilometers in the Swiss Alps, and it took me around eight and a half hours.",
        "Honestly, I remember the volunteers as much as the trail.",
        "Everything was so well organized, and I kept thinking that someone put a lot of time and effort into making my race go well, almost for free.",
        "So I built an agent to help that person.",
        ("I called it Rubaleez, after the tape that marks the trail.", "I called it Rubalise, after the tape that marks the trail."),
    ],
    "s2a": [
        "So here's what the organizer starts with.",
        "The first thing is the roadbook. It's a PDF, and the page I care about is basically a screenshot of a spreadsheet.",
        "It lists every checkpoint, what time the fastest runner gets there, what time the slowest one does, and the cut-off time, after which you're out of the race.",
        "The second thing is the sign-up form.",
        "A hundred people filled it in, and they wrote in normal sentences.",
        "One guy is running the race himself, so he can only help on Friday evening.",
        "A woman is coming with three friends, and they'd like an aid station together.",
        ("Another one says: put me at Tah-nay, I love that place, I'm seventy-one and still fit.", "Another one says: put me at Taney, I love that place, I'm seventy-one and still fit."),
        "From those two files, one person has to work out who's where and at what time, over three days and fifty shifts.",
        "If they get it wrong, someone reaches an aid station at two in the morning and there's nobody there.",
    ],
    "s2b": [
        "So how do you go from that to a schedule?",
        "First you read the roadbook. That's one model call on the pages as images.",
        "It gives back the checkpoints, the times, the cut-offs, and a list of what it wasn't sure about, so the organizer can check.",
        "Then the form. One call per line, and what someone wrote becomes real fields.",
        "Then you build the schedule, and that part is not done by the model.",
        "Language models are bad at counting, and bad at respecting fifty constraints at the same time.",
        "So the plan comes from a constraint solver. It takes about ten seconds, and it can tell you why there wasn't a better answer.",
        "The agent running all of this is the orchestrator.",
        "It's built with Strands, the open-source agent SDK from AWS.",
        "It talks to the organizer and it calls the tools.",
        "Then there's a second agent, and I call it the contradictor.",
        "It gets the finished plan without knowing how it was built, and it looks for problems that no rule describes.",
        "It can't change anything, it just reports.",
        "And nothing is sent to the volunteers unless the organizer says yes.",
        "That check is in the code, not in the prompt.",
    ],
    "s3": [
        "This is what comes out.",
        "Every checkpoint has a colour. Green means the team is complete, orange means it's a bit short, and red means someone is missing.",
        "Underneath is the schedule, shift by shift, over three days.",
        "If I click on a checkpoint, I only see its shifts.",
        "This one is green, because the colour is about race day.",
        "But the day before, there's a red shift. It's a supply run in a four-by-four, to the two aid stations you can't reach by road.",
        "I click on it, and the agent tells me it's one person short, and that only one volunteer out of a hundred can actually take it.",
        "And then it tells me what I can do about that.",
        "Three people are free and have a licence, they just don't have the right car.",
        "Lend one of them a four-by-four, and the shift is covered.",
        "It doesn't only tell me no. It tells me what to change.",
    ],
    "s3bis": [
        "That panel is a checker, and a checker only knows the rules somebody wrote down.",
        "So there's a second agent that reads the finished plan and looks for the rest.",
        "Here it noticed that one team leader is bringing three friends, and those three are doing most of the work at that checkpoint.",
        "If she cancels, the post is empty.",
        "Nobody had written a rule about that.",
    ],
    "s4": [
        "And then there's race day, which is really the point.",
        "It's eleven in the morning and two volunteers aren't coming.",
        "I tell the agent, the way I'd tell a colleague.",
        "It finds who's affected and fixes the plan with as few changes as possible.",
        "Shifts that are already over don't move.",
        "People who are already at their post get flagged, because those you call yourself.",
        "And it asks before it sends anything.",
    ],
    "s5": [
        "Everything here is measured. The roadbook reading, the form, ten solver scenarios, the race-day repairs.",
        "It runs on Amazon Bedrock AgentCore, and the code is public.",
        "For a triathlon, it's another template file.",
        "Volunteers make races happen.",
        "The person who organizes them should have a decent tool.",
    ],
}

ORDRE = ["s1", "s2a", "s2b", "s3", "s3bis", "s4", "s5"]


def phrases(scene: str) -> list[tuple[str, str]]:
    """(texte lu, texte affiché) pour chaque phrase de la scène."""
    return [(p, p) if isinstance(p, str) else p for p in SCENES[scene]]
