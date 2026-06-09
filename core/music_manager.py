import asyncio
import yt_dlp

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

YDL_SEARCH_OPTS = {
    'quiet': True,
    'skip_download': True,
    'extract_flat': True,
    'cookies_from_browser': 'chrome',
}

YDL_PLAY_OPTS = {
    'quiet': True,
    'format': 'bestaudio/best',
    'skip_download': True,
    'cookies_from_browser': 'chrome',
}


class MusicManager:

    def __init__(self):
        self._states: dict = {}

    def get_state(self, channel_id: int) -> dict:
        if channel_id not in self._states:
            self._states[channel_id] = {
                "songs": [],
                "is_playing": False,
                "is_skip": False,
            }
        return self._states[channel_id]

    def clear_state(self, channel_id: int) -> None:
        if channel_id in self._states:
            del self._states[channel_id]

    async def search_yt(self, keyword: str, max_results: int = 5) -> list | None:
        search_query = f"ytsearch{max_results}:{keyword}"

        def fetch():
            with yt_dlp.YoutubeDL(YDL_SEARCH_OPTS) as ydl:
                return ydl.extract_info(search_query, download=False)

        info = await asyncio.to_thread(fetch)

        if 'entries' in info and len(info['entries']) > 0:
            result = []
            for entry in info['entries']:
                if entry:
                    result.append(entry)
                if len(result) >= max_results:
                    break
            return result
        return None

    async def fetch_audio_url(self, song: dict) -> dict:
        url = song.get('webpage_url') or song.get('url', '')

        def fetch():
            with yt_dlp.YoutubeDL(YDL_PLAY_OPTS) as ydl:
                return ydl.extract_info(url, download=False)

        return await asyncio.to_thread(fetch)

    async def fetch_single(self, url: str) -> dict:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': False,
            'noplaylist': True,
            'cookies_from_browser': 'chrome',
        }

        def fetch():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        return await asyncio.to_thread(fetch)