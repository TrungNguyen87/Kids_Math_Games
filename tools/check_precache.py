"""
Check that web/sw.js precaches every file the app actually ships.

The service worker's PRECACHE list is written by hand, because the app has no
build step to generate it. That is a good trade until someone adds a game and
forgets the list - and the failure mode is nasty: the app works perfectly in
testing and then 404s on that one game, offline, in front of a child.

So: compare the list against what is on disk, in both directions.

Run it locally with `python3 tools/check_precache.py`; CI runs it before every
deploy (.github/workflows/deploy-pages.yml).
"""
import pathlib
import re
import sys

WEB = pathlib.Path(__file__).resolve().parent.parent / "web"
SW = WEB / "sw.js"

# Files that are deliberately not precached.
#   sw.js       - the browser fetches it itself, and caching it would pin the
#                 old worker in place.
#   index.html  - listed as both "./" and "./index.html"; handled below.
EXEMPT = {"sw.js"}


def precached_paths():
    source = SW.read_text(encoding="utf-8")
    block = re.search(r"const PRECACHE = \[(.*?)\];", source, re.S)
    if not block:
        raise SystemExit("could not find the PRECACHE array in web/sw.js")
    entries = re.findall(r'"\./([^"]*)"', block.group(1))
    # "./" is the directory index; treat it as index.html for this comparison.
    return {entry or "index.html" for entry in entries}


def shipped_paths():
    found = set()
    for path in WEB.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(WEB).as_posix()
        if relative in EXEMPT:
            continue
        found.add(relative)
    return found


def main():
    listed = precached_paths()
    shipped = shipped_paths()

    missing = sorted(shipped - listed)  # on disk, not precached
    stale = sorted(listed - shipped)  # precached, not on disk

    if missing:
        print("These files ship but are NOT in sw.js PRECACHE:", file=sys.stderr)
        for path in missing:
            print(f"  ./{path}", file=sys.stderr)
    if stale:
        # cache.addAll() rejects the whole install if any entry 404s, so a stale
        # entry breaks offline support entirely, not just for that one file.
        print("These are in sw.js PRECACHE but do NOT exist:", file=sys.stderr)
        for path in stale:
            print(f"  ./{path}", file=sys.stderr)

    if missing or stale:
        print(
            "\nFix web/sw.js PRECACHE so it matches the contents of web/.",
            file=sys.stderr,
        )
        return 1

    print(f"sw.js precache OK: {len(listed)} entries match the files in web/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
