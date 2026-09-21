#!/usr/bin/env sh
set -e

command -v apt >/dev/null 2>&1 || {
    echo "Error: command 'apt' was not found."
    echo "This installation script requires a Debian/Ubuntu-based Linux distribution."
    exit 1
}

sudo apt update
sudo apt install -y python3 python3-pip

python3 -m pip install numpy sounddevice screeninfo
