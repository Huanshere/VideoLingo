from abc import ABC, abstractmethod

from .Base_TTS_Task import Base_TTS_Task as TTS_Task
import json
from typing import List, Dict, Literal, Optional, Any, Union, Generator, Tuple
from pydantic import BaseModel, Field, model_validator
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Union, Generator, Tuple
from typing_extensions import Literal
import numpy as np
import wave,io

class Base_TTS_Synthesizer(ABC):
    """
    Abstract base class for a Text-To-Speech (TTS) synthesizer.

    Attributes:
        ui_config (Dict[str, List]): A dictionary containing UI configuration settings.
        debug_mode (bool): Flag to toggle debug mode for additional logging and debugging information.

    """

    ui_config: Dict[str, List] = {}
    debug_mode: bool = False

    def __init__(self, **kwargs):
        """
        Initializes the TTS synthesizer with optional UI configurations and debug mode setting.

        Args:
            ui_config (Dict[str, List], optional): Configuration for user interface settings.
            debug_mode (bool, optional): Enables or disables debug mode.

        """
        self.ui_config = kwargs.get("ui_config", {})
        self.debug_mode = kwargs.get("debug_mode", False)

    @abstractmethod
    def generate(
        self,
        task: TTS_Task,
        return_type: Literal["filepath", "numpy"] = "numpy",
        save_path: Optional[str] = None,
    ) -> Union[str, Generator[Tuple[int, np.ndarray], None, None], Any]:
        """
        Generates speech from a given TTS task.

        Args:
            task (TTS_Task): The task containing data and parameters for speech synthesis.
            return_type (Literal["filepath", "numpy"], optional): The type of return value, either a file path or audio data.
            save_path (str, optional): The path to save the audio file.
        Returns:
            Union[str, Generator[Tuple[int, np.ndarray], None, None], Any]: Depending on the return_type, returns a file path, a generator of audio data, or other types.

        """
        pass

    @abstractmethod
    def get_characters(self):
        """
        Retrieves the available characters and their emotions for the TTS.

        Returns:
            Dict[str, List[str]]: A dictionary mapping character names to lists of their emotions.
        """
        pass

    @abstractmethod
    def params_parser(self, data):
        """
        Parses input data into a TTS_Task.

        Args:
            data (Any): The raw input data to be parsed.

        Returns:
            TTS_Task: A TTS task object created from the input data.
        """
        pass

    @abstractmethod
    def ms_like_parser(self, data):
        """
        Parses input data in a Microsoft-like format into a TTS_Task.

        Args:
            data (Any): The raw input data to be parsed.

        Returns:
            TTS_Task: A TTS task object created from the Microsoft-like formatted input data.
        """
        pass


def get_wave_header_chunk(sample_rate: int, channels: int = 1, sample_width: int = 2):
    """
    Generate a wave header with no data.

    Args:
        sample_rate (int): The sample rate of the audio.
        channels (int, optional): The number of audio channels. Defaults to 1.
        sample_width (int, optional): The sample width in bytes. Defaults to 2.

    Returns:
        bytes: The wave header as bytes.
    """
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as vfout:
        vfout.setnchannels(channels)
        vfout.setsampwidth(sample_width)
        vfout.setframerate(sample_rate)

    wav_buf.seek(0)
    return wav_buf.read()
