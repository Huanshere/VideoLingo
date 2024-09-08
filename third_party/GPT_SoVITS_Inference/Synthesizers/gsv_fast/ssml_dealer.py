import os, json
from typing import List , Dict
from uuid import uuid4

import sys
sys.path.append(".")

import xml.etree.ElementTree as ET
from .gsv_task import GSV_TTS_Task as TTS_Task
from Synthesizers.base import Base_TTS_Synthesizer, ParamItem, init_params_config

import tempfile
import soundfile as sf

import numpy as np
import requests, librosa


special_dict_speed = {
    "x-slow": 0.5,
    "slow": 0.75,
    "medium": 1.0,
    "fast": 1.25,
    "x-fast": 1.5,
    "default": 1.0
}


special_dict_break_strength = {
    "x-weak": 0.25,
    "weak": 0.5,
    "medium": 0.75,
    "strong": 1.0,
    "x-strong": 1.25,
    "default": 0.75
}


def load_time(time:str) -> float:
    if time.endswith("ms"):
        return float(time[:-2]) / 1000
    if time.endswith("s"):
        return float(time[:-1])
    if time.endswith("min"):
        return float(time[:-3]) * 60
    return float(time)

def get_value_from_special_dict(key:str, special_dict:Dict[str, float]) -> float:
    if key in special_dict:
        return special_dict[key]
    return key

class SSML_Dealer:
    def __init__(self,params_config:Dict[str, ParamItem]):
        self.ssml: str = ""
        self.task_list: Dict[str, TTS_Task] = {}
        self.task_queue : List[str] = []
        self.audio_download_queue : List[str] = []
        self.root : ET.Element = None
        self.tts_synthesizer = None
        self.params_config = TTS_Task().params_config
    
    def get_value_from_root(self, root:ET.Element, key:str, special_dict:Dict[str, float]=None):
        if key in self.params_config:
            for alias in self.params_config[key].alias:
                if root.get(alias) is not None:
                    if special_dict is not None:
                        return get_value_from_special_dict(root.get(alias), special_dict)
                    else:
                        return root.get(alias)


    
    def analyze_element(self, root: ET.Element, father_task:TTS_Task):
        task = TTS_Task(father_task)
        self.task_list[task.uuid] = task
        root.set("uuid", task.uuid)
        root.tag = root.tag.split('}')[-1].lower()
        task.text = root.text.strip() if root.text is not None else ""
        print(f"--------{root.tag} : {task.text}") # debug
        if root.tag in ["audio", "mstts:backgroundaudio"]:
            if root.get("src") is not None:
                self.audio_download_queue.append({"uuid": task.uuid, "src": root.get("src")})
            task.text = ""
        else:
            if root.tag in ["bookmark", "break", "mstts:silence", "mstts:viseme"]:
                task.text = ""

            
            task.update_value('text_language', self.get_value_from_root(root, 'text_language'))
            task.update_value('character', self.get_value_from_root(root, 'character'))
            task.update_value('emotion', self.get_value_from_root(root, 'emotion'))
            task.update_value('speed', self.get_value_from_root(root, 'speed', special_dict_speed))
            
            # task.update_value('top_k', root)
            # task.update_value('top_p', root)
            # task.update_value('temperature', root)
            # task.update_value('batch_size', root)
            
            # task.update_value('loudness', root) # need to recheck
            # task.update_value('pitch', root)
            
                
            task.stream = False
            if task.text.strip() != "":
                self.task_queue.append(task.uuid)
        if root.tail is not None:
            new_task = TTS_Task(father_task)
            self.task_list[new_task.uuid] = new_task
            new_task.text = root.tail.strip()
            if new_task.text != "":
                self.task_queue.append(new_task.uuid)
                root.set("tail_uuid", new_task.uuid)
        for child in root:
            self.analyze_element(child, father_task)
        
        
    
    def generate_audio_from_element(self, root: ET.Element, default_silence: float = 0.3) -> np.ndarray:
        # 认定所有的音频文件都已经生成
        audio_data = np.array([])
        uuid = root.get("uuid")
        task = self.task_list[uuid]
        sr = 32000
        # print(f"--------{root.tag}") # debug
        if root.tag in ["break"]:
            # print(f"--------break: {root.get('time')}") # debug
            time_ = root.get("time")
            duration = 0.75
            if time_ is not None:
                duration = load_time(time_)
            strength_ = root.get("strength")
            if strength_ in special_dict_break_strength:
                duration = special_dict_break_strength[strength_]
            audio_data = np.zeros(int(duration * sr))
        elif task.audio_path not in ["", None]:
            audio_data, sr = sf.read(task.audio_path)
        
        for child in root:
            audio_data = np.concatenate([audio_data, self.generate_audio_from_element(child)])
        
        if default_silence > 0:
            audio_data = np.concatenate([audio_data, np.zeros(int(default_silence * sr))])
        
        if root.get("tail_uuid") is not None:
            audio_path = self.task_list[root.get("tail_uuid")].audio_path
            if audio_path not in ["", None]:
                audio_data_tail, sr = sf.read(audio_path)
                audio_data = np.concatenate([audio_data, audio_data_tail])
        
        return audio_data
    
    def read_ssml(self, ssml:str):
        self.ssml = ssml
        try:
            self.root = ET.fromstring(ssml)
            self.analyze_element(self.root, None)
        except Exception as e:
            raise ValueError("Invalid SSML.")
        
    def generate_tasks(self, tts_synthesizer, tmp_dir:str):
        # 先按照人物排序
        self.task_queue.sort(key=lambda x: self.task_list[x].character)
        for uuid in self.task_queue:
            task = self.task_list[uuid]
            if task.text.strip() == "":
                continue
            gen = tts_synthesizer.generate_from_text(task)
            sr, audio_data = next(gen)
            
            tmp_file = os.path.join(tmp_dir, f"{task.uuid}.wav")
            
            sf.write(tmp_file, audio_data, sr, format='wav')
            task.audio_path = tmp_file

    def download_audio(self, tmp_dir:str, sample_rate:int=32000):
        for audio in self.audio_download_queue:
            # 另开一个线程下载音频
            response = requests.get(audio["src"])
            # 重采样
            audio_format = audio["src"].split(".")[-1]
            tmp_file = os.path.join(tmp_dir, f"{uuid4()}.{audio_format}")
            with open(tmp_file, 'wb') as f:
                f.write(response.content)
            audio_data, sr = librosa.load(tmp_file, sr=sample_rate)
            sf.write(tmp_file, audio_data, sr, format='wav')
            self.task_list[audio["uuid"]].audio_path = tmp_file
    
    def generate_from_ssml(self, ssml:str, tts_synthesizer, format:str="wav"):
        self.read_ssml(ssml)
        tmp_dir = tempfile.mkdtemp()
        self.generate_tasks(tts_synthesizer, tmp_dir)
        self.download_audio(tmp_dir)
        audio_data = self.generate_audio_from_element(self.root)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp_file:
            sf.write(tmp_file, audio_data, 32000, format=format)
            return tmp_file.name

if __name__ == "__main__":
    ssml = """
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
<audio src="https://d38nvwmjovqyq6.cloudfront.net/va90web25003/companions/Foundations%20of%20Rock/5.04.mp3" >
</audio>
    <voice name="en-US-AvaNeural">
        Welcome <break /> to text to speech.
        Welcome <break strength="medium" /> to text to speech.
        Welcome <break time="750ms" /> to text to speech.
    </voice>
</speak>
"""
    # ssml_dealer = SSML_Dealer()
    # # tts_synthesizer = TTS_synthesizer()
    # print(ssml_dealer.generate_from_ssml(ssml, tts_synthesizer))
    
    # for task in ssml_dealer.task_list.values():
    #     print(task)