#!/bin/bash
echo "Starting NAS Service..."
cd "$(dirname "$0")"
cargo run --release