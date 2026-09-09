"""Test du serveur MCP par le vrai protocole : on lance le serveur en sous-processus (stdio),
on liste ses outils, et on enchaîne un scénario complet sans aucun LLM.

Lancer : python serveur/test_serveur.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ICI = Path(__file__).resolve().parent


def texte(resultat) -> str:
    """Le contenu texte d'un résultat d'outil MCP."""
    morceaux = []
    for c in resultat.content:
        if getattr(c, "type", "") == "text":
            morceaux.append(c.text)
    return "\n".join(morceaux)


def court(s: str, n: int = 700) -> str:
    return s if len(s) <= n else s[:n] + " ..."


async def main():
    etat = Path(tempfile.mkdtemp(prefix="etat_test_"))
    env = dict(os.environ, COURSE_ETAT=str(etat), PYTHONIOENCODING="utf-8")
    params = StdioServerParameters(command=sys.executable, args=[str(ICI / "serveur_course.py")], env=env, cwd=str(ICI.parent))
    async with stdio_client(params) as (lecture, ecriture):
        async with ClientSession(lecture, ecriture) as session:
            await session.initialize()
            outils = await session.list_tools()
            print(f"{len(outils.tools)} outils exposés :")
            for t in outils.tools:
                print(f"  - {t.name:<22} {t.description.splitlines()[0][:90]}")

            async def appel(nom, **args):
                r = await session.call_tool(nom, args)
                print(f"\n== {nom}({', '.join(f'{k}={v!r}' for k, v in args.items())})")
                print(court(texte(r)))
                return r

            await appel("etat_resume")
            await appel("charger_donnees")
            await appel("resoudre")
            await appel("verifier", max_alertes=5)
            await appel("plan_par_poste", poste_id="S11")
            await appel("plan_par_personne", benevole="Michel Perrin")
            await appel("deroger", regle_id="B2", auteur="orga", justification="Grand Pré soir : on tiendra à 2, Sandra confirme", poste_id="S14")
            await appel("regle_modifier", regle_id="A4", auteur="orga", justification="nos habitués font volontiers 12 h", parametres={"journee_longue_h": 12})
            await appel("publier", auteur="orga", justification="plan v1 validé en réunion")
            await appel("resoudre", absents=["B001", "B011"], heure="2025-09-06T11:00")
            await appel("journal_lire", n=8)
    print(f"\nÉtat du test dans {etat}")


if __name__ == "__main__":
    asyncio.run(main())
