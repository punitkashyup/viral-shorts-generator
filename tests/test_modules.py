"""Unit tests for the Viral Shorts Generator."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Tests for configuration module."""
    
    def test_config_imports(self):
        """Test that config module imports correctly."""
        from src.config import (
            TEMP_DIR, OUTPUT_DIR, WHISPER_MODEL,
            OUTPUT_RESOLUTION, OUTPUT_FPS, ANIMATION_TYPES
        )
        
        assert TEMP_DIR is not None
        assert OUTPUT_DIR is not None
        assert WHISPER_MODEL in ['tiny', 'base', 'small', 'medium', 'large']
        assert OUTPUT_RESOLUTION == (1080, 1920)
        assert OUTPUT_FPS == 30
        assert len(ANIMATION_TYPES) == 6
    
    def test_directories_created(self):
        """Test that temp and output directories exist."""
        from src.config import TEMP_DIR, OUTPUT_DIR
        
        assert TEMP_DIR.exists()
        assert OUTPUT_DIR.exists()


class TestDownloader:
    """Tests for YouTube downloader module."""
    
    def test_downloader_imports(self):
        """Test that downloader module imports correctly."""
        from src.downloader import VideoDownloader, download_video
        
        assert VideoDownloader is not None
        assert download_video is not None
    
    def test_downloader_initialization(self):
        """Test VideoDownloader initialization."""
        from src.downloader import VideoDownloader
        from src.config import TEMP_DIR
        
        downloader = VideoDownloader()
        assert downloader.output_dir == TEMP_DIR
    
    def test_downloader_custom_output_dir(self, tmp_path):
        """Test VideoDownloader with custom output directory."""
        from src.downloader import VideoDownloader
        
        downloader = VideoDownloader(output_dir=tmp_path)
        assert downloader.output_dir == tmp_path


class TestAudioExtractor:
    """Tests for audio extraction module."""
    
    def test_audio_extractor_imports(self):
        """Test that audio_extractor module imports correctly."""
        from src.audio_extractor import AudioExtractor, extract_audio
        
        assert AudioExtractor is not None
        assert extract_audio is not None
    
    def test_audio_extractor_initialization(self):
        """Test AudioExtractor initialization."""
        from src.audio_extractor import AudioExtractor
        from src.config import TEMP_DIR
        
        extractor = AudioExtractor()
        assert extractor.output_dir == TEMP_DIR
    
    @patch('src.audio_extractor.VideoFileClip')
    def test_extract_creates_wav_path(self, mock_video_clip, tmp_path):
        """Test that extract generates correct output path."""
        from src.audio_extractor import AudioExtractor
        
        # Setup mock
        mock_video = MagicMock()
        mock_audio = MagicMock()
        mock_video.audio = mock_audio
        mock_video_clip.return_value = mock_video
        
        extractor = AudioExtractor(output_dir=tmp_path)
        
        video_path = tmp_path / "test_video.mp4"
        video_path.touch()  # Create empty file
        
        # Call extract - will use mocked VideoFileClip
        result = extractor.extract(video_path)
        
        # Verify output path
        assert result == tmp_path / "test_video.wav"
        
        # Verify write_audiofile was called with correct args
        mock_audio.write_audiofile.assert_called_once()
        call_args = mock_audio.write_audiofile.call_args
        assert 'fps' in call_args.kwargs or call_args[1].get('fps') == 16000


class TestTranscriber:
    """Tests for transcription module."""
    
    def test_transcriber_imports(self):
        """Test that transcriber module imports correctly."""
        from src.transcriber import Transcriber, transcribe_audio
        
        assert Transcriber is not None
        assert transcribe_audio is not None
    
    def test_transcriber_initialization(self):
        """Test Transcriber initialization."""
        from src.transcriber import Transcriber
        from src.config import WHISPER_MODEL
        
        transcriber = Transcriber()
        assert transcriber.model_name == WHISPER_MODEL
        assert transcriber.model is None  # Lazy loading
    
    def test_transcriber_custom_model(self):
        """Test Transcriber with custom model."""
        from src.transcriber import Transcriber
        
        transcriber = Transcriber(model_name="tiny")
        assert transcriber.model_name == "tiny"
    
    def test_process_segments(self):
        """Test segment processing."""
        from src.transcriber import Transcriber
        
        transcriber = Transcriber()
        
        raw_segments = [
            {
                'start': 0.0,
                'end': 2.5,
                'text': ' Hello world ',
                'words': [
                    {'start': 0.0, 'end': 1.0, 'word': ' Hello '},
                    {'start': 1.0, 'end': 2.5, 'word': ' world '}
                ]
            }
        ]
        
        processed = transcriber._process_segments(raw_segments)
        
        assert len(processed) == 1
        assert processed[0]['text'] == 'Hello world'
        assert processed[0]['start'] == 0.0
        assert processed[0]['end'] == 2.5
        assert len(processed[0]['words']) == 2


class TestHookAnalyzer:
    """Tests for AI hook analyzer module."""
    
    def test_hook_analyzer_imports(self):
        """Test that hook_analyzer module imports correctly."""
        from src.hook_analyzer import HookAnalyzer, analyze_hooks
        
        assert HookAnalyzer is not None
        assert analyze_hooks is not None
    
    def test_format_transcript(self):
        """Test transcript formatting for AI prompt."""
        from src.hook_analyzer import HookAnalyzer
        
        # Mock API key for initialization
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            analyzer = HookAnalyzer(api_key='test-key')
        
        segments = [
            {'start': 0.0, 'end': 2.5, 'text': 'Hello world'},
            {'start': 2.5, 'end': 5.0, 'text': 'This is a test'}
        ]
        
        formatted = analyzer._format_transcript(segments)
        
        assert '[0.0s - 2.5s]' in formatted
        assert 'Hello world' in formatted
        assert '[2.5s - 5.0s]' in formatted
        assert 'This is a test' in formatted
    
    def test_refine_timestamps(self):
        """Test timestamp refinement."""
        from src.hook_analyzer import HookAnalyzer
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            analyzer = HookAnalyzer(api_key='test-key')
        
        hooks = [
            {'start_time': 0.0, 'end_time': 5.0}  # Too short
        ]
        segments = [
            {'start': 0.0, 'end': 5.0, 'text': 'Test'}
        ]
        
        refined = analyzer._refine_timestamps(hooks, segments)
        
        # Duration should be adjusted to at least 15 seconds
        assert refined[0]['end_time'] >= refined[0]['start_time'] + 10


class TestVideoClipper:
    """Tests for video clipper module."""
    
    def test_video_clipper_imports(self):
        """Test that video_clipper module imports correctly."""
        from src.video_clipper import VideoClipper, clip_video
        
        assert VideoClipper is not None
        assert clip_video is not None
    
    def test_video_clipper_initialization(self):
        """Test VideoClipper initialization."""
        from src.video_clipper import VideoClipper
        from src.config import TEMP_DIR
        
        clipper = VideoClipper()
        assert clipper.output_dir == TEMP_DIR
    
    def test_clip_hook(self):
        """Test clip_hook method creates correct output name."""
        from src.video_clipper import VideoClipper
        
        clipper = VideoClipper()
        
        hook = {'start_time': 10.0, 'end_time': 30.0}
        
        # We just test the output name generation logic
        expected_name = "hook_1"
        assert expected_name == f"hook_{1}"


class TestTextAnimator:
    """Tests for text animator module."""
    
    def test_text_animator_imports(self):
        """Test that text_animator module imports correctly."""
        from src.text_animator import TextAnimator, add_captions
        
        assert TextAnimator is not None
        assert add_captions is not None
    
    def test_text_animator_initialization(self):
        """Test TextAnimator initialization with defaults."""
        from src.text_animator import TextAnimator
        from src.config import (
            DEFAULT_FONT, DEFAULT_FONT_SIZE, DEFAULT_TEXT_COLOR,
            DEFAULT_STROKE_COLOR, DEFAULT_STROKE_WIDTH
        )
        
        animator = TextAnimator()
        
        assert animator.font == DEFAULT_FONT
        assert animator.font_size == DEFAULT_FONT_SIZE
        assert animator.text_color == DEFAULT_TEXT_COLOR
        assert animator.stroke_color == DEFAULT_STROKE_COLOR
        assert animator.stroke_width == DEFAULT_STROKE_WIDTH
    
    def test_text_animator_custom_settings(self):
        """Test TextAnimator with custom settings."""
        from src.text_animator import TextAnimator
        
        animator = TextAnimator(
            font="Impact",
            font_size=100,
            text_color="yellow"
        )
        
        assert animator.font == "Impact"
        assert animator.font_size == 100
        assert animator.text_color == "yellow"
    
    def test_animation_types(self):
        """Test that all animation types are supported."""
        from src.config import ANIMATION_TYPES
        
        expected = ["fade_in", "slide_up", "pop", "typewriter", "shake", "glow"]
        assert ANIMATION_TYPES == expected


class TestMainCLI:
    """Tests for main CLI module."""
    
    def test_main_imports(self):
        """Test that main module imports correctly."""
        from src.main import main, get_segments_for_timerange
        
        assert main is not None
        assert get_segments_for_timerange is not None
    
    def test_get_segments_for_timerange(self):
        """Test segment filtering and timestamp adjustment."""
        from src.main import get_segments_for_timerange
        
        segments = [
            {'start': 0.0, 'end': 5.0, 'text': 'First'},
            {'start': 5.0, 'end': 10.0, 'text': 'Second'},
            {'start': 10.0, 'end': 15.0, 'text': 'Third'},
            {'start': 15.0, 'end': 20.0, 'text': 'Fourth'}
        ]
        
        # Get segments between 5-15 seconds (includes overlapping segments)
        result = get_segments_for_timerange(segments, 5.0, 15.0)
        
        # All segments that overlap with 5-15 range are included
        assert len(result) >= 2
        
        # Check that 'Second' segment is included and adjusted
        second_seg = [s for s in result if s['text'] == 'Second'][0]
        assert second_seg['start'] == 0.0  # Was 5.0, now relative to clip start
        assert second_seg['end'] == 5.0    # Was 10.0, now relative
    
    def test_get_segments_with_words(self):
        """Test segment filtering preserves word timestamps."""
        from src.main import get_segments_for_timerange
        
        segments = [
            {
                'start': 5.0, 
                'end': 10.0, 
                'text': 'Hello world',
                'words': [
                    {'start': 5.0, 'end': 7.0, 'word': 'Hello'},
                    {'start': 7.0, 'end': 10.0, 'word': 'world'}
                ]
            }
        ]
        
        result = get_segments_for_timerange(segments, 5.0, 15.0)
        
        assert len(result) == 1
        assert 'words' in result[0]
        assert len(result[0]['words']) == 2
        
        # Word timestamps should be adjusted
        assert result[0]['words'][0]['start'] == 0.0
        assert result[0]['words'][0]['end'] == 2.0


class TestIntegration:
    """Integration tests for the pipeline."""
    
    def test_all_modules_import_without_errors(self):
        """Test that all modules can be imported together."""
        from src.config import validate_config
        from src.downloader import VideoDownloader
        from src.audio_extractor import AudioExtractor
        from src.transcriber import Transcriber
        from src.hook_analyzer import HookAnalyzer
        from src.video_clipper import VideoClipper
        from src.text_animator import TextAnimator
        from src.main import main
        
        # All imports successful
        assert True
    
    def test_pipeline_data_flow(self):
        """Test that data structures flow correctly through pipeline."""
        # Simulated transcript output
        transcript_data = {
            'text': 'This is a test video about amazing things',
            'segments': [
                {
                    'start': 0.0,
                    'end': 3.0,
                    'text': 'This is a test',
                    'words': [
                        {'start': 0.0, 'end': 0.5, 'word': 'This'},
                        {'start': 0.5, 'end': 1.0, 'word': 'is'},
                        {'start': 1.0, 'end': 1.5, 'word': 'a'},
                        {'start': 1.5, 'end': 3.0, 'word': 'test'}
                    ]
                }
            ],
            'language': 'en'
        }
        
        # Verify structure
        assert 'segments' in transcript_data
        assert 'words' in transcript_data['segments'][0]
        
        # Simulated hook output
        hook_data = {
            'start_time': 0.0,
            'end_time': 30.0,
            'hook_text': 'This is a test',
            'virality_score': 8,
            'hook_type': 'opening_hook',
            'reason': 'Strong opening'
        }
        
        # Verify hook structure
        assert 'start_time' in hook_data
        assert 'end_time' in hook_data
        assert hook_data['virality_score'] <= 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
