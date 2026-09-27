<div align="center">

<img src="/docs/logo.png" alt="VideoLingo Logo" height="140">

# Объединяя Мир, Кадр за Кадром

<a href="https://trendshift.io/repositories/12200" target="_blank"><img src="https://trendshift.io/api/badge/repositories/12200" alt="Huanshere%2FVideoLingo | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[**English**](/README.md)｜[**简体中文**](/translations/README.zh.md)｜[**繁體中文**](/translations/README.zh-TW.md)｜[**日本語**](/translations/README.ja.md)｜[**Español**](/translations/README.es.md)｜[**Русский**](/translations/README.ru.md)｜[**Français**](/translations/README.fr.md)

</div>

## 🌟 Обзор ([Попробуйте VL бесплатно!](https://videolingo.io))

VideoLingo объединяет распознавание речи, перевод, разбиение субтитров и озвучивание в интерфейсе Streamlit. Он создаёт файлы субтитров и, при необходимости, видео с субтитрами или озвучиванием. Качество перевода зависит от исходного звука, языка и выбранных моделей.

Ключевые особенности:
- 🎥 Загрузка видео с YouTube через yt-dlp

- Пословное распознавание речи и временное выравнивание с Qwen3-ASR + Qwen3-ForcedAligner

- **📝 Сегментация субтитров на основе NLP и ИИ**

- **📚 Пользовательская + ИИ-генерируемая терминология для согласованного перевода**

- Прямой перевод с необязательным анализом и естественной переформулировкой

- Разбиение субтитров с настраиваемыми ограничениями длины

- **🗣️ Дубляж с помощью GPT-SoVITS, Azure, OpenAI и других**

- 🚀 Запуск и обработка в один клик в Streamlit

- 🌍 Многоязычная поддержка в интерфейсе Streamlit

- 📝 Подробное логирование с возможностью возобновления прогресса

- 🔍 Селектор моделей с поиском — автоматическое получение полного списка моделей от вашего API-провайдера

- ⏯️ Управление задачами — пауза, возобновление или остановка обработки на любом этапе

Проект объединяет транскрипцию, перевод, оформление субтитров и озвучивание.

## 🎥 Демонстрация

<table>
<tr>
<td width="33%">

### Двойные Субтитры
---
https://github.com/user-attachments/assets/a5c3d8d1-2b29-4ba9-b0d0-25896829d951

</td>
<td width="33%">

### Клонирование Голоса Cosy2
---
https://github.com/user-attachments/assets/e065fe4c-3694-477f-b4d6-316917df7c0a

</td>
<td width="33%">

### GPT-SoVITS с моим голосом
---
https://github.com/user-attachments/assets/47d965b2-b4ab-4a0b-9d08-b49a7bf3508c

</td>
</tr>
</table>

### Поддержка языков

**Поддержка входных языков (будет добавлено больше):**

🇺🇸 Английский 🤩 | 🇷🇺 Русский 😊 | 🇫🇷 Французский 🤩 | 🇩🇪 Немецкий 🤩 | 🇮🇹 Итальянский 🤩 | 🇪🇸 Испанский 🤩 | 🇯🇵 Японский 😊 | 🇨🇳 Китайский 🤩

Языки озвучивания зависят от выбранного метода TTS.

## Установка

VideoLingo работает в Windows и Linux, на Mac с Apple Silicon (macOS 14 или новее) и на Mac с Intel с распознаванием на CPU. Для установки используется Python 3.12.

### Windows: установка одним двойным щелчком 🎉

1. Откройте [последний выпуск](https://github.com/Huanshere/VideoLingo/releases/latest) и скачайте **Source code (zip)**.
2. Распакуйте ZIP в удобное место, например на рабочий стол, и откройте полученную папку.
3. Дважды щёлкните `OneKeyStart.bat`. Не закрывайте окно, пока загружаются и устанавливаются необходимые компоненты. Для первого запуска нужен интернет; это может занять некоторое время.
4. Когда откроется VideoLingo, укажите адрес API, ключ и модель на боковой панели. В следующий раз используйте тот же `OneKeyStart.bat`: он проверит установку и запустит приложение.

Для этого способа в Windows не нужно самостоятельно устанавливать Git, uv или Python.

### Установка из исходного кода (Windows, macOS, Linux)

```bash
git clone https://github.com/Huanshere/VideoLingo.git
cd VideoLingo
uv run --no-project --python 3.12 setup_env.py --yes --launch
```

Затем запускайте `OneKeyStart.bat` в Windows или `.venv/bin/python -m streamlit run st.py` в macOS/Linux. Apple Silicon автоматически использует MLX, Mac с Intel — CPU; дополнительное разделение вокала не устанавливается автоматически.

#### Docker (необязательно)

Для контейнера NVIDIA в Linux нужны Docker, совместимый драйвер и [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). Образ использует ту же установку Python 3.12 и зависимости приложения, по умолчанию CUDA 12.8.1/cu128. Вариант CUDA 12.6 и сохранение данных описаны в [документации Docker](/docs/pages/docs/docker.en-US.md).

```bash
docker build -t videolingo .
docker run -d -p 8501:8501 --gpus all videolingo
```

## API
VideoLingo поддерживает формат API, подобный OpenAI, и различные интерфейсы TTS:
- LLM: выберите провайдера OpenAI-совместимого Chat Completions и модель, способную возвращать нужный структурированный JSON. URL API, ключ и модель задаются на боковой панели.
- Распознавание речи: локальный Qwen3-ASR + ForcedAligner (по умолчанию) или API ElevenLabs. Установщик не ставит WhisperX; чтобы использовать его как бэкенд, см. [WhisperX (ручная установка)](../docs/pages/docs/whisperx-manual.en-US.md).
- TTS: Azure, OpenAI, Fish TTS, SiliconFlow Fish/CosyVoice2, GPT-SoVITS, Edge TTS, F5-TTS и собственный адаптер в `core/tts_backend/custom_tts.py`.

Для подробных инструкций по установке, настройке API и пакетному режиму обратитесь к документации: [English](/docs/pages/docs/start.en-US.md) | [中文](/docs/pages/docs/start.zh-CN.md)

## Текущие ограничения

1. Шум и языковые модели выравнивания влияют на распознавание и время слов. Разделение голоса может помочь. Проверяйте субтитры: числа и символы могут не иметь надёжных временных меток.

2. Ответы LLM должны соответствовать требуемой структуре JSON. При ошибке проверьте `output/gpt_log/error.json`. Успешные ответы в кэше и завершённые этапы могут использоваться повторно; смена модели не пересоздаёт все результаты. Не начинайте с удаления всех выходных данных.

3. Качество и тайминг озвучивания зависят от перевода, сервиса TTS и темпа речи. Изменение скорости не гарантирует естественности и идеальной синхронизации.

4. Локальное распознавание использует один основной язык распознавания и выравнивания на аудиосегмент. Для смешанной речи точный текст и время на всех языках не гарантируются.

5. Озвучивание не назначает автоматически отдельный голос каждому говорящему.

## Лицензия

Проект распространяется по лицензии Apache 2.0. Благодарим проекты:

[Qwen3-ASR](https://github.com/Qwen/Qwen3-ASR), [MLX Audio](https://github.com/Blaizzy/mlx-audio), [whisperX](https://github.com/m-bain/whisperX), [yt-dlp](https://github.com/yt-dlp/yt-dlp), [json_repair](https://github.com/mangiucugna/json_repair), [BELLE](https://github.com/LianjiaTech/BELLE)

## Контакты

- [Issues](https://github.com/Huanshere/VideoLingo/issues) и [Pull Requests](https://github.com/Huanshere/VideoLingo/pulls) на GitHub
- Twitter: [@Huanshere](https://twitter.com/Huanshere)
- Email: team@videolingo.io

## История звёзд

[![Star History Chart](https://api.star-history.com/svg?repos=Huanshere/VideoLingo&type=Timeline)](https://star-history.com/#Huanshere/VideoLingo&Timeline)

---

<p align="center">Если VideoLingo вам полезен, поставьте звезду проекту!</p>
