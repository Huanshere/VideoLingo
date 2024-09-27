from funasr import AutoModel
# paraformer-zh is a multi-functional asr model
# use vad, punc, spk or not as you need
model = AutoModel(model="paraformer-zh", model_revision="v2.0.4",
                  vad_model="fsmn-vad", vad_model_revision="v2.0.4",
                  punc_model="ct-punc-c", punc_model_revision="v2.0.4",
                  # spk_model="cam++", spk_model_revision="v2.0.2",
                  )
res = model.generate(input=r"output\audio\raw_full_audio.wav", 
            batch_size_s=300, 
            hotword='Comfy UI')
print(res)
# save res[0]['text'] to a file
with open('paraformer.txt', 'w', encoding='utf-8') as f:
    f.write(res[0]['text'])
