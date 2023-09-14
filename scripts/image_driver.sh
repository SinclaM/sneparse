#!/bin/bash

# Array to store failed values
fails=()

function run_batch {
    local retries=0
    local i=$1
    local increment=$2

    while [[ $retries -lt 3 ]]; do
        echo "Doing batch starting at $i ..."
        DISPLAY= python -u scripts/make_images.py "$i" "$BATCH_COUNT" --cache-file "$CACHE_FILE"

        # Check the exit status of the previous command
        if [[ $? -eq 0 ]]; then
            return 0
        else
            retries=$((retries + 1))
            echo "Attempt $retries failed."
        fi
    done

    # All retries failed, add i to fails array
    fails+=("$i")
}

# Will be larger than needed because of duplicates.
NUM_SNE=$(cat "resources/epoch${EPOCH}_cross_matches.csv" | wc -l)

BATCH_COUNT=100
CACHE_FILE="sne_cache.pickle"

DISPLAY= python -u scripts/make_images.py 0 "$BATCH_COUNT" --make-cache-file "$CACHE_FILE"

for ((i = BATCH_COUNT; i <= NUM_SNE; i += BATCH_COUNT)); do
    run_batch "$i" "$BATCH_COUNT"
done

# Print the fails array
echo "Failed batches: ${fails[@]}"

rm -f "$CACHE_FILE"
