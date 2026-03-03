import requests
import json
import sys
import time
import functools
import threading
import os

from core.utils.config_utils import load_key

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 尝试导入，如果未安装则忽略导入错误
try:
    if load_key("capcut.installed"):
        from core.capcut_api.settings.local import PORT
        # Base URL of the service, please modify according to actual situation
        BASE_URL = f"http://localhost:{PORT}"
    else:
        PORT = None
        BASE_URL = None
except ImportError:
    PORT = None
    BASE_URL = None

# 装饰器，检查是否安装了CapCutAPI
def require_capcut_api(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not load_key("capcut.installed") or BASE_URL is None:
            print(f"CapCutAPI not installed. Function '{func.__name__}' cannot be used.")
            return {"success": False, "error": "CapCutAPI not installed"}
        return func(*args, **kwargs)
    return wrapper

@require_capcut_api
def make_request(endpoint, data, method='POST'):
    """Send HTTP request to the server and handle the response"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    try:
        if method == 'POST':
            response = requests.post(url, data=json.dumps(data), headers=headers)
        elif method == 'GET':
            response = requests.get(url, params=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        response.raise_for_status()  # Raise an exception if the request fails
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except json.JSONDecodeError:
        print("Unable to parse server response")

@require_capcut_api
def get_font_types():
    """Get the list of available font types from the CapCut server"""
    try:
        return make_request("get_font_types", {}, method='GET')
    except Exception as e:
        print(f"Error getting font types: {e}")
        return {"success": False, "output": [], "error": str(e)}

@require_capcut_api
def add_audio_track(audio_url, start, end, target_start, volume=1.0, 
                    speed=1.0, track_name="main_audio", effect_type=None, effect_params=None, draft_id=None):
    """API call to add audio track"""
    data = {
        "audio_url": audio_url,
        "start": start,
        "end": end,
        "target_start": target_start,
        "volume": volume,
        "speed": speed,
        "track_name": track_name,
        "effect_type": effect_type,
        "effect_params": effect_params
    }
    
    if draft_id:
        data["draft_id"] = draft_id
        
    return make_request("add_audio", data)

@require_capcut_api
def add_text_impl(text, start, end, font, font_color, font_size, track_name,draft_folder="123", draft_id=None,
                  vertical=False, transform_x=0.5, transform_y=0.5, font_alpha=1.0,
                  border_color=None, border_width=0.0, border_alpha=1.0,
                  background_color=None, background_alpha=1.0, background_style=None,
                  bubble_effect_id=None, bubble_resource_id=None,
                  effect_effect_id=None, outro_animation=None):
    """API call to add text"""
    data = {
        "draft_folder": draft_folder,
        "text": text,
        "start": start,
        "end": end,
        "font": font,
        "color": font_color,
        "size": font_size,
        "alpha": font_alpha,
        "track_name": track_name,
        "vertical": vertical,
        "transform_x": transform_x,
        "transform_y": transform_y
    }
    
    # Add border parameters
    if border_color:
        data["border_color"] = border_color
        data["border_width"] = border_width
        data["border_alpha"] = border_alpha
    
    # Add background parameters
    if background_color:
        data["background_color"] = background_color
        data["background_alpha"] = background_alpha
        if background_style:
            data["background_style"] = background_style
    
    # Add bubble effect parameters
    if bubble_effect_id:
        data["bubble_effect_id"] = bubble_effect_id
        if bubble_resource_id:
            data["bubble_resource_id"] = bubble_resource_id
    
    # Add text effect parameters
    if effect_effect_id:
        data["effect_effect_id"] = effect_effect_id
    
    if draft_id:
        data["draft_id"] = draft_id
        
    if outro_animation:
        data["outro_animation"] = outro_animation
        
    return make_request("add_text", data)

@require_capcut_api
def add_image_impl(image_url, width, height, start, end, track_name, draft_id=None,
                  transform_x=0, transform_y=0, scale_x=1.0, scale_y=1.0, transition=None, transition_duration=None,
                  # New mask-related parameters
                  mask_type=None, mask_center_x=0.0, mask_center_y=0.0, mask_size=0.5,
                  mask_rotation=0.0, mask_feather=0.0, mask_invert=False,
                  mask_rect_width=None, mask_round_corner=None):
    """API call to add image"""
    data = {
        "image_url": image_url,
        "width": width,
        "height": height,
        "start": start,
        "end": end,
        "track_name": track_name,
        "transform_x": transform_x,
        "transform_y": transform_y,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "transition": transition,
        "transition_duration": transition_duration or 0.5,  # Default transition duration is 0.5 seconds
        # Add mask-related parameters
        "mask_type": mask_type,
        "mask_center_x": mask_center_x,
        "mask_center_y": mask_center_y,
        "mask_size": mask_size,
        "mask_rotation": mask_rotation,
        "mask_feather": mask_feather,
        "mask_invert": mask_invert,
        "mask_rect_width": mask_rect_width,
        "mask_round_corner": mask_round_corner
    }
    
    if draft_id:
        data["draft_id"] = draft_id
        
    return make_request("add_image", data)

@require_capcut_api
def generate_image_impl(prompt, width, height, start, end, track_name, draft_id=None,
                  transform_x=0, transform_y=0, scale_x=1.0, scale_y=1.0, transition=None, transition_duration=None):
    """API call to add image"""
    data = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "start": start,
        "end": end,
        "track_name": track_name,
        "transform_x": transform_x,
        "transform_y": transform_y,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "transition": transition,
        "transition_duration": transition_duration or 0.5  # Default transition duration is 0.5 seconds
    }
    
    if draft_id:
        data["draft_id"] = draft_id
        
    return make_request("generate_image", data)

@require_capcut_api
def add_sticker_impl(resource_id, start, end, draft_id=None, transform_x=0, transform_y=0,
                    alpha=1.0, flip_horizontal=False, flip_vertical=False, rotation=0.0,
                    scale_x=1.0, scale_y=1.0, track_name="sticker_main", relative_index=0,
                    width=1080, height=1920):
    """API call to add sticker"""
    data = {
        "sticker_id": resource_id,
        "start": start,
        "end": end,
        "transform_x": transform_x,
        "transform_y": transform_y,
        "alpha": alpha,
        "flip_horizontal": flip_horizontal,
        "flip_vertical": flip_vertical,
        "rotation": rotation,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "track_name": track_name,
        "relative_index": relative_index,
        "width": width,
        "height": height
    }
    
    if draft_id:
        data["draft_id"] = draft_id
        
    return make_request("add_sticker", data)

@require_capcut_api
def add_video_keyframe_impl(draft_id, track_name, property_type=None, time=None, value=None, 
                           property_types=None, times=None, values=None):
    """API call to add video keyframe
    
    Supports two modes:
    1. Single keyframe: using property_type, time, value parameters
    2. Batch keyframes: using property_types, times, values parameters (in list form)
    """
    data = {
        "draft_id": draft_id,
        "track_name": track_name
    }
    
    # Add single keyframe parameters (if provided)
    if property_type is not None:
        data["property_type"] = property_type
    if time is not None:
        data["time"] = time
    if value is not None:
        data["value"] = value
    
    # Add batch keyframe parameters (if provided)
    if property_types is not None:
        data["property_types"] = property_types
    if times is not None:
        data["times"] = times
    if values is not None:
        data["values"] = values
    
    return make_request("add_video_keyframe", data)

@require_capcut_api
def add_video_impl(video_url, start=None, end=None, width=None, height=None, track_name="main",
                   draft_id=None, transform_y=0, scale_x=1, scale_y=1, transform_x=0,
                   speed=1.0, target_start=0, relative_index=0, transition=None, transition_duration=None,
                   # Mask-related parameters
                   mask_type=None, mask_center_x=0.5, mask_center_y=0.5, mask_size=1.0,
                   mask_rotation=0.0, mask_feather=0.0, mask_invert=False,
                   mask_rect_width=None, mask_round_corner=None):
    """API call to add video track"""
    data = {
        "video_url": video_url,
        "height": height,
        "track_name": track_name,
        "transform_y": transform_y,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "transform_x": transform_x,
        "speed": speed,
        "target_start": target_start,
        "relative_index": relative_index,
        "transition": transition,
        "transition_duration": transition_duration or 0.5,  # Default transition duration is 0.5 seconds
        # Mask-related parameters
        "mask_type": mask_type,
        "mask_center_x": mask_center_x,
        "mask_center_y": mask_center_y,
        "mask_size": mask_size,
        "mask_rotation": mask_rotation,
        "mask_feather": mask_feather,
        "mask_invert": mask_invert,
        "mask_rect_width": mask_rect_width,
        "mask_round_corner": mask_round_corner
    }
    if draft_id:
        data['draft_id'] = draft_id
    if start:
        data["start"] = start
    if end:
        data["end"] = end
    if width:
        data["width"] = width
    if height:
        data["height"] = height
    return make_request("add_video", data)

@require_capcut_api
def add_effect(effect_type, start, end, draft_id=None, track_name="effect_01",
              params=None, width=1080, height=1920):
    """API call to add effect"""
    data = {
        "effect_type": effect_type,
        "start": start,
        "end": end,
        "track_name": track_name,
        "params": params or [],
        "width": width,
        "height": height
    }
    
    if draft_id:
        data["draft_id"] = draft_id
        
    return make_request("add_effect", data)

@require_capcut_api
def create_draft(width, height, draft_id=None):
    """API call to create a new draft"""
    data = {
        "width": width,
        "height": height
    }
    
    if draft_id:
        data["draft_id"] = draft_id
        
    return make_request("create_draft", data)

@require_capcut_api
def add_subtitle(srt, track_name="subtitle_main", draft_id=None, font_size=8, 
                font = None,
                font_color="#FFFFFF", border_color=None, border_width=0, transform_y=0):
    """API call to add subtitle from SRT file"""
    data = {
        "srt": srt,
        "track_name": track_name,
        "font_size": font_size,
        "font_color": font_color,
        "transform_y": transform_y
    }
    
    if font:
        data["font"] = font

    if border_color:
        data["border_color"] = border_color
        data["border_width"] = border_width
    
    if draft_id:
        data["draft_id"] = draft_id
        
    return make_request("add_subtitle", data)

@require_capcut_api
def save_draft(draft_id, draft_folder):
    """API call to save draft to specified folder"""
    data = {
        "draft_id": draft_id,
        "draft_folder": draft_folder
    }
    
    return make_request("save_draft", data)
