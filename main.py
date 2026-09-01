"""scan -> dedupe -> sort -> notify. Exits 0 even on a quiet day."""

import logging
import sys

import notify
import scan
import seen_store


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
        notify.send_email([], failures, False, fetched)
        return 0

    # Most junior first; reposts sink within their tier; then company for
    # a stable order run to run.
    fresh.sort(key=lambda j: (
        j.get("exp_rank", 9),
        j.get("is_repost", False),
        (j.get("company") or "").lower(),
    ))

    wa_ok = notify.send_whatsapp(fresh)
    notify.send_email(fresh, failures, wa_ok, fetched)
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    sys.exit(run())
