from openai import OpenAI
from pathlib import Path
import base64
from core.utils import *

def wav_to_base64(wav_file_path):
    with open(wav_file_path, 'rb') as audio_file:
        audio_content = audio_file.read()
    base64_audio = base64.b64encode(audio_content).decode('utf-8')
    return base64_audio

@except_handler("Failed to generate audio using SiliconFlow TTS")
def cosyvoice_tts_for_videolingo(text, save_as, number, task_df):
    prompt_text = task_df.loc[task_df['number'] == number, 'origin'].values[0]
    API_KEY = load_key("sf_cosyvoice2.api_key")
    # 设置参考音频路径
    current_dir = Path.cwd()
    ref_audio_path = current_dir / f"output/audio/refers/{number}.wav"
    
    # 如果参考音频不存在，使用第一个音频作为备选
    if not ref_audio_path.exists():
        ref_audio_path = current_dir / "output/audio/refers/1.wav"
        if not ref_audio_path.exists():
            try:
                from core._9_refer_audio import extract_refer_audio_main
                print(f"参考音频文件不存在，尝试提取: {ref_audio_path}")
                extract_refer_audio_main()
            except Exception as e:
                print(f"提取参考音频失败: {str(e)}")
                raise

    reference_base64 = wav_to_base64(ref_audio_path)
    client = OpenAI(api_key=API_KEY, base_url="https://api.siliconflow.cn/v1")

    save_path = Path(save_as)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with client.audio.speech.with_streaming_response.create(
        model="FunAudioLLM/CosyVoice2-0.5B",
        voice="",
        input=text,
        response_format="wav",
        extra_body={"references": [{"audio": f"data:audio/wav;base64,{reference_base64}", "text": prompt_text}]}
    ) as response:
        response.stream_to_file(save_path)
    
    print(f"音频已成功保存至: {save_path}")
    return True