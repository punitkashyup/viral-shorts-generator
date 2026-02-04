"""Speech-to-text transcription using OpenAI Whisper."""

from pathlib import Path
from typing import Optional, List, Dict
import whisper
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import WHISPER_MODEL

console = Console()


class Transcriber:
    """Transcribe audio to text with timestamps using Whisper."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or WHISPER_MODEL
        self.model = None
    
    def _load_model(self):
        """Load the Whisper model (lazy loading)."""
        if self.model is None:
            console.print(f"[bold yellow]🔄 Loading Whisper model:[/] {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            console.print("[bold green]✅ Model loaded![/]")
    
    def transcribe(self, audio_path: Path, language: str = "en") -> Dict:
        """
        Transcribe audio file to text with timestamps.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (default: English)
            
        Returns:
            Dictionary containing full text and segments with timestamps
        """
        self._load_model()
        
        console.print(f"[bold blue]🎤 Transcribing:[/] {audio_path.name}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            progress.add_task("Transcribing audio...", total=None)
            
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=True,
                verbose=False
            )
        
        # Process segments into a cleaner format
        segments = self._process_segments(result.get('segments', []))
        
        console.print(f"[bold green]✅ Transcription complete![/] ({len(segments)} segments)")
        
        return {
            'text': result.get('text', ''),
            'segments': segments,
            'language': result.get('language', language)
        }
    
    def _process_segments(self, raw_segments: List[Dict]) -> List[Dict]:
        """
        Process raw Whisper segments into a cleaner format.
        
        Returns list of segments with:
        - start: Start time in seconds
        - end: End time in seconds
        - text: Segment text
        - words: List of words with individual timestamps
        """
        segments = []
        
        for seg in raw_segments:
            segment = {
                'start': round(seg['start'], 2),
                'end': round(seg['end'], 2),
                'text': seg['text'].strip(),
            }
            
            # Add word-level timestamps if available
            if 'words' in seg:
                segment['words'] = [
                    {
                        'start': round(w['start'], 2),
                        'end': round(w['end'], 2),
                        'word': w['word'].strip()
                    }
                    for w in seg['words']
                ]
            
            segments.append(segment)
        
        return segments
    
    def get_transcript_text(self, segments: List[Dict]) -> str:
        """Get the full transcript text from segments."""
        return ' '.join(seg['text'] for seg in segments)


def transcribe_audio(
    audio_path: Path, 
    model_name: Optional[str] = None,
    language: str = "en"
) -> Dict:
    """
    Convenience function to transcribe audio.
    
    Args:
        audio_path: Path to the audio file
        model_name: Whisper model name (tiny, base, small, medium, large)
        language: Language code
        
    Returns:
        Dictionary with transcription results
    """
    transcriber = Transcriber(model_name)
    return transcriber.transcribe(audio_path, language)
