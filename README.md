# 🎬 MrBeast Viral Shorts Generator

Automatically extract viral hook moments from YouTube videos and generate professional short-form content with animated text overlays.

## ✨ Features

- **YouTube Download**: Download videos using yt-dlp
- **AI Transcription**: Convert speech to text with word-level timestamps using Whisper
- **Smart Hook Detection**: GPT-4 AI analyzes transcripts to find the most viral moments
- **Vertical Format**: Auto-crops videos to 9:16 aspect ratio for TikTok/Shorts/Reels
- **Animated Captions**: 6 professional text animation styles

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/punit/workstation/shorts
pip install -r requirements.txt
```

### 2. Install FFmpeg (if not already installed)

```bash
# macOS
brew install ffmpeg
```

### 3. Set Up API Key

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 4. Generate Viral Shorts

```bash
python -m src.main "https://www.youtube.com/watch?v=VIDEO_ID"
```

## 📖 Usage

### Basic Usage

```bash
python -m src.main "YOUTUBE_URL"
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--hooks, -n` | Number of hooks to generate | 3 |
| `--animation, -a` | Text animation style | pop |
| `--word-by-word/--sentence` | Animate word-by-word or sentences | word-by-word |
| `--keep-temp` | Keep temporary files | False |
| `--output-dir, -o` | Custom output directory | ./output |

### Animation Styles

| Style | Description |
|-------|-------------|
| `fade_in` | Smooth fade from transparent |
| `slide_up` | Text slides up from bottom |
| `pop` | Zoom in with bounce effect |
| `typewriter` | Character reveal effect |
| `shake` | Attention-grabbing shake |
| `glow` | Pulsing glow effect |

### Examples

```bash
# Generate 5 hooks with slide animation
python -m src.main "URL" --hooks 5 --animation slide_up

# Sentence-by-sentence captions
python -m src.main "URL" --sentence

# Custom output directory
python -m src.main "URL" -o ./my_shorts
```

## 📁 Project Structure

```
shorts/
├── src/
│   ├── main.py           # CLI entry point
│   ├── config.py         # Configuration
│   ├── downloader.py     # YouTube download
│   ├── audio_extractor.py# Video → Audio
│   ├── transcriber.py    # Audio → Text
│   ├── hook_analyzer.py  # AI hook detection
│   ├── video_clipper.py  # Segment extraction
│   └── text_animator.py  # Animated captions
├── output/               # Generated shorts
├── temp/                 # Temporary files
├── requirements.txt
└── .env
```

## ⚙️ Configuration

Edit `.env` to customize:

```env
OPENAI_API_KEY=your_key_here
WHISPER_MODEL=base          # tiny/base/small/medium/large
MAX_CLIP_DURATION=60        # Max clip length in seconds
```

## 🎨 Customization

Edit `src/config.py` to change:
- Font style and size
- Text color and stroke
- Output resolution
- FPS settings

## 📝 License

MIT License - Use freely for creating content!

---

**Built with ❤️ for content creators**
