#!/bin/bash
# Hackathon Episode Recording Pipeline
# Records hackathon episodes using the existing shmotime-recorder.js

# Configuration
EPISODE_DIR="./episodes/hackathon"
RECORDING_DIR="./recordings/hackathon"
RECORDER_SCRIPT="./scripts/shmotime-recorder.js"
RENDERER_BASE_URL="${RENDERER_URL:-https://shmotime.com/shmotime_episode/}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create directories if they don't exist
mkdir -p "$EPISODE_DIR"
mkdir -p "$RECORDING_DIR"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Function to serve episode files locally
start_local_server() {
    print_status "Starting local HTTP server for episode files..."
    cd "$EPISODE_DIR"
    python3 -m http.server 8000 &
    SERVER_PID=$!
    cd - > /dev/null
    print_status "Local server started on http://localhost:8000 (PID: $SERVER_PID)"
    sleep 2
}

# Function to stop local server
stop_local_server() {
    if [ ! -z "$SERVER_PID" ]; then
        print_status "Stopping local server..."
        kill $SERVER_PID 2>/dev/null
    fi
}

# Function to record a single episode
record_episode() {
    local episode_file=$1
    local episode_name=$(basename "$episode_file" .json)
    local output_file="$RECORDING_DIR/HACK_${episode_name}.mp4"
    
    print_status "Recording episode: $episode_name"
    
    # Construct the URL for the episode
    if [[ "$RENDERER_BASE_URL" == *"localhost"* ]]; then
        # Local server URL
        episode_url="${RENDERER_BASE_URL}?episode=http://localhost:8000/$(basename $episode_file)"
    else
        # Remote URL (would need to upload episode first)
        episode_url="${RENDERER_BASE_URL}${episode_name}/"
    fi
    
    print_status "Episode URL: $episode_url"
    
    # Check if recorder exists
    if [ ! -f "$RECORDER_SCRIPT" ]; then
        print_error "Recorder script not found: $RECORDER_SCRIPT"
        return 1
    fi
    
    # Run the recorder
    node "$RECORDER_SCRIPT" "$episode_url" --output "$output_file"
    
    if [ $? -eq 0 ]; then
        print_status "Recording completed: $output_file"
        return 0
    else
        print_error "Recording failed for $episode_name"
        return 1
    fi
}

# Function to batch record all episodes
batch_record() {
    local pattern=$1
    local episode_files=()
    
    # Find all episode files
    if [ -z "$pattern" ]; then
        episode_files=("$EPISODE_DIR"/*.json)
    else
        episode_files=("$EPISODE_DIR"/*"$pattern"*.json)
    fi
    
    # Check if any files found
    if [ ${#episode_files[@]} -eq 0 ] || [ ! -f "${episode_files[0]}" ]; then
        print_warning "No episode files found matching pattern: $pattern"
        return 1
    fi
    
    print_status "Found ${#episode_files[@]} episode(s) to record"
    
    # Start local server if using localhost
    if [[ "$RENDERER_BASE_URL" == *"localhost"* ]]; then
        start_local_server
        trap stop_local_server EXIT
    fi
    
    # Record each episode
    local success_count=0
    local fail_count=0
    
    for episode_file in "${episode_files[@]}"; do
        if [ -f "$episode_file" ]; then
            record_episode "$episode_file"
            if [ $? -eq 0 ]; then
                ((success_count++))
            else
                ((fail_count++))
            fi
            
            # Add delay between recordings
            sleep 5
        fi
    done
    
    # Summary
    print_status "Recording batch complete!"
    print_status "Success: $success_count | Failed: $fail_count"
}

# Main script logic
case "$1" in
    "single")
        if [ -z "$2" ]; then
            print_error "Usage: $0 single <episode_file>"
            exit 1
        fi
        record_episode "$2"
        ;;
    
    "batch")
        batch_record "$2"
        ;;
    
    "serve")
        print_status "Starting episode file server..."
        start_local_server
        print_status "Server running. Press Ctrl+C to stop."
        wait
        ;;
    
    *)
        echo "Hackathon Episode Recording Pipeline"
        echo "Usage:"
        echo "  $0 single <episode_file>  - Record a single episode"
        echo "  $0 batch [pattern]        - Record all episodes (optionally matching pattern)"
        echo "  $0 serve                  - Start local server for episode files"
        echo ""
        echo "Environment Variables:"
        echo "  RENDERER_URL - Base URL for the renderer (default: https://shmotime.com/shmotime_episode/)"
        echo ""
        echo "Examples:"
        echo "  $0 single ./episodes/hackathon/episode_001.json"
        echo "  $0 batch"
        echo "  $0 batch TEST"
        echo "  RENDERER_URL=http://localhost:3000 $0 batch"
        exit 1
        ;;
esac