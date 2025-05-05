<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# Connecter le Monde, Image par Image

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 Aperçu ([Essayez VL maintenant !](https://videolingo.io))

VideoLingo est un outil tout-en-un de traduction, de localisation et de doublage vidéo visant à générer des sous-titres de qualité Netflix. Il élimine les traductions automatiques rigides et les sous-titres multi-lignes tout en ajoutant un doublage de haute qualité, permettant le partage des connaissances à l'échelle mondiale au-delà des barrières linguistiques.

Fonctionnalités principales :
- 🎥 Téléchargement de vidéos YouTube via yt-dlp

- **🎙️ Reconnaissance de sous-titres au niveau des mots et à faible illusion avec WhisperX**

- **📝 Segmentation des sous-titres basée sur le NLP et l'IA**

- **📚 Terminologie personnalisée + générée par IA pour une traduction cohérente**

- **🔄 Processus en 3 étapes : Traduction-Réflexion-Adaptation pour une qualité cinématographique**

- **✅ Sous-titres uniquement sur une ligne, aux normes Netflix**

- **🗣️ Doublage avec GPT-SoVITS, Azure, OpenAI et plus**

- 🚀 Démarrage et traitement en un clic dans Streamlit

- 🌍 Support multi-langues dans l'interface utilisateur Streamlit

- 📝 Journalisation détaillée avec reprise de la progression

Différence par rapport aux projets similaires : **Sous-titres sur une seule ligne uniquement, qualité de traduction supérieure, expérience de doublage transparente**

## 🎥 Démo

<table>
<tr>
<td width="33%">

### Sous-titres Doubles
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Clonage Vocal Cosy2
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS avec ma voix
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### Support des langues

**Support des langues d'entrée (d'autres à venir) :**

🇺🇸 Anglais 🤩 | 🇷🇺 Russe 😊 | 🇫🇷 Français 🤩 | 🇩🇪 Allemand 🤩 | 🇮🇹 Italien 🤩 | 🇪🇸 Espagnol 🤩 | 🇯🇵 Japonais 😐 | 🇨🇳 Chinois* 😊

> *Le chinois utilise un modèle whisper séparé amélioré par la ponctuation, pour l'instant...

**La traduction prend en charge toutes les langues, tandis que la langue de doublage dépend de la méthode TTS choisie.**

## Installation

Vous rencontrez un problème ? Discutez avec notre agent IA gratuit en ligne [**ici**](https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh) pour vous aider.

> **Note :** Pour les utilisateurs Windows avec un GPU NVIDIA, suivez ces étapes avant l'installation :
> 1. Installez [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. Installez [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. Ajoutez `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` à votre PATH système
> 4. Redémarrez votre ordinateur

> **Note :** FFmpeg est requis. Veuillez l'installer via les gestionnaires de paquets :
> - Windows : ```choco install ffmpeg``` (via [Chocolatey](https://chocolatey.org/))
> - macOS : ```brew install ffmpeg``` (via [Homebrew](https://brew.sh/))
> - Linux : ```sudo apt install ffmpeg``` (Debian/Ubuntu)

1. Clonez le dépôt

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. Installez les dépendances (nécessite `python=3.10`)

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. Démarrer l'application

```bash
streamlit run st.py
```

### Docker
Alternativement, vous pouvez utiliser Docker (nécessite CUDA 12.4 et NVIDIA Driver version >550), voir [Documentation Docker](/docs/pages/docs/docker.en-US.md) :

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## APIs
VideoLingo prend en charge le format d'API OpenAI et diverses interfaces TTS :
- LLM : `claude-3-5-sonnet`, `gpt-4.1`, `deepseek-v3`, `gemini-2.0-flash`, ... (triés par performance, soyez prudent avec gemini-2.5-flash...)
- WhisperX : Exécutez whisperX localement ou utilisez l'API 302.ai
- TTS : `azure-tts`, `openai-tts`, `siliconflow-fishtts`, **`fish-tts`**, `GPT-SoVITS`, `edge-tts`, `*custom-tts`(Vous pouvez modifier votre propre TTS dans custom_tts.py !)

> **Note :** VideoLingo fonctionne avec **[302.ai](https://gpt302.saaslink.net/C2oHR9)** - une seule clé API pour tous les services (LLM, WhisperX, TTS). Ou exécutez localement avec Ollama et Edge-TTS gratuitement, sans API nécessaire !

Pour des instructions détaillées sur l'installation, la configuration de l'API et le mode batch, veuillez consulter la documentation : [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## Limitations actuelles

1. Les performances de transcription de WhisperX peuvent être affectées par le bruit de fond de la vidéo, car il utilise le modèle wav2vac pour l'alignement. Pour les vidéos avec une musique de fond forte, veuillez activer l'amélioration de la séparation vocale. De plus, les sous-titres se terminant par des chiffres ou des caractères spéciaux peuvent être tronqués prématurément en raison de l'incapacité de wav2vac à mapper les caractères numériques (par exemple, "1") à leur forme parlée ("un").

2. L'utilisation de modèles plus faibles peut entraîner des erreurs lors des processus intermédiaires en raison des exigences strictes de format JSON pour les réponses. Si cette erreur se produit, veuillez supprimer le dossier `output` et réessayer avec un LLM différent, sinon l'exécution répétée lira la réponse erronée précédente causant la même erreur.

3. La fonction de doublage peut ne pas être parfaite à 100% en raison des différences de débit et d'intonation entre les langues, ainsi que de l'impact de l'étape de traduction. Cependant, ce projet a mis en œuvre un traitement d'ingénierie extensif pour les débits de parole afin d'assurer les meilleurs résultats de doublage possibles.

4. **La reconnaissance de transcription vidéo multilingue ne conservera que la langue principale**. C'est parce que whisperX utilise un modèle spécialisé pour une seule langue lors de l'alignement forcé des sous-titres au niveau des mots, et supprimera les langues non reconnues.

5. **Impossible de doubler séparément plusieurs personnages**, car la capacité de distinction des locuteurs de whisperX n'est pas suffisamment fiable.

## 📄 Licence

Ce projet est sous licence Apache 2.0. Remerciements spéciaux aux projets open source suivants pour leurs contributions :

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contactez-moi

- Soumettez des [Issues](https://github.com/Huanshere/VideoLingo/issues) ou des [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) sur GitHub
- DM moi sur Twitter : [@Huanshere](https://twitter.com/Huanshere)
- Envoyez-moi un email à : team@videolingo.io

## ⭐ Historique des étoiles

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">Si vous trouvez VideoLingo utile, donnez-moi une ⭐️ !</p> 