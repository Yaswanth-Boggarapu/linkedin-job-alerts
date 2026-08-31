"""Run the real adapter and count losses at each stage."""
import config, gradireland, scan
OUT=[]
def say(*p):
    l=" ".join(str(x) for x in p); print(l); OUT.append(l)

say("## adapter run\n")
say(f"USE_GRADIRELAND={config.USE_GRADIRELAND} GRADIRELAND_HOURS={config.GRADIRELAND_HOURS}\n")

total=0
for role in config.ROLES:
    try:
        rows = gradireland.fetch(role, hours_old=config.GRADIRELAND_HOURS)
        total += len(rows)
        say(f"- {role!r} -> {len(rows)} kept")
        for r in rows[:3]:
            say(f"    {r['title'][:60]!r} | {r['company'][:28]!r} | {r['location'][:30]!r} | {r['date_posted']}")
        # how many would the title filter then drop?
        dropped=[r['title'] for r in rows if scan._excluded(r['title'])]
        if dropped:
            say(f"    title-filter would drop {len(dropped)}: {dropped[:4]}")
    except Exception as exc:
        import traceback
        say(f"- {role!r} -> EXCEPTION {type(exc).__name__}: {exc}")
        say("```\n"+traceback.format_exc()+"```")

say(f"\n**total kept across roles: {total}**")

# what does a wide-open window give?
try:
    wide = gradireland.fetch("data", hours_old=24*365)
    say(f"\n- sanity: 'data' with a 1-year window -> {len(wide)} rows")
except Exception as exc:
    say(f"\n- sanity failed: {exc}")

open("probe-result.md","w").write("\n".join(OUT))
