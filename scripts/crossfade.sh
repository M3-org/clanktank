#!/bin/bash

# Default output file
output_file="output.mp4"
input_file=""

# Parse command-line options
while [[ "$#" -gt 0 ]]; do
  case $1 in
    -i) input_file="$2"; shift 2 ;;
    -o) output_file="$2"; shift 2 ;;
    *) break ;;
  esac
done

# Function to build melt command
build_melt_command() {
  local -a videos=("$@")
  if [ ${#videos[@]} -lt 2 ]; then
    echo "Error: Need at least 2 video files for crossfade. Found ${#videos[@]}."
    exit 1
  fi

  melt_cmd="${videos[0]}"
  for ((i=1; i<${#videos[@]}; i++)); do
    melt_cmd="$melt_cmd -mix 25 -mixer luma ${videos[$i]}"
  done
  melt_cmd="$melt_cmd -consumer avformat:$output_file vcodec=libx264 acodec=aac"
  echo "Running: $melt_cmd"
  melt $melt_cmd
}

# Check if input file is provided
if [ -n "$input_file" ]; then
  if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' not found."
    exit 1
  fi
  # Read videos from file, line by line
  mapfile -t videos < "$input_file"
  build_melt_command "${videos[@]}"
else
  # Use command-line arguments
  if [ "$#" -eq 0 ]; then
    echo "Usage: $0 [-i input.txt] [-o output.mp4] video1 video2 [video3 ...]"
    echo "  -i: Read video files from a text file (one per line)"
    echo "  -o: Specify output file (default: output.mp4)"
    exit 1
  fi
  build_melt_command "$@"
fi
