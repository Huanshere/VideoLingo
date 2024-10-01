# VideoLingo : Connecter le monde, image par image
<p align="center">
      <a href="https://www.python.org" target="_blank"><img src="https://img.shields.io/badge/Python-3.10-blue.svg" alt="Python"></a>
      <a href="https://github.com/Huanshere/VideoLingo/blob/main/LICENSE" target="_blank"><img src="https://img.shields.io/github/license/Huanshere/VideoLingo.svg" alt="License"></a>
      <a href="https://github.com/Huanshere/VideoLingo/stargazers" target="_blank"><img src="https://img.shields.io/github/stars/Huanshere/VideoLingo.svg" alt="GitHub stars"></a>
    </p>
    
[**中文**](README.md) | [**English**](README.en.md)｜[**日本語**](README.ja.md)
    
**Groupe QQ : 875297969**
    
</div>
    
 ## 🌟 Introduction au projet
    
 VideoLingo est un outil tout-en-un de traduction et de doublage pour vidéos, visant à produire des sous-titres de qualité Netflix, à éliminer les traductions mécaniques rigides et les sous-titres sur plusieurs lignes, tout en ajoutant un doublage de haute qualité. Il permet de partager des connaissances au-delà des barrières linguistiques à travers le monde. Grâce à une interface web intuitive Streamlit, vous pouvez accomplir tout le processus, depuis le lien vidéo jusqu'à l'intégration de sous-titres bilingues de haute qualité et même le doublage, en quelques clics, créant facilement des vidéos localisées de qualité Netflix.
    
 Caractéristiques principales et fonctionnalités :
    - 🎥 Utilise yt-dlp pour télécharger des vidéos depuis des liens YouTube
    
   - 🎙️ Utilise WhisperX pour une reconnaissance des sous-titres au niveau des mots
    
- **📝 Utilise le NLP et GPT pour segmenter les sous-titres en fonction du sens des phrases**
    
- **📚 GPT résume et extrait une base de connaissances terminologiques pour une traduction contextualisée**
    
- **🔄 Traduction en trois étapes (directe, réflexion et paraphrase), rivalisant avec la qualité de traduction professionnelle**
    
- **✅ Vérifie la longueur d'une seule ligne selon les normes Netflix, évitant strictement les sous-titres en double ligne**
    
- **🗣️ Utilise des méthodes comme GPT-SoVITS pour un doublage aligné de haute qualité**
    
- 🚀 Lancement d'un package intégré en un clic, production de vidéos en un clic via Streamlit
    
- 📝 Journalisation détaillée de chaque étape d'opération, avec support de reprise en cas d'interruption
    
- 🌐 Support multilingue complet, permettant une localisation vidéo dans plusieurs langues
    
## 🎥 Démonstration
    
  <table>
    <tr>
    <td width="25%">
    
### Traduction russe
---
https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7
    
</td>
    <td width="25%">
    
### GPT-SoVITS
 ---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c
    
</td>
    <td width="25%">
    
 ### Fish TTS Ding Zhen
 ---
 https://github.com/user-attachments/assets/e7bb9090-d2ef-4261-9dc5-56bd67dc710d
    
 </td>
    <td width="25%">
    
### OAITTS
---
https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768
    
   </td>
    </tr>
    </table>
    
### Support linguistique :
    
Langues d'entrée actuellement supportées et exemples :
    
| Langue d'entrée | Niveau de support | Démo de traduction | Démo de doublage |
|----------------|-------------------|--------------------|------------------|
| Anglais | 🤩 | [Anglais vers chinois](https://github.com/user-attachments/assets/127373bb-c152-4b7a-8d9d-e586b2c62b4b) | À venir |
| Russe | 😊 | [Russe vers chinois](https://github.com/user-attachments/assets/25264b5b-6931-4d39-948c-5a1e4ce42fa7) | À venir |
| Français | 🤩 | [Français vers japonais](https://github.com/user-attachments/assets/3ce068c7-9854-4c72-ae77-f2484c7c6630) | À venir |
| Allemand | 🤩 | [Allemand vers chinois](https://github.com/user-attachments/assets/07cb9d21-069e-4725-871d-c4d9701287a3) | À venir |
| Italien | 🤩 | [Italien vers chinois](https://github.com/user-attachments/assets/f1f893eb-dad3-4460-aaf6-10cac999195e) | À venir |
| Espagnol | 🤩 | [Espagnol vers chinois](https://github.com/user-attachments/assets/c1d28f1c-83d2-4f13-a1a1-859bd6cc3553) | À venir |
| Japonais | 😐 | [Japonais vers chinois](https://github.com/user-attachments/assets/856c3398-2da3-4e25-9c36-27ca2d1f68c2) | À venir |
| Chinois* | 🤩 | [Chinois vers anglais](https://github.com/user-attachments/assets/48f746fe-96ff-47fd-bd23-59e9202b495c) | [Talk-show du professeur Luo Xiang](https://github.com/user-attachments/assets/85c64f8c-06cf-4af9-b153-ee9d2897b768) |
    > *Le chinois nécessite une configuration séparée du modèle whisperX, voir l'installation à partir du code source
    
Le support des langues de traduction couvre toutes les langues gérées par le grand modèle linguistique, tandis que le support des langues pour le doublage dépend de la méthode TTS choisie.
    ## 🚀 Package intégré en un clic pour Windows
    
### Notes importantes :
    
1. Le package intégré utilise la version CPU de torch, d'une taille d'environ **2,6G**.
    2. Lors de l'utilisation de UVR5 pour la séparation des voix dans l'étape devoix, la version CPU sera nettement plus lente que torch avec accélération GPU.
3. Le package intégré **ne supporte que l'appel à whisperXapi ☁️ via API**, et ne supporte pas l'exécution locale de whisperX 💻.
4. Le whisperXapi utilisé dans le package intégré ne supporte pas la transcription en chinois. Si vous avez besoin d'utiliser le chinois, veuillez installer à partir du code source et utiliser whisperX localement 💻.
5. Le package intégré n'a pas encore effectué la séparation des voix UVR5 dans l'étape de transcription, il n'est donc pas recommandé d'utiliser des vidéos avec une musique de fond bruyante.

Si vous avez besoin des fonctionnalités suivantes, veuillez installer à partir du code source (nécessite un GPU Nvidia et au moins **20G** d'espace disque) :
- La langue d'entrée est le chinois
- Exécuter whisperX localement 💻
- Utiliser UVR5 accéléré par GPU pour la séparation des voix
- Transcrire des vidéos avec une musique de fond bruyante

### Instructions de téléchargement et d'utilisation

1. Téléchargez le package en un clic `v1.4` (800 Mo) : [Téléchargement direct](https://vip.123pan.cn/1817874751/8209290) | [Sauvegarde Baidu](https://pan.baidu.com/s/1H_3PthZ3R3NsjS0vrymimg?pwd=ra64)

2. Après extraction, double-cliquez sur `OneKeyStart.bat` dans le dossier

3. Dans la fenêtre du navigateur qui s'ouvre, configurez les paramètres nécessaires dans la barre latérale, puis créez votre vidéo en un clic !
   
  ![attentionen](https://github.com/user-attachments/assets/9ff9d8e1-5422-466f-9e28-1803f23afdc7)

> 💡 Remarque : Ce projet nécessite la configuration de grands modèles linguistiques, WhisperX et TTS. Veuillez lire attentivement la section **Préparation de l'API** ci-dessous

## 📋 Préparation de l'API
Ce projet nécessite l'utilisation de grands modèles linguistiques, WhisperX et TTS. Plusieurs options sont fournies pour chaque composant. **Veuillez lire attentivement le guide de configuration 😊**
### 1. **Obtenez une API_KEY pour les grands modèles linguistiques** :

| Modèle recommandé | Fournisseur recommandé | base_url | Prix | Efficacité |
|:-----|:---------|:---------|:-----|:---------|
| claude-3-5-sonnet-20240620 (par défaut) | [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB) | https://yunwu.zeabur.app | ¥15 / 1M tokens | 🤩 |
| deepseek-coder | [deepseek](https://platform.deepseek.com/api_keys) | https://api.deepseek.com | ¥2 / 1M tokens | 😲 |
> Remarque : L'API Yunwu supporte également l'interface tts-1 d'OpenAI, qui peut être utilisée lors de l'étape de doublage.

> Rappel : deepseek a une très faible probabilité d'erreurs lors de la traduction. En cas d'erreurs, veuillez passer au modèle claude 3.5 sonnet.

#### Questions fréquentes

<details>
<summary>Quel modèle dois-je choisir ?</summary>

- 🌟 Utilisation par défaut de Claude 3.5, excellente qualité de traduction, très bonne cohérence, sans saveur IA.
- 🚀 Si vous utilisez deepseek, la traduction d'une vidéo d'une heure coûte environ ¥1, avec des résultats moyens.
</details>

<details>
<summary>Comment obtenir une clé API ?</summary>

1. Cliquez sur le lien du fournisseur recommandé ci-dessus
2. Créez un compte et rechargez-le
3. Créez une nouvelle clé API sur la page des clés API
4. Pour l'API Yunwu, assurez-vous de vérifier `Quota illimité`, sélectionnez le modèle `claude-3-5-sonnet-20240620`, et il est recommandé de choisir le canal `Pure AZ 1.5x`.
</details>

<details>
<summary>Puis-je utiliser d'autres modèles ?</summary>

- ✅ Supporte les interfaces d'API similaires à OAI, mais vous devez les changer vous-même dans la barre latérale de Streamlit.
- ⚠️ Cependant, d'autres modèles (en particulier les petits modèles) ont une faible capacité à suivre les instructions et sont très susceptibles de signaler des erreurs lors de la traduction, ce qui est fortement déconseillé.
</details>

### 2. **Préparer un token Replicate** (uniquement en utilisant whisperXapi ☁️)

VideoLingo utilise WhisperX pour la reconnaissance vocale, supportant à la fois le déploiement local et l'API cloud.
#### Comparaison des options :
| Option | Inconvénients |
|:-----|:-----|
| **whisperX 🖥️** | • Installation de CUDA 🛠️<br>• Téléchargement du modèle 📥<br>• Exigence de haute VRAM 💾 |
| **whisperXapi ☁️** | • Nécessite un VPN 🕵️‍♂️<br>• Carte Visa 💳<br>• **Mauvais effet sur le chinois** 🚫 |

#### Obtenir le token
   - Inscrivez-vous sur [Replicate](https://replicate.com/account/api-tokens), liez un moyen de paiement par carte Visa, et obtenez le token
   - **Ou rejoignez le groupe QQ pour obtenir un token de test gratuit dans l'annonce du groupe**

### 3. **API TTS**
VideoLingo propose plusieurs méthodes d'intégration TTS. Voici une comparaison (sautez cette étape si vous ne faites que traduire sans doublage) :

| Option TTS | Avantages | Inconvénients | Effet en chinois | Effet en langues non-chinoises |
|:---------|:-----|:-----|:---------|:-----------|
| 🎙️ OpenAI TTS | Émotions réalistes | Le chinois sonne comme un étranger | 😕 | 🤩 |
| 🔊 Azure TTS  | Effet naturel | Recharge peu pratique | 🤩 | 😃 |
| 🎤 Fish TTS (recommandé) | Excellent | Nécessite une recharge | 😱 | 😱 |
| 🗣️ GPT-SoVITS (bêta) | Clonage vocal local | Actuellement supporte uniquement l'entrée en anglais avec sortie en chinois, nécessite un GPU pour l'inférence du modèle, idéal pour des vidéos mono-personnes sans BGM évidente, et le modèle de base doit être proche de la voix d'origine | 😂 | 🚫 |

- Pour OpenAI TTS, nous recommandons d'utiliser [Yunwu API](https://yunwu.zeabur.app/register?aff=TXMB);
- **Les clés gratuites Azure TTS peuvent être obtenues dans l'annonce du groupe QQ** ou vous pouvez vous inscrire et recharger vous-même sur le [site officiel](https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python);
- **Les clés gratuites Fish TTS peuvent être obtenues dans l'annonce du groupe QQ** ou vous pouvez vous inscrire et recharger vous-même sur le [site officiel](https://fish.audio/zh-CN/go-api/)

<details>
<summary>Comment choisir une voix OpenAI ?</summary>

Vous pouvez trouver la liste des voix sur le [site officiel](https://platform.openai.com/docs/guides/text-to-speech/voice-options), telles que `alloy`, `echo`, `nova`, et `fable`. Modifiez `OAI_VOICE` dans `config.py` pour changer la voix.

</details>

<details>
<summary>Comment choisir une voix Azure ?</summary>

Il est recommandé d'écouter et de choisir la voix souhaitée dans l'[expérience en ligne](https://speech.microsoft.com/portal/voicegallery), et de trouver le code correspondant pour cette voix dans le code à droite, tel que `zh-CN-XiaoxiaoMultilingualNeural`.

</details>

<details>
<summary>Comment choisir une voix Fish TTS ?</summary>

Rendez-vous sur le [site officiel](https://fish.audio/zh-CN/) pour écouter et choisir la voix souhaitée, et trouvez le code correspondant pour cette voix dans l'URL, comme Ding Zhen est `54a5170264694bfc8e9ad98df7bd89c3`. Les voix populaires ont été ajoutées à `config.py`, modifiez simplement `FISH_TTS_CHARACTER`. Si vous devez utiliser d'autres voix, veuillez modifier le dictionnaire `FISH_TTS_CHARACTER_ID_DICT` dans `config.py`.

</details>

<details>
<summary>Tutoriel d'utilisation de GPT-SoVITS-v2</summary>

1. Consultez le document Yuque [officiel](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO) pour vérifier les exigences de configuration et télécharger le package intégré.

2. Placez `GPT-SoVITS-v2-xxx` au même niveau que le répertoire de `VideoLingo`. **Notez qu'ils doivent être des dossiers parallèles.**

3. Choisissez l'une des méthodes suivantes pour configurer le modèle :

   a. Modèle auto-entraîné :
   - Après l'entraînement du modèle, `tts_infer.yaml` sous `GPT-SoVITS-v2-xxx\GPT_SoVITS\configs` sera automatiquement rempli avec l'adresse de votre modèle. Copiez et renommez-le en `nom_personnage_anglais_voulu.yaml`
   - Dans le même répertoire que le fichier `yaml`, placez l'audio de référence que vous utiliserez plus tard, nommé `nom_personnage_anglais_voulu_texte_contenu_audio.wav` ou `.mp3`, par exemple `Huanyuv2_Hello, this is a test audio.wav`
   - Dans la barre latérale de la page web VideoLingo, définissez `GPT-SoVITS Character` sur `nom_personnage_anglais_voulu`.

   b. Utilisation du modèle pré-entraîné :
   - Téléchargez mon modèle depuis [ici](https://vip.123pan.cn/1817874751/8137723), extrayez-le et écrasez-le dans `GPT-SoVITS-v2-xxx`.
   - Définissez `GPT-SoVITS Character` sur `Huanyuv2`.

   c. Utilisation d'autres modèles entraînés :
   - Placez le fichier de modèle `xxx.ckpt` dans le dossier `GPT_weights_v2` et le fichier modèle `xxx.pth` dans le dossier `SoVITS_weights_v2`.
   - Référez-vous à la méthode a, renommez le fichier `tts_infer.yaml` et modifiez le `t2s_weights_path` et `vits_weights_path` dans la section `custom` du fichier pour pointer vers vos modèles, par exemple :
  
      ```yaml
      # Exemple de configuration pour la méthode b :
      t2s_weights_path: GPT_weights_v2/Huanyu_v2-e10.ckpt
      version: v2
      vits_weights_path: SoVITS_weights_v2/Huanyu_v2_e10_s150.pth
      ```
   - Référez-vous à la méthode a, placez l'audio de référence que vous utiliserez plus tard dans le même répertoire que le fichier `yaml`, nommé `nom_personnage_anglais_voulu_texte_contenu_audio.wav` ou `.mp3`, par exemple `Huanyuv2_Hello, this is a test audio.wav`. Le programme le reconnaîtra et l'utilisera automatiquement.
   - ⚠️ Avertissement : **Veuillez utiliser l'anglais pour nommer le `nom_personnage`**, sinon des erreurs se produiront. Le `texte_contenu_audio` peut être en chinois. Il est toujours en version bêta et peut produire des erreurs.

 ```
   # Structure de répertoire attendue :
   .
   ├── VideoLingo
   │   └── ...
   └── GPT-SoVITS-v2-xxx
       ├── GPT_SoVITS
       │   └── configs
       │       ├── tts_infer.yaml
       │       ├── nom_personnage_anglais_voulu.yaml
       │       └── nom_personnage_anglais_voulu_texte_contenu_audio_de_reference.wav
       ├── GPT_weights_v2
       │   └── [Votre fichier modèle GPT]
       └── SoVITS_weights_v2
           └── [Votre fichier modèle SoVITS]

 ```


     
Après la configuration, assurez-vous de sélectionner le `Mode Audio de Référence` dans la barre latérale de la page web. VideoLingo ouvrira automatiquement le port API d'inférence de GPT-SoVITS dans la ligne de commande pop-up lors de l'étape de doublage. Vous pouvez le fermer manuellement une fois le doublage terminé. Notez que cette méthode n'est toujours pas très stable et peut entraîner des mots ou des phrases manquants, ainsi que d'autres bugs, donc utilisez-la avec précaution.</details>

## 🛠️ Processus d'installation du code source

### Prérequis pour Windows

Avant de commencer l'installation de VideoLingo, assurez-vous d'avoir **20G** d'espace disque libre et complétez les étapes suivantes :

| Dépendance | whisperX 🖥️ | whisperX ☁️ |
|:-----|:-------------------|:----------------|
| Anaconda 🐍 | [Télécharger](https://www.anaconda.com/products/distribution#download-section) | [Télécharger](https://www.anaconda.com/products/distribution#download-section) |
| Git 🌿 | [Télécharger](https://git-scm.com/download/win) | [Télécharger](https://git-scm.com/download/win) |
| Cuda Toolkit 12.6 🚀 | [Télécharger](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe) | - |
| Cudnn 9.3.0 🧠 | [Télécharger](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe) | - |

> Remarque : Lors de l'installation d'Anaconda, cochez "Ajouter au chemin système", et redémarrez votre ordinateur après l'installation 🔄

### Étapes d'installation

Quelques connaissances en Python sont nécessaires. Supporte Win, Mac, Linux. Si vous rencontrez des problèmes, vous pouvez demander à GPT tout au long du processus~

1. Ouvrir l'invite Anaconda et passer au répertoire du bureau :
   ```bash
   cd desktop
   ```

2. Cloner le projet et passer au répertoire du projet :
   ```bash
   git clone https://github.com/Huanshere/VideoLingo.git
   cd VideoLingo
   ```

3. Créer et activer l'environnement virtuel (**doit être 3.10.0**) :
   ```bash
   conda create -n videolingo python=3.10.0 -y
   conda activate videolingo
   ```

4. Exécuter le script d'installation :
   ```bash
   python install.py
   ```
   Suivez les instructions pour sélectionner la méthode Whisper souhaitée, le script installera automatiquement les versions correspondantes de torch et whisper.

5. Uniquement pour les utilisateurs qui ont besoin de la transcription en chinois :

   Veuillez télécharger manuellement le modèle Belle-whisper-large-v3-zh-punct ([Lien Baidu](https://pan.baidu.com/s/1NyNtkEM0EMsjdCovncsx0w?pwd=938n)) et le remplacer dans le dossier `_model_cache` à la racine du projet.

6. 🎉 Entrez la commande ou cliquez sur `OneKeyStart.bat` pour lancer l'application Streamlit :
   ```bash
    streamlit run st.py
    ```

7. Définissez la clé dans la barre latérale de la page web qui s'ouvre, et assurez-vous de sélectionner la méthode whisper.

   ![attentionen](https://github.com/user-attachments/assets/9ff9d8e1-5422-466f-9e28-1803f23afdc7)

8. (Optionnel) Des paramètres plus avancés peuvent être modifiés manuellement dans `config.py`.

<!-- Ce projet utilise un développement modulaire structuré. Vous pouvez exécuter les fichiers `core\step__.py` dans l'ordre. Documentation technique : [Chinois](./docs/README_guide_zh.md) | [Anglais](./docs/README_guide_en.md) (À mettre à jour) -->

## ⚠️ Précautions

1. UVR5 a des exigences élevées en matière de mémoire. 16 Go de RAM peuvent traiter jusqu'à 30 minutes, 32 Go de RAM peuvent traiter jusqu'à 50 minutes. Veuillez faire attention aux longues vidéos.
   
2. Il y a une très faible probabilité d'erreurs de 'phrases' lors de l'étape de traduction. Si vous en rencontrez, merci de nous en informer.
   
3. La qualité de la fonction de doublage est instable. Pour une meilleure qualité, essayez de choisir une vitesse TTS adaptée à la vidéo originale. Par exemple, la vitesse de OAITTS est relativement rapide, tandis que pour FishTTS, veuillez écouter des échantillons avant de faire votre choix.

## 📄 Licence

Ce projet est sous licence Apache 2.0. Lorsque vous utilisez ce projet, veuillez suivre ces règles :

1. Lors de la publication de travaux, il est **recommandé (mais non obligatoire) de créditer VideoLingo pour la génération de sous-titres**.
2. Suivez les termes des modèles de langage large et des TTS utilisés pour une attribution correcte.
3. Si vous copiez le code, veuillez inclure l'intégralité de la licence Apache 2.0.

Nous remercions sincèrement les projets open-source suivants pour leurs contributions, qui ont fourni un soutien important au développement de VideoLingo :

- [whisperX](https://github.com/m-bain/whisperX)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [json_repair](https://github.com/mangiucugna/json_repair)
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)
- [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contactez-nous

- Rejoignez notre groupe QQ : 875297969
- Soumettez [Issues](https://github.com/Huanshere/VideoLingo/issues) ou des [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) sur GitHub.


## ⭐ Historique des Stars

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">Si vous trouvez VideoLingo utile, n'hésitez pas à nous donner une ⭐️!</p>




    
