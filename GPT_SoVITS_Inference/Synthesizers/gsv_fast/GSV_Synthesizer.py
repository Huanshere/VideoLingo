import io, wave
import os, json, sys
import threading
from typing import Any, Union, Generator, Literal, List, Dict, Tuple
from Synthesizers.base import Base_TTS_Synthesizer, load_config
import re
from .gsv_task import GSV_TTS_Task as TTS_Task
from .ssml_dealer import SSML_Dealer

from time import time as tt
import numpy as np
import hashlib  
import soundfile as sf

from .gsv_config import load_infer_config, auto_generate_infer_config, get_device_info
from datetime import datetime

dict_language = {
    "中文": "all_zh",#全部按中文识别
    "英文": "en",#全部按英文识别#######不变
    "日文": "all_ja",#全部按日文识别
    "中英混合": "zh",#按中英混合识别####不变
    "日英混合": "ja",#按日英混合识别####不变
    "多语种混合": "auto",#多语种启动切分识别语种
    "auto": "auto",
    "zh": "zh",
    "en": "en",
    "ja": "ja",
    "all_zh": "all_zh",
    "all_ja": "all_ja",
}

from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
class GSV_Synthesizer(Base_TTS_Synthesizer):
    device: str = "auto"
    is_half: bool = False
    models_path:str = "models/gsv"
    cnhubert_base_path:str = "models/pretrained_models/gsv/chinese-hubert-base"
    bert_base_path:str = "models/pretrained_models/gsv/chinese-roberta-wwm-ext-large"
    save_prompt_cache:bool = True
    prompt_cache_dir:str = "cache/prompt_cache"
    default_character:str = None

    ui_config:dict = None
    tts_pipline:TTS = None
    character:str = None

    def __init__(self, config_path:str=None, **kwargs):
        super().__init__()

        # 获取当前位置的上一级的上一级目录
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if config_path is None:
            config_path = os.path.join(root_dir, "gsv_config.json")
        config_dict = load_config(config_path)
        config_dict.update(kwargs)
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        if self.debug_mode:
            print(f"GSV_Synthesizer config: {config_dict}")

        self.device, self.is_half = get_device_info(self.device, self.is_half)
        tts_config = TTS_Config("")
        tts_config.device , tts_config.is_half = self.device, self.is_half
        tts_config.cnhubert_base_path = self.cnhubert_base_path
        tts_config.bert_base_path = self.bert_base_path
        self.tts_pipline = TTS(tts_config)

        if self.default_character is None:
            self.default_character = next(iter(self.get_characters()), None)

        self.load_character(self.default_character)
        # 获取当前文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ui_config_path = os.path.join(current_dir, "configs/ui_config.json")
        with open(ui_config_path, 'r', encoding='utf-8') as f:
            self.ui_config = json.load(f)

    # from https://github.com/RVC-Boss/GPT-SoVITS/pull/448
    def get_streaming_tts_wav(self, params):
        # from https://huggingface.co/spaces/coqui/voice-chat-with-mistral/blob/main/app.py
        def wave_header_chunk(frame_input=b"", channels=1, sample_width=2, sample_rate=32000):
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, "wb") as vfout:
                vfout.setnchannels(channels)
                vfout.setsampwidth(sample_width)
                vfout.setframerate(sample_rate)
                vfout.writeframes(frame_input)

            wav_buf.seek(0)
            return wav_buf.read()
        chunks = self.tts_pipline.run(params)
        yield wave_header_chunk()
        # chunk is tuple[int, np.ndarray], 代表了sample_rate和音频数据
        for chunk in chunks:
            sample_rate, audio_data = chunk
            if audio_data is not None:
                return_data = audio_data.tobytes()
                del audio_data
                yield return_data

    def get_characters(self) -> dict:
        characters_and_emotions = {}
        # trained模型地址  读取 gsv_config.json 文件
        with open("gsv_config.json", "r", encoding='utf-8') as f:
            trained_model_path = json.load(f)['models_path']
        # 从配置文件中读取模型路径
        self.models_path = self.ui_config.get('models_path', trained_model_path)
        print(f"get_characters trained模型地址: {os.environ.get('models_path', trained_model_path)}")

        # 遍历模型路径下的所有文件夹
        for character_subdir in os.listdir(self.models_path):
            subdir_path = os.path.join(self.models_path, character_subdir)
            config_path = os.path.join(subdir_path, "infer_config.json")
            if not os.path.isdir(subdir_path):
                continue
            # 检查路径是否为文件夹并存在配置文件
            if os.path.exists(config_path):
                try:
                    # 尝试读取配置文件并提取情感列表
                    with open(config_path, "r", encoding='utf-8') as f:
                        config = json.load(f)
                        emotion_dict_list = config.get('emotion_list', None)
                        if emotion_dict_list is None:
                            emotion_list = ["default"]
                        else:
                            emotion_list = list(emotion_dict_list.keys())
                except json.JSONDecodeError:
                    # 文件读取或解析失败则使用默认情感
                    emotion_list = ["default"]
            else:
                # 如果不是文件夹或配置文件不存在，也使用默认情感
                emotion_list = ["default"]

            characters_and_emotions[character_subdir] = emotion_list
        return characters_and_emotions

    def load_character_id(self, speaker_id):
        character = list(self.get_characters())[speaker_id]
        return self.load_character(character)

    def load_character(self, character):
        if character in ["", None]:
            if self.character not in ["", None]:
                return
            else:
                character = self.default_character
                print(f"{character}为空，尝试切换到默认角色{self.default_character}")
                return self.load_character(character)
        if str(character).lower() == str(self.character).lower():
            return
        character_path=os.path.join(self.models_path, character)
        if not os.path.exists(character_path):
            print(f"找不到角色文件夹: {character}，沿用之前的角色{self.character}")
            return
            # raise Exception(f"Can't find character folder: {character}")
        assert os.path.exists(character_path), f"找不到角色文件夹: {character}"
        try:
            # 加载配置
            config = load_infer_config(character_path)

            # 尝试从环境变量获取gpt_path，如果未设置，则从配置文件读取
            gpt_path = os.path.join(character_path,config.get("gpt_path"))
            # 尝试从环境变量获取sovits_path，如果未设置，则从配置文件读取
            sovits_path = os.path.join(character_path,config.get("sovits_path"))
        except:
            try:
                # 尝试调用auto_get_infer_config
                auto_generate_infer_config(character_path)
                self.load_character(character)
                return 
            except:
                # 报错
                raise Exception("找不到模型文件！请把有效模型放置在模型文件夹下，确保其中至少有pth、ckpt和wav三种文件。")
        
        self.character = character

        t0 = tt()
        self.tts_pipline.init_t2s_weights(gpt_path)
        self.tts_pipline.init_vits_weights(sovits_path)
        t1 = tt()
        print(f"加载角色成功: {character}, 耗时: {t1-t0:.2f}s")

    def generate_from_text(self, task: TTS_Task):
        self.load_character(task.character)
        task.character = self.character
        # 加载环境配置
        if task.ref_audio_path is None or not os.path.exists(task.ref_audio_path):
            task.ref_audio_path, task.prompt_text, task.prompt_language = self.get_ref_infos(self.character, task.emotion)

        return self.get_wav_from_text_api(
            text=task.text,
            text_language=task.text_language,
            ref_audio_path=task.ref_audio_path,
            prompt_text=task.prompt_text,
            prompt_language=task.prompt_language,
            batch_size=task.batch_size,
            speed=task.speed,
            top_k=task.top_k,
            top_p=task.top_p,
            temperature=task.temperature,
            cut_method=task.cut_method,
            max_cut_length=task.max_cut_length,
            seed=task.seed,
            parallel_infer=task.parallel_infer,
            repetition_penalty=task.repetition_penalty,
            stream=task.stream
        )

    def generate_from_ssml(self, task: TTS_Task):
        dealer = SSML_Dealer()
        return dealer.generate_from_ssml(task.ssml, self)

    def generate(
        self,
        task: TTS_Task,
        return_type: Literal["filepath", "numpy"] = "numpy",
        save_path: str = None,
    ) -> Union[str, Generator[Tuple[int, np.ndarray], None, None], Any]:
        if self.debug_mode:
            print(f"task: {task}")
        gen = None
        if task.task_type == "text":
            gen = self.generate_from_text(task)
        elif task.task_type == "ssml":
            gen = self.generate_from_ssml(task)

        if return_type == "numpy":
            return gen
        elif return_type == "filepath":
            if save_path is None:
                save_path = f"tmp_audio/{datetime.now().strftime('%Y%m%d%H%M%S')}.{task.format}"
            sr, audio_data = next(gen)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            sf.write(save_path, audio_data, sr)
            del audio_data
            return save_path
        
    @staticmethod
    def calc_short_md5(string):
        m = hashlib.md5()
        m.update(string.encode())
        return m.hexdigest()[:8]
    
    def get_ref_infos(self, character, emotion) -> Tuple[str, str, str]:
        if self.debug_mode:
            print(f"try to get ref infos, character: {character}, emotion: {emotion}")
        character_path = os.path.join(self.models_path, character)
        config: Dict[str, Any] = load_infer_config(character_path)
        emotion_dict: Dict = config.get("emotion_list", None)
        if emotion_dict is None:
            return None, None, None
        emotion_name_list = list(emotion_dict.keys())
        if emotion not in emotion_name_list:
            emotion = emotion_name_list[0]
        for emotion_name, details in emotion_dict.items():
            if emotion_name == emotion:
                relative_path = details['ref_wav_path']
                ref_audio_path = os.path.join(os.path.join(self.models_path,self.character), relative_path)
                prompt_text = details['prompt_text']
                prompt_language = details['prompt_language']
                
                return ref_audio_path, prompt_text, prompt_language
        return None, None, None

    def get_wav_from_text_api(
        self,
        text: str,
        text_language="auto",
        ref_audio_path=None,
        prompt_text=None,
        prompt_language="auto",
        batch_size=1,
        speed=1.0,
        top_k=12,
        top_p=0.6,
        temperature=0.6,
        cut_method="auto_cut",
        max_cut_length=100,
        seed=-1,
        stream=False,
        parallel_infer=True,
        repetition_penalty=1.35,
        **kwargs
    ):

        text = re.sub(r"\r|<br>", "\n", text)
        text = re.sub(r"\t|……|…", "。", text)
        
        assert os.path.exists(ref_audio_path), f"找不到参考音频文件: {ref_audio_path}"
        prompt_cache_path = ""

        if self.save_prompt_cache:
            prompt_cache_path = f"{self.prompt_cache_dir}/prompt_cache_{self.calc_short_md5(ref_audio_path + prompt_text + prompt_language)}.pickle"

        try:
            text_language = dict_language[text_language]
            prompt_language = dict_language[prompt_language]
            if "-" in text_language:
                text_language = text_language.split("-")[0]
            if "-" in prompt_language:
                prompt_language = prompt_language.split("-")[0]
        except:
            text_language = "auto"
            prompt_language = "auto"
        ref_free = False

        if cut_method == "auto_cut":
            cut_method = f"auto_cut_{max_cut_length}"

        params = {
            "text": text,
            "text_lang": text_language.lower(),
            "prompt_cache_path": prompt_cache_path,
            "ref_audio_path": ref_audio_path,
            "prompt_text": prompt_text,
            "prompt_lang": prompt_language.lower(),
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "text_split_method": cut_method, 
            "batch_size": batch_size,
            "speed_factor": speed,
            "ref_text_free": ref_free,
            "split_bucket":True,
            "return_fragment":stream,
            "seed": seed,
            "parallel_infer": parallel_infer,
            "repetition_penalty": repetition_penalty
        }
        # 调用原始的get_tts_wav函数
        # 注意：这里假设get_tts_wav函数及其所需的其它依赖已经定义并可用
 
        if stream == False:
            return self.tts_pipline.run(params)
        else:
            return self.get_streaming_tts_wav(params)

    @staticmethod   
    def params_parser(data) -> TTS_Task:
        task = TTS_Task(**data)
        return task

    @staticmethod
    def ms_like_parser(data) -> TTS_Task:
        inputs = data.get("inputs", [])
        try:
            data["text"] = inputs[0]["text"]
        except:
            pass
        task = TTS_Task(**data)
        return task
