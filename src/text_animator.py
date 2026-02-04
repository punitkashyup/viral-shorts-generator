"""Animated text overlay for viral shorts."""

import math
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Callable
from moviepy import (
    VideoFileClip, TextClip, CompositeVideoClip, 
    concatenate_videoclips, ColorClip
)
from rich.console import Console

from .config import (
    OUTPUT_DIR, OUTPUT_RESOLUTION, OUTPUT_FPS,
    DEFAULT_FONT, DEFAULT_FONT_SIZE, DEFAULT_TEXT_COLOR,
    DEFAULT_STROKE_COLOR, DEFAULT_STROKE_WIDTH
)

console = Console()


class TextAnimator:
    """Add animated text overlays to video clips."""
    
    def __init__(
        self,
        font: str = DEFAULT_FONT,
        font_size: int = DEFAULT_FONT_SIZE,
        text_color: str = DEFAULT_TEXT_COLOR,
        stroke_color: str = DEFAULT_STROKE_COLOR,
        stroke_width: int = DEFAULT_STROKE_WIDTH
    ):
        self.font = font
        self.font_size = font_size
        self.text_color = text_color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
    
    def add_animated_captions(
        self,
        video_path: Path,
        segments: List[Dict],
        animation_type: str = "pop",
        output_path: Optional[Path] = None,
        word_by_word: bool = True
    ) -> Path:
        """
        Add animated captions to a video clip.
        
        Args:
            video_path: Path to the video clip
            segments: Transcript segments with timestamps
            animation_type: Type of animation (fade_in, slide_up, pop, typewriter)
            output_path: Optional output path
            word_by_word: Animate word by word vs sentence by sentence
            
        Returns:
            Path to the final video with captions
        """
        console.print(f"[bold cyan]✨ Adding animated text ({animation_type})...[/]")
        
        # Load the video
        video = VideoFileClip(str(video_path))
        video_duration = video.duration
        
        # Get video dimensions
        video_w, video_h = video.size
        
        # Create text clips with animations
        text_clips = []
        
        if word_by_word:
            text_clips = self._create_word_clips(
                segments, video_w, video_h, animation_type, video_duration
            )
        else:
            text_clips = self._create_sentence_clips(
                segments, video_w, video_h, animation_type, video_duration
            )
        
        # Composite video with text
        final_video = CompositeVideoClip([video] + text_clips)
        
        # Set duration
        final_video = final_video.set_duration(video_duration)
        
        # Generate output path
        if output_path is None:
            output_path = OUTPUT_DIR / f"{video_path.stem}_captioned.mp4"
        
        output_path.parent.mkdir(exist_ok=True)
        
        # Write final video
        final_video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            fps=OUTPUT_FPS
        )
        
        # Clean up
        video.close()
        for clip in text_clips:
            clip.close()
        final_video.close()
        
        console.print(f"[bold green]✅ Video saved:[/] {output_path.name}")
        return output_path
    
    def _create_word_clips(
        self,
        segments: List[Dict],
        video_w: int,
        video_h: int,
        animation_type: str,
        max_duration: float
    ) -> List[TextClip]:
        """Create animated text clips for each word."""
        clips = []
        
        for segment in segments:
            if 'words' not in segment:
                continue
            
            for word_data in segment['words']:
                start = word_data['start']
                end = word_data['end']
                word = word_data['word'].upper()  # Uppercase for impact
                
                # Skip if outside video duration
                if start >= max_duration:
                    continue
                
                # Adjust end time
                end = min(end, max_duration)
                duration = end - start
                
                if duration <= 0:
                    continue
                
                # Create text clip
                text_clip = self._create_animated_text(
                    text=word,
                    start=start,
                    duration=duration,
                    video_w=video_w,
                    video_h=video_h,
                    animation_type=animation_type
                )
                
                if text_clip:
                    clips.append(text_clip)
        
        return clips
    
    def _create_sentence_clips(
        self,
        segments: List[Dict],
        video_w: int,
        video_h: int,
        animation_type: str,
        max_duration: float
    ) -> List[TextClip]:
        """Create animated text clips for each sentence."""
        clips = []
        
        for segment in segments:
            start = segment['start']
            end = segment['end']
            text = segment['text'].upper()
            
            # Skip if outside video duration
            if start >= max_duration:
                continue
            
            # Limit text length per line
            if len(text) > 40:
                # Split into multiple lines
                words = text.split()
                lines = []
                current_line = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) > 35:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = len(word)
                    else:
                        current_line.append(word)
                        current_length += len(word) + 1
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                text = '\n'.join(lines)
            
            # Adjust times
            end = min(end, max_duration)
            duration = end - start
            
            if duration <= 0:
                continue
            
            text_clip = self._create_animated_text(
                text=text,
                start=start,
                duration=duration,
                video_w=video_w,
                video_h=video_h,
                animation_type=animation_type,
                is_sentence=True
            )
            
            if text_clip:
                clips.append(text_clip)
        
        return clips
    
    def _create_animated_text(
        self,
        text: str,
        start: float,
        duration: float,
        video_w: int,
        video_h: int,
        animation_type: str,
        is_sentence: bool = False
    ) -> Optional[TextClip]:
        """Create a single animated text clip."""
        try:
            # Adjust font size for sentences vs words
            font_size = self.font_size if not is_sentence else int(self.font_size * 0.8)
            
            # Create base text clip
            txt_clip = TextClip(
                text,
                fontsize=font_size,
                font=self.font,
                color=self.text_color,
                stroke_color=self.stroke_color,
                stroke_width=self.stroke_width,
                method='caption',
                size=(int(video_w * 0.9), None),
                align='center'
            )
            
            # Position at bottom third of screen
            txt_clip = txt_clip.set_position(('center', video_h * 0.7))
            
            # Apply animation
            txt_clip = self._apply_animation(
                txt_clip, animation_type, duration
            )
            
            # Set timing
            txt_clip = txt_clip.set_start(start).set_duration(duration)
            
            return txt_clip
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create text clip: {e}[/]")
            return None
    
    def _apply_animation(
        self,
        clip: TextClip,
        animation_type: str,
        duration: float
    ) -> TextClip:
        """Apply animation effect to text clip."""
        
        if animation_type == "fade_in":
            # Fade in effect
            clip = clip.crossfadein(min(0.3, duration / 3))
            
        elif animation_type == "slide_up":
            # Slide up from bottom
            def slide_up(t):
                if t < 0.3:
                    return ('center', 0.85 - (0.15 * (t / 0.3)))
                return ('center', 0.7)
            clip = clip.set_position(slide_up)
            
        elif animation_type == "pop":
            # Pop/scale effect (zoom in quickly then settle)
            def pop_effect(t):
                if t < 0.15:
                    scale = 0.5 + (0.7 * (t / 0.15))  # Scale from 0.5 to 1.2
                elif t < 0.25:
                    scale = 1.2 - (0.2 * ((t - 0.15) / 0.1))  # Scale from 1.2 to 1.0
                else:
                    scale = 1.0
                return scale
            
            clip = clip.resize(lambda t: pop_effect(t))
            clip = clip.crossfadein(0.1)
            
        elif animation_type == "typewriter":
            # Typewriter effect (handled differently - show progressively)
            clip = clip.crossfadein(0.05)
            
        elif animation_type == "shake":
            # Shake effect for emphasis
            def shake(t):
                if t < 0.2:
                    offset = 5 * math.sin(t * 50)
                    return ('center', 0.7 + offset / 1000)
                return ('center', 0.7)
            clip = clip.set_position(shake)
            
        elif animation_type == "glow":
            # Simple glow effect via opacity pulse
            def glow_opacity(t):
                return 0.8 + 0.2 * math.sin(t * 6)
            clip = clip.set_opacity(glow_opacity)
        
        return clip


def add_captions(
    video_path: Path,
    segments: List[Dict],
    animation_type: str = "pop",
    output_path: Optional[Path] = None,
    word_by_word: bool = True
) -> Path:
    """
    Convenience function to add animated captions.
    """
    animator = TextAnimator()
    return animator.add_animated_captions(
        video_path, segments, animation_type, output_path, word_by_word
    )
