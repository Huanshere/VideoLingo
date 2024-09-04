import os,sys,json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.step2_whisperapi import get_whisper_language
## ================================================================
# @ step4_splitbymeaning.py
def get_split_prompt(sentence, num_parts = 2, word_limit = 20):
    # ! only support num_parts = 2
    language = get_whisper_language()
    split_prompt = f"""
### Role
You are a professional and experienced Netflix subtitle splitter in {language}.

### Task
Your task is to split the given subtitle text into **{num_parts}** parts, each should be less than {word_limit} words.

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
def get_summary_prompt(source_content):
    src_language = get_whisper_language()
    from config import TARGET_LANGUAGE
    summary_prompt = f"""
### Role
You are a professional video translation expert and terminology consultant. Your expertise lies not only in accurately understanding the original {src_language} text but also in extracting key professional terms and optimizing the translation to better suit the expression habits and cultural background of {TARGET_LANGUAGE}.

### Task Description 
For the provided original {src_language} video text, you need to:
1. Summarize the video's main topic in one sentence
2. Extract professional terms that appear in the video, and provide {TARGET_LANGUAGE} translations or suggest keeping the original language terms. Avoid extracting simple, common words.
3. For each translated term, provide a brief explanation

### Analysis and Summary Steps
Please think in two steps, processing the text line by line:  
1. Topic summarization:
   - Quickly skim through the entire text to understand the general idea
   - Summarize the topic in one concise sentence
2. Term extraction:
   - Carefully read the entire text, marking professional terms
   - For each term, provide a {TARGET_LANGUAGE} translation or suggest keeping the original, only the word itself is needed, not the pronunciation
   - Add a brief explanation for each term to help the translator understand
   - If the word is a fixed abbreviation, please keep the original.

### Output Format
Please output your analysis results in the following JSON format, where <> represents placeholders:
{{
    "theme": "<Briefly summarize the theme of this video in 1 sentence>",
    "terms": [
        {{
            "original": "<Term 1 in the {src_language}>",
            "translation": "<{TARGET_LANGUAGE} translation or keep original>",
            "explanation": "<Brief explanation of the term>"
        }},
        {{
            "original": "<Term 2 in the {src_language}>",
            "translation": "<{TARGET_LANGUAGE} translation or keep original>",
            "explanation": "<Brief explanation of the term>"
        }},
        ...
    ]
}}

### Single Output Example (Using French as an example)

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

### Video text data to be processed
<video_text_to_summarize>
{source_content}
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

def get_prompt_faithfulness(lines, shared_prompt):
    from config import TARGET_LANGUAGE
    # Split lines by \n
    line_splits = lines.split('\n')
    
    # Create JSON return format example
    json_format = {}
    for i, line in enumerate(line_splits, 1):
        json_format[i] = {
            "Original Subtitle": line,
            "Direct Translation": f"<<direct {TARGET_LANGUAGE} translation>>"
        }
    
    src_language = get_whisper_language()
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
    from config import TARGET_LANGUAGE
    json_format = {}
    for key, value in faithfulness_result.items():
        json_format[key] = {
            "Original Subtitle": value['Original Subtitle'],
            "Direct Translation": value['Direct Translation'],
            "Translation Reflection": "<<reflection on the direct translation version>>",
            "Free Translation": f"<<retranslated result, aiming for fluency and naturalness, conforming to {TARGET_LANGUAGE} expression habits>>"
        }

    src_language = get_whisper_language()
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

### Output Format
Please complete the following JSON data, where << >> represents placeholders that should not appear in your answer, and return your translation results in JSON format:
{json.dumps(json_format, ensure_ascii=False, indent=4)}
'''
    return prompt_expressiveness.strip()


## ================================================================
# @ step6_splitforsub.py
def get_align_prompt(src_sub, tr_sub, src_part):
    from config import TARGET_LANGUAGE
    src_language = get_whisper_language()
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
2. Provide 3 different splitting schemes for the {target_language} subtitles
3. Evaluate these schemes and select the best one
4. Never leave empty lines. If it's difficult to split based on meaning, you may appropriately rewrite the sentences that need to be aligned

### Subtitle Data
<subtitles>
{src_language} Original: "{src_sub}"
{target_language} Original: "{tr_sub}"
Pre-processed {src_language} Subtitles ([br] indicates split points): {src_part}
</subtitles>

### Processing Steps
Please follow these steps and provide the results for each step in the JSON output:
1. Analysis and Comparison: Briefly analyze the word order, sentence structure, and semantic correspondence between {src_language} and {target_language} subtitles. Point out key word correspondences, similarities and differences in sentence patterns, and language features that may affect splitting.
2. Start Alignment: Based on your analysis, provide 3 different alignment methods for {target_language} subtitles according to the format. The split positions in {src_language} must be consistent with the pre-processed {src_language} split version and cannot be changed arbitrarily.
3. Evaluation and Selection: Examine and briefly evaluate the 3 schemes, considering factors such as sentence completeness, semantic coherence, and appropriateness of split points.
4. Best Scheme: Select the best alignment scheme, output only a single number, 1 or 2 or 3.

### Output Format
Please complete the following JSON data, where << >> represents placeholders, and return your results in JSON format:
{{
    "analysis": "<<Detailed analysis of word order, structure, and semantic correspondence between {src_language} and {target_language} subtitles>>",
    "align_way_1": [
        {align_parts_json}
    ],
    "align_way_2": [
        {align_parts_json}
    ],
    "comparison": "<<Brief evaluation and comparison of the 3 alignment schemes>>",
    "best_way": "<<Number of the best alignment scheme, 1 or 2 or 3>>"
}}
'''

    align_parts_json = ','.join(
        f'''
        {{
            "src_part_{i+1}": "<<{src_splits[i]}>>",
            "target_part_{i+1}": "<<Corresponding aligned {TARGET_LANGUAGE} subtitle part>>"
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
# @ step9_generate_audio_task.py @ step10_generate_audio.py
def get_subtitle_trim_prompt(trans_text, duration, fierce_mode = False):
    src_language = get_whisper_language()
    if not fierce_mode:
        rule = 'Only consider a. Replacing commas with spaces to reduce pause time. b. Reducing filler words without modifying meaningful content. c. Omitting unnecessary modifiers or pronouns, for example "Please explain your thought process" can be shortened to "Please explain thought process"'
    else:
        rule = 'Consider a. Replacing commas with spaces, reducing filler words to decrease pause time. b. Streamlining unimportant conjunctions, modifiers, and pronouns in the subtitle while preserving all sentence structures. For example: "Suppose we are overly idealistic physicists, assume there is no friction, all collisions are perfectly elastic" can be changed to: "Suppose we are idealistic physicists no friction all collisions are elastic"'

    trim_prompt = '''
### Role Definition
You are a professional {src_language} subtitle editor, editing and optimizing subtitles before handing them over to voice actors. Your expertise lies in cleverly condensing subtitles while ensuring the original meaning remains intact.

### Subtitle Data
<subtitles>
Subtitle: "{trans_text}"
Duration: {duration} seconds
</subtitles>

### Processing Rules
{rule}

### Processing Steps
Please follow these steps and provide the results in the JSON output:
1. Analysis: Briefly analyze the subtitle's structure, key information, potential locations for replacing commas with spaces, and filler words that can be omitted.
2. Trimming: Based on the rules and analysis, optimize the subtitle by shortening it according to the processing rules.

### Output Format
Please complete the following JSON data, where << >> represents content you need to fill in:
{{
    "analysis": "<<Brief analysis of the subtitle, including structure, key information, and potential processing locations>>",
    "trans_text_processed": "<<Optimized and shortened subtitle>>"
}}
'''
    return trim_prompt.format(
        src_language=src_language,
        trans_text=trans_text,
        duration=duration,
        rule=rule
    )