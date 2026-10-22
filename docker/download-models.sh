#!/usr/bin/env bash
# Download the three GGUF files for the local stack.
#
# The files are large (about 8.3 GB), so the script resumes partial downloads
# and verifies the SHA-256 before it renames the file into place.
#
# Usage:
#   bash docker/download-models.sh          # download what is missing
#   bash docker/download-models.sh --check  # verify without downloading
#
# The destination defaults to <repo>/models and can be overridden with
# RPTR_MODELS_DIR. Set HF_TOKEN only if a repository starts requiring auth.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${RPTR_MODELS_DIR:-$ROOT/models}"
CHECK_ONLY=0
if [[ "${1:-}" == "--check" ]]; then
    CHECK_ONLY=1
fi

mkdir -p "$DEST"

# name|repo|bytes|sha256|license
MANIFEST=(
    "embeddinggemma-2-Q8_0.gguf|ggml-org/embeddinggemma-2-GGUF|309855456|2188ac1deca4b77dffefd603c2776a9d76d9d74ec01841392982ebb840b09135|Apache-2.0"
    "LFM2.5-8B-A1B-Q4_K_M.gguf|LiquidAI/LFM2.5-8B-A1B-GGUF|5155564768|4923ec14f06b968b74d663e5949867d2d9c3bf13a20b8be1a9f9af39989b2bb0|LFM Open License 1.0"
    "d1-3B-Q8_0.gguf|LiquidAI/d1-3B-GGUF|2874781280|2f0942d5a5f64cf69c3356d2be439b71644b1f0eb3a580912a5a0179eeaba77d|LFM Open License 1.0"
)

auth=()
if [[ -n "${HF_TOKEN:-}" ]]; then
    auth=(-H "Authorization: Bearer ${HF_TOKEN}")
fi

verify() {
    local path="$1" expected_size="$2" expected_sha="$3"
    [[ -f "$path" ]] || return 1
    local actual_size
    actual_size="$(stat -c%s "$path")"
    [[ "$actual_size" == "$expected_size" ]] || return 1
    echo "${expected_sha}  ${path}" | sha256sum --check --status -
}

missing=0
for entry in "${MANIFEST[@]}"; do
    IFS='|' read -r name repo size sha license <<<"$entry"
    path="$DEST/$name"

    if verify "$path" "$size" "$sha"; then
        echo "ok       $name  ($(numfmt --to=iec-i --suffix=B "$size"), $license)"
        continue
    fi

    if [[ -f "$path" ]]; then
        echo "bad      $name  (size or checksum mismatch, will download again)"
        rm -f "$path"
    else
        echo "missing  $name  ($(numfmt --to=iec-i --suffix=B "$size"), $license)"
    fi
    missing=1

    if [[ "$CHECK_ONLY" == "1" ]]; then
        continue
    fi

    tmp="$path.part"
    url="https://huggingface.co/$repo/resolve/main/$name"
    echo "fetch    $url"
    curl --fail --location --retry 5 --retry-delay 2 --retry-all-errors \
        --continue-at - --output "$tmp" "${auth[@]}" "$url"

    if ! verify "$tmp" "$size" "$sha"; then
        echo "error: $name failed verification; leaving $tmp in place" >&2
        exit 1
    fi
    mv "$tmp" "$path"
    echo "done     $name"
done

if [[ "$CHECK_ONLY" == "1" && "$missing" == "1" ]]; then
    echo "one or more model files are missing or incomplete" >&2
    exit 1
fi

echo
echo "Models are in $DEST"
echo "Start the router with: pixi run llm-up"
