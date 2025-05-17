import pandas as pd
from core.utils.config_utils import load_key, get_joiner
from rich import print as rprint

def merge_words_by_speaker(df, joiner):
    merged = []
    current_speaker = None
    current_tokens = []

    for token, speaker in zip(df["text"], df["speaker"]):
        # when speaker changes, flush the last segment
        if speaker != current_speaker and current_tokens:
            merged.append({"speaker": current_speaker, "text": joiner.join(current_tokens)})
            current_tokens = []

        current_tokens.append(token)
        current_speaker = speaker

    # flush the last segment
    if current_tokens:
        merged.append({"speaker": current_speaker, "text": joiner.join(current_tokens)})

    return pd.DataFrame(merged)

def merge_by_speaker():
    # get language and joiner
    whisper_language = load_key("whisper.language")
    language = load_key("whisper.detected_language") if whisper_language == 'auto' else whisper_language
    joiner = get_joiner(language)
    rprint(f"[blue]🔍 Using {language} language joiner: '{joiner}'[/blue]")
    
    # get word level result
    chunks = pd.read_excel("output/log/cleaned_chunks.xlsx")
    chunks.text = chunks.text.apply(lambda x: x.strip('"').strip(""))
    
    # merge words by speaker
    merged_chunks = merge_words_by_speaker(chunks, joiner)
    merged_chunks.to_excel("output/log/merged_by_speaker.xlsx", index=False)
    rprint(f"[green]💾 Chunks merged by speaker saved to →  output/log/merged_by_speaker.xlsx[/green]")
    
    return merged_chunks

if __name__ == "__main__":
    merge_by_speaker() 