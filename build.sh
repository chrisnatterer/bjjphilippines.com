#!/usr/bin/env bash
set -euo pipefail

# Inject the current commit SHA into the footer of every HTML page.
# Cloudflare Pages exposes CF_PAGES_COMMIT_SHA at build time; falls back
# to local git for manual runs.

COMMIT="${CF_PAGES_COMMIT_SHA:-$(git rev-parse HEAD 2>/dev/null || echo dev)}"
SHORT="${COMMIT:0:7}"

echo "Injecting commit $SHORT into HTML footers"

find . -name '*.html' -type f -print0 | while IFS= read -r -d '' f; do
  python3 - "$f" "$COMMIT" "$SHORT" <<'PY'
import sys, pathlib
path, full, short = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
c = p.read_text()
c = c.replace(
    'https://github.com/chrisnatterer/bjjphilippines.com/commit/dev',
    f'https://github.com/chrisnatterer/bjjphilippines.com/commit/{full}',
)
c = c.replace(
    'rel="noopener">dev</a>',
    f'rel="noopener">{short}</a>',
)
p.write_text(c)
PY
done
