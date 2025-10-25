# Examples

This directory contains example scripts demonstrating how to use the `yt-chat-downloader` package.

## Files

- `basic_usage.py` - Basic usage examples for the Python API

## Running Examples

Make sure you have the package installed:

```bash
pip install yt-chat-downloader
```

Then run any example:

```bash
python examples/basic_usage.py
```

Remember to replace `VIDEO_ID` with an actual YouTube video ID in the examples!

## Example Use Cases

### 1. Archive a Live Stream Chat

```python
from yt_chat_downloader import YouTubeChatDownloader

downloader = YouTubeChatDownloader()
messages = downloader.download_chat(
    video_url="https://www.youtube.com/watch?v=LIVE_VIDEO_ID",
    output_file="archived_chat.json"
)
```

### 2. Analyze Comment Sentiment

```python
from yt_chat_downloader import YouTubeChatDownloader

downloader = YouTubeChatDownloader()
messages = downloader.download_chat(
    video_url="VIDEO_ID",
    chat_type="comments",
    quiet=True
)

# Process comments for sentiment analysis
for msg in messages:
    comment_text = msg['comment']
    # Your sentiment analysis code here
```

### 3. Track Super Chats

```python
from yt_chat_downloader import YouTubeChatDownloader

downloader = YouTubeChatDownloader()
messages = downloader.download_chat(
    video_url="VIDEO_ID",
    chat_type="live"
)

# Filter super chats
super_chats = [m for m in messages if m['message_type'] == 'super_chat']

total_revenue = 0
for sc in super_chats:
    print(f"{sc['user_display_name']}: {sc['purchase_amount']} - {sc['comment']}")
```

