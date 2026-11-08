#!/usr/bin/env bash
# Set up a Magic Lantern build environment inside WSL (Ubuntu) and build EOS M.
# Run from Ubuntu:  bash "/mnt/c/Users/hengz/Desktop/Claude Projects/Canon/ml-dev/setup_wsl.sh"
set -euo pipefail

# Same commit as the build on the camera (2025-06-20.EOSM.202, 2025_release_01),
# so modules we build match the installed autoexec.bin.
ML_COMMIT=ed3e7c0dfacfdeaf3349dee73edf9e3621217462
SRC="$HOME/ml/magiclantern_simplified"

echo "== Installing packages (asks for your Ubuntu password) =="
sudo apt-get update
# the compiler, and what build_fork.sh needs (it checks before it builds): ML's module help
# text (docutils; distutils, from setuptools), the films' colour tables (numpy), the donation
# QR codes (segno), the card files (zip, unzip) and the film OS module's link test (newlib,
# qemu-user), as CI has them. Ubuntu's python3 has no pip, so the Python modules come from apt.
sudo apt-get install -y build-essential make git zip unzip python3 \
    gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi qemu-user \
    python3-docutils python3-setuptools python3-numpy python3-segno

echo "== Getting Magic Lantern source =="
mkdir -p "$HOME/ml"
if [ ! -d "$SRC/.git" ]; then
    git clone https://github.com/reticulatedpines/magiclantern_simplified.git "$SRC"
fi
cd "$SRC"
git fetch origin
git checkout -q "$ML_COMMIT"
git switch -q -c film-mode 2>/dev/null || git switch -q film-mode

echo "== Toolchain =="
arm-none-eabi-gcc --version | head -1
python3 --version

echo "== Building EOSM.202 =="
cd platform/EOSM.202
make -j"$(nproc)" 2>&1 | tee "$HOME/ml/build_eosm.log"
ls -l build/
echo "== Done. Log: ~/ml/build_eosm.log =="
