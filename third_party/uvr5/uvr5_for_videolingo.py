import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from third_party.uvr5.vr import AudioPre
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
def uvr5_for_videolingo(music_file, save_dir):
    from config import MODEL_DIR
    ap = AudioPre(agg=10, model_path=os.path.join(MODEL_DIR, "uvr5_weights", "HP2_all_vocals.pth"), device=device, is_half=False)
    ap._path_audio_(music_file, save_dir, save_dir, format='wav')

if __name__ == '__main__':
    uvr5_for_videolingo(r'output\audio\raw_full_audio.wav', r'output\audio')
