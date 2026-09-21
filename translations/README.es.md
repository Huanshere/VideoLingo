<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# Conectando el Mundo, Cuadro por Cuadro

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 Descripción General ([¡Prueba VL Gratis!](https://videolingo.io))

VideoLingo reúne reconocimiento de voz, traducción, segmentación de subtítulos y doblaje en Streamlit. Genera archivos de subtítulos y, opcionalmente, videos subtitulados o doblados. La calidad depende del audio original, el idioma y los modelos elegidos.

Características principales:
- 🎥 Descarga de videos de YouTube mediante yt-dlp

- Reconocimiento y alineación de voz a nivel de palabra con WhisperX

- **📝 Segmentación de subtítulos impulsada por NLP e IA**

- **📚 Terminología personalizada + generada por IA para una traducción coherente**

- Traducción directa con reflexión y reformulación natural opcionales

- Segmentación de subtítulos con límites de longitud configurables

- **🗣️ Doblaje con GPT-SoVITS, Azure, OpenAI y más**

- 🚀 Inicio y procesamiento con un clic en Streamlit

- 🌍 Soporte multilingüe en la interfaz de Streamlit

- 📝 Registro detallado con reanudación de progreso

- 🔍 Selector de modelos con búsqueda — obtiene automáticamente la lista completa de modelos desde tu API

- ⏯️ Control de tareas — pausa, reanuda o detén el procesamiento en cualquier paso

El proyecto integra transcripción, traducción, composición de subtítulos y doblaje.

## 🎥 Demo

<table>
<tr>
<td width="33%">

### Subtítulos Duales
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Clonación de Voz Cosy2
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS con mi voz
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### Soporte de Idiomas

**Soporte de idiomas de entrada (más por venir):**

🇺🇸 Inglés 🤩 | 🇷🇺 Ruso 😊 | 🇫🇷 Francés 🤩 | 🇩🇪 Alemán 🤩 | 🇮🇹 Italiano 🤩 | 🇪🇸 Español 🤩 | 🇯🇵 Japonés 😐 | 🇨🇳 Chino* 😊

> *Para reconocer chino localmente, selecciona chino explícitamente para usar el modelo Belle Whisper con puntuación mejorada.

Los idiomas de traducción dependen del LLM elegido; los de doblaje, del método TTS.

## Instalación

¿Tienes algún problema? Chatea con nuestro agente de IA en línea gratuito [**aquí**](https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh) para ayudarte.

Instala [Git](https://git-scm.com/downloads), [uv](https://docs.astral.sh/uv/getting-started/installation/) y [FFmpeg](https://ffmpeg.org/download.html). Abre de nuevo la terminal y comprueba `git --version`, `uv --version` y `ffmpeg -version`.

Para NVIDIA, instala un controlador compatible con tu GPU. El instalador selecciona PyTorch `cu128` si `nvidia-smi` indica CUDA >=12.8, y `cu126` en caso contrario; sin NVIDIA, selecciona paquetes CPU. Selecciona paquetes Python, no instala el CUDA Toolkit del sistema. WhisperX en GPU también necesita las bibliotecas CUDA 12 cuBLAS y cuDNN 9 accesibles al proceso; consulta los [requisitos GPU](../docs/pages/docs/start.en-US.md#gpu-runtime).

> **Nota:** Se requiere FFmpeg. Por favor, instálalo a través de gestores de paquetes:
> - Windows: elige una compilación con **bibliotecas compartidas** desde la [página de FFmpeg](https://ffmpeg.org/download.html) y añade su directorio `bin` al PATH.
> - macOS: ```brew install ffmpeg``` (vía [Homebrew](https://brew.sh/))
> - Linux: ```sudo apt install ffmpeg``` (Debian/Ubuntu)

### Instalación con uv

uv descarga Python 3.13 y crea un entorno `.venv` aislado, sin Python preinstalado. La aplicación admite Python 3.10–3.13. Usa **bibliotecas compartidas FFmpeg 7** con TorchCodec 0.7; FFmpeg 8/9 solo no es compatible. Consulta la [compilación Windows verificada](../docs/pages/docs/start.en-US.md#ffmpeg-runtime).

1. Clona el repositorio

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. Crea el entorno e instala las dependencias

```bash
uv run --no-project --python 3.13 setup_env.py
```

3. Inicia la aplicacion

```bash
.venv\Scripts\streamlit run st.py        # Windows
.venv/bin/streamlit run st.py            # macOS / Linux
```

O haz doble clic en `OneKeyStart.bat` en Windows. Prefiere `~/.venvs/videolingo` si existe y después el `.venv` del proyecto. Abre `http://localhost:8501` y configura la URL API, la clave y el modelo en la barra lateral.

### Docker
Para un contenedor NVIDIA en Linux, instala Docker, un controlador compatible y [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). La imagen utiliza la misma instalación de Python 3.13 y las mismas dependencias, con CUDA 12.8.1/cu128 por defecto. Consulta la [documentación de Docker](/docs/pages/docs/docker.en-US.md) para la variante CUDA 12.6 y la persistencia de datos.

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## APIs
VideoLingo admite formato de API similar a OpenAI y varias interfaces TTS:
- LLM: elige un proveedor compatible con OpenAI Chat Completions y un modelo capaz de devolver el JSON estructurado requerido. Configura la URL API, la clave y el modelo en la barra lateral.
- Reconocimiento de voz: WhisperX local o la API ElevenLabs.
- TTS: Azure, OpenAI, Fish TTS, SiliconFlow Fish/CosyVoice2, GPT-SoVITS, Edge TTS, F5-TTS y un adaptador personalizado en `core/tts_backend/custom_tts.py`.

Para instrucciones detalladas de instalación, configuración de API y modo por lotes, consulta la documentación: [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## Limitaciones Actuales

1. El ruido y los modelos de alineación de cada idioma afectan al reconocimiento y los tiempos de las palabras. La separación de voz puede ayudar. Revisa los subtítulos: números y símbolos pueden carecer de tiempos fiables.

2. Las respuestas deben cumplir la estructura JSON requerida. Si fallan, revisa `output/gpt_log/error.json`. Se pueden reutilizar respuestas correctas en caché y etapas completadas; cambiar el modelo no las regenera todas. No empieces eliminando toda la salida.

3. La calidad y los tiempos del doblaje dependen de la traducción, el servicio TTS y la velocidad del habla. Ajustar la velocidad no garantiza naturalidad ni sincronización perfecta.

4. WhisperX local utiliza un idioma de reconocimiento y alineación por segmento. El habla multilingüe no garantiza texto y tiempos precisos para todos los idiomas.

5. El flujo de doblaje no asigna automáticamente una voz distinta a cada hablante.

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia Apache 2.0. Un agradecimiento especial a los siguientes proyectos de código abierto por sus contribuciones:

[whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contáctame

- Envía [Issues](https://github.com/Huanshere/VideoLingo/issues) o [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) en GitHub
- Envíame un DM en Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Envíame un correo a: team@videolingo.io

## ⭐ Historial de Estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">Si encuentras útil VideoLingo, ¡por favor dame una ⭐️!</p>
