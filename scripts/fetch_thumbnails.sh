#!/bin/bash

# relies on event stream json from playcanvas project

cat paste.txt | jq -r '.events[0].detail.actors | to_entries[] | .value | select(.image | test(".png")) | [.id, .image, .image_thumb] | @tsv' | while IFS=$'\t' read -r id image thumb; do wget -O "${id}_headshot.png" "${image}" && wget -O "${id}_thumb.png" "${thumb}"; done
