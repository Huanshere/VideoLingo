from funasr import AutoModel

model = AutoModel(model="fa-zh", model_revision="v2.0.4")

wav_file = r"output\audio\raw_full_audio.wav"
text_file = "paraformer.txt"
res = model.generate(input=(wav_file, text_file), data_type=("sound", "text"))
print(res)
# save res[0] as json
print(len(res))
import json
with open('fa_timestamp.json', 'w', encoding='utf-8') as f:
    json.dump(res[0], f, indent=4, ensure_ascii=False)

