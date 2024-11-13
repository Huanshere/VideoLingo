import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from core import step1_ytdlp, step2_whisperX, step3_1_spacy_split, step3_2_splitbymeaning
from core import step4_1_summarize, step4_2_translate_all, step5_splitforsub, step6_generate_final_timeline 
from core import step7_merge_sub_to_vid, step8_gen_audio_task, step10_gen_audio, step11_merge_audio_to_vid
from core.onekeycleanup import cleanup
from core.config_utils import load_key
import shutil
from functools import partial

def process_video(file, dubbing=False, is_retry=False):
    if not is_retry:
        prepare_output_folder('output')
    
    steps = [
        ("Processing input file", partial(process_input_file, file)),
        ("Transcribing with Whisper", partial(step2_whisperX.transcribe)),
        ("Splitting sentences", split_sentences),
        ("Summarizing and translating", summarize_and_translate),
        ("Processing and aligning subtitles", process_and_align_subtitles),
        ("Merging subtitles to video", step7_merge_sub_to_vid.merge_subtitles_to_video),
    ]
    
    if dubbing:
        steps.extend([
            ("Generating audio tasks", step8_gen_audio_task.gen_audio_task_main),
            ("Generating audio using SoVITS", step10_gen_audio.process_sovits_tasks),
            ("Merging generated audio with video", step11_merge_audio_to_vid.merge_main),
        ])
    
    current_step = ""
    for step_name, step_func in steps:
        current_step = step_name
        for attempt in range(3):
            try:
                print(f"Executing: {step_name}...")
                result = step_func()
                if result is not None:
                    globals().update(result)
                break
            except Exception as e:
                if attempt == 2:
                    error_message = f"Error in step '{current_step}': {str(e)}"
                    print(error_message)
                    cleanup("batch/output/ERROR")
                    return False, current_step, error_message
                print(f"Attempt {attempt + 1} failed. Retrying...")
    
    print("All steps completed successfully!")
    cleanup("batch/output")
    return True, "", ""

def prepare_output_folder(output_folder):
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

def process_input_file(file):
    if file.startswith('http'):
        step1_ytdlp.download_video_ytdlp(file, resolution=load_key("ytb_resolution"), cutoff_time=None)
        video_file = step1_ytdlp.find_video_files()
    else:
        input_file = os.path.join('batch', 'input', file)
        output_file = os.path.join('output', file)
        shutil.copy(input_file, output_file)
        video_file = output_file
    return {'video_file': video_file}

def split_sentences():
    step3_1_spacy_split.split_by_spacy()
    step3_2_splitbymeaning.split_sentences_by_meaning()

def summarize_and_translate():
    step4_1_summarize.get_summary()
    step4_2_translate_all.translate_all()

def process_and_align_subtitles():
    step5_splitforsub.split_for_sub_main()
    step6_generate_final_timeline.align_timestamp_main()
