<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# Connecter le Monde, Image par Image

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 Aperçu ([Essayez VL maintenant !](https://videolingo.io))

VideoLingo réunit reconnaissance vocale, traduction, segmentation des sous-titres et doublage dans Streamlit. Il produit des fichiers de sous-titres et, en option, des vidéos sous-titrées ou doublées. La qualité dépend de l'audio source, de la langue et des modèles choisis.

Fonctionnalités principales :
- 🎥 Téléchargement de vidéos YouTube via yt-dlp

- Reconnaissance vocale et alignement au niveau des mots avec Qwen3-ASR + Qwen3-ForcedAligner

- **📝 Segmentation des sous-titres basée sur le NLP et l'IA**

- **📚 Terminologie personnalisée + générée par IA pour une traduction cohérente**

- Traduction directe avec réflexion et reformulation naturelle facultatives

- Segmentation des sous-titres avec limites de longueur configurables

- **🗣️ Doublage avec GPT-SoVITS, Azure, OpenAI et plus**

- 🚀 Démarrage et traitement en un clic dans Streamlit

- 🌍 Support multi-langues dans l'interface utilisateur Streamlit

- 📝 Journalisation détaillée avec reprise de la progression

- 🔍 Sélecteur de modèles avec recherche — récupère automatiquement la liste complète des modèles depuis votre API

- ⏯️ Contrôle des tâches — mettez en pause, reprenez ou arrêtez le traitement à n'importe quelle étape

Le projet rassemble transcription, traduction, mise en page des sous-titres et doublage.

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

🇺🇸 Anglais 🤩 | 🇷🇺 Russe 😊 | 🇫🇷 Français 🤩 | 🇩🇪 Allemand 🤩 | 🇮🇹 Italien 🤩 | 🇪🇸 Espagnol 🤩 | 🇯🇵 Japonais 😊 | 🇨🇳 Chinois 🤩

Les langues de doublage dépendent du service TTS choisi.

## Installation

VideoLingo fonctionne sous Windows, macOS (Apple Silicon / Intel) et Linux.

### Demander à votre agent IA local 🤖

Si votre agent IA peut utiliser votre ordinateur, envoyez-lui ce message :

> Installe et lance Huanshere/VideoLingo depuis GitHub sur mon ordinateur.

### Windows : installation en un clic 🎉

1. Ouvrez la [dernière version](https://github.com/Huanshere/VideoLingo/releases/latest) et téléchargez **Source code (zip)**.
2. Décompressez le ZIP sur le Bureau ou dans un autre dossier, puis ouvrez ce dossier.
3. Double-cliquez sur `OneKeyStart.bat` et gardez la fenêtre ouverte. Au premier lancement, le script prépare automatiquement uv, Python 3.12, les dépendances et FFmpeg. Une connexion Internet est nécessaire.
4. Une fois VideoLingo ouvert, renseignez l’URL de l’API, la clé et le modèle dans la barre latérale. Ensuite, double-cliquez sur le même script pour le relancer.

### Installation depuis le code source (Windows, macOS, Linux)

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
uv run start.py
```

Pour le relancer, exécutez `uv run start.py` dans le dossier VideoLingo. Apple Silicon utilise MLX ; les Mac Intel utilisent le CPU pour la reconnaissance. La séparation vocale facultative n’est pas installée automatiquement sur les Mac Intel.

#### Docker (facultatif)

Pour un conteneur NVIDIA sous Linux, installez Docker, un pilote compatible et le [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). L'image utilise la même installation Python 3.12 et les mêmes dépendances, avec CUDA 12.8.1/cu128 par défaut. Voir la [documentation Docker](/docs/pages/docs/docker.en-US.md) pour la variante CUDA 12.6 et la persistance des données.

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## APIs
VideoLingo prend en charge le format d'API OpenAI et diverses interfaces TTS :
- LLM : choisissez un fournisseur compatible avec OpenAI Chat Completions et un modèle capable de produire le JSON structuré requis. Configurez l'URL API, la clé et le modèle dans la barre latérale.
- Reconnaissance vocale : Qwen3-ASR + ForcedAligner en local (par défaut) ou l'API ElevenLabs. L'installateur n'installe pas WhisperX ; pour l'utiliser comme backend, voir [WhisperX (installation manuelle)](../docs/pages/docs/whisperx-manual.en-US.md).
- TTS : Azure, OpenAI, Fish TTS, SiliconFlow Fish/CosyVoice2, GPT-SoVITS, Edge TTS, F5-TTS et adaptateur personnalisé dans `core/tts_backend/custom_tts.py`.

Pour des instructions détaillées sur l'installation, la configuration de l'API et le mode batch, veuillez consulter la documentation : [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## Limitations actuelles

1. Le bruit et les modèles d'alignement propres à chaque langue influencent la reconnaissance et les horodatages. La séparation vocale peut aider. Vérifiez les sous-titres : nombres et symboles peuvent manquer d'horodatages fiables.

2. Les réponses doivent respecter la structure JSON attendue. En cas d'erreur, consultez `output/gpt_log/error.json`. Les réponses réussies en cache et les étapes terminées peuvent être réutilisées ; changer de modèle ne les régénère pas toutes. Ne commencez pas par supprimer toutes les sorties.

3. La qualité et le timing du doublage dépendent de la traduction, du service TTS et du débit. L'ajustement de vitesse ne garantit ni naturel ni synchronisation parfaite.

4. La reconnaissance locale utilise une langue principale de reconnaissance et d'alignement par segment audio. Pour un discours multilingue, le texte et les horodatages ne sont pas garantis dans toutes les langues.

5. Le doublage n'attribue pas automatiquement une voix différente à chaque locuteur.

## 📄 Licence

Ce projet est sous licence Apache 2.0. Remerciements spéciaux aux projets open source suivants pour leurs contributions :

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR), [MLX Audio](https://github.com/Blaizzy/mlx-audio), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contactez-moi

- Soumettez des [Issues](https://github.com/Huanshere/VideoLingo/issues) ou des [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) sur GitHub
- DM moi sur Twitter : [@Huanshere](https://twitter.com/Huanshere)
- Envoyez-moi un email à : team@videolingo.io

## ⭐ Historique des étoiles

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">Si vous trouvez VideoLingo utile, donnez-moi une ⭐️ !</p>
