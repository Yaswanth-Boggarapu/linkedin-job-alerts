"""Delivery. Email is the durable record; WhatsApp is the ping.

WhatsApp template parameters cannot contain newlines, so the WhatsApp message
is deliberately a short summary. The full table goes by email.
"""

import logging
import smtplib
from email.message import EmailMessage

import requests

import config

log = logging.getLogger(__name__)

SITE_NAMES = {
    "linkedin": "LinkedIn",
    "indeed": "Indeed",
    "glassdoor": "Glassdoor",
    "google": "Google",
    "gradireland": "gradireland",
    "jobs_ie": "jobs.ie",
    "zip_recruiter": "ZipRecruiter",
}

TH = "padding:8px 12px;text-align:left;border-bottom:2px solid #ddd;font-size:13px"
TD = "padding:8px 12px;border-bottom:1px solid #eee;vertical-align:top"


def _rows(jobs):
    out = []
    for job in jobs:
        repost = (" <span style='color:#b26a00;font-size:11px'>[repost]</span>"
                  if job.get("is_repost") else "")
        exp = job.get("exp_label") or "Not stated"
        # Grey out the ones we couldn't classify so the real signal stands out.
        exp_style = "color:#999" if exp == "Not stated" else "color:#1a7f37;font-weight:600"
        out.append(
            f"<tr>"
            f"<td style='{TD}'><a href='{job['job_url']}'>{job.get('title') or ''}</a>{repost}</td>"
            f"<td style='{TD}'>{job.get('company') or ''}</td>"
            f"<td style='{TD};{exp_style}'>{exp}</td>"
            f"<td style='{TD}'>{job.get('location') or ''}</td>"
            f"<td style='{TD};color:#666'>{SITE_NAMES.get(job.get('site'), job.get('site') or '')}</td>"
            f"</tr>"
        )
    return "".join(out)


def _sources_table(jobs, fetched, failures):
    """Per-source health, so a broken scraper is visible at a glance."""
    new_by_site = {}
    for job in jobs:
        site = job.get("site")
        new_by_site[site] = new_by_site.get(site, 0) + 1

    failed_sites = {f.split("/")[0].split(":")[0] for f in failures}

    rows = []
    sites = (set(fetched) | set(new_by_site) | failed_sites) - {"_dropped"}
    for site in sorted(sites):
        got = fetched.get(site, 0)
        new = new_by_site.get(site, 0)
        if site in failed_sites and not got:
            status, colour = "failed", "#c00"
        elif got == 0:
            status, colour = "no results", "#b26a00"
        else:
            status, colour = "ok", "#1a7f37"
        rows.append(
            f"<tr><td style='{TD}'>{SITE_NAMES.get(site, site)}</td>"
            f"<td style='{TD}'>{got}</td><td style='{TD}'>{new}</td>"
            f"<td style='{TD};color:{colour}'>{status}</td></tr>"
        )

    return (
        f"<h3 style='font-size:14px;margin:24px 0 6px'>Sources this run</h3>"
        f"<table style='border-collapse:collapse;font-size:12px'>"
        f"<tr><th style='{TH}'>Source</th><th style='{TH}'>Fetched</th>"
        f"<th style='{TH}'>New</th><th style='{TH}'>Status</th></tr>"
        f"{''.join(rows)}</table>"
    )


def _html(jobs, failures, wa_ok, fetched=None):
    note = ""
    if failures:
        note = (f"<p style='color:#888;font-size:12px'>{len(failures)} queries "
                f"were rate-limited or failed this run: {', '.join(failures[:8])}</p>")

    wa_line = ""
    if config.WA_TOKEN:
        wa_line = ("<p style='color:#1a7f37;font-size:12px'>WhatsApp ping sent.</p>"
                   if wa_ok else
                   "<p style='color:#c00;font-size:12px'>WhatsApp ping failed "
                   "(see the run log). Email is unaffected.</p>")

    return (
        f"<div style='font-family:-apple-system,Segoe UI,sans-serif'>"
        f"<h2 style='margin-bottom:4px'>{len(jobs)} new roles</h2>"
        f"<p style='color:#666;font-size:13px;margin-top:0'>"
        f"Sorted with the most junior roles first.</p>"
        f"<table style='border-collapse:collapse;font-size:14px;width:100%'>"
        f"<tr>"
        f"<th style='{TH}'>Role</th><th style='{TH}'>Company</th>"
        f"<th style='{TH}'>Experience</th><th style='{TH}'>Location</th>"
        f"<th style='{TH}'>Source</th>"
        f"</tr>{_rows(jobs)}</table>{note}{wa_line}</div>"
    )


def _plain(jobs):
    lines = []
    for j in jobs:
        lines.append(
            f"{j.get('title')} | {j.get('company')} | {j.get('exp_label')} | "
            f"{j.get('location')} | {SITE_NAMES.get(j.get('site'), j.get('site'))}\n"
            f"  {j.get('job_url')}"
        )
    return "\n".join(lines) or "No new roles today."


def send_email(jobs, failures, wa_ok=False, fetched=None):
    if not (config.SMTP_USER and config.SMTP_PASS and config.DIGEST_TO):
        log.warning("email not configured, skipping")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"{len(jobs)} new roles" if jobs else "No new roles today"
    msg["From"] = config.SMTP_USER
    msg["To"] = config.DIGEST_TO
    msg.set_content(_plain(jobs))
    msg.add_alternative(_html(jobs, failures, wa_ok, fetched), subtype="html")

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
    headline = f"{top.get('title')} at {top.get('company') or 'unknown'}"[:120]
    headline = " ".join(headline.split())   # no newlines allowed in params

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
        log.warning("whatsapp failed %s: %s", resp.status_code, resp.text[:400])
        return False
    log.info("whatsapp sent")
    return True
