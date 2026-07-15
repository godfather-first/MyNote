#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

sudo apt update
sudo apt install -y \
  git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
  zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo6 \
  cmake libffi-dev libssl-dev python3 python3-pip python3-venv

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install buildozer cython

buildozer android debug

echo
echo "APK build finished. Check the bin/ directory."

