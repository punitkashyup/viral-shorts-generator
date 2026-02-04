"""Main CLI entry point for the Viral Shorts Generator."""

import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import validate_config, OUTPUT_DIR, TEMP_DIR
from .downloader import download_video
from .audio_extractor import extract_audio
from .transcriber import transcribe_audio
from .hook_analyzer import analyze_hooks
from .video_clipper import VideoClipper
from .text_animator import TextAnimator

console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║        🎬 VIRAL SHORTS GENERATOR 🎬                       ║
║    Create viral hook videos from YouTube content          ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold magenta"))


@click.command()
@click.argument('youtube_url')
@click.option('--hooks', '-n', default=3, help='Number of hooks to generate')
@click.option('--animation', '-a', default='pop', 
              type=click.Choice(['fade_in', 'slide_up', 'pop', 'typewriter', 'shake', 'glow']),
              help='Text animation style')
@click.option('--word-by-word/--sentence', default=True, 
              help='Animate word by word or sentence by sentence')
@click.option('--keep-temp/--no-keep-temp', default=False,
              help='Keep temporary files after processing')
@click.option('--output-dir', '-o', type=click.Path(), default=None,
              help='Custom output directory')
def main(
    youtube_url: str,
    hooks: int,
    animation: str,
    word_by_word: bool,
    keep_temp: bool,
    output_dir: Optional[str]
):
    """
    Generate viral hook shorts from a YouTube video.
    
    YOUTUBE_URL: The URL of the YouTube video to process.
    
    Example:
        python -m src.main "https://youtube.com/watch?v=..."
    """
    print_banner()
    
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        console.print(f"[bold red]❌ Configuration Error:[/]\n{e}")
        sys.exit(1)
    
    # Set output directory
    final_output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    final_output_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Download the video
        console.print("\n[bold]📥 Step 1/6: Downloading video...[/]")
        video_path = download_video(youtube_url)
        
        # Step 2: Extract audio
        console.print("\n[bold]🎵 Step 2/6: Extracting audio...[/]")
        audio_path = extract_audio(video_path)
        
        # Step 3: Transcribe audio
        console.print("\n[bold]🎤 Step 3/6: Transcribing audio...[/]")
        transcript = transcribe_audio(audio_path)
        
        # Step 4: Analyze for hooks
        console.print("\n[bold]🤖 Step 4/6: Finding viral hooks...[/]")
        found_hooks = analyze_hooks(transcript, num_hooks=hooks)
        
        if not found_hooks:
            console.print("[bold red]❌ No hooks found in the video.[/]")
            sys.exit(1)
        
        # Step 5 & 6: Generate clips with captions
        console.print("\n[bold]✂️ Step 5/6: Creating clips...[/]")
        console.print("[bold]✨ Step 6/6: Adding animated captions...[/]")
        
        clipper = VideoClipper(TEMP_DIR)
        animator = TextAnimator()
        
        generated_shorts = []
        
        for i, hook in enumerate(found_hooks, 1):
            console.print(f"\n[cyan]Processing hook {i}/{len(found_hooks)}...[/]")
            
            # Clip the video segment
            clip_path = clipper.clip_hook(video_path, hook, i)
            
            # Get segments for this clip's time range
            clip_segments = get_segments_for_timerange(
                transcript['segments'],
                hook['start_time'],
                hook['end_time']
            )
            
            # Add animated captions
            output_path = final_output_dir / f"viral_hook_{i}.mp4"
            final_path = animator.add_animated_captions(
                clip_path,
                clip_segments,
                animation_type=animation,
                output_path=output_path,
                word_by_word=word_by_word
            )
            
            generated_shorts.append(final_path)
        
        # Clean up temp files
        if not keep_temp:
            cleanup_temp_files()
        
        # Print summary
        print_summary(generated_shorts, found_hooks)
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/] {e}")
        console.print("[dim]Run with --help for usage information.[/]")
        raise


def get_segments_for_timerange(
    segments: list,
    start_time: float,
    end_time: float
) -> list:
    """Get transcript segments that fall within a time range, adjusting timestamps."""
    clip_segments = []
    
    for seg in segments:
        # Check if segment overlaps with our time range
        if seg['end'] >= start_time and seg['start'] <= end_time:
            # Adjust timestamps to be relative to clip start
            adjusted_seg = {
                'start': max(0, seg['start'] - start_time),
                'end': min(end_time - start_time, seg['end'] - start_time),
                'text': seg['text']
            }
            
            # Adjust word timestamps if present
            if 'words' in seg:
                adjusted_words = []
                for word in seg['words']:
                    if word['end'] >= start_time and word['start'] <= end_time:
                        adjusted_words.append({
                            'start': max(0, word['start'] - start_time),
                            'end': min(end_time - start_time, word['end'] - start_time),
                            'word': word['word']
                        })
                adjusted_seg['words'] = adjusted_words
            
            clip_segments.append(adjusted_seg)
    
    return clip_segments


def cleanup_temp_files():
    """Remove temporary files."""
    console.print("\n[dim]🧹 Cleaning up temporary files...[/]")
    
    import shutil
    for item in TEMP_DIR.iterdir():
        try:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception:
            pass


def print_summary(shorts: list, hooks: list):
    """Print a summary of generated shorts."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]🎉 GENERATION COMPLETE! 🎉[/]",
        style="green"
    ))
    
    console.print(f"\n[bold]Generated {len(shorts)} viral shorts:[/]\n")
    
    for i, (short, hook) in enumerate(zip(shorts, hooks), 1):
        virality = "⭐" * min(hook.get('virality_score', 5), 10)
        hook_type = hook.get('hook_type', 'unknown').replace('_', ' ').title()
        console.print(f"  [cyan]{i}.[/] {short.name}")
        console.print(f"      Type: [magenta]{hook_type}[/] | Score: {virality}")
        console.print(f"      [dim]{hook.get('hook_text', '')[:60]}...[/]\n")
    
    console.print(f"\n[bold]📁 Output location:[/] {OUTPUT_DIR.absolute()}")
    console.print("\n[dim]Tip: Review the clips and pick the best ones for your channel![/]")


if __name__ == '__main__':
    main()
