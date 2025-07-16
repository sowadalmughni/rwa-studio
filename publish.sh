#!/usr/bin/env bash
set -euo pipefail

##### CONFIG ###############################################################
PROJECT_ROOT="/home/ubuntu/rwa-studio-package"
REPO_SLUG="sowadalmughni/rwa-studio"
EMAIL="sowadalmughni@gmail.com"
###########################################################################

cd "$PROJECT_ROOT"

echo "🧹  1/6  Scanning for forbidden strings…"
for term in "MANUS AI" "manus ai" "community discord" "built to the highest standards" "20 years"; do
  if rg -i --no-heading "$term" -g '!.git/**' -g '!publish.sh' . 2>/dev/null; then
     echo "❌  Remove or edit '$term' before publishing." && exit 1
  fi
done
echo "✅  Clean."

echo "📄  2/6  MIT LICENSE already exists…"
if [ ! -f LICENSE ]; then
cat > LICENSE <<EOF
MIT License

Copyright (c) $(date +%Y) $EMAIL

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
fi

echo "🚚  3/6  Initialising git repo…"
[ -d .git ] || git init
git add .
git commit -m "Initial open-source release of RWA Studio" || echo "Nothing to commit"

echo "🔑  4/6  Authenticating GitHub CLI…"
: "\${GITHUB_TOKEN:?Please export GITHUB_TOKEN before running this script}"
echo "\$GITHUB_TOKEN" | gh auth login --with-token

echo "🌐  5/6  Creating public repository '$REPO_SLUG'…"
if ! gh repo view "$REPO_SLUG" &>/dev/null; then
  gh repo create "$REPO_SLUG" --public --source . --remote origin --push
else
  git remote add origin "https://github.com/\${REPO_SLUG}.git" 2>/dev/null || true
  git push -u origin main
fi

echo "🎉  6/6  Done — your code is live at https://github.com/$REPO_SLUG"

