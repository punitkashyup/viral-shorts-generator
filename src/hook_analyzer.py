"""AI-powered hook analyzer using OpenAI GPT-4."""

import json
from typing import List, Dict, Optional
from openai import OpenAI
from rich.console import Console
from rich.table import Table

from .config import OPENAI_API_KEY

console = Console()


class HookAnalyzer:
    """Analyze transcripts to find viral hook moments using GPT-4."""
    
    HOOK_ANALYSIS_PROMPT = """You are an expert viral video editor who specializes in creating attention-grabbing short-form content.

Analyze this transcript from a MrBeast video and identify the TOP {num_hooks} viral hook moments that would make amazing TikTok/YouTube Shorts.

TRANSCRIPT:
{transcript}

For each hook, provide:
1. start_time: The exact start timestamp in seconds
2. end_time: The exact end timestamp in seconds  
3. hook_text: The exact text of the hook moment
4. virality_score: Rating from 1-10 (10 = most viral potential)
5. hook_type: One of ["opening_hook", "shocking_reveal", "emotional_peak", "curiosity_gap", "call_to_action"]
6. reason: Brief explanation of why this moment is engaging

IMPORTANT RULES:
- Each clip should be 15-60 seconds long
- Focus on moments that would make someone STOP scrolling
- Look for: surprising numbers, emotional moments, questions, reveals, dramatic statements
- The hook should work as a standalone short video
- Prefer moments from the first half of the video for opening hooks

Respond ONLY with valid JSON in this exact format:
{{
    "hooks": [
        {{
            "start_time": 0.0,
            "end_time": 30.0,
            "hook_text": "The exact quote from the video",
            "virality_score": 9,
            "hook_type": "opening_hook",
            "reason": "Why this is engaging"
        }}
    ]
}}"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file.")
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze(
        self, 
        transcript_data: Dict, 
        num_hooks: int = 3
    ) -> List[Dict]:
        """
        Analyze transcript and find viral hooks.
        
        Args:
            transcript_data: Dictionary with 'segments' from transcriber
            num_hooks: Number of hooks to find
            
        Returns:
            List of hook dictionaries with timestamps and metadata
        """
        console.print("[bold magenta]🤖 Analyzing for viral hooks...[/]")
        
        # Format transcript with timestamps for context
        formatted_transcript = self._format_transcript(transcript_data['segments'])
        
        # Call GPT-4 for analysis
        prompt = self.HOOK_ANALYSIS_PROMPT.format(
            num_hooks=num_hooks,
            transcript=formatted_transcript
        )
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a viral video expert. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        hooks = result.get('hooks', [])
        
        # Validate and refine hook timestamps
        hooks = self._refine_timestamps(hooks, transcript_data['segments'])
        
        # Sort by virality score
        hooks.sort(key=lambda x: x.get('virality_score', 0), reverse=True)
        
        # Display results
        self._display_hooks(hooks)
        
        return hooks
    
    def _format_transcript(self, segments: List[Dict]) -> str:
        """Format transcript segments for the AI prompt."""
        lines = []
        for seg in segments:
            timestamp = f"[{seg['start']:.1f}s - {seg['end']:.1f}s]"
            lines.append(f"{timestamp} {seg['text']}")
        return "\n".join(lines)
    
    def _refine_timestamps(
        self, 
        hooks: List[Dict], 
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Refine hook timestamps to align with actual segment boundaries.
        """
        for hook in hooks:
            # Find the closest segment start/end
            start_time = hook.get('start_time', 0)
            end_time = hook.get('end_time', 30)
            
            # Adjust to segment boundaries
            for seg in segments:
                if abs(seg['start'] - start_time) < 2:
                    hook['start_time'] = seg['start']
                    break
            
            for seg in reversed(segments):
                if abs(seg['end'] - end_time) < 2:
                    hook['end_time'] = seg['end']
                    break
            
            # Ensure valid duration
            duration = hook['end_time'] - hook['start_time']
            if duration < 10:
                hook['end_time'] = hook['start_time'] + 15
            elif duration > 60:
                hook['end_time'] = hook['start_time'] + 60
        
        return hooks
    
    def _display_hooks(self, hooks: List[Dict]):
        """Display found hooks in a nice table."""
        table = Table(title="🎬 Viral Hooks Found", show_lines=True)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Time", style="yellow", width=15)
        table.add_column("Hook Text", style="white", width=50)
        table.add_column("Score", style="green", width=6)
        table.add_column("Type", style="magenta", width=15)
        
        for i, hook in enumerate(hooks, 1):
            time_range = f"{hook['start_time']:.1f}s - {hook['end_time']:.1f}s"
            text = hook.get('hook_text', '')[:50] + "..." if len(hook.get('hook_text', '')) > 50 else hook.get('hook_text', '')
            score = f"⭐ {hook.get('virality_score', 0)}/10"
            hook_type = hook.get('hook_type', 'unknown').replace('_', ' ').title()
            
            table.add_row(str(i), time_range, text, score, hook_type)
        
        console.print(table)


def analyze_hooks(
    transcript_data: Dict,
    num_hooks: int = 3,
    api_key: Optional[str] = None
) -> List[Dict]:
    """
    Convenience function to analyze transcript for hooks.
    
    Args:
        transcript_data: Transcription result from transcriber
        num_hooks: Number of hooks to find
        api_key: Optional OpenAI API key
        
    Returns:
        List of hook dictionaries
    """
    analyzer = HookAnalyzer(api_key)
    return analyzer.analyze(transcript_data, num_hooks)
