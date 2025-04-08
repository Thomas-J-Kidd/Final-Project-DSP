# Zonos TTS Dashboard

A web-based dashboard for text-to-speech synthesis using the [Zonos](https://github.com/Zyphra/Zonos) library.

![Zonos TTS Dashboard](Zonos/assets/ZonosHeader.png)

## Overview

This project provides a user-friendly web interface for the Zonos text-to-speech system. It allows users to:

- Input text to be synthesized into speech
- Upload reference audio for speaker cloning
- Adjust emotional parameters (happiness, sadness, anger, fear)
- Control speech rate and pitch variation
- Generate and download high-quality synthesized speech

## Project Structure

- `app.py`: Flask backend that interfaces with the Zonos library
- `index.html`: Frontend web interface
- `setup_zonos.sh`: Setup script for installing dependencies
- `requirements.txt`: Python dependencies
- `Zonos/`: Git submodule containing the Zonos library

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- Git
- espeak-ng (for phonemization)

### Installation

1. Clone this repository with submodules:
   ```bash
   git clone --recurse-submodules https://github.com/Thomas-J-Kidd/Final-Project-DSP.git
   cd Final-Project-DSP
   ```

2. Run the setup script (Linux/macOS):
   ```bash
   chmod +x setup_zonos.sh
   ./setup_zonos.sh
   ```

   This script will:
   - Install system dependencies
   - Create a Python virtual environment
   - Install required Python packages
   - Set up the Zonos library

3. Alternatively, you can set up manually:
   ```bash
   # Install system dependencies (Ubuntu/Debian)
   sudo apt-get update
   sudo apt-get install -y espeak-ng python3-venv git

   # Create and activate virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -e ./Zonos
   ```

## Usage

1. Activate the virtual environment (if not already activated):
   ```bash
   source .venv/bin/activate
   ```

2. Start the Flask server:
   ```bash
   python app.py
   ```

3. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

4. In the web interface:
   - Enter the text you want to synthesize
   - Upload a reference audio file (.wav or .mp3)
   - Adjust the emotion sliders and other parameters
   - Click "Generate Speech"
   - Listen to and download the generated audio

## About Zonos

[Zonos](https://github.com/Zyphra/Zonos) is a text-to-speech system developed by Zyphra. This project uses Zonos as a git submodule, allowing for easy updates while maintaining a separate codebase for the web interface.

The Zonos library provides:
- High-quality text-to-speech synthesis
- Speaker cloning capabilities
- Emotional control
- Support for multiple languages

## License

This project is licensed under the terms of the license included in the Zonos repository.

## Acknowledgments

- [Zyphra](https://github.com/Zyphra) for creating the Zonos text-to-speech system
