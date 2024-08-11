import io, wave
import os, json, sys
import threading

from Synthesizers.base import Base_TTS_Synthesizer ,load_config

from .remote_task import Remote_TTS_Task as TTS_Task, set_based_synthesizer, get_ui_config
import requests
from urllib import parse
from datetime import datetime
from typing import Union, Generator, Tuple, Any, Optional, Dict, Literal
import numpy as np
import soundfile as sf

class Remote_Synthesizer(Base_TTS_Synthesizer):
    url :str = "http://127.0.0.1:5000"
    tts_endpoint:str = "/tts"
    character_endpoint:str = "/character_list"
    based_synthesizer :str = "gsv_fast"
    class Config:
        extra = "ignore"
    def __init__(self, config_path:str = None, **kwargs):
        super().__init__(**kwargs)
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "configs", "config.json")
        config_dict = load_config(config_path)
        config_dict.update(kwargs)
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        set_based_synthesizer(self.based_synthesizer)
        self.ui_config = get_ui_config(self.based_synthesizer)

    def get_characters(self)-> dict:
        url = self.url + self.character_endpoint
        res = requests.get(url)
        return json.loads(res.text)

    @staticmethod
    def stream_audio(url, data: Dict[str, Any]) -> Generator[Tuple[int, np.ndarray], None, None]:
        headers = {"Content-Type": "application/json"}
        # 发起POST请求，获取响应流
        response = requests.post(
            url, data=json.dumps(data), headers=headers, stream=True
        )
        chunk_size = 1024
        # 确保请求成功
        if response.status_code == 200:
            # 循环读取音频流
            for chunk in response.iter_content(chunk_size):
                # 将二进制数据转换为numpy数组，这里假设音频数据是16位整数格式
                audiodata = np.frombuffer(chunk, dtype=np.int16)
                yield 32000, audiodata
        else:
            raise Exception(
                f"Failed to get audio stream, status code: {response.status_code}"
            )
    def generate(
        self,
        task: TTS_Task,
        return_type: Literal["filepath", "numpy"] = "numpy",
        save_path: Optional[str] = None,
    ) -> Union[str, Generator[Tuple[int, np.ndarray], None, None], Any]:
        
        
        url = self.url + self.tts_endpoint
        data = task.data
        print(return_type)
        
        if self.debug_mode:
            print(f"generate task: \n{data}")
        headers = {"Content-Type": "application/json"}
        if return_type == "filepath" or (
            return_type == "numpy" and not task.stream
        ):
            if save_path is None:
                save_path = f"tmp_audio/{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
            res = requests.post(url, data=json.dumps(data), headers=headers)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                if return_type == "filepath":
                    return save_path
                else:
                    audiodata, sr = sf.read(save_path)
                    return ((sr, audiodata) for _ in range(1))
            else:
                raise Exception(f"remote synthesizer error: {res.text}")

        elif return_type == "numpy" and task.stream:
            return self.stream_audio(url, data)
            

    def params_parser(self, data) -> TTS_Task:
        task = TTS_Task(based_synthesizer=self.based_synthesizer, **data)
        return task

    def ms_like_parser(self,data) -> TTS_Task:
        task = TTS_Task(based_synthesizer=self.based_synthesizer, **data)
        return task
