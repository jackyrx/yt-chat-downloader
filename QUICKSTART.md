# Quick Start Guide

Get started with **yt-chat-downloader** in 2 minutes!

## Installation

```bash
pip install yt-chat-downloader
```

Or install from source:
```bash
git clone https://github.com/yourusername/yt-chat-downloader.git
cd yt-chat-downloader
pip install -e .
```

## Basic Usage

### 1. Download Everything (Chat + Comments)

```bash
yt-chat-downloader "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

Output: `youtube_chat_dQw4w9WgXcQ_1234567890.json`

### 2. Download Only Live Chat Replay

```bash
yt-chat-downloader dQw4w9WgXcQ --chat-type live
```

### 3. Download Only Regular Comments

```bash
yt-chat-downloader dQw4w9WgXcQ --chat-type comments
```

### 4. Specify Output File

```bash
yt-chat-downloader dQw4w9WgXcQ -o my_chat.json
```

### 5. Quiet Mode (No Progress Output)

```bash
yt-chat-downloader dQw4w9WgXcQ --quiet
```

## Python Usage

```python
from yt_chat_downloader import YouTubeChatDownloader

# Create downloader
downloader = YouTubeChatDownloader()

# Download chat
messages = downloader.download_chat(
    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    chat_type="both",
    output_file="output.json"
)

# Process messages
print(f"Total messages: {len(messages)}")

for msg in messages[:5]:  # First 5 messages
    user = msg['user_display_name']
    comment = msg['comment']
    print(f"{user}: {comment}")
```

## Output Format

The output is a JSON file with this structure:

```json
[
  {
    "user_id": "UCxxxxx",
    "user_display_name": "John Doe",
    "user_handle": "@johndoe",
    "datetime": "2024-01-15T10:30:00",
    "timestamp": "1:23:45",
    "comment": "Great video!",
    "message_type": "text",
    "badges": ["Member (6 months)"],
    "message_id": "xxx",
    "purchase_amount": "",
    "video_offset_ms": "5025000"
  }
]
```

## Live Stream Mode

For **active live streams**, the tool automatically detects them and enters continuous polling mode:

```bash
yt-chat-downloader "LIVE_VIDEO_ID"
```

```
🔴 LIVE STREAM DETECTED - Continuous polling mode enabled
⌨️  Press Ctrl+C to stop downloading
[downloading messages in real-time...]
```

Press **Ctrl+C** to stop and save progress.

## Common Use Cases

### Archive a Live Stream
```bash
yt-chat-downloader LIVE_VIDEO_ID -o archive.json
```

### Get All Comments from a Video
```bash
yt-chat-downloader VIDEO_ID --chat-type comments -o comments.json
```

### Monitor Live Stream in Real-Time
```bash
yt-chat-downloader LIVE_VIDEO_ID --chat-type live
```

## Tips

1. **Video ID vs URL**: Both work! 
   - `yt-chat-downloader dQw4w9WgXcQ` 
   - `yt-chat-downloader "https://www.youtube.com/watch?v=dQw4w9WgXcQ"`

2. **Auto-generated filenames**: If you don't specify `-o`, the filename is automatically generated with video ID and timestamp.

3. **Interruption safety**: Press Ctrl+C anytime - your progress is saved!

4. **No chat available**: If a video doesn't have live chat or comments disabled, you'll see an error message.

## Help

Get full command help:
```bash
yt-chat-downloader --help
```

## Troubleshooting

**"Could not find continuation token"**
- Video may not have live chat enabled
- Try with `--chat-type comments` instead

**"Failed to get video info"**
- Check if the video ID is correct
- Video might be private or deleted

**Import error**
- Make sure package is installed: `pip install yt-chat-downloader`
- Try reinstalling: `pip uninstall yt-chat-downloader && pip install yt-chat-downloader`

## Next Steps

- Read the full [README.md](README.md) for advanced features
- Check out [examples/](examples/) for Python API examples
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

---

Happy downloading! 🎬

