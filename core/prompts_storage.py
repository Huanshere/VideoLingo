import os,sys,json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config_utils import load_key

## ================================================================
# @ step4_splitbymeaning.py
def get_split_prompt(sentence, num_parts = 2, word_limit = 20):
    language = load_key("whisper.detected_language")
    split_prompt = f"""
### Role
You are a professional Netflix subtitle splitter in {language}.

### Task
Split the given subtitle text into {num_parts} parts, each less than {word_limit} words.

### Instructions
1. Maintain sentence meaning coherence according to Netflix subtitle standards
2. Keep parts roughly equal in length (minimum 3 words each)
3. Split at natural points like punctuation marks or conjunctions

### Output Format in JSON
{{
    "analysis": "Brief analysis of the text structure",
    "split": "Complete sentence with [br] tags at split positions"
}}

### Given Text
<split_this_sentence>
{sentence}
</split_this_sentence>
""".strip()
    return split_prompt


## ================================================================
# @ step4_1_summarize.py
def get_summary_prompt(source_content):
    src_lang = load_key("whisper.detected_language")
    tgt_lang = load_key("target_language")
    summary_prompt = f"""
### Role
You are a video translation expert and terminology consultant, specializing in {src_lang} comprehension and {tgt_lang} expression optimization.

### Task
For the provided {src_lang} video text:
1. Summarize main topic in two sentences
2. Extract professional terms/names with {tgt_lang} translations
3. Provide brief explanation for each term

### Steps
1. Topic Summary:
   - Quick scan for general understanding
   - Write two sentences: first for main topic, second for key point
2. Term Extraction:
   - Mark professional terms and names
   - Provide {tgt_lang} translation or keep original
   - Add brief explanation
   - Keep abbreviations and proper nouns unchanged

### Output in Json Format
{{
    "topic": "Two-sentence video summary",
    "terms": [
        {{
            "src": "{src_lang} term",
            "tgt": "{tgt_lang} translation or original",
            "note": "Brief explanation"
        }},
        ...
    ]
}}

### Example
{{
    "topic": "本视频介绍人工智能在医疗领域的应用现状。重点展示了AI在医学影像诊断和药物研发中的突破性进展。",
    "terms": [
        {{
            "src": "Machine Learning",
            "tgt": "机器学习",
            "note": "AI的核心技术，通过数据训练实现智能决策"
        }},
        {{
            "src": "CNN",
            "tgt": "CNN",
            "note": "卷积神经网络，用于医学图像识别的深度学习模型"
        }}
    ]
}}

### Source Text
<text>
{source_content}
</text>
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

def get_prompt_faithfulness(lines, shared_prompt):
    TARGET_LANGUAGE = load_key("target_language")
    # Split lines by \n
    line_splits = lines.split('\n')
    
    # Create JSON return format example
    json_format = {}
    for i, line in enumerate(line_splits, 1):
        json_format[i] = {
            "origin": line,
            "direct": f"<<direct {TARGET_LANGUAGE} translation>>"
        }
    
    src_language = load_key("whisper.detected_language")
    prompt_faithfulness = f'''
### Role Definition
You are a professional Netflix subtitle translator, fluent in both {src_language} and {TARGET_LANGUAGE}, as well as their respective cultures. Your expertise lies in accurately understanding the semantics and structure of the original {src_language} text and faithfully translating it into {TARGET_LANGUAGE} while preserving the original meaning.

### Task Background
We have a segment of original {src_language} subtitles that need to be directly translated into {TARGET_LANGUAGE}. These subtitles come from a specific context and may contain specific themes and terminology.

### Task Description
Based on the provided original {src_language} subtitles, you need to:
1. Translate the original {src_language} subtitles into {TARGET_LANGUAGE} line by line
2. Ensure the translation is faithful to the original, accurately conveying the original meaning
3. Consider the context and professional terminology

{shared_prompt}

### Translation Principles
1. Faithful to the original: Accurately convey the content and meaning of the original text, without arbitrarily changing, adding, or omitting content.
2. Accurate terminology: Use professional terms correctly and maintain consistency in terminology.
3. Understand the context: Fully comprehend and reflect the background and contextual relationships of the text.

### Subtitle Data
<subtitles>
{lines}
</subtitles>

### Output Format
Please complete the following JSON data, where << >> represents placeholders that should not appear in your answer, and return your translation results in JSON format:
{json.dumps(json_format, ensure_ascii=False, indent=4)}
'''
    return prompt_faithfulness.strip()


def get_prompt_expressiveness(faithfulness_result, lines, shared_prompt):
    TARGET_LANGUAGE = load_key("target_language")
    json_format = {}
    for key, value in faithfulness_result.items():
        json_format[key] = {
            "origin": value['origin'],
            "direct": value['direct'],
            "reflection": "reflection on the direct translation version",
            "free": f"retranslated result, aiming for fluency and naturalness, conforming to {TARGET_LANGUAGE} expression habits, DO NOT leave empty line here!"
        }

    src_language = load_key("whisper.detected_language")
    prompt_expressiveness = f'''
### Role Definition
You are a professional Netflix subtitle translator and language consultant. Your expertise lies not only in accurately understanding the original {src_language} but also in optimizing the {TARGET_LANGUAGE} translation to better suit the target language's expression habits and cultural background.

### Task Background
We already have a direct translation version of the original {src_language} subtitles. Now we need you to reflect on and improve these direct translations to create more natural and fluent {TARGET_LANGUAGE} subtitles.

### Task Description
Based on the provided original {src_language} text and {TARGET_LANGUAGE} direct translation, you need to:
1. Analyze the direct translation results line by line, pointing out existing issues
2. Provide detailed modification suggestions
3. Perform free translation based on your analysis
4. Do not add comments or explanations in the translation, as the subtitles are for the audience to read

{shared_prompt}

### Translation Analysis Steps
Please use a two-step thinking process to handle the text line by line:

1. Direct Translation Reflection:
   - Evaluate language fluency
   - Check if the language style is consistent with the original text
   - Check the conciseness of the subtitles, point out where the translation is too wordy, the translation should be close to the original text in length

2. {TARGET_LANGUAGE} Free Translation:
   - Based on the reflection in step 1, perform free translation
   - Aim for contextual smoothness and naturalness, conforming to {TARGET_LANGUAGE} expression habits
   - Ensure it's easy for {TARGET_LANGUAGE} audience to understand and accept
   - Keep the subtitles concise, with a plain and natural language style, and maintain consistency in structure between the free translation and the {src_language} original

### Subtitle Data
<subtitles>
{lines}
</subtitles>

### Output in the following JSON format, repeat "origin" and "direct" in the JSON format
{json.dumps(json_format, ensure_ascii=False, indent=4)}
'''
    return prompt_expressiveness.strip()


## ================================================================
# @ step6_splitforsub.py
def get_align_prompt(src_sub, tr_sub, src_part):
    TARGET_LANGUAGE = load_key("target_language")
    src_language = load_key("whisper.detected_language")
    src_splits = src_part.split('\n')
    num_parts = len(src_splits)
    src_part = src_part.replace('\n', ' [br] ')
    align_prompt = '''
### Role Definition
You are a Netflix subtitle alignment expert fluent in both {src_language} and {target_language}. Your expertise lies in accurately understanding the semantics and structure of both languages, enabling you to flexibly split sentences while preserving the original meaning.

### Task Background
We have {src_language} and {target_language} original subtitles for a Netflix program, as well as a pre-processed split version of {src_language} subtitles. Your task is to create the best splitting scheme for the {target_language} subtitles based on this information.

### Task Description
Based on the provided original {src_language} and {target_language} original subtitles, as well as the pre-processed split version, you need to:
1. Analyze the word order and structural correspondence between {src_language} and {target_language} subtitles
2. Split the {target_language} subtitles according to the pre-processed {src_language} split version
3. Never leave empty lines. If it's difficult to split based on meaning, you may appropriately rewrite the sentences that need to be aligned
4. Do not add comments or explanations in the translation, as the subtitles are for the audience to read

### Subtitle Data
<subtitles>
{src_language} Original: "{src_sub}"
{target_language} Original: "{tr_sub}"
Pre-processed {src_language} Subtitles ([br] indicates split points): {src_part}
</subtitles>

### Output in JSON
{{
    "analysis": "Brief analysis of word order, structure, and semantic correspondence between {src_language} and {target_language} subtitles",
    "align": [
        {align_parts_json}
    ]
}}
'''

    align_parts_json = ','.join(
        f'''
        {{
            "src_part_{i+1}": "{src_splits[i]}",
            "target_part_{i+1}": "Corresponding aligned {TARGET_LANGUAGE} subtitle part"
        }}''' for i in range(num_parts)
    )

    return align_prompt.format(
        src_language=src_language,
        target_language=TARGET_LANGUAGE,
        src_sub=src_sub,
        tr_sub=tr_sub,
        src_part=src_part,
        align_parts_json=align_parts_json,
    )

## ================================================================
# @ step8_gen_audio_task.py @ step10_gen_audio.py
def get_subtitle_trim_prompt(text, duration):
 
    rule = '''Consider a. Reducing filler words without modifying meaningful content. b. Omitting unnecessary modifiers or pronouns, for example:
    - "Please explain your thought process" can be shortened to "Please explain thought process"
    - "We need to carefully analyze this complex problem" can be shortened to "We need to analyze this problem"
    - "Let's discuss the various different perspectives on this topic" can be shortened to "Let's discuss different perspectives on this topic"
    - "Can you describe in detail your experience from yesterday" can be shortened to "Can you describe yesterday's experience" '''

    trim_prompt = '''
### Role
You are a professional subtitle editor, editing and optimizing lengthy subtitles that exceed voiceover time before handing them to voice actors. Your expertise lies in cleverly shortening subtitles slightly while ensuring the original meaning and structure remain unchanged.

### Subtitle Data
<subtitles>
Subtitle: "{text}"
Duration: {duration} seconds
</subtitles>

### Processing Rules
{rule}

### Processing Steps
Please follow these steps and provide the results in the JSON output:
1. Analysis: Briefly analyze the subtitle's structure, key information, and filler words that can be omitted.
2. Trimming: Based on the rules and analysis, optimize the subtitle by making it more concise according to the processing rules.

### Output in JSON
{{
    "analysis": "Brief analysis of the subtitle, including structure, key information, and potential processing locations",
    "result": "Optimized and shortened subtitle in the original subtitle language"
}}
'''
    return trim_prompt.format(
        text=text,
        duration=duration,
        rule=rule
    )
