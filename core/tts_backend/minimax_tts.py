import math
import replicate
from pathlib import Path
from typing import List, Tuple
import requests
import os

import pandas as pd
from pydub import AudioSegment
from rich import print as rprint

from core.utils import *
from core.utils.models import _AUDIO_REFERS_DIR
from core._1_ytdlp import find_video_files

def _get_speaker_config_id(speaker: str) -> str:
    video_file = find_video_files()
    base_name = Path(video_file).stem
    speaker_id = f"{base_name}_{speaker}"
    return speaker_id

# ! WARNING: upload file to tmpfiles.org and get url
def _upload_file_to_tmpfiles(file_path: str) -> str:
    with open(file_path, "rb") as f:
        response = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f})
    if response.status_code != 200:
        raise RuntimeError(f"Failed to upload file to tmpfiles.org: {response.text}")
    result = response.json()
    if not result.get("data", {}).get("url"):
        raise RuntimeError(f"Failed to get URL from tmpfiles.org: {result}")
    file_url = result["data"]["url"].replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
    rprint(f"[green]File uploaded to: {file_url}")
    return file_url

@except_handler("Minimax clone voice failed", retry=2)
def clone_voice(file_path: str) -> str:
    # clone voice from local file, get voice_id
    rprint("[bold] ⚠ Warning: Minimax voice cloning costs $3 for each voice, take care of your wallet![/bold]")
    client = replicate.Client(api_token=load_key("minimax.replicate_token"))
    
    # !upload file to tmpfiles.org and get url
    file_url = _upload_file_to_tmpfiles(file_path)
    
    # BUG: minimax/voice-cloning 通过api上传的文件在云端的url是不带ext的，会被minimax报错！所以暂时只能使用第三方托管（带ext）
    payload = {"voice_file": file_url, "model": "speech-02-turbo"}
    
    result = client.run("minimax/voice-cloning", input=payload)
    voice_id = result.get("voice_id")
    if not voice_id:
        raise RuntimeError(f"clone voice failed, voice_id not found, original result: {result}")
    return voice_id

@except_handler("Minimax tts failed", retry=2)
def tts_to_file(text: str, voice_id: str, output_path: str) -> str:
    """use minimax/speech-02-turbo to generate audio from text, and save to local mp3."""
    client = replicate.Client(api_token=load_key("minimax.replicate_token"))
    output = client.run(
        "minimax/speech-02-turbo",
        input={
            "text": text,
            "emotion": "auto",
            "voice_id": voice_id,
            "language_boost": "Automatic",
            "sample_rate": 16000,
            "english_normalization": False, # idk how useful this is
        }
    )

    response = requests.get(output) # output is a mp3 url
    temp_mp3_path = output_path + ".temp.mp3"
    with open(temp_mp3_path, "wb") as f:
        f.write(response.content)
    audio = AudioSegment.from_mp3(temp_mp3_path) # save as wav
    audio.export(output_path, format="wav")
    
    # del tmp
    if os.path.exists(temp_mp3_path):
        os.remove(temp_mp3_path)
    return output_path


def build_ref_audio(task_df: pd.DataFrame, speaker: str, min_total: float = 10.0, min_merge_clip: float = 1.0) -> str:
    """Generate a ≥10 s reference-audio clip for the speaker of *target_number*."""
    rprint("[blue]🎯 Starting reference audio selection process...")

    # 1️⃣ filter and sort by duration
    df_speaker = task_df[task_df["speaker"] == speaker].copy()
    df_speaker.sort_values("duration", ascending=False, inplace=True)
    if df_speaker.empty:
        raise ValueError(f"No clips found for speaker {speaker}")
    rprint(f"[cyan]📑 Found {len(df_speaker)} clips, longest {df_speaker.iloc[0]['duration']:.2f}s")

    # 2️⃣ select clips
    selected: List[Tuple[int, int]] = []  # (number, repeat)
    total = 0.0
    for _, row in df_speaker.iterrows():
        if total >= min_total:
            break
        num, dur = int(row["number"]), float(row["duration"])
        if not selected:
            selected.append((num, 1))
            total += dur
            rprint(f"[yellow]➕ Add clip {num} ({dur:.2f}s) — total {total:.2f}s")
            continue
        if dur < min_merge_clip:
            rprint(f"[magenta]⏭️  Clip {num} too short ({dur:.2f}s < {min_merge_clip}s); will use repetition instead")
            break
        selected.append((num, 1))
        total += dur
        rprint(f"[yellow]➕ Add clip {num} ({dur:.2f}s) — total {total:.2f}s")

    # 3️⃣ if total < 10 s, repeat all selected clips
    if total < min_total:
        original_total = total
        repeats_needed = math.ceil((min_total - total) / total)
        original_selected = selected.copy()
        # repeat all selected clips
        for _ in range(repeats_needed):
            for num, rep in original_selected:
                selected.append((num, rep))
                total += float(df_speaker.loc[df_speaker["number"] == num, "duration"].iloc[0]) * rep
                if total >= min_total:
                    break
            if total >= min_total:
                break
        rprint(f"[orange1]🔁 Repeating all selected clips {repeats_needed}× to reach {total:.2f}s from original {original_total:.2f}s")

    # 4️⃣ concatenate and clip
    rprint("[blue]🎛️  Concatenating audio segments...")
    ref_audio = AudioSegment.empty()
    for num, rep in selected:
        path = Path(_AUDIO_REFERS_DIR) / f"{num}.wav"
        if not path.exists():
            raise FileNotFoundError(f"Missing audio file {path}")
        clip = AudioSegment.from_mp3(path)
        ref_audio += clip * rep

    # 5️⃣ export
    export_path = Path(_AUDIO_REFERS_DIR) / f"{speaker}.mp3"
    ref_audio = ref_audio.set_frame_rate(16000)
    ref_audio.export(str(export_path), format="mp3")
    rprint(f"[green]💾 Exported reference audio to [bold]{export_path}[/]")

    rprint(f"[green]✅ Reference audio ready — final length: {len(ref_audio)/1000:.2f}s")
    return str(export_path)

def clone_all_speakers(task_df: pd.DataFrame):
    """Clone all speakers in the task_df."""
    rprint("[bold]🎯 Starting voice cloning all speakers...")
    unique_speakers = task_df["speaker"].unique()
    voice_config = load_key("minimax.voice_id_list")
    rprint(f"[cyan]Found {len(unique_speakers)} unique speakers: {unique_speakers}")
    
    for speaker in unique_speakers:
        speaker_id = _get_speaker_config_id(speaker)
        
        # check if voice_id exists
        if speaker_id in voice_config:
            rprint(f"[cyan]Voice ID already exists for {speaker}: {voice_config[speaker_id]}")
            continue
        # clone voice
        ref_audio_path = build_ref_audio(task_df, speaker)
        voice_id = clone_voice(ref_audio_path)
        voice_config[speaker_id] = voice_id
        rprint(f"[green]Successfully cloned voice for {speaker}: {voice_id}")
    
        # update config
        update_key("minimax.voice_id_list", voice_config)
    rprint(f"[green]✅ All {len(unique_speakers)} speakers' voices cloned")

def minimax_tts_for_videolingo(text, save_as, number, task_df):
    # get speaker of current task
    speaker = task_df[task_df["number"] == number]["speaker"].iloc[0]
    speaker_id = _get_speaker_config_id(speaker)
    
    # check if voice_id exists, clone all speakers if not
    voice_config = load_key("minimax.voice_id_list")
    if speaker_id in voice_config.keys():
        voice_id = voice_config[speaker_id]
        rprint(f"[cyan]Using existing voice_id for {speaker}: {voice_id}")
    else:
        clone_all_speakers(task_df)
        # reload voice_config
        voice_config = load_key("minimax.voice_id_list")
        voice_id = voice_config[speaker_id]

    # tts
    rprint(f"[blue]Synthesizing speech for {speaker} with voice_id {voice_id}, text: {text}")
    output_path = tts_to_file(text=text, voice_id=voice_id, output_path=save_as)
    rprint(f"[green]✅ Speech synthesized and saved to {output_path}")
    return output_path

if __name__ == "__main__":
    from core.utils.models import _8_1_AUDIO_TASK
    task_df = pd.read_excel(_8_1_AUDIO_TASK)
    clone_all_speakers(task_df)
    text = task_df[task_df["number"] == 1]["text"].iloc[0]
    minimax_tts_for_videolingo(text, "output/test_minimax.mp3", 1, task_df)
