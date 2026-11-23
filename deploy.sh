#!/bin/bash
# One-time setup. Run it yourself:  bash ~/Documents/icloud-sender/server/deploy.sh
# What it does:
#  1. makes an encryption key (stays on this Mac in ../.queuekey)
#  2. encrypts the test queue into queue.csv.enc
#  3. creates a PUBLIC GitHub repo heynyazi/icloud-sender-run (script + encrypted files only)
#  4. stores 4 secrets in that repo: QUEUE_KEY, ICLOUD_PASS, ICLOUD_USER, FROM_NAME
# Public repo = unlimited free Actions minutes. The queue and sent log are encrypted, the secrets are not visible.
set -e
cd "$(dirname "$0")"
[ -f ../.queuekey ] || { openssl rand -hex 24 > ../.queuekey; chmod 600 ../.queuekey; }
printf 'queue.csv\nsent.log\n' > .gitignore
cp ../test.csv queue.csv
openssl enc -aes-256-cbc -pbkdf2 -salt -pass file:../.queuekey -in queue.csv -out queue.csv.enc
rm queue.csv
git init -q -b main 2>/dev/null || true
git add -A
git commit -qm "icloud sender" || true
gh repo create icloud-sender-run --public --source . --push
gh secret set QUEUE_KEY --repo heynyazi/icloud-sender-run < ../.queuekey
gh secret set ICLOUD_PASS --repo heynyazi/icloud-sender-run < ../.pass
gh secret set ICLOUD_USER --repo heynyazi/icloud-sender-run < ../.user
gh secret set FROM_NAME --repo heynyazi/icloud-sender-run < ../.name
gh secret list --repo heynyazi/icloud-sender-run
echo "DONE. Tell Claude."
