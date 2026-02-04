"""Video clipper for extracting hook segments."""

from pathlib import Path
from typing import Optional, Dict, Tuple
from moviepy import VideoFileClip, CompositeVideoClip
from rich.console import Console

from .config import TEMP_DIR, OUTPUT_RESOLUTION

console = Console()


class VideoClipper:
    """Extract and resize video segments for shorts."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or TEMP_DIR
        self.output_dir.mkdir(exist_ok=True)
    
    def clip(
        self,
        video_path: Path,
        start_time: float,
        end_time: float,
        output_name: Optional[str] = None,
        crop_to_vertical: bool = True
    ) -> Path:
        """
        Extract a segment from a video.
        
        Args:
            video_path: Path to the source video
            start_time: Start time in seconds
            end_time: End time in seconds
            output_name: Optional output filename
            crop_to_vertical: Whether to crop to 9:16 aspect ratio
            
        Returns:
            Path to the clipped video
        """
        console.print(f"[bold blue]✂️ Clipping:[/] {start_time:.1f}s - {end_time:.1f}s")
        
        # Load video
        video = VideoFileClip(str(video_path))
        
        # Extract subclip (MoviePy 2.x uses subclipped instead of subclip)
        clip = video.subclipped(start_time, min(end_time, video.duration))
        
        # Crop to vertical format if requested
        if crop_to_vertical:
            clip = self._crop_to_vertical(clip)
        
        # Generate output path
        if output_name is None:
            output_name = f"{video_path.stem}_clip_{int(start_time)}_{int(end_time)}"
        output_path = self.output_dir / f"{output_name}.mp4"
        
        # Write clip
        clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=str(self.output_dir / "temp_audio.m4a"),
            remove_temp=True
        )
        
        # Clean up
        clip.close()
        video.close()
        
        console.print(f"[bold green]✅ Clip saved:[/] {output_path.name}")
        return output_path
    
    def _crop_to_vertical(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Crop video to 9:16 vertical aspect ratio.
        Centers on the middle of the frame (good for talking head videos).
        """
        original_w, original_h = clip.size
        target_w, target_h = OUTPUT_RESOLUTION  # 1080x1920
        target_ratio = target_h / target_w  # 16/9 for vertical
        
        original_ratio = original_h / original_w
        
        if original_ratio < target_ratio:
            # Video is wider than target - crop width
            new_w = int(original_h / target_ratio)
            new_h = original_h
            x_center = original_w // 2
            x1 = x_center - new_w // 2
            x2 = x_center + new_w // 2
            clip = clip.cropped(x1=x1, x2=x2)
        else:
            # Video is taller than target - crop height
            new_w = original_w
            new_h = int(original_w * target_ratio)
            y_center = original_h // 2
            y1 = y_center - new_h // 2
            y2 = y_center + new_h // 2
            clip = clip.cropped(y1=y1, y2=y2)
        
        # Resize to target resolution (MoviePy 2.x uses resized)
        clip = clip.resized(newsize=OUTPUT_RESOLUTION)
        
        return clip
    
    def clip_hook(
        self,
        video_path: Path,
        hook: Dict,
        hook_number: int = 1
    ) -> Path:
        """
        Extract a clip based on a hook dictionary.
        
        Args:
            video_path: Path to source video
            hook: Hook dictionary with start_time and end_time
            hook_number: Hook number for naming
            
        Returns:
            Path to the clipped video
        """
        return self.clip(
            video_path=video_path,
            start_time=hook['start_time'],
            end_time=hook['end_time'],
            output_name=f"hook_{hook_number}"
        )


def clip_video(
    video_path: Path,
    start_time: float,
    end_time: float,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Convenience function to clip a video segment.
    """
    clipper = VideoClipper(output_dir)
    return clipper.clip(video_path, start_time, end_time)
