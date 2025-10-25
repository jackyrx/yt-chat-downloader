"""
YouTube Chat/Comment Downloader Core Module

Downloads YouTube live chat replay and regular comments using innertube API and yt-dlp.
Outputs data in JSON format with user information, timestamps, and message content.

Features:
- Continuous polling mode for live streams - runs until Ctrl+C
- No arbitrary iteration limits
- Waits and retries when no continuation token is found (live streams)
- Waits and retries when duplicate continuation detected (live streams)
- Only stops on KeyboardInterrupt or fatal errors
"""

import json
import re
import time
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse

import requests
import yt_dlp
from dateutil import parser as date_parser


class YouTubeChatDownloader:
    """Main class for downloading YouTube chat and comments."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats."""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/v/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If no pattern matches, assume the input is already a video ID
        return url
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing control characters and extra whitespace."""
        if not text:
            return ""
        # Remove control characters and normalize unicode
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def _generate_handle_from_display_name(self, display_name: str) -> str:
        """Generate a clean handle from display name following YouTube conventions."""
        if not display_name:
            return "@unknown"
        
        # Remove the @ if it's already there
        clean_name = display_name.lstrip('@')
        
        # Remove or replace special characters, keep alphanumeric, underscore, hyphen
        # YouTube handles can contain letters, numbers, underscore, and hyphen
        clean_name = re.sub(r'[^\w\-]', '', clean_name)
        
        # Remove multiple consecutive underscores/hyphens
        clean_name = re.sub(r'[_\-]+', '_', clean_name)
        
        # Ensure it doesn't start or end with underscore/hyphen
        clean_name = clean_name.strip('_-')
        
        # If nothing left, use fallback
        if not clean_name:
            clean_name = "user"
        
        # Ensure reasonable length (YouTube handles are typically 3-30 characters)
        if len(clean_name) > 30:
            clean_name = clean_name[:30]
        
        return f"@{clean_name}"
    
    def _extract_author_info(self, renderer: Dict) -> Dict[str, str]:
        """Extract and normalize author information from renderer.
        
        Returns dict with keys: display_name, handle, author_id, thumbnail
        """
        result = {
            'display_name': '',
            'handle': '',
            'author_id': '',
            'thumbnail': ''
        }
        
        # Get author ID first
        result['author_id'] = renderer.get("authorExternalChannelId", "")
        
        # Get thumbnail
        if "authorPhoto" in renderer and "thumbnails" in renderer["authorPhoto"]:
            thumbnails = renderer["authorPhoto"]["thumbnails"]
            if thumbnails:
                result['thumbnail'] = thumbnails[0].get("url", "")
        
        # Strategy 1: Try to get both handle and display name from different sources
        author_name_simple = ""
        if "authorName" in renderer:
            author_name_simple = renderer["authorName"].get("simpleText", "").strip()
        
        # Check accessibility data for additional info
        accessibility_text = ""
        handle_from_accessibility = ""
        display_name_from_accessibility = ""
        
        if ("authorName" in renderer and 
            "accessibility" in renderer["authorName"] and
            "accessibilityData" in renderer["authorName"]["accessibility"]):
            accessibility_text = renderer["authorName"]["accessibility"]["accessibilityData"].get("label", "")
            
            # Try to extract handle from accessibility (often contains @handle)
            handle_match = re.search(r'@([\w\-_.]+)', accessibility_text)
            if handle_match:
                handle_from_accessibility = f"@{handle_match.group(1)}"
            
            # Sometimes accessibility contains display name without @
            if not handle_match and accessibility_text and not accessibility_text.startswith('@'):
                display_name_from_accessibility = self._normalize_text(accessibility_text)
        
        # Strategy 2: Determine what author_name_simple contains
        author_name_simple = self._normalize_text(author_name_simple)
        
        if author_name_simple.startswith('@'):
            # simpleText is a handle
            result['handle'] = author_name_simple
            # Try to get display name from accessibility or use handle as fallback
            if display_name_from_accessibility:
                result['display_name'] = display_name_from_accessibility
            else:
                result['display_name'] = author_name_simple.lstrip('@')
        else:
            # simpleText is likely a display name
            result['display_name'] = author_name_simple
            # Use handle from accessibility if available, otherwise generate
            if handle_from_accessibility:
                result['handle'] = handle_from_accessibility
            else:
                result['handle'] = self._generate_handle_from_display_name(author_name_simple)
        
        # Strategy 3: Fallback handling - ensure both fields are populated
        if not result['display_name'] and result['handle']:
            result['display_name'] = result['handle'].lstrip('@')
        elif not result['handle'] and result['display_name']:
            result['handle'] = self._generate_handle_from_display_name(result['display_name'])
        elif not result['display_name'] and not result['handle']:
            # Last resort fallbacks
            if author_name_simple:
                if author_name_simple.startswith('@'):
                    result['handle'] = author_name_simple
                    result['display_name'] = author_name_simple.lstrip('@')
                else:
                    result['display_name'] = author_name_simple
                    result['handle'] = self._generate_handle_from_display_name(author_name_simple)
            else:
                # Very last resort
                result['display_name'] = "Unknown User"
                result['handle'] = "@unknown"
        
        # Final normalization
        result['display_name'] = self._normalize_text(result['display_name'])
        if not result['handle'].startswith('@'):
            result['handle'] = f"@{result['handle']}"
        
        return result
    
    def get_video_info(self, video_id: str) -> Dict:
        """Get video information using yt-dlp."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info
            except Exception as e:
                raise Exception(f"Failed to get video info: {e}")
    
    def fetch_html(self, url: str) -> str:
        """Fetch HTML content from YouTube page."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
        response = self.session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    
    def extract_innertube_params(self, html: str) -> tuple:
        """Extract innertube API key, version, and ytInitialData from HTML."""
        # Extract API key
        key_match = re.search(r'INNERTUBE_API_KEY["\']\s*:\s*"([^"]+)"', html)
        api_key = key_match.group(1) if key_match else None
        
        # Extract client version
        ver_match = re.search(r'INNERTUBE_CONTEXT_CLIENT_VERSION["\']\s*:\s*"([^"]+)"', html)
        version = ver_match.group(1) if ver_match else "2.20201021.03.00"
        
        # Extract ytInitialData
        yid_match = re.search(r'ytInitialData["\']?\s*[:=]\s*(\{.*?\})[;\n]', html, flags=re.DOTALL)
        yid = json.loads(yid_match.group(1)) if yid_match else None
        
        return api_key, version, yid
    
    def find_continuation(self, ytInitialData: Dict) -> Optional[str]:
        """Find continuation token in ytInitialData."""
        def walk(obj):
            if isinstance(obj, dict):
                if "continuation" in obj:
                    return obj["continuation"]
                for v in obj.values():
                    res = walk(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = walk(item)
                    if res:
                        return res
            return None
        return walk(ytInitialData)
    
    def get_live_chat_data(self, api_key: str, version: str, continuation: str, is_live: bool = False, retries: int = 3) -> Dict:
        """Get live chat data using innertube API with proper parameters."""
        endpoint = "get_live_chat" if is_live else "get_live_chat_replay"
        url = f"https://www.youtube.com/youtubei/v1/live_chat/{endpoint}?key={api_key}"
        
        data = {
            "context": {"client": {"clientName": "WEB", "clientVersion": version}},
            "continuation": continuation,
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Content-Type": "application/json"
        }
        
        for attempt in range(retries):
            try:
                response = self.session.post(url, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    raise Exception(f"Bad request (400) using {endpoint} endpoint")
                else:
                    print(f"⚠️ HTTP {e.response.status_code}: {e} — Retry {attempt+1}/{retries}")
                    time.sleep(3)
            except requests.exceptions.RequestException as e:
                print(f"⚠️ {type(e).__name__}: {e} — Retry {attempt+1}/{retries}")
                time.sleep(3)
        
        raise Exception(f"Failed to get live chat after {retries} retries")
    
    def ms_to_timestamp(self, ms: Union[str, int]) -> str:
        """Convert milliseconds to MM:SS or HH:MM:SS format."""
        try:
            s = int(ms) // 1000
            m, s = divmod(s, 60)
            h, m = divmod(m, 60)
            if h > 0:
                return f"{h}:{m:02d}:{s:02d}"
            return f"{m}:{s:02d}"
        except:
            return "0:00"
    
    def extract_next_continuation(self, json_data: Dict) -> Optional[str]:
        """Extract next continuation token from API response."""
        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "continuation":
                        return v
                    res = walk(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = walk(item)
                    if res:
                        return res
            return None
        return walk(json_data)
    
    def parse_live_chat_messages(self, chat_data: Dict) -> tuple:
        """Parse live chat messages from API response."""
        messages = []
        latest_offset = 0
        
        # Get actions from different possible locations
        actions = None
        if "actions" in chat_data:
            actions = chat_data["actions"]
        elif "continuationContents" in chat_data:
            actions = chat_data["continuationContents"]["liveChatContinuation"].get("actions", [])
        elif "contents" in chat_data:
            actions = chat_data["contents"]["liveChatRenderer"].get("actions", [])
        
        if not actions:
            return messages, latest_offset
        
        for action in actions:
            if "replayChatItemAction" in action:
                # Handle replay chat items (VOD live chat replay)
                replay_action = action["replayChatItemAction"]
                video_offset = replay_action.get("videoOffsetTimeMsec", "0")
                
                # Skip negative timestamps
                try:
                    offset_ms = int(float(video_offset))
                    if offset_ms < 0:
                        continue
                except:
                    continue
                
                # Get the actual chat item
                chat_actions = replay_action.get("actions", [])
                if chat_actions and "addChatItemAction" in chat_actions[0]:
                    item = chat_actions[0]["addChatItemAction"]["item"]
                    
                    # Parse different message types
                    for msg_type in ["liveChatTextMessageRenderer", "liveChatPaidMessageRenderer", "liveChatMembershipItemRenderer"]:
                        if msg_type in item:
                            renderer = item[msg_type]
                            message_data = self._parse_message_renderer(renderer, video_offset)
                            if message_data:
                                messages.append(message_data)
                                if offset_ms > latest_offset:
                                    latest_offset = offset_ms
                                    
            elif "addChatItemAction" in action:
                # Handle regular live chat items (active live streams)
                item = action["addChatItemAction"]["item"]
                
                # Get timestamp from action if available (for live streams)
                video_offset = "0"
                if "timestampUsec" in action.get("addChatItemAction", {}):
                    video_offset = str(int(action["addChatItemAction"]["timestampUsec"]) // 1000)  # Convert to ms
                
                for msg_type in ["liveChatTextMessageRenderer", "liveChatPaidMessageRenderer", "liveChatMembershipItemRenderer"]:
                    if msg_type in item:
                        renderer = item[msg_type]
                        message_data = self._parse_message_renderer(renderer, video_offset)
                        if message_data:
                            messages.append(message_data)
                            try:
                                offset_ms = int(float(video_offset))
                                if offset_ms > latest_offset:
                                    latest_offset = offset_ms
                            except:
                                pass
        
        return messages, latest_offset
    
    def _parse_message_renderer(self, renderer: Dict, video_offset: str = "0") -> Optional[Dict]:
        """Parse message renderer (both text and paid messages)."""
        try:
            # Get author info
            author = renderer.get("authorName", {})
            author_name = author.get("simpleText", "").strip()
            if not author_name:
                return None

            # Get author ID
            author_id = renderer.get("authorExternalChannelId", "")
            
            # Parse message text
            message_text = ""
            if "message" in renderer and "runs" in renderer["message"]:
                for run in renderer["message"]["runs"]:
                    if "text" in run:
                        message_text += run["text"]
            elif "message" in renderer and "simpleText" in renderer["message"]:
                message_text = renderer["message"]["simpleText"]
            
            message_text = self._normalize_text(message_text)
            if not message_text:
                return None
            
            # Handle timestamps
            time_text = "0:00"
            iso_timestamp = ""
            
            # Try to get video offset timestamp
            if video_offset and video_offset != "0":
                try:
                    offset_ms = int(float(video_offset))
                    if offset_ms >= 0:  # Skip negative timestamps
                        time_text = self.ms_to_timestamp(offset_ms)
                except:
                    pass
            
            # Try to get timestamp from renderer
            if "timestampText" in renderer:
                timestamp_text = renderer["timestampText"].get("simpleText", "").strip()
                if timestamp_text and not timestamp_text.startswith("-"):
                    time_text = timestamp_text
            
            # Try to get microsecond timestamp for ISO format
            if "timestampUsec" in renderer:
                try:
                    dt = datetime.fromtimestamp(int(renderer["timestampUsec"]) / 1000000)
                    iso_timestamp = dt.isoformat()
                except:
                    pass
            
            # Determine message type
            message_type = "text"
            purchase_amount = ""
            
            if "liveChatPaidMessageRenderer" in str(renderer):
                message_type = "super_chat"
                if "purchaseAmountText" in renderer:
                    purchase_amount = renderer["purchaseAmountText"].get("simpleText", "")
            elif "liveChatMembershipItemRenderer" in str(renderer):
                message_type = "membership"
            
            return {
                "renderer": renderer,
                "author": json.dumps(renderer),
                "user_id": author_id,
                "user_display_name": author_name,
                "user_handle": author_name,
                "datetime": iso_timestamp,
                "timestamp": time_text,
                "comment": message_text,
                "message_type": message_type,
                "badges": self._extract_badges(renderer),
                "message_id": renderer.get("id", ""),
                "purchase_amount": purchase_amount,
                "video_offset_ms": video_offset
            }
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None
    
    def _extract_badges(self, renderer: Dict) -> List[str]:
        """Extract author badges from renderer."""
        badges = []
        if "authorBadges" in renderer:
            for badge in renderer["authorBadges"]:
                if "liveChatAuthorBadgeRenderer" in badge:
                    # Try multiple ways to get badge info
                    badge_info = badge["liveChatAuthorBadgeRenderer"]
                    badge_text = ""
                    
                    # Method 1: From accessibility
                    if "accessibility" in badge_info:
                        badge_text = badge_info["accessibility"].get("accessibilityData", {}).get("label", "")
                    
                    # Method 2: From tooltip
                    if not badge_text and "tooltip" in badge_info:
                        badge_text = badge_info["tooltip"]
                    
                    # Method 3: From customThumbnail alt text
                    if not badge_text and "customThumbnail" in badge_info:
                        badge_text = badge_info["customThumbnail"].get("accessibility", {}).get("accessibilityData", {}).get("label", "")
                    
                    if badge_text:
                        badges.append(self._normalize_text(badge_text))
        return badges
    
    def get_regular_comments(self, video_id: str) -> List[Dict]:
        """Get regular video comments using yt-dlp with refined author info."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        comments = []
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                if 'comments' in info:
                    for comment in info['comments']:
                        # Refined author info extraction for regular comments
                        author_name = self._normalize_text(comment.get('author', ''))
                        author_id = comment.get('author_id', '')
                        
                        # Determine if author name is handle or display name
                        if author_name.startswith('@'):
                            user_handle = author_name
                            user_display_name = author_name.lstrip('@')
                        else:
                            user_display_name = author_name
                            user_handle = self._generate_handle_from_display_name(author_name)
                        
                        # Ensure both fields are populated
                        if not user_display_name and user_handle:
                            user_display_name = user_handle.lstrip('@')
                        elif not user_handle and user_display_name:
                            user_handle = self._generate_handle_from_display_name(user_display_name)
                        elif not user_display_name and not user_handle:
                            user_display_name = "Unknown User"
                            user_handle = "@unknown"
                        
                        # Parse timestamp
                        comment_timestamp = comment.get('timestamp', '')
                        iso_timestamp = ""
                        if comment_timestamp:
                            try:
                                # If it's a unix timestamp
                                if isinstance(comment_timestamp, (int, float)):
                                    dt = datetime.fromtimestamp(comment_timestamp)
                                    iso_timestamp = dt.isoformat()
                                elif isinstance(comment_timestamp, str):
                                    # Try to parse as ISO format or other formats
                                    try:
                                        dt = date_parser.parse(comment_timestamp)
                                        iso_timestamp = dt.isoformat()
                                    except:
                                        iso_timestamp = comment_timestamp
                            except:
                                iso_timestamp = str(comment_timestamp)
                        
                        comment_data = {
                            "user_id": author_id,
                            "user_display_name": user_display_name,
                            "user_handle": user_handle,
                            "datetime": iso_timestamp,
                            "timestamp": "",
                            "comment": self._normalize_text(comment.get('text', '')),
                            "message_type": "comment",
                            "like_count": comment.get('like_count', 0),
                            "reply_count": comment.get('reply_count', 0),
                            "author_thumbnail": comment.get('author_thumbnail', ''),
                            "message_id": comment.get('id', ''),
                            "badges": [],
                            "purchase_amount": "",
                            "video_offset_ms": "0"
                        }
                        comments.append(comment_data)
        except Exception as e:
            print(f"Error getting regular comments: {e}")
        
        return comments
    
    def save_messages_incremental(self, messages: List[Dict], output_file: str):
        """Save messages to JSON file incrementally."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error saving to file: {e}")
    
    def print_message(self, msg: Dict):
        """Print message in real-time with formatted output."""
        datetime_str = msg.get('datetime', '')
        if datetime_str:
            # Format ISO datetime to more readable format
            try:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                datetime_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        timestamp = msg.get('timestamp', '')
        display_name = msg.get('user_display_name', '')
        handle = msg.get('user_handle', '')
        comment = msg.get('comment', '')
        badges = msg.get('badges', [])
        
        # Use timestamp or datetime, prefer timestamp for video offset
        time_display = timestamp if timestamp and timestamp != '0:00' else datetime_str
        
        # Add badges to display if present
        badge_str = ""
        if badges:
            badge_str = f" [{', '.join(badges)}]"
        
        # Format: [datetime] handle (display name)[badges]: message
        if time_display:
            print(f"[{time_display}] {handle} ({display_name}){badge_str}: {comment}")
        else:
            print(f"{handle} ({display_name}){badge_str}: {comment}")
    
    def download_chat(self, video_url: str, chat_type: str = "both", output_file: Optional[str] = None, quiet: bool = False) -> List[Dict]:
        """Main method to download chat/comments with continuous polling for live streams."""
        video_id = self.extract_video_id(video_url)
        all_messages = []
        
        if not quiet:
            print(f"Downloading chat for video ID: {video_id}")
        
        # Get video info first
        try:
            video_info = self.get_video_info(video_id)
            if not quiet:
                print(f"Video title: {video_info.get('title', 'Unknown')}")
            duration = video_info.get('duration', 0)
            is_live = video_info.get('is_live', False)
            if not quiet and is_live:
                print(f"🔴 LIVE STREAM DETECTED - Continuous polling mode enabled")
                print(f"⌨️  Press Ctrl+C to stop downloading")
        except Exception as e:
            if not quiet:
                print(f"Warning: Could not get video info: {e}")
            duration = 0
            is_live = False
        
        if chat_type in ["live", "both"]:
            if not quiet:
                print("Downloading live chat...")
                print("="*60)
            try:
                # Fetch HTML to get innertube parameters
                full_url = f"https://www.youtube.com/watch?v={video_id}"
                html = self.fetch_html(full_url)
                api_key, version, yid = self.extract_innertube_params(html)
                
                if not api_key:
                    if not quiet:
                        print("❌ Could not extract innertube API key")
                    return all_messages
                
                if not yid:
                    if not quiet:
                        print("❌ Could not extract ytInitialData")
                    return all_messages
                
                # Find initial continuation token
                continuation = self.find_continuation(yid)
                if not continuation:
                    if not quiet:
                        print("❌ Could not find continuation token - video may not have live chat")
                    if chat_type == "live":
                        return all_messages
                    # If "both", continue to try regular comments
                    continuation = None
                
                if continuation and not quiet:
                    print(f"✅ Found continuation token")
                    print(f"✅ API Key: {api_key[:20]}...")
                    print(f"✅ Client Version: {version}")
                    print("="*60)
                
                # Only proceed if we have a valid continuation token
                if not continuation:
                    print("⚠️ No continuation token, skipping live chat download")
                else:
                    # Track seen continuations for duplicate detection
                    seen_continuations = {}  # Map continuation to count
                    max_seen_offset = 0
                    total_messages = 0
                    request_count = 0
                    
                    # Determine if we should use live or replay endpoint
                    # Try replay first, fall back to live if it fails
                    is_live_stream = False
                    first_request = True
                    
                    # Counters for waiting/polling
                    no_continuation_count = 0
                    duplicate_continuation_count = 0
                    
                    # Fetch chat messages continuously until interrupted
                    while True:
                        request_count += 1
                        
                        # Check for duplicate continuation (with tolerance for live streams)
                        if continuation in seen_continuations:
                            seen_continuations[continuation] += 1
                            duplicate_continuation_count += 1
                            
                            # For live streams, wait and retry instead of stopping
                            if is_live_stream or is_live:
                                if not quiet:
                                    print(f"⏸️  Duplicate continuation #{duplicate_continuation_count} - waiting for new messages... (Ctrl+C to stop)")
                                time.sleep(5)  # Wait 5 seconds before retrying
                                
                                # After 10 duplicates, try refreshing the continuation
                                if duplicate_continuation_count >= 10:
                                    if not quiet:
                                        print(f"🔄 Refreshing continuation token...")
                                    try:
                                        html = self.fetch_html(full_url)
                                        _, _, yid = self.extract_innertube_params(html)
                                        new_continuation = self.find_continuation(yid)
                                        if new_continuation and new_continuation != continuation:
                                            continuation = new_continuation
                                            seen_continuations = {}  # Reset seen continuations
                                            duplicate_continuation_count = 0
                                            if not quiet:
                                                print(f"✅ Got new continuation token")
                                            continue
                                    except:
                                        pass
                                    
                                # Continue polling
                                continue
                            else:
                                # For replays, stop on duplicate
                                if not quiet:
                                    print("🔁 Duplicate continuation in replay - end of chat reached")
                                break
                        else:
                            seen_continuations[continuation] = 1
                            duplicate_continuation_count = 0  # Reset counter
                        
                        # Get chat data - try both endpoints on first request
                        try:
                            if first_request:
                                try:
                                    chat_data = self.get_live_chat_data(api_key, version, continuation, is_live=False)
                                    first_request = False
                                except Exception as e:
                                    if "400" in str(e):
                                        # Try the live endpoint instead
                                        print("⚠️ Replay endpoint failed, trying live stream endpoint...")
                                        try:
                                            chat_data = self.get_live_chat_data(api_key, version, continuation, is_live=True)
                                            is_live_stream = True
                                            first_request = False
                                            print("✅ Using live stream endpoint")
                                        except Exception as e2:
                                            raise Exception(f"Both endpoints failed: {e}, {e2}")
                                    else:
                                        raise
                            else:
                                # Use the endpoint that worked
                                chat_data = self.get_live_chat_data(api_key, version, continuation, is_live=is_live_stream)
                        except Exception as e:
                            if not quiet:
                                print(f"❌ Error getting chat data: {e}")
                            if is_live_stream or is_live:
                                if not quiet:
                                    print(f"⏸️  Waiting before retry...")
                                time.sleep(10)
                                continue
                            else:
                                break
                        
                        messages, latest_offset = self.parse_live_chat_messages(chat_data)
                        
                        if latest_offset > max_seen_offset:
                            max_seen_offset = latest_offset
                        
                        # Print and save each message in real-time
                        for msg in messages:
                            all_messages.append(msg)
                            total_messages += 1
                            
                            # Print message in real-time
                            if not quiet:
                                self.print_message(msg)
                        
                        # Save to file incrementally (every batch)
                        if output_file:
                            self.save_messages_incremental(all_messages, output_file)
                        
                        # Get next continuation token
                        next_continuation = self.extract_next_continuation(chat_data)
                        if not next_continuation:
                            no_continuation_count += 1
                            
                            # For live streams, wait and retry instead of stopping
                            if is_live_stream or is_live:
                                if not quiet:
                                    print(f"⏸️  No continuation token #{no_continuation_count} - waiting for new messages... (Ctrl+C to stop)")
                                time.sleep(5)  # Wait 5 seconds before retrying with same continuation
                                
                                # After multiple attempts, try refreshing
                                if no_continuation_count >= 5:
                                    if not quiet:
                                        print(f"🔄 Attempting to refresh continuation...")
                                    try:
                                        html = self.fetch_html(full_url)
                                        _, _, yid = self.extract_innertube_params(html)
                                        new_continuation = self.find_continuation(yid)
                                        if new_continuation:
                                            continuation = new_continuation
                                            seen_continuations = {}  # Reset
                                            no_continuation_count = 0
                                            if not quiet:
                                                print(f"✅ Got new continuation token")
                                            continue
                                    except:
                                        pass
                                
                                # Continue with same continuation
                                continue
                            else:
                                # For replays, stop when no continuation
                                if not quiet:
                                    print("\n🟢 No more continuation tokens - end of replay")
                                break
                        else:
                            continuation = next_continuation
                            no_continuation_count = 0  # Reset counter
                        
                        # Rate limiting - slower for live streams to avoid hammering API
                        if is_live_stream or is_live:
                            time.sleep(1.0)  # 1 second between requests for live
                        else:
                            time.sleep(0.08)  # Faster for replays
                        
                        # Progress update every 50 requests
                        if not quiet and request_count % 50 == 0:
                            print(f"\n⏳ Progress: {total_messages} messages, {request_count} requests, {max_seen_offset//1000}s video time\n")
                    
                    if not quiet:
                        print(f"\n{'='*60}")
                        print(f"✅ Live chat download complete: {total_messages} messages")
                        print(f"📊 Total requests: {request_count}")
                        print(f"{'='*60}")
                        
            except KeyboardInterrupt:
                if not quiet:
                    print(f"\n\n⚠️  Download interrupted by user (Ctrl+C)")
                    print(f"💾 Saving messages...")
                if output_file:
                    self.save_messages_incremental(all_messages, output_file)
                raise
            except Exception as e:
                print(f"Error downloading live chat: {e}")
        
        if chat_type in ["comments", "both"]:
            if not quiet:
                print("\nDownloading regular comments...")
                print("="*60)
            try:
                comments = self.get_regular_comments(video_id)
                
                # Print each comment in real-time
                for comment in comments:
                    all_messages.append(comment)
                    if not quiet:
                        self.print_message(comment)
                
                # Save after adding comments
                if output_file and comments:
                    self.save_messages_incremental(all_messages, output_file)
                
                if not quiet:
                    print(f"\n{'='*60}")
                    print(f"✅ Found {len(comments)} regular comments")
                    print(f"{'='*60}")
            except Exception as e:
                if not quiet:
                    print(f"Error downloading regular comments: {e}")
        
        # Sort by timestamp if available
        all_messages.sort(key=lambda x: int(x.get('video_offset_ms', '0')) if x.get('video_offset_ms', '0').isdigit() else 0)
        
        # Final save to file with sorted messages
        if output_file:
            self.save_messages_incremental(all_messages, output_file)
            if not quiet:
                print(f"\n💾 Saved {len(all_messages)} messages to {output_file}")
        
        return all_messages

