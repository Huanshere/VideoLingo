import os, json, sys

from uuid import uuid4
from typing import Literal
import urllib.parse
import hashlib

from pydantic import BaseModel, Field, model_validator
from typing import Literal, List, Optional, Dict, Any, Union
from uuid import uuid4
import hashlib

def convert_value_type(value: Any, type_: str):
    if value is None:
        return None
    if isinstance(value, str):
        value = urllib.parse.unquote(value)
    if type(value).__name__ == type_:
        # 如果值的类型和参数的类型一致，直接返回值
        return value
    if type_ == "int":
        return int(value)
    elif type_ == "float":
        if isinstance(value, str) and value[-1] == "%":
            return float(value[:-1]) / 100
        else:
            return float(value)
    elif type_ == "bool":
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("true", "1", "t", "y", "yes", "allow", "allowed")
    else:  # 默认为字符串
        return str(value)


class ParamItem(BaseModel):
    """
    Represents a parameter item for a TTS task.

    Attributes:
        type (str): The data type of the parameter.
        default (Any): The default value of the parameter.
        alias (List[str]): The list of aliases for the parameter.
        label (Optional[str]): The label for the parameter.
        name (Optional[str]): The name of the parameter.
        description (Optional[str]): The description of the parameter.
        min_value (Optional[float]): The minimum value of the parameter.
        max_value (Optional[float]): The maximum value of the parameter.
        step (Optional[float]): The step value for the parameter.
        choices (Optional[List[str]]): The list of choices for the parameter.
    """
    type: str
    component_type: Optional[str] = None
    default: Any
    alias: List[str]
    label: Optional[str] = None
    name: Optional[str]
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    choices: Optional[List[str]] = None

    def __init__(self, **data):
        if not data.get("type"):
            data.update({"type": "str"})
        super().__init__(**data)
        self.default = convert_value_type(self.default, self.type)


def init_params_config(res: dict):

    result = {}
    for key, value in res.items():
        if value.get("label") is None:
            value.update({"label": key})
        value.update({"name": key})
        result[key] = ParamItem(**value)
    return result


class Base_TTS_Task(BaseModel):
    """
    Base class for TTS (Text-to-Speech) tasks.

    Attributes:
        uuid (str): Unique identifier for the task.
        params_config (Dict[str, ParamItem]): Configuration parameters for the task.

        task_type (Literal["text", "ssml", "audio"]): Type of the task. Can be "text", "ssml", or "audio".
        audio_path (Optional[str]): Path to the audio file.
        src (Optional[str]): Source url.
        ssml (Optional[str]): SSML (Speech Synthesis Markup Language) text.

        text (Optional[str]): Text content.

        format (Optional[str]): Audio format.
        sample_rate (Optional[int]): Sample rate of the audio.
        loudness (Optional[float]): Loudness of the audio.
        speed (Optional[float]): Speed of the audio.
        stream (Optional[bool]): Flag indicating if the audio should be streamed.

        save_temp (Optional[bool]): Flag indicating if the temporary files should be saved.

        disabled_features (Optional[List[str]]): List of disabled features.

    """

    uuid: str = None
    params_config: Dict[str, ParamItem]

    task_type: Literal["text", "ssml", "audio"] = Field(default="text")
    audio_path: Optional[str] = None
    src: Optional[str] = None
    ssml: Optional[str] = None
    
    text: Optional[str] = None

    character: Optional[str] = None
    emotion: Optional[str] = None

    format: Optional[str] = None
    sample_rate: Optional[int] = None
    loudness: Optional[float] = None
    speed: Optional[float] = None
    stream: Optional[bool] = None
    
    save_temp: Optional[bool] = False

    disabled_features: Optional[List[str]] = None

    class Config:
        populate_by_name = True
        extra = "ignore"

    def __init__(self, other_task: Union[BaseModel, dict, None] = None, **data):
        if isinstance(other_task, BaseModel):
            # 如果 task 是 Base_TTS_Task 实例，从该实例复制属性
            data = other_task.model_dump()
            super().__init__(**data)
        else:
            # 如果 task 是字典，直接使用这个字典
            if isinstance(other_task, dict):
                data = other_task
            assert "params_config" in data, "params_config is not defined."
            super().__init__(params_config=data.get("params_config"))
            self.set_default_values()
            self.set_values(**data)
        self.uuid = str(uuid4())

    def update_value(self, key: str, value: Any, allow_none: bool = False):
        if not allow_none and value is None:
            return
        
        assert self.params_config is not None, "params_config is not defined."
        for param_key, param_value in self.params_config.items():
                if key in param_value.alias:
                    if hasattr(self, param_key):
                        value = convert_value_type(value, param_value.type)
                        setattr(self, param_key, value)
                    else:
                        pass
                        # raise ValueError(f"Attribute {param_key} not found. Something went wrong in params_config.json.")

    def set_values(self, **data):
        assert self.params_config is not None, "params_config is not defined."
        for key, value in data.items():
            if hasattr(self, key):
                value = convert_value_type(value, type(getattr(self, key)).__name__)
                setattr(self, key, value)
            else:
                self.update_value(key, value)

    def set_default_values(self):
        assert self.params_config is not None, "params_config is not defined."
        for key, value in self.params_config.items():
            if (
                hasattr(self, key)
                and getattr(self, key) is None
                and value.default is not None
            ):
                setattr(self, key, value.default)

    @property
    def md5(self):
        m = hashlib.md5()
        if self.task_type == "text":
            m.update(self.text.encode())
        elif self.task_type == "ssml":
            m.update(self.ssml.encode())
        elif self.task_type == "audio":
            m.update(self.src.encode())
        return m.hexdigest()

    def __str__(self):
        dict_content: dict = self.model_dump(exclude={"params_config"})
        # 收集所有值为None的键
        keys_to_remove = [key for key, value in dict_content.items() if value is None]

        # 弹出这些键
        for key in keys_to_remove:
            dict_content.pop(key)
        return json.dumps(dict_content, indent=4, ensure_ascii=False)

    def copy(self, update: Dict[str, Any] = {}, deep: bool = False):
        update["uuid"] = str(uuid4())
        return super().model_copy(update=update, deep=deep)
