# YouTube Chat Downloader

This tool provides a simple method for retrieving chat logs from both past (VOD) and ongoing YouTube live streams for data analysis.
Live stream chats contain valuable data for understanding audience sentiment, identifying trends, and measuring engagement. 
This downloader makes that data accessible for your research.

A Python package to download YouTube live chat replays and regular comments from any YouTube video. Perfect for archiving live streams, analyzing chat interactions, or collecting comment data.

## Features

- 🔴 **Live Stream Support**: Continuous polling mode for active live streams
- 💬 **Chat Replay**: Download complete chat history from finished live streams
- 📝 **Regular Comments**: Fetch standard video comments
- 🎯 **Multiple Formats**: Support for text messages, super chats, and membership messages
- 📊 **Rich Metadata**: Includes user info, timestamps, badges, and more
- 💾 **Auto-saving**: Incremental JSON output (survives interruptions)
- ⌨️ **Graceful Interruption**: Press Ctrl+C to stop and save progress

## Installation

### From PyPI (when published)

```bash
pip install yt-chat-downloader
```

### From Source

```bash
git clone https://github.com/yourusername/yt-chat-downloader.git
cd yt-chat-downloader
pip install -e .
```

## Quick Start

### Command Line

Download both chat replay and comments:

```bash
yt-chat-downloader "https://www.youtube.com/watch?v=VIDEO_ID"
```

Download only live chat replay:

```bash
yt-chat-downloader VIDEO_ID --chat-type live
```

Download only regular comments:

```bash
yt-chat-downloader VIDEO_ID --chat-type comments
```

Specify output file:

```bash
yt-chat-downloader VIDEO_ID -o my_chat.json
```

Quiet mode (minimal output):

```bash
yt-chat-downloader VIDEO_ID --quiet
```

### Python API

```python
from yt_chat_downloader import YouTubeChatDownloader

# Initialize downloader
downloader = YouTubeChatDownloader()

# Download chat and comments
messages = downloader.download_chat(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    chat_type="both",  # Options: "live", "comments", "both"
    output_file="chat_data.json",
    quiet=False
)

# Process messages
for msg in messages:
    print(f"{msg['user_display_name']}: {msg['comment']}")
```

## Output Format

The downloader saves messages in JSON format with the following structure:

```json
[
  {
    "user_id": "UC...",
    "user_display_name": "Dev maker",
    "user_handle": "@devmaker",
    "datetime": "2024-01-15T10:30:00",
    "timestamp": "1:23:45",
    "comment": "Great stream!",
    "message_type": "text",
    "badges": ["Verified", "Member (6 months)"],
    "message_id": "...",
    "purchase_amount": "",
    "video_offset_ms": "5025000"
  }
]
```

### Message Types

- `text`: Regular chat message
- `super_chat`: Super Chat (paid message)
- `membership`: Membership milestone/welcome message
- `comment`: Regular video comment

## Live Stream Mode

For active live streams, the downloader enters **continuous polling mode**:

1. Automatically detects live streams
2. Polls for new messages continuously
3. Saves progress incrementally
4. Handles API rate limiting
5. Retries on temporary failures
6. Runs until you press Ctrl+C

Example:

```bash
yt-chat-downloader "https://www.youtube.com/watch?v=LIVE_VIDEO_ID"
# 🔴 LIVE STREAM DETECTED - Continuous polling mode enabled
# ⌨️  Press Ctrl+C to stop downloading
# [downloading messages...]
# ^C
# ⚠️  Download interrupted by user
# 💾 Messages saved to: youtube_chat_LIVE_VIDEO_ID_1234567890.json
```

## Dependencies

- Python 3.7+
- `click` - Command-line interface
- `requests` - HTTP requests
- `yt-dlp` - YouTube metadata extraction
- `python-dateutil` - Date parsing

## Use Cases

- **Archive live streams**: Save chat before it's deleted
- **Research & Analysis**: Analyze viewer engagement and sentiment
- **Content Creation**: Create highlight reels with chat context
- **Moderation**: Review chat history for moderation purposes
- **Bot Development**: Collect training data for chatbots

## Limitations

- Requires video to have live chat enabled
- Some videos may have chat disabled or deleted
- Rate limiting applies (handled automatically)
- Very old videos may have incomplete chat data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and archival purposes. Please respect YouTube's Terms of Service and the privacy of content creators and chat participants. Use responsibly.

## Acknowledgments

- Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp) for video metadata
- Uses YouTube's internal InnerTube API for chat data

## Support

If you encounter any issues or have questions:

- Open an issue on [GitHub](https://github.com/yourusername/yt-chat-downloader/issues)
- Check existing issues for solutions
- Provide video ID and error messages when reporting bugs

---

Made with ❤️ for the YouTube archiving community