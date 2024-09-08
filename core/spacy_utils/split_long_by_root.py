import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import os,sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.spacy_utils.load_nlp_model import init_nlp
from config import get_joiner, WHISPER_LANGUAGE
from core.step2_whisper import get_whisper_language

def split_long_sentence(doc):
    tokens = [token.text for token in doc]
    n = len(tokens)
    
    # 动态规划数组，dp[i]表示从开始到第i个token的最优分割方案
    dp = [float('inf')] * (n + 1)
    dp[0] = 0
    
    # 记录最优分割点
    prev = [0] * (n + 1)
    
    for i in range(1, n + 1):
        for j in range(max(0, i - 100), i):  # 限制查找范围，避免过长的句子
            if i - j >= 30:  # 确保分句长度至少为30
                token = doc[i-1]
                if j == 0 or (token.is_sent_end or token.pos_ in ['VERB', 'AUX'] or token.dep_ == 'ROOT'):
                    if dp[j] + 1 < dp[i]:
                        dp[i] = dp[j] + 1
                        prev[i] = j
    
    # 根据最优分割点重建句子
    sentences = []
    i = n
    language = get_whisper_language() if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE # 考虑强制英文的情况
    joiner = get_joiner(language)
    while i > 0:
        j = prev[i]
        sentences.append(joiner.join(tokens[j:i]).strip())
        i = j
    
    return sentences[::-1]  # 反转列表以保持原始顺序

def split_extremely_long_sentence(doc):
    tokens = [token.text for token in doc]
    n = len(tokens)
    
    num_parts = (n + 59) // 60  # 向上取整
    
    part_length = n // num_parts
    
    sentences = []
    language = get_whisper_language() if WHISPER_LANGUAGE == 'auto' else WHISPER_LANGUAGE # 考虑强制英文的情况
    joiner = get_joiner(language)
    for i in range(num_parts):
        start = i * part_length
        end = start + part_length if i < num_parts - 1 else n
        sentence = joiner.join(tokens[start:end])
        sentences.append(sentence)
    
    return sentences

def split_long_by_root_main(nlp):

    with open("output/log/sentence_splitbyconnector.txt", "r", encoding="utf-8") as input_file:
        sentences = input_file.readlines()

    all_split_sentences = []
    for sentence in sentences:
        doc = nlp(sentence.strip())
        if len(doc) > 60:
            split_sentences = split_long_sentence(doc)
            if any(len(nlp(sent)) > 60 for sent in split_sentences):
                split_sentences = [subsent for sent in split_sentences for subsent in split_extremely_long_sentence(nlp(sent))]
            all_split_sentences.extend(split_sentences)
            print(f"✂️  分割长句: {sentence[:30]}...")
        else:
            all_split_sentences.append(sentence.strip())

    with open("output/log/sentence_splitbynlp.txt", "w", encoding="utf-8") as output_file:
        for sentence in all_split_sentences:
            output_file.write(sentence + "\n")

    print("💾 Long sentences split by root saved to →  `sentence_splitbynlp.txt`")

if __name__ == "__main__":
    nlp = init_nlp()
    split_long_by_root_main(nlp)
    # raw = "平口さんの盛り上げごまが初めて売れました本当に嬉しいです本当にやっぱり見た瞬間いいって言ってくれるそういうコマを作るのがやっぱりいいですよねその2ヶ月後チコさんが何やらそわそわしていましたなんか気持ち悪いやってきたのは平口さんの駒の評判を聞きつけた愛知県の収集家ですこの男性師匠大沢さんの駒も持っているといいますちょっと褒めすぎかなでも確実にファンは広がっているようです自信がない部分をすごく感じてたのでこれで自信を持って進んでくれるなっていう本当に始まったばっかりこれからいろいろ挑戦していってくれるといいなと思って今月平口さんはある場所を訪れましたこれまで数々のタイトル戦でコマを提供してきた老舗5番手平口さんのコマを扱いたいと言いますいいですねぇ困ってだんだん成長しますので大切に使ってそういう長く良い駒になる駒ですね商談が終わった後店主があるものを取り出しましたこの前の名人戦で使った駒があるんですけど去年、名人銭で使われた盛り上げごま低く盛り上げて品良くするというのは難しい素晴らしいですね平口さんが目指す高みですこういった感じで作れればまだまだですけどただ、多分、咲く。"
    # nlp = init_nlp()
    # doc = nlp(raw.strip())
    # for sent in split_still_long_sentence(doc):
    #     print(sent, '\n==========')
