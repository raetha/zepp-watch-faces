#!/usr/bin/env bash
# Upload one face's test build to Zepp's preview service with the real `zeus preview`: the
# only kind of install the Zepp app lists under Developer Mode
# (docs/development.md -> "Preview uploads from CI"). Zeus builds the package itself, in
# preview mode (no intermediate products), for the given watches only.
#
#   tools/zeus_preview.sh <face dev dir> <out dir> "<Zeus device names, comma-separated>"
#
# e.g. tools/zeus_preview.sh faces/sextant-dev out-dev/sextant "Amazfit Balance 3,Amazfit Balance 3 Ti"
# Needs ZEPP_APPTOKEN, ZEPP_USERID and ZEPP_CNAME (the developer login, see the guide):
# tools/zeus_login.sh puts them in Zeus's own login file while it runs.
# Writes <out>/preview-url.txt, preview-qr.png and preview-expires.txt.
# Adapted from raetha/zepp-kestrel.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
proj="$1"; out="$2"; devices="$3"
mkdir -p "$out"
source "$root/tools/zeus_login.sh"
log="$(mktemp)"
# no terminal: an expired login would wait for a browser forever, hence the timeout;
# a comma-separated -t list needs -s
(cd "$proj" && NODE_OPTIONS="--require $root/tools/zeus_preview_hook.cjs" timeout ${ZEUS_TIMEOUT:-600} zeus preview -s -t "$devices" </dev/null >"$log" 2>&1) || true
url="$(tr '\r' '\n' <"$log" | grep -o 'ZEUS_PREVIEW_URL=.*' | head -1 | cut -d= -f2- || true)"
if [ -z "$url" ]; then
  tr '\r' '\n' <"$log" | grep -v '^\s*$' | tail -15
  if grep -q "login page has been opened" "$log"; then
    echo "::error title=Zepp preview ($(basename "$proj"))::Zepp refused the login: it has expired. Log in again and update ZEPP_APPTOKEN."
  else
    echo "::error title=Zepp preview ($(basename "$proj"))::zeus preview gave no QR code (log above)"
  fi
  rm -f "$log"
  exit 1
fi
rm -f "$log"
echo "$url" > "$out/preview-url.txt"
date -u -d '+7 days' '+%Y-%m-%d %H:%M UTC' > "$out/preview-expires.txt"
python3 - "$out/preview-qr.png" "$url" <<'EOF'
import sys
import qrcode
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=3)
qr.add_data(sys.argv[2])
qr.make(fit=True)
qr.make_image(fill_color="#14223A", back_color="white").save(sys.argv[1])
EOF
echo "preview uploaded ($(basename "$proj"), $devices): expires $(cat "$out/preview-expires.txt")"
