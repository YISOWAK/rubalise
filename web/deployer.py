"""Déploie la page de démonstration : une Lambda avec URL publique qui sert index.html
et relaie les messages vers le runtime AgentCore.

Idempotent : relancer met à jour le code et la configuration.

Lancer (profil admin) :
    AWS_PROFILE=admin python web/deployer.py --runtime-arn arn:aws:bedrock-agentcore:...:runtime/xxx
"""
from __future__ import annotations

import argparse
import io
import json
import secrets
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import boto3

ICI = Path(__file__).resolve().parent
REGION = "us-east-1"
NOM = "rubalise-demo-web"


def zip_lambda() -> bytes:
    """Le code du relais + la page + boto3 récent (celui de Lambda peut ne pas connaître bedrock-agentcore)."""
    tmp = Path(tempfile.mkdtemp(prefix="rubalise_lambda_"))
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--target", str(tmp), "boto3", "--upgrade"], check=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in tmp.rglob("*"):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(tmp).as_posix())
        z.write(ICI / "lambda_proxy.py", "lambda_proxy.py")
        z.writestr("index.html", page_construite())
    return buf.getvalue()


def page_construite() -> str:
    """index.html avec les figures injectées (schéma d'architecture, profil du parcours)."""
    page = (ICI / "index.html").read_text(encoding="utf-8")
    svg = (ICI.parent / "docs" / "architecture.svg").read_text(encoding="utf-8")
    svg = svg.replace("svg { font-family", "#archi svg { font-family", 1)
    page = page.replace("{{ARCHITECTURE_SVG}}", svg)
    profil = ICI / "profil.svg"
    page = page.replace("{{PROFIL_SVG}}", profil.read_text(encoding="utf-8") if profil.exists() else "")
    score = ICI / "score_traduction.txt"
    page = page.replace("{{SCORE_TRADUCTION}}", score.read_text(encoding="utf-8").strip() if score.exists() else "mesure en cours sur les 100 lignes")
    return page


def role_lambda(iam, runtime_arn: str, bucket: str) -> str:
    nom = f"{NOM}-role"
    trust = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}
    try:
        arn = iam.get_role(RoleName=nom)["Role"]["Arn"]
    except iam.exceptions.NoSuchEntityException:
        arn = iam.create_role(RoleName=nom, AssumeRolePolicyDocument=json.dumps(trust), Description="Relais web Rubalise vers AgentCore")["Role"]["Arn"]
        time.sleep(8)  # propagation IAM
    politique = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["bedrock-agentcore:InvokeAgentRuntime"], "Resource": [runtime_arn, runtime_arn + "/runtime-endpoint/*"]},
        {"Effect": "Allow", "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], "Resource": "*"},
        {"Effect": "Allow", "Action": ["s3:PutObject", "s3:GetObject"], "Resource": f"arn:aws:s3:::{bucket}/jobs/*"},
        {"Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": f"arn:aws:s3:::{bucket}"},
        {"Effect": "Allow", "Action": ["lambda:InvokeFunction"], "Resource": f"arn:aws:lambda:{REGION}:*:function:{NOM}"},
    ]}
    iam.put_role_policy(RoleName=nom, PolicyName="invoke-agentcore-et-logs", PolicyDocument=json.dumps(politique))
    return arn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-arn", required=True)
    ap.add_argument("--cle", default="", help="clé de démo à mettre dans le lien (?k=...) ; générée si absente")
    args = ap.parse_args()
    cle = args.cle or secrets.token_urlsafe(9)

    session = boto3.Session(region_name=REGION)
    iam, lam, s3, apigw = session.client("iam"), session.client("lambda"), session.client("s3"), session.client("apigatewayv2")
    compte = session.client("sts").get_caller_identity()["Account"]
    bucket = f"{NOM}-{compte}"
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:  # noqa: BLE001
        s3.create_bucket(Bucket=bucket)  # us-east-1 : pas de LocationConstraint
        s3.put_bucket_lifecycle_configuration(Bucket=bucket, LifecycleConfiguration={"Rules": [{"ID": "purge-jobs", "Status": "Enabled", "Filter": {"Prefix": "jobs/"}, "Expiration": {"Days": 2}}]})
        print("bucket créé :", bucket)
    role = role_lambda(iam, args.runtime_arn, bucket)
    code = zip_lambda()
    env = {"Variables": {"AGENT_RUNTIME_ARN": args.runtime_arn, "AGENT_REGION": REGION, "CLE_DEMO": cle, "BUCKET_RESULTATS": bucket}}
    try:
        lam.get_function(FunctionName=NOM)
        lam.update_function_code(FunctionName=NOM, ZipFile=code)
        lam.get_waiter("function_updated").wait(FunctionName=NOM)
        lam.update_function_configuration(FunctionName=NOM, Environment=env, Timeout=600, MemorySize=512, Role=role)
        print("fonction mise à jour")
    except lam.exceptions.ResourceNotFoundException:
        for tentative in range(6):
            try:
                lam.create_function(FunctionName=NOM, Runtime="python3.12", Role=role, Handler="lambda_proxy.handler",
                                    Code={"ZipFile": code}, Timeout=600, MemorySize=512, Environment=env,
                                    Description="Page de démonstration Rubalise, relais vers AgentCore")
                break
            except lam.exceptions.InvalidParameterValueException as e:  # le rôle n'est pas encore assumable
                if tentative == 5:
                    raise
                time.sleep(6)
        print("fonction créée")
    lam.get_waiter("function_active").wait(FunctionName=NOM)

    # Une API HTTP devant la Lambda (l'URL Lambda publique est bloquée sur ce compte).
    fn_arn = lam.get_function(FunctionName=NOM)["Configuration"]["FunctionArn"]
    apis = [a for a in apigw.get_apis()["Items"] if a["Name"] == "rubalise-demo"]
    api = apis[0] if apis else apigw.create_api(Name="rubalise-demo", ProtocolType="HTTP", Target=fn_arn, RouteKey="$default")
    try:
        lam.add_permission(FunctionName=NOM, StatementId="apigw-publique", Action="lambda:InvokeFunction", Principal="apigateway.amazonaws.com",
                           SourceArn=f"arn:aws:execute-api:{REGION}:{compte}:{api['ApiId']}/*")
    except lam.exceptions.ResourceConflictException:
        pass
    url = api["ApiEndpoint"] + "/"
    lien = f"{url}?k={cle}"
    (ICI / "lien_demo.txt").write_text(lien + "\n", encoding="utf-8")
    print("\nLien de démonstration :", lien)
    print("(enregistré dans web/lien_demo.txt)")


if __name__ == "__main__":
    main()
