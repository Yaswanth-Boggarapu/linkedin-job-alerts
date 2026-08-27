"""One-off WhatsApp connectivity check. Run via the wa-test workflow."""

import os
import sys

import requests

TOKEN = os.environ["WA_TOKEN"]
PHONE_ID = os.environ["WA_PHONE_ID"]
TO = os.environ["WA_TO"]

resp = requests.post(
    f"https://graph.facebook.com/v25.0/{PHONE_ID}/messages",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={
        "messaging_product": "whatsapp",
        "to": TO,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    },
    timeout=30,
)
print("status:", resp.status_code)
print("body:", resp.text)
sys.exit(0 if resp.status_code < 300 else 1)
