import subprocess
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def edge_tts(text, savepath):
    from config import EDGE_VOICE
    command = [
        "edge-tts",
        "--voice", EDGE_VOICE,
        "--text", text,
        "--write-media", savepath

    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Audio saved successfully to {savepath}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        print(f"Error output: {e.stderr}")
        return False

def edge_tts_for_videolingo(text, save_as, number, task_df):
    edge_tts(text, save_as)

# edge_tts("你好，世界！", "output/audio/edge_tts.wav")