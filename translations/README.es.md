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

- Reconocimiento y alineación de voz a nivel de palabra con Qwen3-ASR + Qwen3-ForcedAligner

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

🇺🇸 Inglés 🤩 | 🇷🇺 Ruso 😊 | 🇫🇷 Francés 🤩 | 🇩🇪 Alemán 🤩 | 🇮🇹 Italiano 🤩 | 🇪🇸 Español 🤩 | 🇯🇵 Japonés 😊 | 🇨🇳 Chino 🤩

Los idiomas de doblaje dependen del método TTS elegido.

## Instalación

VideoLingo funciona en Windows y Linux, en Mac con Apple Silicon (macOS 14 o posterior) y en Mac Intel con reconocimiento por CPU. La instalación usa Python 3.12.

### Windows: instalación con un clic 🎉

1. Abre la [última versión](https://github.com/Huanshere/VideoLingo/releases/latest) y descarga **Source code (zip)**.
2. Descomprime el ZIP en un lugar fácil de encontrar, como el escritorio, y abre la carpeta extraída.
3. Haz doble clic en `OneKeyStart.bat`. Deja la ventana abierta mientras descarga e instala lo necesario. La primera ejecución requiere Internet y puede tardar un poco.
4. Cuando se abra VideoLingo, introduce la URL de la API, la clave y el modelo en la barra lateral. La próxima vez, usa el mismo `OneKeyStart.bat`: comprobará la instalación e iniciará la aplicación.

Con este método para Windows no necesitas instalar Git, uv ni Python por tu cuenta.

### Instalación desde el código fuente (Windows, macOS, Linux)

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
uv run --no-project --python 3.12 setup_env.py --yes --launch
```

Después, usa `OneKeyStart.bat` en Windows o `.venv/bin/python -m streamlit run st.py` en macOS/Linux. Apple Silicon usa MLX; los Mac Intel usan la CPU para el reconocimiento; la separación de voces opcional no se instala automáticamente allí.

#### Docker (opcional)

Para un contenedor NVIDIA en Linux, instala Docker, un controlador compatible y [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). La imagen utiliza la misma instalación de Python 3.12 y las mismas dependencias, con CUDA 12.8.1/cu128 por defecto. Consulta la [documentación de Docker](/docs/pages/docs/docker.en-US.md) para la variante CUDA 12.6 y la persistencia de datos.

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## APIs
VideoLingo admite formato de API similar a OpenAI y varias interfaces TTS:
- LLM: elige un proveedor compatible con OpenAI Chat Completions y un modelo capaz de devolver el JSON estructurado requerido. Configura la URL API, la clave y el modelo en la barra lateral.
- Reconocimiento de voz: Qwen3-ASR + ForcedAligner local (predeterminado) o la API ElevenLabs. El instalador no instala WhisperX; para usarlo como backend, consulta [WhisperX (instalación manual)](../docs/pages/docs/whisperx-manual.en-US.md).
- TTS: Azure, OpenAI, Fish TTS, SiliconFlow Fish/CosyVoice2, GPT-SoVITS, Edge TTS, F5-TTS y un adaptador personalizado en `core/tts_backend/custom_tts.py`.

Para instrucciones detalladas de instalación, configuración de API y modo por lotes, consulta la documentación: [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## Limitaciones Actuales

1. El ruido y los modelos de alineación de cada idioma afectan al reconocimiento y los tiempos de las palabras. La separación de voz puede ayudar. Revisa los subtítulos: números y símbolos pueden carecer de tiempos fiables.

2. Las respuestas deben cumplir la estructura JSON requerida. Si fallan, revisa `output/gpt_log/error.json`. Se pueden reutilizar respuestas correctas en caché y etapas completadas; cambiar el modelo no las regenera todas. No empieces eliminando toda la salida.

3. La calidad y los tiempos del doblaje dependen de la traducción, el servicio TTS y la velocidad del habla. Ajustar la velocidad no garantiza naturalidad ni sincronización perfecta.

4. El reconocimiento local utiliza un idioma principal de reconocimiento y alineación por segmento de audio. El habla multilingüe no garantiza texto y tiempos precisos para todos los idiomas.

5. El flujo de doblaje no asigna automáticamente una voz distinta a cada hablante.

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia Apache 2.0. Un agradecimiento especial a los siguientes proyectos de código abierto por sus contribuciones:

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR), [MLX Audio](https://github.com/Blaizzy/mlx-audio), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## 📬 Contáctame

- Envía [Issues](https://github.com/Huanshere/VideoLingo/issues) o [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) en GitHub
- Envíame un DM en Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Envíame un correo a: team@videolingo.io

## ⭐ Historial de Estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">Si encuentras útil VideoLingo, ¡por favor dame una ⭐️!</p>
