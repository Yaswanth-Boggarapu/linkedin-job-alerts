"""scan -> dedupe -> sort -> notify. Exits 0 even on a quiet day."""

import json
import logging
import sys
from datetime import datetime, timezone

import notify
import scan
import seen_store


def _write_run_log(stats, fetched, failures, new_count):
    """A committed record of what each source did, so failures are debuggable
    after the fact without re-running anything."""
    try:
        with open("last-run.json", "w") as fh:
            json.dump({
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "fetched": fetched,
                "new": new_count,
                "dedupe": stats,
                "failures": failures,
            }, fh, indent=2, sort_keys=True)
    except Exception as exc:          # never let logging break a run
        logging.warning("could not write run log: %s", exc)


def run():
    jobs, failures, fetched = scan.collect()

    state = seen_store.load()
    fresh, stats = seen_store.filter_new(jobs, state)
    seen_store.save(state)

    logging.info("stats: %s", stats)

    if not fresh:
        # Still send, so a silent source failure is visible rather than
        # looking identical to a genuinely quiet day.
        logging.info("nothing new today")
        _write_run_log(stats, fetched, failures, 0)
        notify.send_email([], failures, False, fetched)
        return 0

    # Most junior first; reposts sink within their tier; then company for
    # a stable order run to run.
    fresh.sort(key=lambda j: (
        j.get("exp_rank", 9),
        j.get("is_repost", False),
        (j.get("company") or "").lower(),
    ))

    _write_run_log(stats, fetched, failures, len(fresh))

    wa_ok = notify.send_whatsapp(fresh)
    notify.send_email(fresh, failures, wa_ok, fetched)
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    sys.exit(run())
