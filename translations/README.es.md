<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# Conectando el Mundo, Cuadro por Cuadro

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 Descripción General ([¡Prueba VL Gratis!](https://videolingo.io))

VideoLingo es una herramienta todo en uno para traducción, localización y doblaje de videos, diseñada para generar subtítulos de calidad Netflix. Elimina las traducciones mecánicas y los subtítulos de múltiples líneas mientras agrega doblaje de alta calidad, permitiendo compartir conocimiento globalmente a través de las barreras del idioma.

Características principales:
- 🎥 Descarga de videos de YouTube mediante yt-dlp

- **🎙️ Reconocimiento de subtítulos a nivel de palabra y baja ilusión con WhisperX**

- **📝 Segmentación de subtítulos impulsada por NLP e IA**

- **📚 Terminología personalizada + generada por IA para una traducción coherente**

- **🔄 Proceso de 3 pasos Traducción-Reflexión-Adaptación para calidad cinematográfica**

- **✅ Solo subtítulos de una línea, estándar Netflix**

- **🗣️ Doblaje con GPT-SoVITS, Azure, OpenAI y más**

- 🚀 Inicio y procesamiento con un clic en Streamlit

- 🌍 Soporte multilingüe en la interfaz de Streamlit

- 📝 Registro detallado con reanudación de progreso

Diferencia con proyectos similares: **Solo subtítulos de una línea, calidad superior de traducción, experiencia de doblaje perfecta**

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

> *El chino utiliza un modelo whisper mejorado con puntuación por ahora...

**La traducción admite todos los idiomas, mientras que el idioma del doblaje depende del método TTS elegido.**

## Instalación

¿Tienes algún problema? Chatea con nuestro agente de IA en línea gratuito [**aquí**](https://share.fastgpt.in/chat/share?shareId=066w11n3r9aq6879r4z0v9rh) para ayudarte.

> **Nota:** Para usuarios de Windows con GPU NVIDIA, sigue estos pasos antes de la instalación:
> 1. Instala [CUDA Toolkit 12.6](https://developer.download.nvidia.com/compute/cuda/12.6.0/local_installers/cuda_12.6.0_560.76_windows.exe)
> 2. Instala [CUDNN 9.3.0](https://developer.download.nvidia.com/compute/cudnn/9.3.0/local_installers/cudnn_9.3.0_windows.exe)
> 3. Agrega `C:\Program Files\NVIDIA\CUDNN\v9.3\bin\12.6` a tu PATH del sistema
> 4. Reinicia tu computadora

> **Nota:** Se requiere FFmpeg. Por favor, instálalo a través de gestores de paquetes:
> - Windows: ```choco install ffmpeg``` (vía [Chocolatey](https://chocolatey.org/))
> - macOS: ```brew install ffmpeg``` (vía [Homebrew](https://brew.sh/))
> - Linux: ```sudo apt install ffmpeg``` (Debian/Ubuntu)

1. Clona el repositorio

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
```

2. Instala las dependencias (requiere `python=3.10`)

```bash
conda create -n videolingo python=3.10.0 -y
conda activate videolingo
python install.py
```

3. Inicia la aplicación

```bash
streamlit run st.py
```

### Docker
Alternativamente, puedes usar Docker (requiere CUDA 12.4 y versión del controlador NVIDIA >550), consulta la [documentación de Docker](/docs/pages/docs/docker.en-US.md):

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## APIs
VideoLingo admite formato de API similar a OpenAI y varias interfaces TTS:
- LLM: `claude-3-5-sonnet`, `gpt-4.1`, `deepseek-v3`, `gemini-2.0-flash`, ... (ordenados por rendimiento, ten cuidado con gemini-2.5-flash...)
- WhisperX: Ejecuta whisperX localmente o usa la API de 302.ai
- TTS: `azure-tts`, `openai-tts`, `siliconflow-fishtts`, **`fish-tts`**, `GPT-SoVITS`, `edge-tts`, `*custom-tts`(¡Puedes modificar tu propio TTS en custom_tts.py!)

> **Nota:** VideoLingo funciona con **[302.ai](https://gpt302.saaslink.net/C2oHR9)** - una clave API para todos los servicios (LLM, WhisperX, TTS). ¡O ejecútalo localmente con Ollama y Edge-TTS gratis, sin necesidad de API!

Para instrucciones detalladas de instalación, configuración de API y modo por lotes, consulta la documentación: [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## Limitaciones Actuales

1. El rendimiento de transcripción de WhisperX puede verse afectado por el ruido de fondo del video, ya que utiliza el modelo wav2vac para la alineación. Para videos con música de fondo fuerte, activa la Mejora de Separación de Voz. Además, los subtítulos que terminan con números o caracteres especiales pueden truncarse temprano debido a la incapacidad de wav2vac para mapear caracteres numéricos (por ejemplo, "1") a su forma hablada ("uno").

2. El uso de modelos más débiles puede provocar errores durante los procesos intermedios debido a los estrictos requisitos de formato JSON para las respuestas. Si ocurre este error, elimina la carpeta `output` y vuelve a intentarlo con un LLM diferente, de lo contrario, la ejecución repetida leerá la respuesta errónea anterior causando el mismo error.

3. La función de doblaje puede no ser 100% perfecta debido a las diferencias en las velocidades de habla y entonación entre idiomas, así como al impacto del paso de traducción. Sin embargo, este proyecto ha implementado un extenso procesamiento de ingeniería para las velocidades de habla para garantizar los mejores resultados posibles de doblaje.

4. **El reconocimiento de transcripción de video multilingüe solo mantendrá el idioma principal**. Esto se debe a que whisperX utiliza un modelo especializado para un solo idioma al alinear forzosamente los subtítulos a nivel de palabra, y eliminará los idiomas no reconocidos.

5. **No se pueden doblar múltiples personajes por separado**, ya que la capacidad de distinción de hablantes de whisperX no es suficientemente confiable.

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