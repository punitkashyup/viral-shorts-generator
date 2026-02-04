"""YouTube video downloader using yt-dlp."""

import os
from pathlib import Path
from typing import Optional, Callable
import yt_dlp
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .config import TEMP_DIR

console = Console()


class VideoDownloader:
    """Download YouTube videos using yt-dlp."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or TEMP_DIR
        self.output_dir.mkdir(exist_ok=True)
    
    def download(
        self, 
        url: str, 
        progress_callback: Optional[Callable] = None
    ) -> Path:
        """
        Download a YouTube video.
        
        Args:
            url: YouTube video URL
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to the downloaded video file
        """
        video_info = self._get_video_info(url)
        video_id = video_info.get('id', 'video')
        video_title = video_info.get('title', 'Untitled')
        
        console.print(f"[bold green]📥 Downloading:[/] {video_title}")
        
        output_template = str(self.output_dir / f"{video_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'progress_hooks': [self._create_progress_hook(progress_callback)],
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        video_path = self.output_dir / f"{video_id}.mp4"
        
        if not video_path.exists():
            # Try to find the file with different extension
            for ext in ['mp4', 'mkv', 'webm']:
                potential_path = self.output_dir / f"{video_id}.{ext}"
                if potential_path.exists():
                    video_path = potential_path
                    break
        
        if not video_path.exists():
            raise FileNotFoundError(f"Downloaded video not found at {video_path}")
        
        console.print(f"[bold green]✅ Downloaded:[/] {video_path.name}")
        return video_path
    
    def _get_video_info(self, url: str) -> dict:
        """Get video metadata without downloading."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info or {}
    
    def _create_progress_hook(self, callback: Optional[Callable] = None):
        """Create a progress hook for yt-dlp."""
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        task_id = None
        started = False
        
        def hook(d):
            nonlocal task_id, started
            
            if d['status'] == 'downloading':
                if not started:
                    progress.start()
                    task_id = progress.add_task("Downloading...", total=100)
                    started = True
                
                if d.get('total_bytes'):
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    progress.update(task_id, completed=percent)
                elif d.get('total_bytes_estimate'):
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    progress.update(task_id, completed=percent)
                
                if callback:
                    callback(d)
                    
            elif d['status'] == 'finished':
                if started:
                    progress.update(task_id, completed=100)
                    progress.stop()
                console.print("[dim]Processing video...[/]")
        
        return hook


def download_video(url: str, output_dir: Optional[Path] = None) -> Path:
    """
    Convenience function to download a YouTube video.
    
    Args:
        url: YouTube video URL
        output_dir: Optional output directory
        
    Returns:
        Path to the downloaded video file
    """
    downloader = VideoDownloader(output_dir)
    return downloader.download(url)
