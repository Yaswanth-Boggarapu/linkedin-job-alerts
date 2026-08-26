"""scan -> dedupe -> notify. Exits 0 even on a quiet day."""

import logging
import sys

import notify
import scan
import seen_store


def run():
    jobs, failures = scan.collect()

    state = seen_store.load()
    fresh, stats = seen_store.filter_new(jobs, state)
    seen_store.save(state)

    logging.info("stats: %s", stats)

    if not fresh:
        logging.info("nothing new today")
        return 0

    fresh.sort(key=lambda j: (j.get("is_repost", False), j.get("company") or ""))

    notify.send_email(fresh, failures)
    notify.send_whatsapp(fresh)
    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    sys.exit(run())
