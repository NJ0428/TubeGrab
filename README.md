# TubeGrab

A fast, modern YouTube downloader built with Python and PySide6.

## Features

- Download videos from YouTube in multiple resolutions (up to 4K)
- Choose output format: MP4, WEBM, MP3, M4A
- Audio extraction to MP3/M4A (requires FFmpeg)
- Concurrent download queue with configurable concurrency limit
- Real-time download progress with speed and ETA indicators
- Dark and light themes
- Persistent settings (download folder, theme, concurrency)
- Open downloaded files directly from the download list
- Retry failed downloads

## Requirements

- Python 3.12 or newer
- [FFmpeg](https://ffmpeg.org/) (required for audio extraction and some video merging; must be on PATH)
- pip packages listed in `requirements.txt`

## Quick Start

```bash
git clone https://github.com/your-username/TubeGrab.git
cd TubeGrab
pip install -r requirements.txt
python main.py
```

## Build Standalone Executable

Install PyInstaller, then run:

```bash
pip install pyinstaller
pyinstaller TubeGrab.spec
```

The executable will be placed in the `dist/` directory.

## Usage

1. Paste a YouTube URL into the URL field (or use the **Paste** button).
2. Click **Fetch Info** to load video metadata.
3. Select the desired resolution and format.
4. Choose a save folder with **Browse...** or type a path directly.
5. Click **Download** to add the job to the queue.
6. Monitor progress in the download list below.
7. Once complete, click **Open File** to reveal the file in Explorer.

## Project Structure

```
TubeGrab/
├── main.py                        # Application entry point
├── TubeGrab.spec                  # PyInstaller build spec
├── requirements.txt
├── assets/
│   ├── icons/
│   └── styles/
│       ├── dark.qss
│       └── light.qss
└── app/
    ├── core/
    │   ├── download_manager.py    # Download queue and worker orchestration
    │   ├── downloader.py          # yt-dlp wrapper
    │   └── ffmpeg.py              # FFmpeg detection
    ├── models/
    │   ├── download_task.py       # DownloadTask dataclass
    │   └── video.py               # VideoInfo dataclass
    ├── ui/
    │   ├── main_window.py         # Main application window
    │   ├── components/
    │   │   ├── download_item.py   # Per-download card widget
    │   │   ├── url_input.py       # URL input with validation
    │   │   ├── video_info.py      # Video metadata display
    │   │   └── progress_card.py   # Status bar queue summary
    │   └── dialogs/
    │       ├── about_dialog.py    # About dialog
    │       ├── ffmpeg_dialog.py   # FFmpeg not-found warning
    │       └── settings_dialog.py # Application settings
    ├── utils/
    │   ├── config.py              # JSON config persistence
    │   ├── logger.py              # Logging setup
    │   └── validators.py          # URL validation helpers
    └── workers/
        ├── download_worker.py     # Background download thread
        └── metadata_worker.py     # Background metadata fetch thread
```

## License

MIT License. See [LICENSE](LICENSE) for details.
