#!/usr/bin/env bash
#
# Generate the 'repo' branch for Unmanic plugin repository.
#
# Reads each plugin's info.json from main, builds a zip archive,
# and assembles repo.json. The result is force-pushed to the 'repo' branch.
#
# Usage: ./generate_repo.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
GITHUB_USER="rgregg"
GITHUB_REPO="unmanic-plugins"
REPO_BRANCH="repo"
BASE_URL="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${REPO_BRANCH}"

# Work in a temp directory
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

REPO_DIR="${WORK_DIR}/repo"
mkdir -p "$REPO_DIR"

# Build zip files for each plugin
for plugin_dir in "$REPO_ROOT"/*/; do
    [ -f "${plugin_dir}/info.json" ] || continue
    plugin_id="$(basename "$plugin_dir")"
    version="$(python3 -c "import json; print(json.load(open('${plugin_dir}/info.json'))['version'])")"

    plugin_out="${REPO_DIR}/${plugin_id}"
    mkdir -p "$plugin_out"

    cp "${plugin_dir}/info.json" "$plugin_out/"
    [ -f "${plugin_dir}/description.md" ] && cp "${plugin_dir}/description.md" "$plugin_out/"
    [ -f "${plugin_dir}/changelog.md" ] && cp "${plugin_dir}/changelog.md" "$plugin_out/"

    zip_name="${plugin_id}-${version}.zip"
    (cd "$REPO_ROOT" && zip -r "${plugin_out}/${zip_name}" "$plugin_id" \
        -x "*/__pycache__/*" "*/.*" "*.pyc")
done

# Generate repo.json with Python (avoids shell escaping issues)
python3 << PYEOF
import json, os, glob

base_url = "${BASE_URL}"
repo_dir = "${REPO_DIR}"

plugins = []
for info_path in sorted(glob.glob(os.path.join(repo_dir, "*/info.json"))):
    plugin_dir = os.path.dirname(info_path)
    plugin_id = os.path.basename(plugin_dir)

    with open(info_path) as f:
        entry = json.load(f)

    # Find the zip file
    zips = glob.glob(os.path.join(plugin_dir, "*.zip"))
    if not zips:
        continue
    zip_name = os.path.basename(zips[0])

    entry["package_url"] = f"{base_url}/{plugin_id}/{zip_name}"
    plugins.append(entry)

repo = {
    "repo": {
        "id": "repository.${GITHUB_USER}",
        "name": "${GITHUB_USER} Unmanic Plugins",
        "icon": "",
        "repo_data_directory": f"{base_url}/",
        "repo_data_url": f"{base_url}/repo.json"
    },
    "plugins": plugins
}

with open(os.path.join(repo_dir, "repo.json"), "w") as f:
    json.dump(repo, f, indent=4)

print(f"Generated repo.json with {len(plugins)} plugins")
PYEOF

# Push to repo branch
cd "$REPO_ROOT"
git_tmp="${WORK_DIR}/git-repo"
git clone --no-checkout "$(git remote get-url origin)" "$git_tmp"
cd "$git_tmp"

git checkout --orphan "$REPO_BRANCH"
git rm -rf . 2>/dev/null || true

cp -r "${REPO_DIR}/"* .
git add -A
git commit -m "Update plugin repository

Generated from main branch by generate_repo.sh"

git push origin "$REPO_BRANCH" --force

echo ""
echo "Repo branch pushed. Add this URL to Unmanic:"
echo "  ${BASE_URL}/repo.json"
