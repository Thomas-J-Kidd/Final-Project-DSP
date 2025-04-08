#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
VENV_DIR=".venv"
ZONOS_REPO_URL="https://github.com/Zyphra/Zonos.git"
ZONOS_DIR="Zonos"

# --- Helper Functions ---
print_info() {
    echo "INFO: $1"
}

print_success() {
    echo "SUCCESS: $1"
}

print_warning() {
    echo "WARNING: $1"
}

print_error() {
    echo "ERROR: $1" >&2
    exit 1
}

# --- Check for root/sudo ---
# Installing system packages requires root privileges.
if [[ $EUID -ne 0 ]]; then
    print_info "This script needs to install system packages using apt."
    print_info "You might be prompted for your sudo password."
    SUDO='sudo'
else
    SUDO=''
fi

# --- 1. Install System Dependencies ---
print_info "Updating package list and installing system dependencies (espeak-ng, python3-venv, git)..."
$SUDO apt-get update -y
$SUDO apt-get install -y espeak-ng python3-venv git
print_success "System dependencies installed."

# --- 2. Create Python Virtual Environment ---
if [ -d "$VENV_DIR" ]; then
    print_info "Virtual environment '$VENV_DIR' already exists. Skipping creation."
else
    print_info "Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created."
fi

# Define paths to venv executables
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Ensure pip is up-to-date within the venv
print_info "Updating pip in the virtual environment..."
"$VENV_PYTHON" -m pip install --upgrade pip

# --- 3. Install Core Python Libraries ---
print_info "Installing core Python libraries (Flask, Flask-CORS, torch, torchaudio) into '$VENV_DIR'..."
# Note: Installing torch might take a while depending on your internet connection and system.
"$VENV_PIP" install Flask Flask-CORS torch torchaudio
print_success "Core Python libraries installed."

# --- 4. Clone Zonos Repository ---
if [ -d "$ZONOS_DIR" ]; then
    print_info "Zonos directory '$ZONOS_DIR' already exists. Skipping clone."
    # Optional: Add logic here to pull latest changes if needed
    # (cd "$ZONOS_DIR" && git pull)
else
    print_info "Cloning Zonos repository from $ZONOS_REPO_URL..."
    git clone "$ZONOS_REPO_URL"
    print_success "Zonos repository cloned into '$ZONOS_DIR'."
fi

# --- 5. Install Zonos ---
print_info "Installing Zonos library in editable mode into '$VENV_DIR'..."
# We run pip from the virtual env, targeting the setup.py in the Zonos directory
"$VENV_PIP" install -e "$ZONOS_DIR"
print_success "Zonos library installed."

# --- Optional: Install Compile Extra (for Hybrid Model) ---
# If you plan to use the Zonos-v0.1-hybrid model, uncomment the following lines.
# Note: This has additional dependencies and GPU requirements (Nvidia 3000+ series).
# print_info "Installing Zonos [compile] extra (optional, for hybrid model)..."
# "$VENV_PIP" install -e "$ZONOS_DIR[compile]"
# print_success "Zonos [compile] extra installed."

# --- Completion ---
print_success "Setup complete!"
print_info "To activate the virtual environment, run: source $VENV_DIR/bin/activate"
print_info "You can then run the Flask backend (e.g., 'python app.py') from within the activated environment."

exit 0
