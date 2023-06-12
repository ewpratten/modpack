#! /bin/bash
set -ex

# Run packwiz and grep for "Failed to check updates for (mod name)"
echo "n" | packwiz update --all | grep "Failed to check updates for"