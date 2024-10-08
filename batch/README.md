# VideoLingo Batch Mode

[English](./README.md) | [简体中文](./README.zh.md)

Before utilizing the batch mode, ensure you have familiarized yourself with the Streamlit mode and properly configured the parameters in `config.yaml`.

## Usage Guide

> Note: All referenced files, with the exception of `config.yaml`, are located within the `batch` folder.

### 1. Video File Preparation

- Upload your video files for processing to the `input` folder
- YouTube links can be specified in the subsequent step

### 2. Task Configuration

Modify the `tasks_setting.xlsx` file as follows:

| Field | Description | Acceptable Values |
|-------|-------------|-------------------|
| Video File | Video filename (excluding `input/` prefix) or YouTube URL | - |
| Source Language | Original language of the video | 'en', 'zh', 'auto', or leave empty for default |
| Target Language | Desired translation language | Use natural language description, or leave empty for default |
| Dubbing | Enable or disable dubbing | 0 or empty: no dubbing; 1: enable dubbing |

Example configuration:

| Video File | Source Language | Target Language | Dubbing |
|------------|-----------------|-----------------|---------|
| https://www.youtube.com/xxx | | German | |
| Kungfu Panda.mp4 | |  | 1 |

### 3. Executing Batch Processing

1. Launch `OneKeyBatch.bat` with a double-click
2. Processed files will be stored in the `output` folder
3. Monitor task progress in the `Status` column of `tasks_setting.xlsx`

> Note: Keep `tasks_setting.xlsx` closed during execution to prevent interruptions due to file access conflicts.


## Important Considerations

### Handling Interruptions

In the event of an unexpected command line closure, language settings in `config.yaml` may be altered. Verify these settings before attempting to resume processing.

### Error Management

- Files that fail to process will be relocated to the `output/ERROR` folder
- Detailed error messages are logged in the `Status` column of `tasks_setting.xlsx`
- To reattempt processing:
  1. Transfer the specific video folder from `ERROR` to the root directory
  2. Rename this folder to `output`
  3. Utilize the Streamlit mode to reinitiate processing
