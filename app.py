import os
import io
import tempfile
import torch
import torchaudio
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS  # Import CORS

# --- Zonos Imports ---
# Ensure the zonos library and its dependencies are installed and importable
try:
    # Check for transformers library first (needed for init_empty_weights)
    try:
        import transformers
        print(f"Transformers version: {transformers.__version__}")
    except ImportError:
        print("Error: Transformers library not found. This is required for Zonos.")
        print("Please install it with: pip install transformers")
        exit()
        
    # Now try to import Zonos components
    from zonos.model import Zonos
    from zonos.conditioning import make_cond_dict
    from zonos.utils import DEFAULT_DEVICE as device
    
    print(f"Using device: {device}")
except ImportError:
    print("Error: Zonos library not found or not installed correctly.")
    print("Please ensure Zonos is installed following its README instructions.")
    print("You may need to run: pip install -e ./Zonos")
    exit()

# --- Configuration ---
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for all routes, allowing requests from your frontend

# Choose the model type: "transformer" or "hybrid"
MODEL_TYPE = "transformer" # Or "hybrid" if requirements met
MODEL_NAME = f"Zyphra/Zonos-v0.1-{MODEL_TYPE}"

# Global variable to hold the loaded model (load only once)
zonos_model = None

# Create a temporary directory for uploads if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Helper Function to Load Model ---
def load_zonos_model():
    """Loads the Zonos model if it hasn't been loaded yet."""
    global zonos_model
    if zonos_model is None:
        print(f"Loading Zonos model: {MODEL_NAME} on device: {device}...")
        try:
            zonos_model = Zonos.from_pretrained(MODEL_NAME, device=device)
            print("Zonos model loaded successfully.")
        except Exception as e:
            print(f"Error loading Zonos model: {e}")
            # You might want to handle this more gracefully depending on your setup
            raise RuntimeError(f"Failed to load Zonos model: {e}")
    return zonos_model

# --- Route for the root URL ---
@app.route('/')
def index():
    """Serve the index.html file when the root URL is accessed."""
    return app.send_static_file('index.html')

# --- API Endpoint for Text-to-Speech ---
@app.route('/synthesize', methods=['POST'])
def synthesize_speech():
    """
    Handles TTS requests from the frontend.
    Expects 'textInput', 'audioFile', and emotion/parameter values in the form data.
    """
    print("Received /synthesize request") # Log request

    # --- 1. Load Model (if necessary) ---
    try:
        model = load_zonos_model()
        if model is None:
             return jsonify({"error": "Model could not be loaded."}), 500
    except Exception as e:
        print(f"Model loading failed: {e}")
        return jsonify({"error": f"Model loading failed: {str(e)}"}), 500

    # --- 2. Get Data from Request ---
    if 'audioFile' not in request.files:
        print("Error: No audio file part in request")
        return jsonify({"error": "No reference audio file provided."}), 400

    file = request.files['audioFile']
    text_to_synthesize = request.form.get('textInput', '')
    language_code = request.form.get('language', 'en-us') # Default or get from form

    if file.filename == '':
        print("Error: No selected file")
        return jsonify({"error": "No selected audio file."}), 400

    if not text_to_synthesize:
        print("Error: No text provided")
        return jsonify({"error": "No text provided for synthesis."}), 400

    # --- 3. Process Uploaded Audio File ---
    try:
        # Save the uploaded file temporarily
        temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])
        temp_audio_path = os.path.join(temp_dir, file.filename)
        file.save(temp_audio_path)
        print(f"Reference audio saved temporarily to: {temp_audio_path}")

        # Load audio and create speaker embedding
        wav, sampling_rate = torchaudio.load(temp_audio_path)
        print("Creating speaker embedding...")
        speaker_embedding = model.make_speaker_embedding(wav, sampling_rate)
        print("Speaker embedding created.")

        # Clean up the temporary file and directory
        os.remove(temp_audio_path)
        os.rmdir(temp_dir)

    except Exception as e:
        print(f"Error processing reference audio: {e}")
        # Clean up if error occurs after saving
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
             os.remove(temp_audio_path)
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
             os.rmdir(temp_dir)
        return jsonify({"error": f"Failed to process reference audio: {str(e)}"}), 500

    # --- 4. Get Parameters and Prepare Conditioning ---
    try:
        print("Preparing conditioning dictionary...")
        # Get parameters from form, converting to float, with defaults
        happiness = float(request.form.get('happiness', 0.0))
        sadness = float(request.form.get('sadness', 0.0))
        anger = float(request.form.get('anger', 0.0))
        fear = float(request.form.get('fear', 0.0))
        
        # Create emotion vector in the format expected by Zonos
        # Format: [Happiness, Sadness, Disgust, Fear, Surprise, Anger, Other, Neutral]
        # Default values for emotions not in our UI
        disgust = 0.0256
        surprise = 0.0256
        other = 0.2564
        neutral = max(0.1, 1.0 - happiness - sadness - anger - fear - disgust - surprise - other)
        
        # Ensure values are between 0 and 1
        emotion_vector = [
            min(1.0, max(0.0, happiness)),
            min(1.0, max(0.0, sadness)),
            disgust,
            min(1.0, max(0.0, fear)),
            surprise,
            min(1.0, max(0.0, anger)),
            other,
            neutral
        ]
        
        # Get other parameters
        rate_factor = float(request.form.get('rate', 1.0))
        pitch_variation = float(request.form.get('pitchVariation', 0.5))
        
        # Map pitch_variation to pitch_std (20-150 range)
        # 0.0 -> 20 (minimal variation)
        # 0.5 -> 45 (normal speech)
        # 1.0 -> 150 (very expressive)
        pitch_std = 20.0 + pitch_variation * 130.0
        
        # Create conditioning dictionary using Zonos function
        cond_dict = make_cond_dict(
            text=text_to_synthesize,
            speaker=speaker_embedding,
            language=language_code,
            emotion=emotion_vector,
            pitch_std=pitch_std,
            speaking_rate=15.0 * rate_factor  # Adjust speaking rate based on rate factor
        )

        # Prepare conditioning tensors
        conditioning = model.prepare_conditioning(cond_dict)
        print("Conditioning prepared.")

    except Exception as e:
        print(f"Error preparing conditioning: {e}")
        return jsonify({"error": f"Failed to prepare conditioning: {str(e)}"}), 500

    # --- 5. Generate and Decode Audio ---
    try:
        print("Generating audio codes...")
        with torch.inference_mode():
            codes = model.generate(conditioning)
        print("Audio codes generated.")

        print("Decoding codes into waveform...")
        wavs = model.autoencoder.decode(codes).cpu()
        print("Waveform decoded.")

        # --- 6. Prepare and Send Response ---
        # Save the first generated waveform to an in-memory buffer
        output_buffer = io.BytesIO()
        torchaudio.save(output_buffer, wavs[0], model.autoencoder.sampling_rate, format="wav")
        output_buffer.seek(0) # Rewind buffer to the beginning

        print("Sending audio response.")
        return send_file(
            output_buffer,
            mimetype='audio/wav',
            as_attachment=False, # Send inline to be played directly
            # download_name='generated_speech.wav' # Use if as_attachment=True
        )

    except Exception as e:
        print(f"Error during generation or sending response: {e}")
        return jsonify({"error": f"Failed during audio generation: {str(e)}"}), 500

# --- Run the Flask App ---
if __name__ == '__main__':
    print("Starting Flask server...")
    # Load the model once on startup (optional, can also load on first request)
    # load_zonos_model()
    # Run the app. 'host=0.0.0.0' makes it accessible on your network.
    # Use debug=True only for development (auto-reloads on code changes)
    app.run(host='0.0.0.0', port=5000, debug=True)
