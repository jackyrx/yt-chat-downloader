#!/usr/bin/env python3
"""
Basic usage examples for yt-chat-downloader
"""

from yt_chat_downloader import YouTubeChatDownloader


def example_basic():
    """Basic example: Download both chat and comments"""
    downloader = YouTubeChatDownloader()
    
    video_url = "https://www.youtube.com/watch?v=VIDEO_ID"
    
    messages = downloader.download_chat(
        video_url=video_url,
        chat_type="both",
        output_file="output.json",
        quiet=False
    )
    
    print(f"Downloaded {len(messages)} messages")


def example_live_chat_only():
    """Download only live chat replay"""
    downloader = YouTubeChatDownloader()
    
    messages = downloader.download_chat(
        video_url="VIDEO_ID",
        chat_type="live",
        output_file="live_chat.json"
    )
    
    return messages


def example_comments_only():
    """Download only regular comments"""
    downloader = YouTubeChatDownloader()
    
    messages = downloader.download_chat(
        video_url="VIDEO_ID",
        chat_type="comments",
        output_file="comments.json"
    )
    
    return messages


def example_process_messages():
    """Example: Download and process messages"""
    downloader = YouTubeChatDownloader()
    
    messages = downloader.download_chat(
        video_url="VIDEO_ID",
        chat_type="both",
        quiet=True
    )
    
    # Count message types
    message_types = {}
    for msg in messages:
        msg_type = msg.get('message_type', 'unknown')
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
    
    print("Message type breakdown:")
    for msg_type, count in message_types.items():
        print(f"  {msg_type}: {count}")
    
    # Find super chats
    super_chats = [m for m in messages if m.get('message_type') == 'super_chat']
    print(f"\nFound {len(super_chats)} super chats")
    
    # Get unique users
    unique_users = set(m.get('user_id') for m in messages if m.get('user_id'))
    print(f"Unique users: {len(unique_users)}")


def example_with_error_handling():
    """Example with proper error handling"""
    downloader = YouTubeChatDownloader()
    
    try:
        messages = downloader.download_chat(
            video_url="VIDEO_ID",
            chat_type="both",
            output_file="output.json"
        )
        print(f"Success! Downloaded {len(messages)} messages")
        
    except KeyboardInterrupt:
        print("Download interrupted by user")
        
    except Exception as e:
        print(f"Error occurred: {e}")


if __name__ == "__main__":
    # Run examples
    print("YouTube Chat Downloader - Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    # example_basic()
    # example_live_chat_only()
    # example_comments_only()
    # example_process_messages()
    # example_with_error_handling()
    
    print("\nEdit this file to run specific examples")

