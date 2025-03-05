#!/usr/bin/env python3
"""
TTS Howdy - A program that reads text output from Ollama and converts it to speech
Designed for Raspberry Pi 5 using Piper TTS
"""

import argparse
import json
import requests
import subprocess
import sys
import os
import tempfile
import time

# Try to import sounddevice, but handle it gracefully if it's missing or PortAudio isn't installed
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except (ImportError, OSError) as e:
    print(f"Warning: Audio playback via sounddevice might not work: {e}")
    print("You may need to install PortAudio and its development headers.")
    print("On Raspberry Pi: sudo apt-get install portaudio19-dev python3-dev")
    print("After installing dependencies, reinstall sounddevice: pip install sounddevice --upgrade")
    SOUNDDEVICE_AVAILABLE = False
    # Import numpy only if needed for other parts of the code
    try:
        import numpy as np
    except ImportError:
        pass


class PiperTTSHowdy:
    def __init__(self, ollama_host="http://localhost:11434", model="tiny-cowboy", 
                 voice_model="en_US-ryan-medium", voice_rate=1.0):
        self.ollama_host = ollama_host
        self.model = model
        self.voice_model = voice_model
        self.voice_rate = voice_rate
        
        # Check if Piper is installed
        try:
            result = subprocess.run(["piper", "--help"], 
                                   capture_output=True, 
                                   text=True, 
                                   check=False)
            if result.returncode != 0:
                print("Warning: Piper TTS might not be correctly installed. Please install it using:")
                print("  pip install piper-tts")
                print("  or follow instructions at https://github.com/rhasspy/piper")
        except FileNotFoundError:
            print("Error: Piper TTS is not installed. Please install it using:")
            print("  pip install piper-tts")
            print("  or follow instructions at https://github.com/rhasspy/piper")
            print("  On Raspberry Pi, you may need: sudo apt-get update && sudo apt-get install -y piper-tts")
            print("\nYou'll also need to download the ryan voice model:")
            print("  mkdir -p ~/.local/share/piper-tts/voices/en_US")
            print("  wget -P ~/.local/share/piper-tts/voices/en_US/ https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx")
            print("  wget -P ~/.local/share/piper-tts/voices/en_US/ https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json")
    
    def download_voice_model(self, voice_name="en_US-ryan-medium"):
        """Download a voice model if it doesn't exist"""
        voice_dir = os.path.expanduser(f"~/.local/share/piper-tts/voices/en_US")
        os.makedirs(voice_dir, exist_ok=True)
        
        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium"
        files_to_download = [
            f"{voice_name}.onnx",
            f"{voice_name}.onnx.json"
        ]
        
        for file in files_to_download:
            target_path = os.path.join(voice_dir, file)
            if not os.path.exists(target_path):
                print(f"Downloading {file}...")
                url = f"{base_url}/{file}"
                try:
                    with requests.get(url, stream=True) as r:
                        r.raise_for_status()
                        with open(target_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    print(f"Downloaded {file} successfully.")
                except Exception as e:
                    print(f"Error downloading {file}: {e}")
        
        return True
    
    def list_voices(self):
        """List available Piper voice models"""
        try:
            # This assumes models are in ~/.local/share/piper-tts/voices/
            voice_dir = os.path.expanduser("~/.local/share/piper-tts/voices/")
            if os.path.exists(voice_dir):
                print("Available Piper voice models:")
                for file in os.listdir(voice_dir):
                    if file.endswith(".onnx"):
                        print(f"  {file.replace('.onnx', '')}")
            else:
                print("Piper voice directory not found. Default voice models may be available.")
                print("You can download voice models from: https://huggingface.co/rhasspy/piper-voices/")
                
            # Try to get voices using piper command
            try:
                result = subprocess.run(["piper", "--list-voices"], 
                                      capture_output=True, 
                                      text=True, 
                                      check=False)
                if result.returncode == 0:
                    print("\nSystem Piper voices:")
                    print(result.stdout)
            except:
                pass
        except Exception as e:
            print(f"Error listing voices: {e}")
            print("You can download voice models from: https://huggingface.co/rhasspy/piper-voices/")

    def generate_response(self, prompt, system_prompt=None):
        """Generate a response from Ollama"""
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "No response generated")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return f"Error: {e}"
    
    def speak_with_piper(self, text):
        """Use Piper TTS to speak the given text"""
        if not text.strip():
            return
            
        try:
            # Create a temporary file for the audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Call Piper TTS to generate speech
            cmd = [
                "piper",
                "--model", self.voice_model,
                "--output_file", temp_filename,
                "--length-scale", str(self.voice_rate)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send text to Piper
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode != 0:
                print(f"Error generating speech: {stderr}")
                return
            
            # Play the generated audio
            audio_played = False
            
            # Try using sounddevice if available
            if SOUNDDEVICE_AVAILABLE:
                try:
                    import wave
                    with wave.open(temp_filename, 'rb') as wf:
                        # Extract audio data
                        audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                        sample_rate = wf.getframerate()
                        
                        # Play audio
                        sd.play(audio_data, sample_rate)
                        sd.wait()  # Wait until audio is finished playing
                    audio_played = True
                except Exception as e:
                    print(f"Error playing audio with sounddevice: {e}")
            
            # Fallback to system player if sounddevice fails or is not available
            if not audio_played:
                try:
                    if sys.platform == "darwin":  # macOS
                        subprocess.run(["afplay", temp_filename])
                        audio_played = True
                    elif sys.platform == "linux":  # Linux/Raspberry Pi
                        result = subprocess.run(["aplay", "--version"], capture_output=True, text=True, check=False)
                        if result.returncode == 0:
                            subprocess.run(["aplay", temp_filename])
                            audio_played = True
                        else:
                            result = subprocess.run(["paplay", "--version"], capture_output=True, text=True, check=False)
                            if result.returncode == 0:
                                subprocess.run(["paplay", temp_filename])
                                audio_played = True
                    elif sys.platform == "win32":  # Windows
                        subprocess.run(["start", temp_filename], shell=True)
                        audio_played = True
                except Exception as e2:
                    print(f"Error playing audio with system player: {e2}")
            
            # Inform if no audio could be played
            if not audio_played:
                print("\nWARNING: Could not play audio. Make sure audio devices are properly configured.")
                print("Audio was generated successfully and saved to:", temp_filename)
                print("Audio file was not deleted for manual playback.")
                return
            
            # Clean up temporary file if audio played successfully
            try:
                os.unlink(temp_filename)
            except:
                pass
                
        except Exception as e:
            print(f"Error with Piper TTS: {e}")
    
    def stream_response(self, prompt, system_prompt=None):
        """Stream response from Ollama and speak each chunk"""
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()
                buffer = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        buffer += chunk
                        
                        # Speak when we have complete sentences or phrases
                        if any(punct in chunk for punct in ".!?,;:") and len(buffer) > 10:
                            print(buffer, end="", flush=True)
                            self.speak_with_piper(buffer)
                            buffer = ""
                
                # Speak any remaining text
                if buffer:
                    print(buffer)
                    self.speak_with_piper(buffer)
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            self.speak_with_piper(f"Error: {e}")
    
    def speak_text(self, text):
        """Just speak the provided text"""
        print(text)
        self.speak_with_piper(text)


def main():
    parser = argparse.ArgumentParser(description='TTS Howdy - Text-to-Speech for Ollama using Piper TTS')
    parser.add_argument('--host', default='http://localhost:11434', 
                        help='Ollama host URL (default: http://localhost:11434)')
    parser.add_argument('--model', default='tiny-cowboy', 
                        help='Ollama model name to use (default: tiny-cowboy)')
    parser.add_argument('--prompt', '-p', help='Prompt to send to Ollama')
    parser.add_argument('--system', '-s', help='System prompt')
    parser.add_argument('--voice-model', default='en_US-ryan-medium',
                        help='Piper TTS voice model to use (default: en_US-ryan-medium)')
    parser.add_argument('--rate', type=float, default=1.0,
                        help='Speech rate/length scale (default: 1.0, lower is faster)')
    parser.add_argument('--list-voices', action='store_true',
                        help='List available Piper voices and exit')
    parser.add_argument('--download-voice', action='store_true',
                        help='Download the default voice model if not present')
    parser.add_argument('--text', '-t', help='Speak provided text directly without calling Ollama')
    parser.add_argument('--stdin', action='store_true',
                        help='Read text from stdin and speak it')
    parser.add_argument('--check-dependencies', action='store_true',
                        help='Check and install required system dependencies')
    
    args = parser.parse_args()
    
    # Check dependencies if requested
    if args.check_dependencies:
        print("Checking system dependencies...")
        if sys.platform == "linux":  # Linux/Raspberry Pi
            missing = []
            
            # Check for Piper
            result = subprocess.run(["which", "piper"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                missing.append("piper-tts")
            
            # Check for audio playback tools
            result = subprocess.run(["which", "aplay"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                missing.append("alsa-utils")
            
            # Check for PortAudio - Raspberry Pi uses different package names
            if not os.path.exists("/usr/lib/libportaudio.so") and not os.path.exists("/usr/lib/arm-linux-gnueabihf/libportaudio.so"):
                missing.append("portaudio19-dev")
            
            if missing:
                print(f"Missing dependencies: {', '.join(missing)}")
                print("\nYou can install them with:")
                print(f"sudo apt-get update && sudo apt-get install -y {' '.join(missing)} python3-dev")
                print("\nFor audio output, you may also need:")
                print("sudo apt-get install -y pulseaudio alsa-utils")
                print("\nAfter installing, reinstall Python dependencies:")
                print("pip install -r requirements.txt --upgrade")
            else:
                print("All system dependencies are installed!")
        elif sys.platform == "darwin":  # macOS
            print("On macOS, ensure you have:")
            print("- Homebrew: https://brew.sh/")
            print("- PortAudio: brew install portaudio")
            print("- Piper TTS: Follow instructions at https://github.com/rhasspy/piper")
        print("\nAfter ensuring all dependencies are installed, run the program again without --check-dependencies")
        return
    
    # Initialize the TTS Howdy instance
    tts = PiperTTSHowdy(
        ollama_host=args.host,
        model=args.model,
        voice_model=args.voice_model,
        voice_rate=args.rate
    )
    
    # Download the voice model if requested
    if args.download_voice:
        tts.download_voice_model(args.voice_model)
        return
    
    # List voices and exit if requested
    if args.list_voices:
        tts.list_voices()
        return
    
    # Direct text-to-speech if text is provided
    if args.text:
        tts.speak_text(args.text)
        return
    
    # Read from stdin if requested
    if args.stdin:
        text = sys.stdin.read()
        tts.speak_text(text)
        return
    
    # Generate and speak response if prompt is provided
    if args.prompt:
        tts.stream_response(args.prompt, args.system)
        return
    
    # If no specific action is requested, start interactive mode
    print(f"TTS Howdy with Piper - Interactive Mode using Ollama model: {args.model}")
    print(f"Voice: {args.voice_model}")
    print("Use Ctrl+C to exit")
    try:
        while True:
            prompt = input("\nYou: ")
            if prompt.lower() in ('exit', 'quit'):
                break
            print("\nOllama:", end=" ", flush=True)
            tts.stream_response(prompt, args.system)
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main()