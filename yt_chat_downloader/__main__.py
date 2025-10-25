"""
Command-line interface for YouTube Chat Downloader.
"""

import re
import time
from typing import Optional

import click

from .downloader import YouTubeChatDownloader


@click.command()
@click.argument('video_url', type=str)
@click.option('--chat-type', '-t', 
              type=click.Choice(['live', 'comments', 'both'], case_sensitive=False),
              default='both',
              help='Type of chat to download: live (live chat replay), comments (regular comments), or both')
@click.option('--output', '-o', 
              type=click.Path(),
              help='Output JSON file path (default: auto-generated)')
@click.option('--quiet', '-q', 
              is_flag=True,
              help='Suppress progress output')
def main(video_url: str, chat_type: str, output: Optional[str], quiet: bool):
    """
    Download YouTube chat/comments for a video.
    
    Continuous polling mode for live streams - runs until Ctrl+C
    
    VIDEO_URL: YouTube video URL or video ID
    
    Examples:
    
        yt-chat-downloader https://www.youtube.com/watch?v=VIDEO_ID
        
        yt-chat-downloader VIDEO_ID --chat-type live
        
        yt-chat-downloader VIDEO_ID -o output.json --quiet
    """
    if not quiet:
        print(f"🎬 YouTube Chat Downloader")
        print(f"📺 Video URL: {video_url}")
        print(f"💬 Chat type: {chat_type}")
        print("=" * 60)
    
    # Generate output filename if not provided
    if not output:
        video_id = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)', video_url)
        if video_id:
            video_id = video_id.group(1)
        else:
            video_id = video_url
        output = f"youtube_chat_{video_id}_{int(time.time())}.json"
    
    try:
        downloader = YouTubeChatDownloader()
        messages = downloader.download_chat(video_url, chat_type, output, quiet=quiet)
        
        if not quiet:
            print(f"\n{'='*60}")
            print(f"✅ Download complete!")
            print(f"📊 Total messages: {len(messages)}")
            print(f"📁 Output file: {output}")
            print(f"{'='*60}")
    
    except KeyboardInterrupt:
        if not quiet:
            print(f"\n\n⚠️  Download interrupted by user")
            print(f"💾 Messages saved to: {output}")
            print(f"📊 Partial download completed")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise click.Abort()


if __name__ == "__main__":
    main()

