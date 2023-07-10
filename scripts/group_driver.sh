#!/bin/bash

# Array to store failed values
fails=()

# Function to retry plot_groups.py
function plot_groups {
    local retries=0
    local i=$1
    local increment=$2

    while [[ $retries -lt 3 ]]; do
        echo "Doing batch starting at $i ..."
        python scripts/plot_groups.py $i 1000

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

for i in {0..100000..1000}; do
    plot_groups "$i" 1000
done

# Print the fails array
echo "Failed batches: ${fails[@]}"

