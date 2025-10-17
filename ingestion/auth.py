# ingestion/auth.py
from dotenv import load_dotenv; load_dotenv()

import os
import time
from simple_salesforce import Salesforce
import requests

class SFConnectionManager:
    def __init__(self):
        self._sf = None
        self._expires_at = 0

    def _login_password_flow(self):
        return Salesforce(
            username=os.getenv("SALESFORCE_USERNAME"),
            password=os.getenv("SALESFORCE_PASSWORD"),
            security_token=os.getenv("SALESFORCE_SECURITY_TOKEN"),
            domain=os.getenv("SALESFORCE_DOMAIN", "login"),
            client_id="sf-ai-agent-mcp",
        )

    def _login_client_credentials(self):
        token_url = os.getenv("SF_TOKEN_URL")
        data = {
            "grant_type": "client_credentials",
            "client_id": os.getenv("SF_CLIENT_ID"),
            "client_secret": os.getenv("SF_CLIENT_SECRET"),
        }
        resp = requests.post(token_url, data=data, timeout=20)
        resp.raise_for_status()
        tok = resp.json()
        access_token = tok["access_token"]
        instance_url = tok["instance_url"]
        self._expires_at = int(time.time()) + int(tok.get("expires_in", 3000))
        return Salesforce(instance_url=instance_url, session_id=access_token)

    def client(self) -> Salesforce:
        if self._sf and time.time() < self._expires_at - 60:
            return self._sf
        if os.getenv("SF_CLIENT_ID") and os.getenv("SF_CLIENT_SECRET"):
            self._sf = self._login_client_credentials()
        else:
            self._sf = self._login_password_flow()
            self._expires_at = int(time.time()) + 3000
        return self._sf


sf_manager = SFConnectionManager()
