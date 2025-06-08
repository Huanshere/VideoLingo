import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))#补充当前文件的父目录到系统路径
from core.ask_gpt import ask_gpt
import re
from pathlib import Path
from core.prompts_storage import get_title_introduction_prompt
import pandas as pd
from rich import print as rprint
import json
import shutil

def clean_srt_date(srt_date):
    pass

#### 为了提高主页的CTR，需要手动优化标题前缀
prefix_base_dir = '麻省理工分布式系统-'
###
     
def read_all_trans_srt():
    '''
    need move to root path 
    '''
    rprint(f"[yellow]read the srt from the output folder....[/yellow]")
    all_trans_str=[]
    print(os.path.dirname(__file__))
    base_path = Path(os.path.dirname(__file__)).parent  / 'output' 
    # 获取所有Lecture文件夹并按数字排序
    lecture_folders = [f for f in base_path.iterdir() if f.is_dir() and f.name.startswith("Lecture")]
    lecture_folders.sort(key=lambda x: int(re.search(r'Lecture (\d+)', x.name).group(1)))
    
    # 按顺序读取每个trans.srt文件
    for folder in lecture_folders:
        trans_file = folder / "trans.srt"
        if trans_file.exists():
            with open(trans_file, 'r', encoding='utf-8') as f:
                content = str(trans_file.parent) + '||' + str(trans_file.parent.name) + '||' + f.read()
                print(content)
                all_trans_str.append(content)   
    rprint(f"[green]🎉 read the all srt {len(all_trans_str)} from the output folder completed![/green]")
    rprint(f"[green]=================================================[/green]")
    rprint(f"[green]{all_trans_str}[/green]")
    rprint(f"[green]=================================================[/green]")
    return all_trans_str


def copy_and_rename_videos(responses, result_dir_path):
    """
    根据生成的标题，复制并重命名视频文件
    
    Args:
        responses: 包含file_path和title的字典列表
        result_dir_path: 目标目录路径 (字符串或Path对象)
    
    Returns:
        tuple: (成功数量, 总数量)
    """
    rprint(f"[yellow]start copy and rename videos....[/yellow]")
    # 创建result目录
    result_dir = Path(result_dir_path)
    result_dir.mkdir(exist_ok=True)
    
    total_count = len(responses)
    rprint(f"[yellow]start copy and rename videos....[/yellow]")
    for i, response in enumerate(responses, 1):
        file_path = response.get('file_path', '')
        title = response.get('title', f'unknown_{i}')
        
        rprint(f"[yellow]🌐 processing {i+1}/{total_count}[/yellow]")
        # 构建源文件路径
        source_video = Path(file_path) / 'output_sub.mp4'
        
        if source_video.exists():
            # 清理标题作为新文件名
            new_filename = f"{prefix_base_dir} + {title}.mp4"
            target_path = result_dir / new_filename
            
            try:
                # 复制文件
                shutil.copy2(source_video, target_path)
            except Exception as e:
                rprint(f"[red]❌ 复制失败: {e}[/red]")
        else:
            rprint(f"[red]⚠️ 源文件不存在: {source_video}[/red]")
    

# 根据当前output的目录中的简介调用大模型
# 批量生成视频的标题和简介
def get_tasks_setting_info():
     base_path = Path(os.path.dirname(__file__)).parent / 'tasks_setting.xlsx'
     df = pd.read_excel(base_path)
     return df

def json_valid(response_data):
        try:
            json.loads(response_data)
            return response_data
        except (json.JSONDecodeError, ValueError):
            return "{'title':'error', 'introduction':'error'}"
        
def get_title_introduction_batch():
        responses = []
        all_trans_srt =read_all_trans_srt()

        trans_srt_len = len(all_trans_srt)
        for i in range(trans_srt_len):
            trans_srt = all_trans_srt[i]
            rprint(f"[yellow]🌐 processing {i}/{trans_srt_len}[/yellow]")
            prompt = get_title_introduction_prompt(trans_srt);
            try:    
                response = ask_gpt(prompt, response_json=True, log_title='subtitle_trim')      
                responses.append(response)
                rprint(f"[yellow]{responses[-1]}[/yellow]")
            except Exception as e:
                print(f"Error: {e}")
        flat_responses = []
        # 去除responses数组中的空字符串元素
        for item in responses:
            if isinstance(item, list):
                # 如果是列表，展开里面的字典
                flat_responses.extend(item)
            elif isinstance(item, dict):
                # 如果是字典，直接添加
                flat_responses.append(item)

        responses = flat_responses
        rprint(f"[green]=================================================[/green]")
        rprint(f"[green]🎉 responses:[/green]")
        rprint(responses)
        rprint("[green]🎉 All processing completed![/green]")

        base_path = Path(os.path.dirname(__file__)).parent   
        
        tasks_setting_info = get_tasks_setting_info()
        
        copy_and_rename_videos(responses, base_path / 'result') 
        # 将 responses JSON 数组转换成 DataFrame
        responses_df = pd.DataFrame(responses)
        result_df = pd.concat([tasks_setting_info, responses_df], axis=1)
        result_df.to_excel(base_path / 'result.xlsx' , index=False, engine='openpyxl')
        




if __name__ == "__main__":
    get_title_introduction_batch()