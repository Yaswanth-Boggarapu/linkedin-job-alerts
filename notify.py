"""Delivery. Email is the durable record; WhatsApp is the ping.

WhatsApp template parameters cannot contain newlines, so the WhatsApp message
is deliberately a short summary. The full list goes by email.
"""

import logging
import smtplib
from email.message import EmailMessage

import requests

import config

log = logging.getLogger(__name__)


def _html(jobs, failures):
    rows = []
    for job in jobs:
        flag = " <span style='color:#b26a00'>[repost]</span>" if job.get("is_repost") else ""
        rows.append(
            f"<tr><td style='padding:6px 10px'><a href='{job['job_url']}'>{job['title']}</a>{flag}</td>"
            f"<td style='padding:6px 10px'>{job.get('company') or ''}</td>"
            f"<td style='padding:6px 10px'>{job.get('location') or ''}</td>"
            f"<td style='padding:6px 10px;color:#666'>{job.get('site')}</td></tr>"
        )
    note = ""
    if failures:
        note = (f"<p style='color:#888;font-size:12px'>{len(failures)} "
                f"queries were rate-limited this run: {', '.join(failures[:6])}</p>")
    return (
        f"<h2>{len(jobs)} new roles</h2>"
        f"<table style='border-collapse:collapse;font-family:sans-serif;font-size:14px'>"
        f"{''.join(rows)}</table>{note}"
    )


def send_email(jobs, failures):
    if not (config.SMTP_USER and config.SMTP_PASS and config.DIGEST_TO):
        log.warning("email not configured, skipping")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"{len(jobs)} new roles"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.DIGEST_TO
    msg.set_content(
        "\n".join(f"{j['title']} - {j.get('company')} - {j['job_url']}" for j in jobs)
        or "No new roles today."
    )
    msg.add_alternative(_html(jobs, failures), subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(config.SMTP_USER, config.SMTP_PASS)
        smtp.send_message(msg)
    log.info("email sent to %s", config.DIGEST_TO)
    return True


def send_whatsapp(jobs):
    """Short template ping. Requires an approved template with 2 body params."""
    if not (config.WA_TOKEN and config.WA_PHONE_ID and config.WA_TO):
        log.info("whatsapp not configured, skipping")
        return False
    if not jobs:
        return False

    top = jobs[0]
    headline = f"{top['title']} at {top.get('company') or 'unknown'}"[:120]
    # No newlines/tabs allowed in template parameters.
    headline = " ".join(headline.split())

    resp = requests.post(
        f"https://graph.facebook.com/v25.0/{config.WA_PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {config.WA_TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": config.WA_TO,
            "type": "template",
            "template": {
                "name": config.WA_TEMPLATE,
                "language": {"code": "en"},
                "components": [{
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(len(jobs))},
                        {"type": "text", "text": headline},
                    ],
                }],
            },
        },
        timeout=30,
    )
    if resp.status_code >= 300:
        log.warning("whatsapp failed %s: %s", resp.status_code, resp.text[:300])
        return False
    log.info("whatsapp sent")
    return True
