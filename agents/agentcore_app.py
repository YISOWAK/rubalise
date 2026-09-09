"""Point d'entrée AgentCore Runtime : le même orchestrateur, hébergé chez AWS.

Différences avec la version terminal :
- une session AgentCore = un organisateur = un dossier d'état ; l'orchestrateur et son serveur MCP vivent le temps de la session ;
- le garde-fou dur n'a plus de terminal pour dire « oui » : une action réservée (publier, déroger, modifier une règle)
  n'est exécutée que si le message courant de l'organisateur contient une confirmation explicite. C'est du code qui
  regarde le message, pas le modèle qui décide.

Test en local :   agentcore dev            (puis POST /invocations {"prompt": "..."} sur http://localhost:8080)
Déploiement :     agentcore configure -e agents/agentcore_app.py   puis   agentcore launch
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "agents"))

from bedrock_agentcore.runtime import BedrockAgentCoreApp  # noqa: E402

from orchestrateur import Orchestration, client_mcp  # noqa: E402

app = BedrockAgentCoreApp()
SESSIONS: dict[str, "SessionOrga"] = {}
CONFIRMATION = re.compile(r"\b(oui|ok|confirme|confirmé|je confirme|vas[- ]y|valide|validé|d'accord|go)\b", re.I)


class SessionOrga:
    """Un organisateur, son état, son orchestrateur, son serveur MCP."""

    def __init__(self, session_id: str):
        self.message_courant = ""
        self.attente = None
        etat = Path(os.environ.get("COURSE_ETAT_RACINE", "/tmp/etat")) / re.sub(r"[^A-Za-z0-9_-]", "_", session_id)
        etat.mkdir(parents=True, exist_ok=True)
        os.environ["COURSE_ETAT"] = str(etat)
        self.mcp = client_mcp()
        self.mcp.start()
        self.orch = Orchestration(self.mcp, self.confirmer, silencieux=True)

    def confirmer(self, question: str) -> bool:
        """Garde-fou hébergé : vrai seulement si l'organisateur vient d'écrire une confirmation explicite."""
        if CONFIRMATION.search(self.message_courant) and self.attente == "confirmation":
            self.attente = None
            return True
        self.attente = "confirmation"
        return False

    def repondre(self, message: str) -> str:
        self.message_courant = message
        return self.orch.repondre(message)


@app.entrypoint
def invoke(payload: dict, context=None) -> dict:
    prompt = (payload or {}).get("prompt") or (payload or {}).get("message") or ""
    session_id = getattr(context, "session_id", None) or (payload or {}).get("session_id") or "defaut"
    if session_id not in SESSIONS:
        SESSIONS[session_id] = SessionOrga(session_id)
    s = SESSIONS[session_id]
    if not prompt:
        return {"result": "Dis-moi ce que tu veux faire : déposer un roadbook, charger les bénévoles, calculer un plan, signaler un imprévu."}
    reponse = s.repondre(prompt)
    if s.attente == "confirmation":
        reponse += "\n\n(Action réservée à l'organisateur : réponds « oui, confirme » pour l'exécuter.)"
    return {"result": reponse, "session_id": session_id}


if __name__ == "__main__":
    app.run()
