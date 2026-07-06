@echo off
echo Starting NAS Service...
cd /d "%~dp0"
cargo run --release
pause