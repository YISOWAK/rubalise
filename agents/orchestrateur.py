"""L'orchestrateur : un agent Strands qui tient la conversation avec l'organisateur et appelle
les outils du serveur MCP « course ». Le contradicteur est un second agent, à contexte vierge,
appelé automatiquement à chaque plan calculé.

Garde-fou dur : publier, deroger et regle_modifier passent par une confirmation dans le terminal
avant d'être exécutés, quoi que dise le modèle.

Lancer :
    python agents/orchestrateur.py                       (conversation dans le terminal)
    python agents/orchestrateur.py --script demo.txt     (une ligne = un message de l'orga, pour tester)
    COURSE_ETAT=chemin  pour choisir le dossier d'état du serveur
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

from botocore.config import Config
from mcp.client.stdio import StdioServerParameters, stdio_client
from strands import Agent, tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# La console Windows est en cp1252 : on force l'UTF-8 pour ne pas planter sur un accent ou un emoji.
for flux in (sys.stdout, sys.stderr):
    try:
        flux.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

RACINE = Path(__file__).resolve().parent.parent
PROMPTS = RACINE / "agents" / "prompts"
REGION = "us-east-1"
MODELE_ORCHESTRATEUR = "us.anthropic.claude-sonnet-4-6"
MODELE_CONTRADICTEUR = "us.anthropic.claude-opus-4-6-v1"

# Outils du serveur que l'orchestrateur ne voit pas directement : ils passent par un garde-fou ou par calculer_plan.
GARDES = {"publier", "deroger", "regle_modifier"}
CACHES = GARDES | {"resoudre", "verifier"}


def modele(model_id: str, temperature: float = 0.2) -> BedrockModel:
    # Le quota Bedrock du compte est bas : on laisse boto réessayer patiemment sur les 429.
    return BedrockModel(model_id=model_id, region_name=REGION, temperature=temperature,
                        boto_client_config=Config(retries={"max_attempts": 10, "mode": "adaptive"}, read_timeout=300))


def client_mcp() -> MCPClient:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    params = StdioServerParameters(command=sys.executable, args=[str(RACINE / "serveur" / "serveur_course.py")], env=env, cwd=str(RACINE))
    return MCPClient(lambda: stdio_client(params))


def texte_de(resultat) -> str:
    """Le texte d'un résultat d'outil MCP (Strands)."""
    return "\n".join(c["text"] for c in resultat["content"] if "text" in c)


class Orchestration:
    def __init__(self, mcp: MCPClient, confirmer, silencieux: bool = False):
        self.mcp = mcp
        self.confirmer = confirmer          # fonction(question) -> bool ; c'est le garde-fou dur
        self.silencieux = silencieux
        outils_mcp = mcp.list_tools_sync()
        self.lecture = [t for t in outils_mcp if t.tool_name not in CACHES]
        self.contradicteur = Agent(
            model=modele(MODELE_CONTRADICTEUR, 0.3),
            system_prompt=(PROMPTS / "contradicteur.md").read_text(encoding="utf-8"),
            tools=[t for t in outils_mcp if t.tool_name in ("plan_par_poste", "plan_par_personne", "regles_lister")],
            callback_handler=None,
        )
        self.orchestrateur = Agent(
            model=modele(MODELE_ORCHESTRATEUR),
            system_prompt=(PROMPTS / "orchestrateur.md").read_text(encoding="utf-8"),
            tools=self.lecture + [self.calculer_plan, self.publier, self.deroger, self.regle_modifier],
            callback_handler=None if silencieux else self._afficher,
        )

    # -- affichage du flux de l'orchestrateur ---------------------------------
    def _afficher(self, **kw):
        if "data" in kw:
            print(kw["data"], end="", flush=True)
        elif kw.get("current_tool_use", {}).get("name") and kw.get("event", {}).get("contentBlockStart"):
            print(f"\n   [outil : {kw['current_tool_use']['name']}]", flush=True)

    # -- appel brut d'un outil du serveur --------------------------------------
    def _serveur(self, nom: str, **args) -> str:
        r = self.mcp.call_tool_sync(tool_use_id=f"t-{uuid.uuid4().hex[:8]}", name=nom, arguments=args)
        return texte_de(r)

    # -- outils composés, vus par l'orchestrateur ------------------------------
    @tool
    def calculer_plan(self, absents: list[str] | None = None, heure: str = "") -> str:
        """Calcule un plan avec le solveur, le passe au vérificateur de règles, puis le fait relire par le contradicteur.
        absents : ids des bénévoles qui ne viennent plus (jour J). heure : heure courante ISO (jour J), les créneaux terminés ne bougent plus.
        Rend, dans l'ordre : le résultat du solveur, les violations, les remarques du contradicteur."""
        solveur = self._serveur("resoudre", absents=absents or [], heure=heure)
        verif = self._serveur("verifier", max_alertes=30)
        remarques_benevoles = ""
        etat = Path(os.environ.get("COURSE_ETAT", RACINE / "etat"))
        trad = etat / "benevoles_traduits.json"
        if trad.exists():
            d = json.loads(trad.read_text(encoding="utf-8"))
            lignes = []
            for t in d:
                rem = [f"[{r['etiquette']}] {r['texte']}" for r in t["remarques"] if r["etiquette"] != "autre"]
                if rem or t["questions"]:
                    lignes.append(f"{t['id']} {t['nom']} : " + " | ".join(rem + [f"question : {q}" for q in t["questions"]]))
            remarques_benevoles = "\n".join(lignes)
        demande = (f"Résultat du solveur :\n{solveur}\n\nViolations du vérificateur :\n{verif}\n\n"
                   f"Remarques libres des bénévoles et questions ouvertes :\n{remarques_benevoles or '(aucune)'}\n\n"
                   "Relis et rends tes remarques.")
        relecture = str(self.contradicteur(demande))
        return f"=== SOLVEUR ===\n{solveur}\n\n=== VÉRIFICATEUR ===\n{verif}\n\n=== CONTRADICTEUR ===\n{relecture}"

    @tool
    def publier(self, justification: str) -> str:
        """Publie le plan courant vers les bénévoles (messages simulés) et le fige comme référence. Réservé à l'organisateur :
        le programme lui demande confirmation avant d'exécuter."""
        if not self.confirmer(f"L'agent veut PUBLIER le plan ({justification}). Confirmer ?"):
            return "Refusé par l'organisateur : le plan n'est pas publié."
        return self._serveur("publier", auteur="orga", justification=justification)

    @tool
    def deroger(self, regle_id: str, justification: str, poste_id: str = "", benevole_id: str = "") -> str:
        """Accorde une dérogation à une règle sur le plan courant, au nom de l'organisateur, après confirmation."""
        if not self.confirmer(f"L'agent veut DÉROGER à la règle {regle_id} ({poste_id or '-'} / {benevole_id or '-'}) : {justification}. Confirmer ?"):
            return "Refusé par l'organisateur : pas de dérogation."
        return self._serveur("deroger", regle_id=regle_id, auteur="orga", justification=justification, poste_id=poste_id, benevole_id=benevole_id)

    @tool
    def regle_modifier(self, regle_id: str, justification: str, active: bool | None = None, parametres: dict | None = None) -> str:
        """Active, désactive ou paramètre une règle du vérificateur, au nom de l'organisateur, après confirmation."""
        if not self.confirmer(f"L'agent veut MODIFIER la règle {regle_id} (active={active}, paramètres={parametres}) : {justification}. Confirmer ?"):
            return "Refusé par l'organisateur : règle inchangée."
        return self._serveur("regle_modifier", regle_id=regle_id, auteur="orga", justification=justification, active=active, parametres=parametres)

    # -- un tour de conversation -------------------------------------------------
    def repondre(self, message: str) -> str:
        return str(self.orchestrateur(message))


def confirmer_terminal(question: str) -> bool:
    print(f"\n>>> {question} [oui/non] ", end="", flush=True)
    return input().strip().lower() in ("oui", "o", "yes", "y")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="", help="fichier texte : un message de l'organisateur par ligne")
    ap.add_argument("--oui", action="store_true", help="en mode script : répondre oui à toutes les confirmations")
    args = ap.parse_args()

    confirmer = confirmer_terminal
    if args.script and args.oui:
        def confirmer(q):  # noqa: E306
            print(f"\n>>> {q} [oui, automatique en mode script]")
            return True

    mcp = client_mcp()
    with mcp:
        orch = Orchestration(mcp, confirmer)
        if args.script:
            for ligne in Path(args.script).read_text(encoding="utf-8").splitlines():
                if not ligne.strip() or ligne.startswith("#"):
                    continue
                print(f"\n\nORGA > {ligne}\n")
                orch.repondre(ligne)
            print()
            return
        print("Assistant bénévoles. Tape ta demande, ou « quitter ».\n")
        while True:
            try:
                msg = input("\nORGA > ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if msg.lower() in ("quitter", "exit", "q"):
                break
            if msg:
                orch.repondre(msg)
                print()


if __name__ == "__main__":
    main()
