conda activate videolingo
rm -rf output/
python -m core.step1_ytdlp
# 语音识别
python -m core.step2_whisperX

# # # 文本分割
python -m core.step3_1_spacy_split
python -m core.step3_2_splitbymeaning

# # 文本处理和翻译
python -m core.step4_1_summarize
python -m core.step4_2_translate_all

# 字幕处理
python -m core.step5_splitforsub
python -m core.step6_generate_final_timeline
python -m core.step7_merge_sub_to_vid
