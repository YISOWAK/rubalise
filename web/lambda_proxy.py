"""Relais entre la page web et l'agent hébergé sur AgentCore.

Une Lambda derrière une API HTTP :
  GET  /?k=...                -> la page (index.html)
  POST /invoke?k=...          -> {prompt, session_id} : lance le travail en arrière-plan, rend {job_id, session_id}
  GET  /result?k=...&id=...   -> {statut: "en_cours" | "fini" | "erreur", result}

Pourquoi en deux temps : l'API HTTP coupe à 30 secondes, et un plan complet (solveur, vérification,
relecture par le contradicteur) prend 30 à 60 secondes. La Lambda se rappelle donc elle-même en mode
asynchrone pour faire l'appel long, et dépose la réponse dans un petit bucket S3 que la page interroge.

La clé de démo (CLE_DEMO) n'est pas un secret fort : elle évite qu'un lien public serve à n'importe qui.
Le vrai contrôle d'accès est le rôle IAM de la Lambda, seul autorisé à appeler ce runtime.
"""
from __future__ import annotations

import json
import os
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

RUNTIME_ARN = os.environ["AGENT_RUNTIME_ARN"]
CLE_DEMO = os.environ.get("CLE_DEMO", "")
REGION = os.environ.get("AGENT_REGION", "us-east-1")
BUCKET = os.environ.get("BUCKET_RESULTATS", "")
PAGE = open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8").read()

# Un plan complet prend plus d'une minute : délai de lecture long et AUCUN réessai, sinon boto3 relance
# l'appel sur une session encore occupée et la réponse de la première invocation se perd.
agentcore = boto3.client("bedrock-agentcore", region_name=REGION,
                         config=Config(connect_timeout=10, read_timeout=840, retries={"max_attempts": 1}))
s3 = boto3.client("s3", region_name=REGION)
lam = boto3.client("lambda", region_name=REGION)


def reponse(statut: int, corps, type_contenu: str = "application/json"):
    if type_contenu == "application/json":
        corps = json.dumps(corps, ensure_ascii=False)
    return {"statusCode": statut, "headers": {"Content-Type": type_contenu + "; charset=utf-8", "Cache-Control": "no-store"}, "body": corps}


def deposer(job_id: str, contenu: dict):
    s3.put_object(Bucket=BUCKET, Key=f"jobs/{job_id}.json", Body=json.dumps(contenu, ensure_ascii=False).encode("utf-8"), ContentType="application/json")


def travailler(job: dict):
    """Le travail long : appel de l'agent hébergé, résultat déposé dans S3."""
    try:
        r = agentcore.invoke_agent_runtime(
            agentRuntimeArn=RUNTIME_ARN, runtimeSessionId=job["session_id"],
            contentType="application/json", accept="application/json",
            payload=json.dumps({"prompt": job["prompt"], "session_id": job["session_id"]}).encode("utf-8"),
        )
        brut = r["response"].read().decode("utf-8") if hasattr(r.get("response"), "read") else str(r.get("response"))
        try:
            data = json.loads(brut)
            texte = data.get("result") if isinstance(data, dict) else brut
        except json.JSONDecodeError:
            texte = brut
        deposer(job["id"], {"statut": "fini", "result": texte, "session_id": job["session_id"]})
    except Exception as e:  # noqa: BLE001
        deposer(job["id"], {"statut": "erreur", "result": f"{type(e).__name__}: {str(e)[:300]}", "session_id": job["session_id"]})


def handler(event, context):
    # Rappel asynchrone de la Lambda par elle-même
    if isinstance(event, dict) and event.get("_travail"):
        travailler(event["_travail"])
        return {"ok": True}

    chemin = event.get("rawPath", "/")
    methode = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    params = event.get("queryStringParameters") or {}
    if CLE_DEMO and params.get("k", "") != CLE_DEMO:
        return reponse(403, "<p style='font-family:sans-serif'>Lien de démonstration incomplet : il manque la clé.</p>", "text/html")

    if methode == "GET" and chemin.rstrip("/").endswith("result"):
        job_id = params.get("id", "")
        try:
            obj = s3.get_object(Bucket=BUCKET, Key=f"jobs/{job_id}.json")
            return reponse(200, json.loads(obj["Body"].read().decode("utf-8")))
        except ClientError as e:  # NoSuchKey, ou AccessDenied quand l'objet n'existe pas encore
            if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "AccessDenied", "404", "403"):
                return reponse(200, {"statut": "en_cours"})
            return reponse(500, {"erreur": str(e)[:200]})

    if methode == "GET" and chemin.rstrip("/").endswith("etat"):
        session_id = params.get("session", "")
        if not session_id:
            return reponse(400, {"erreur": "session manquante"})
        try:
            r = agentcore.invoke_agent_runtime(agentRuntimeArn=RUNTIME_ARN, runtimeSessionId=session_id, contentType="application/json",
                                               accept="application/json", payload=json.dumps({"action": "etat", "session_id": session_id}).encode("utf-8"))
            brut = r["response"].read().decode("utf-8")
            return reponse(200, json.loads(brut))
        except Exception as e:  # noqa: BLE001
            return reponse(502, {"erreur": f"{type(e).__name__}: {str(e)[:200]}"})

    if methode == "GET":
        return reponse(200, PAGE, "text/html")

    if methode == "POST" and chemin.rstrip("/").endswith("invoke"):
        try:
            corps = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return reponse(400, {"erreur": "corps JSON attendu"})
        prompt = (corps.get("prompt") or "").strip()
        if not prompt:
            return reponse(400, {"erreur": "message vide"})
        session_id = corps.get("session_id") or f"rubalise-{uuid.uuid4()}-{uuid.uuid4().hex[:8]}"
        job = {"id": uuid.uuid4().hex, "prompt": prompt, "session_id": session_id}
        lam.invoke(FunctionName=context.function_name, InvocationType="Event", Payload=json.dumps({"_travail": job}).encode("utf-8"))
        return reponse(202, {"job_id": job["id"], "session_id": session_id})

    return reponse(404, {"erreur": "route inconnue"})
