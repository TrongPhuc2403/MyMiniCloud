
from flask import Flask, jsonify, request
from pathlib import Path
from jose import jwt
import requests
import json
import os

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

OIDC_ISSUER = os.getenv("OIDC_ISSUER", "")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "")

@app.get("/hello")
def hello():
    return jsonify({
        "message": "Hello from App Server!"
    })

@app.get("/student")
def student():
    with open(
        BASE_DIR / "students.json",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    return jsonify(data)

@app.get("/secure")
def secure():
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        return jsonify(
            error="Missing Bearer token"
        ), 401

    if not OIDC_ISSUER or not OIDC_AUDIENCE:
        return jsonify(
            error="OIDC authentication is not configured"
        ), 503

    token = auth.split(" ", 1)[1]

    try:
        jwks_url = os.getenv(
            "OIDC_JWKS_URL",
            OIDC_ISSUER.rstrip("/")
            + "/protocol/openid-connect/certs"
        )

        response = requests.get(
            jwks_url,
            timeout=5
        )
        response.raise_for_status()

        payload = jwt.decode(
            token,
            response.json(),
            algorithms=["RS256"],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_ISSUER
        )

        return jsonify({
            "message": "Secure resource OK",
            "preferred_username":
                payload.get("preferred_username")
        })

    except Exception:
        return jsonify(
            error="Invalid or expired token"
        ), 401

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8081
    )
