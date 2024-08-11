
import os, json, sys
sys.path.append(".")

from uuid import uuid4
from typing import List, Dict, Literal, Optional, Any, Union
import urllib.parse
import hashlib

from Synthesizers.base import Base_TTS_Task, ParamItem, init_params_config
# 获取当前文件目录
current_dir = os.path.dirname(os.path.abspath(__file__))

def get_params_config():
    try:
        with open(os.path.join(current_dir, "configs/params_config.json"), "r", encoding="utf-8") as f:
            return init_params_config(json.load(f))
    except:
        raise FileNotFoundError("params_config.json not found or invalid.")
    

params_config = get_params_config()

from pydantic import BaseModel, Field, model_validator

class GSV_TTS_Task(Base_TTS_Task):
    # character: Optional[str] = None
    # emotion: Optional[str] = None
    ref_audio_path: Optional[str] = None
    prompt_text: Optional[str] = None
    prompt_language: Optional[str] = None
    text_language: Optional[str] = None
    speaker_id: Optional[int] = None
    batch_size: Optional[int] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    temperature: Optional[float] = None
    cut_method: Optional[str] = None
    max_cut_length: Optional[int] = None
    seed: Optional[int] = None
    save_temp: Optional[bool] = False
    parallel_infer : Optional[bool] = True
    repetition_penalty : Optional[float] = 1.35
    # the gsv_fast model only supports 32000 sample rate
    sample_rate: int = 32000
    
    def __init__(self, other_task: Union[BaseModel, dict, None] = None, **data):
        data.setdefault('params_config', params_config)
        super().__init__(other_task, **data)
    
    @property
    def md5(self):
        m = hashlib.md5()
        if self.task_type == "audio":
            m.update(self.src.encode())
        elif self.task_type == "ssml":
            m.update(self.ssml.encode())
        elif self.task_type == "text":
            m.update(self.text.encode())
            m.update(self.text_language.encode())
            m.update(self.character.encode())
            m.update(str(self.speaker_id).encode())
            m.update(str(self.speed).encode())
            m.update(str(self.top_k).encode())
            m.update(str(self.top_p).encode())
            m.update(str(self.temperature).encode())
            m.update(str(self.cut_method).encode())
            m.update(str(self.emotion).encode())
        return m.hexdigest()
    
    

