from typing import Any, Optional, Dict, List, Literal
from pydantic import BaseModel
import os, json

class ConfigItem(BaseModel):
    value : Optional[Any] = None
    default : Optional[Any] = None
    type : Optional[str] = None
    description : Optional[str] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if (self.value is None) and self.default is not None:
            self.value = self.default

def is_config_item(item:Dict[str, Any])->bool:
    """判断是否为配置项"""
    return isinstance(item, dict) and ("value" in item or "default" in item)

def parse_config_dict(input_config:Dict[str, Any], output_config)->Dict[str, Any]:
    
    for key, res in input_config.items():
        if is_config_item(res):
            value = ConfigItem(**res).value
        else:
            if isinstance(res, dict):
                value = parse_config_dict(res, {})
            else:
                value = res
        output_config[key] = value
    return output_config
      
def load_config(config_path:str)->Dict[str, Any]:
    """加载配置文件"""
    assert os.path.exists(config_path), f"配置文件不存在: {config_path}"
    config:Dict[str, Any] = {}
    with open(config_path, 'r', encoding='utf-8') as f:
        config = parse_config_dict(json.load(f), {})
    return config

