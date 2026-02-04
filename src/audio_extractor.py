"""Audio extraction from video files."""

from pathlib import Path
from typing import Optional
from moviepy import VideoFileClip
from rich.console import Console

from .config import TEMP_DIR

console = Console()


class AudioExtractor:
    """Extract audio from video files."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or TEMP_DIR
        self.output_dir.mkdir(exist_ok=True)
    
    def extract(self, video_path: Path, output_format: str = "wav") -> Path:
        """
        Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            output_format: Output audio format (wav recommended for Whisper)
            
        Returns:
            Path to the extracted audio file
        """
        console.print(f"[bold blue]🎵 Extracting audio from:[/] {video_path.name}")
        
        audio_path = self.output_dir / f"{video_path.stem}.{output_format}"
        
        # Load video and extract audio
        video = VideoFileClip(str(video_path))
        
        # Extract audio with settings optimized for Whisper
        video.audio.write_audiofile(
            str(audio_path),
            fps=16000,  # 16kHz sample rate for Whisper
            nbytes=2,   # 16-bit audio
            codec='pcm_s16le' if output_format == 'wav' else None
        )
        
        video.close()
        
        console.print(f"[bold green]✅ Audio extracted:[/] {audio_path.name}")
        return audio_path


def extract_audio(video_path: Path, output_dir: Optional[Path] = None) -> Path:
    """
    Convenience function to extract audio from a video.
    
    Args:
        video_path: Path to the video file
        output_dir: Optional output directory
        
    Returns:
        Path to the extracted audio file
    """
    extractor = AudioExtractor(output_dir)
    return extractor.extract(video_path)
