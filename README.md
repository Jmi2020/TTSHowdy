# TTS Howdy

A text-to-speech application that connects to Ollama to generate responses and speaks them using Piper TTS. Optimized for Raspberry Pi 5.

## Features

- Connects to Ollama for text generation
- Uses Piper TTS for high-quality speech synthesis
- Optimized for Raspberry Pi 5
- Interactive chat mode
- Support for custom voice models

## Requirements

- Python 3.7+
- Ollama installed on your Raspberry Pi or accessible via network
- Piper TTS

## Installation

### 1. Clone this repository

```bash
git clone https://github.com/yourusername/tts-howdy.git
cd tts-howdy
```

### 2. Set up a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate     # On Windows
```

### 3. Install the Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Piper TTS

For Raspberry Pi:

```bash
sudo apt-get update
sudo apt-get install -y piper-tts
```

For other systems, follow instructions at: https://github.com/rhasspy/piper

### 5. Download the voice model

You can download the ryan voice model directly using the script:

```bash
python tts_howdy.py --download-voice
```

Or manually:

```bash
mkdir -p ~/.local/share/piper-tts/voices/en_US
wget -P ~/.local/share/piper-tts/voices/en_US/ https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx
wget -P ~/.local/share/piper-tts/voices/en_US/ https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json
```

### 6. Make sure Ollama is running with your model

The default configuration expects Ollama to be running with the "tiny-cowboy" model loaded:

```bash
ollama run tiny-cowboy
```

## Usage

### Interactive Mode

Simply run the script without parameters to enter interactive chat mode:

```bash
python tts_howdy.py
```

### Speak a Direct Prompt

```bash
python tts_howdy.py --prompt "Tell me a short story about a cowboy"
```

### Use Different Models

```bash
# Use a different Ollama model
python tts_howdy.py --model llama2

# Use a different voice
python tts_howdy.py --voice-model en_US-lessac-medium
```

### List Available Voices

```bash
python tts_howdy.py --list-voices
```

### Speak Directly Without Ollama

```bash
python tts_howdy.py --text "This is a test of the TTS system"
```

### Read from Standard Input

```bash
echo "Hello world" | python tts_howdy.py --stdin
```

## Command Line Options

- `--host`: Ollama host URL (default: http://localhost:11434)
- `--model`: Ollama model name (default: tiny-cowboy)
- `--prompt`, `-p`: Prompt to send to Ollama
- `--system`, `-s`: System prompt for Ollama
- `--voice-model`: Piper TTS voice model (default: en_US-ryan-medium)
- `--rate`: Speech rate/length scale (default: 1.0, lower is faster)
- `--list-voices`: List available Piper voices and exit
- `--download-voice`: Download the default voice model
- `--text`, `-t`: Speak provided text directly
- `--stdin`: Read text from stdin and speak it

## Raspberry Pi Configuration

This application is optimized for Raspberry Pi 5. For best performance:

1. Ensure you have adequate cooling for your Raspberry Pi
2. Use a class 10 microSD card or better yet, an SSD
3. Consider adjusting your GPU memory split if you encounter performance issues

## License

MIT