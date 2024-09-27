from funasr import AutoModel

# 初始化模型
model = AutoModel(model="ct-punc", model_revision="v2.0.4")

# 读取文件并处理每一行
with open('output\\log\\sentence_by_comma.txt', 'r', encoding='utf-8') as file:
    for line in file:
        # 去除行末的换行符
        line = line.strip()
        # 对每行进行标点处理
        res = model.generate(input=line)
        # 打印处理结果
        print(res)