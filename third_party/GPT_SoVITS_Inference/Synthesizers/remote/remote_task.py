
import os, json, sys
sys.path.append(".")

from uuid import uuid4
from typing import List, Dict, Literal, Optional, Any, Union
import urllib.parse
import hashlib

from Synthesizers.base import Base_TTS_Task, ParamItem, init_params_config

global global_based_synthesizer
global_based_synthesizer = None

def set_based_synthesizer(based_synthesizer:str):
    global global_based_synthesizer
    global_based_synthesizer = based_synthesizer

def get_params_config(based_synthesizer:str= None):
    assert based_synthesizer is not None, "based_synthesizer is not set, please init the remote synthesizer first."
    try:
        with open(os.path.join(os.path.dirname(__file__), "configs", "params_config.json"), "r", encoding="utf-8") as f:
            res:dict = json.load(f)
        with open(os.path.join("Synthesizers", based_synthesizer ,"configs", "params_config.json"), "r", encoding="utf-8") as f:
            res.update(json.load(f))
        return init_params_config(res)
    except:
        raise FileNotFoundError("params_config.json not found or invalid.")

params_config = None

def get_ui_config(based_synthesizer:str= None)->Dict[str, Any]:
    if based_synthesizer is None:
        based_synthesizer = global_based_synthesizer
    assert based_synthesizer is not None, "based_synthesizer is not set, please init the remote synthesizer first."
    
    remote_ui_config_path = os.path.join(os.path.dirname(__file__), "configs", "ui_config.json")
    based_ui_config_path = os.path.join("Synthesizers", based_synthesizer ,"configs", "ui_config.json")
    
    ui_config :Dict[str, Any] = {}
    try:
        with open(remote_ui_config_path, "r", encoding="utf-8") as f:
            ui_config.update(json.load(f))
        with open(based_ui_config_path, "r", encoding="utf-8") as f:
            ui_config.update(json.load(f))
        return ui_config
    except:
        raise FileNotFoundError("ui_config.json not found or invalid.")

from pydantic import BaseModel, Field, model_validator
from copy import deepcopy
class Remote_TTS_Task(Base_TTS_Task):
    
    is_remote: Optional[bool] = True
    data : dict = {}
    
    class Config:
        extra = "ignore"
    
    def __init__(self, based_synthesizer:str=None, **data):
        
        global params_config
        based_synthesizer = based_synthesizer if based_synthesizer is not None else global_based_synthesizer
        assert based_synthesizer is not None, "based_synthesizer is not set, please init the remote synthesizer first."
        if params_config is None:
            params_config = get_params_config(based_synthesizer)
        copyed_data = deepcopy(data)
        copyed_data.setdefault("params_config",params_config)
        super().__init__(**copyed_data)
        self.data = data
    
    @property
    def md5(self):
        m = hashlib.md5()
        m.update(self.data.__str__().encode())
        return m.hexdigest()
    
    def __str__(self):
        content = super().__str__()
        return f"{content}"


