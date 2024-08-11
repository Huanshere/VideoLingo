import os, sys, json
from typing import List, Any, Optional ,Dict, Literal   
from pydantic import BaseModel, Field, model_validator

__version__ = "2.6.3"

from Synthesizers.base import load_config


class Api_Config(BaseModel):   
    config_path:str = None
    tts_port: int = 5000
    tts_host: str = "0.0.0.0" 
    synthesizer: str = "gsv_fast"


    def __init__(self, config_path = None):
        super().__init__()
        
        self.config_path = config_path
        assert os.path.exists(self.config_path), f"配置文件不存在: {self.config_path}"
        if os.path.exists(self.config_path):
            all_config = load_config(self.config_path)
            config:dict = all_config.get("common", {})
            for key, value in config.items():
                setattr(self, key, value)
        
class App_Config(BaseModel):

    config_path:str = None
    locale: str = "auto"
    is_share: bool = False
    inbrowser: bool = True
    server_name: str = "0.0.0.0"
    server_port: int = -1 # -1 means auto select
    also_enable_api: bool = True
    synthesizer: str = "gsv_fast"
    max_text_length: int = -1

    @model_validator(mode='after')
    def check_locale(self):
        # Example: validating locale to be one of a set predefined values or patterns
        self.locale = self.locale.replace("-", "_")
        return self

    @staticmethod
    def check_port(port:int, server_name:str):
        url = f"http://{server_name}:{port}"
     
    
    def __init__(self, config_path = None):
        super().__init__()
        
        self.config_path = config_path
        assert os.path.exists(self.config_path), f"配置文件不存在: {self.config_path}"
        if os.path.exists(self.config_path):
            all_config = load_config(self.config_path)
            config = all_config.get("app_config", {})
            for key, value in config.items():
                setattr(self, key, value)

# 获取本文件的绝对路径
current_path = os.path.dirname(os.path.abspath(__file__))
# 获取 current_path 的上级目录
parent_path = os.path.dirname(current_path)
app_config = App_Config(os.path.join(parent_path, "common_config.json"))
api_config = Api_Config(os.path.join(parent_path, "common_config.json"))


