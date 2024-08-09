import json

## ================================================================
# @ step4_splitbymeaning.py
def get_split_prompt(sentence, num_parts = 2, word_limit = 20):
    # ! only support num_parts = 2
    split_prompt = f"""
### Role
You are a professional and experienced Netflix subtitle splitter.

### Task
Your task is to split the given English subtitle text into **{num_parts}** parts, each should be less than {word_limit} words.

### Requirements
1. Try to maintain the coherence of the sentence meaning, split according to Netflix subtitle standards, ensuring the two parts are relatively independent.
2. The length of each part should be roughly equal, no part should be less than 3 words, but the integrity of the sentence is more important.
3. Prioritize splitting at punctuation marks, such as periods, commas, and conjunctions (e.g., "and", "but", "because", "when", "then", "if", "so", "that").

### Steps
1. Analyze the grammar and structure of the given text.
2. Provide 3 different ways to split the text, each with different split points, output complete sentences (do not change any letters or punctuation), insert [br] tags at the split positions.
3. Briefly compare and evaluate the above 3 split methods, considering readability, grammatical structure, and contextual coherence, choose the best split method.
4. Give the best split method number, 1, 2, or 3.

### Output Format
Please provide your answer in the following JSON format, <<>> represents placeholders:
{{
    "analysis": "Brief analysis of the text structure and split strategy",
    "split_way_1": "<<The first split method, output complete sentences, insert [br] as a delimiter at the split position. e.g. this is the first part [br] this is the second part.>>",
    "split_way_2": "<<The second split method>>",
    "split_way_3": "<<The third split method>>",
    "evaluation": "<<Unified brief evaluation of the 3 split methods, written in one sentence, no line breaks>>",
    "best_way": "<<The best split method number, 1, 2, or 3>>"
}}

### Given Text
<split_this_sentence>\n{sentence}\n</split_this_sentence>

""".strip()

    return split_prompt


## ================================================================
# @ step4_1_summarize.py
def get_summary_prompt(English_content, target_language):
    summary_prompt = f"""
### 角色
你是一位专业的英语视频翻译专家和术语顾问。你的专业不仅在于准确理解英语原文,还在于提取关键专业术语,优化译文以更符合{target_language}的表达习惯和文化背景。

### 任务背景
我们需要翻译一些英语视频,其中可能包含一些专业术语。为了确保翻译的准确性和专业性,我们需要你的帮助。

### 任务描述 
对于提供的英语视频文本,你需要:
1. 用一句话概括视频的主题
2. 提取视频中出现的专业术语,并提供{target_language}翻译或建议保留英文术语。避免提取简单、常见的词汇。
3. 对每个翻译的术语,给出简要解释

### 分析和总结步骤
请分两步思考,逐行处理文本:  
1. 主题概括:
   - 快速浏览全文,了解大意
   - 用一句简洁的话概括主题
2. 术语提取:
   - 仔细阅读全文,标记专业术语
   - 对每个术语,提供{target_language}翻译或建议保留英文,只需单词本身,不需要读音
   - 为每个术语添加简要解释,帮助译者理解
   - 如果该词为英文缩写,请保留英文。

### 输出格式
请按以下JSON格式输出你的分析结果,其中<>表示占位符:
{{
    "theme": "<简要概括这个视频的主题,用1句话表示>",
    "terms": [
        {{
            "original": "<英文术语1>",
            "translation": "<{target_language}翻译或保留英文>",
            "explanation": "<术语简要解释>"
        }},
        {{
            "original": "<英文术语2>",
            "translation": "<{target_language}翻译或保留英文>",
            "explanation": "<术语简要解释>"
        }},
        ...
    ]
}}

### 单次输出示例( 以法语为例 )

{{
    "theme": "Ce vidéo résume le musée du Louvre à Paris.",
    "terms": [
        {{
            "original": "Mona Lisa",
            "translation": "La Joconde",
            "explanation": "Le tableau le plus célèbre du Louvre, un portrait de Léonard de Vinci"
        }},
        {{
            "original": "pyramid",
            "translation": "la pyramide",
            "explanation": "Une grande structure en verre et métal en forme de pyramide située à l'entrée principale du Louvre"
        }},
        ...
    ]
}}

### 需要处理的视频文本数据
<video_text_to_summarize>
{English_content}
</video_text_to_summarize>
""".strip()

    return summary_prompt

## ================================================================
# @ step5_translate.py & translate_lines.py

def generate_shared_prompt(previous_content_prompt, after_content_prompt, summary_prompt, things_to_note_prompt):
    return f'''### Context Information
<previous_content>
{previous_content_prompt}
</previous_content>

<subsequent_content>
{after_content_prompt}
</subsequent_content>

### Content Summary
{summary_prompt}

### Points to Note
{things_to_note_prompt}'''



def get_prompt_faithfulness(lines, shared_prompt, target_language = '简体中文'):
    # 按 \n 分割行
    line_splits = lines.split('\n')
    
    # 创建 JSON 返回格式示例
    json_format = {}
    for i, line in enumerate(line_splits, 1):
        json_format[i] = {
            "Original English": line,
            "Direct Translation": f"<<your direct {target_language} translation>>"
        }
    
    prompt_faithfulness = f'''
### 角色定义
你是一位专业的 Netflix 英文字幕翻译专家,精通英语和{target_language}两种语言和文化。你的专长在于准确理解英文原文的语义和结构,并能够忠实地将其翻译成{target_language},同时保持原意。

### 任务背景
我们有一段英文字幕需要直接翻译成{target_language}。这些字幕来自特定的上下文,可能包含特定的主题和术语。

### 任务描述
根据提供的英文字幕,你需要:
1. 逐行将英文字幕翻译成{target_language}
2. 确保翻译忠实于原文,准确传达原意
3. 考虑上下文和专业术语

{shared_prompt}

### 翻译原则
1. 忠于原文:准确传达原文的内容和意思,不要随意更改、添加或省略原文内容。
2. 术语准确:正确使用专业术语,保持术语一致性。
3. 理解语境:充分理解并体现文本的背景和上下文关系。

### 字幕数据
<subtitles>
{lines}
</subtitles>

### 输出格式
请完成以下 JSON 数据,其中 << >> 表示占位符不要出现在你的回答中,用 JSON 格式返回你的翻译结果:
{json.dumps(json_format, ensure_ascii=False, indent=4)}
'''
    return prompt_faithfulness.strip()



def get_prompt_expressiveness(faithfulness_result, lines, shared_prompt, target_language):
    json_format = {}
    for key, value in faithfulness_result.items():
        json_format[key] = {
            "Original English": value['Original English'],
            "Direct Translation": value['Direct Translation'],
            "Translation Reflection": "<<针对直译版本的具体问题,尽可能详尽>>",
            "Free Translation": "<<重新翻译的结果,追求流畅自然,符合{target_language}表达习惯>>"
        }

    prompt_expressiveness = f'''
### 角色定义
你是一名专业的 Netflix 英文字幕翻译专家和语言顾问。你的专长不仅在于准确理解英文原文,还在于优化{target_language}翻译,使之更符合目标语言的表达习惯和文化背景。

### 任务背景
我们已经有了英文字幕的直译版本,现在需要你反思并改进这些直译,创作出更自然流畅的{target_language}字幕。

### 任务描述  
根据提供的英文原文和{target_language}直译版本,你需要:
1. 逐行分析直译结果,指出存在的问题
2. 提供详细的修改建议
3. 在分析的基础上进行自由翻译

{shared_prompt}

### 分析翻译步骤
请用两步思考方式,逐行处理文本:

1. 直译反思:
   - 检查翻译准确性
   - 评估语言流畅度  
   - 检查语言风格是否与原文一致
   - 检查字幕的简洁性，指出翻译过于冗长的地方

2. {target_language} 自由翻译:
   - 在步骤1反思的基础上,进行自由翻译
   - 追求上下文通顺自然,符合{target_language}表达习惯
   - 确保{target_language}观众易于理解和接受
   - 保持字幕简洁,语言风格平实自然,自由翻译和英文原文结构一致

### 字幕数据  
<subtitles>
{lines}
</subtitles>

### 输出格式
请完成以下 JSON 数据,其中 << >> 表示占位符不要出现在你的回答中,并用 JSON 格式返回你的翻译结果:
{json.dumps(json_format, ensure_ascii=False, indent=4)}
'''
    return prompt_expressiveness.strip()


## ================================================================
# @ step6_splitforsub.py
def get_align_prompt(en_original, target_original, en_part, target_language = '简体中文'):
    en_splits = en_part.split('\n')
    num_parts = len(en_splits)
    en_part = en_part.replace('\n', ' [br] ')
    align_prompt = '''
### 角色定义
你是一位精通英语和{target_language}的Netflix字幕对齐专家。你的专长在于准确理解两种语言的语义和结构,能够灵活地分割句子同时保持原意。

### 任务背景
我们有一个Netflix节目的英语和{target_language}原始字幕,以及预处理过的英语字幕分割版本。你的任务是基于这些信息,为{target_language}字幕创建最佳的分割方案。

### 任务描述
基于提供的英语和{target_language}原始字幕以及预处理的英语分割版本,你需要:
1. 分析英语和{target_language}字幕之间的词序和结构对应关系
2. 为{target_language}字幕提供 3 种不同的分割方案
3. 评估这些方案并选择最佳方案
4. 绝不留下空行。如果难以基于意义进行分割,你可以适当地重写需要对齐的句子

### 字幕数据
<subtitles>
英语原文: "{en_original}"
{target_language}原文: "{target_original}"
预处理英语 ( [br] 表示分割点): {en_part}
</subtitles>

### 处理步骤
请按照以下步骤处理,并在JSON输出中提供每个步骤的结果:
1. 分析和比较:简要分析英语和{target_language}字幕之间的词序、句子结构和语义对应关系。指出关键词对应、句型的异同,以及可能影响分割的语言特征。
2. 开始对齐:根据你的分析,按照格式提供 3 种不同的{target_language}字幕对齐方式, 其中英文的分割位置要和预处理的英文分割版本一致，不能擅自更改。
3. 评估和选择:检查并简要评估 3 种方案,考虑句子完整性、语义连贯性和分割点的适当性等因素。
4. 最佳方案:选择最佳对齐方案,只输出单个数字,1 or 2 or 3.

### 输出格式
请完成以下JSON数据,其中 << >> 表示占位符,并用JSON格式返回你的结果:
{{
    "analysis": "<<对英语和{target_language}字幕之间的词序、结构和语义对应关系的详细分析>>",
    "align_way_1": [
        {align_parts_json}
    ],
    "align_way_2": [
        {align_parts_json}
    ],
    "comparison": "<<对 3 种对齐方案的简要评估和比较>>",
    "best_way": "<<最佳对齐方案的编号,1 or 2 or 3>>"
}}
'''

    align_parts_json = ','.join(
        f'''
        {{
            "en_part_{i+1}": "<<{en_splits[i]}>>",
            "target_part_{i+1}": "<<对应的对齐{target_language}字幕部分>>"
        }}''' for i in range(num_parts)
    )

    return align_prompt.format(
        en_original=en_original,
        target_original=target_original,
        en_part=en_part,
        align_parts_json=align_parts_json,
        target_language=target_language
    )

## ================================================================
# @ step9_generate_audio_task.py @ step10_generate_audio.py
def get_subtitle_trim_prompt(trans_text, duration, fierce_mode = False):
    if not fierce_mode:
        rule = '仅仅考虑 a. 将逗号替换为空格，以减少停顿时间。b. 缩减语气词，不要修改有意义的内容。 c. 省略不必要的定语或代词例如"请解释你的思路"可以缩减为"请解释思路"'
    else:
        rule = '考虑 a. 将逗号替换为空格，缩减语气词,以减少停顿时间。b. 精简字幕中不重要的连接词和定语和代词，同时保留所有的句子结构。例如：“假设我们是过于理想化的物理学家,假设没有摩擦,所有碰撞都是完美的弹性碰撞”改为：“假设我们是理想化的物理学家 没有摩擦 所有碰撞都是弹性碰撞”'

    trim_prompt = '''
### 角色定义
你是一位专业的字幕编辑员，再把字幕交给配音员之前对字幕进行编辑和优化。你的专长在于巧妙地精简字幕，但一定要保持原有的意思完整。

### 字幕数据
<subtitles>
字幕: "{trans_text}"
持续时间: {duration} 秒
</subtitles>

### 处理规则
{rule}

### 处理步骤
请按照以下步骤处理，并在JSON输出中提供结果：
1. 分析：简要分析字幕的结构、关键信息和可能逗号替换为空格的位置，以及可以省略的语气词。
2. 裁剪：根据规则和分析，对字幕进行优化，按照处理规则缩短字幕。

### 输出格式
请完成以下JSON数据，其中 << >> 表示需要你填写的内容：
{{
    "analysis": "<<对字幕的简要分析，包括结构、关键信息和可能的处理位置>>",
    "trans_text_processed": "<<优化缩短后的字幕>>"
}}
'''
    return trim_prompt.format(
        trans_text=trans_text,
        duration=duration,
        rule=rule
    )