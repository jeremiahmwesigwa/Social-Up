import yt_dlp
import os
import tempfile
import logging
import re

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.supported_sites = {
            'youtube': r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)',
            'tiktok': r'(?:https?:\/\/)?(?:www\.)?(?:tiktok\.com)',
            'instagram': r'(?:https?:\/\/)?(?:www\.)?(?:instagram\.com)',
            'facebook': r'(?:https?:\/\/)?(?:www\.)?(?:facebook\.com|fb\.watch)'
        }

    def is_supported_url(self, url):
        for pattern in self.supported_sites.values():
            if re.match(pattern, url):
                return True
        return False

    def get_video_info(self, url):
        if not url:
            raise ValueError("URL cannot be empty")

        if not self.is_supported_url(url):
            raise ValueError("Unsupported video platform")

        logger.debug(f"Getting video info for URL: {url}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                logger.debug("Extracting video information...")
                info = ydl.extract_info(url, download=False)
                formats = []
                
                # Filter and simplify format information
                for f in info.get('formats', []):
                    # Include formats with either video or audio
                    if not (f.get('vcodec') == 'none' and f.get('acodec') == 'none'):
                        ext = f.get('ext', '')
                        if ext in ['mp4', 'webm']:
                            height = f.get('height', '?')
                            quality = f'{height}p' if height != '?' else 'best'
                            formats.append({
                                'ext': ext,
                                'quality': quality,
                                'format_id': f.get('format_id', '')
                            })

                result = {
                    'title': info.get('title', 'Untitled'),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': info.get('duration', 0),
                    'formats': formats
                }
                logger.debug(f"Successfully extracted video info: {result}")
                return result
            except Exception as e:
                logger.error(f"Error extracting video info: {str(e)}")
                raise Exception(f"Failed to get video info: {str(e)}")

    def download_video(self, url, format_ext):
        if not self.is_supported_url(url):
            raise ValueError("Unsupported video platform")

        logger.debug(f"Downloading video from URL: {url} in format: {format_ext}")
        
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, 'video.%(ext)s')

        ydl_opts = {
            'format': f'best[ext={format_ext}]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                logger.debug("Starting video download...")
                ydl.download([url])
                output_file = os.path.join(temp_dir, f'video.{format_ext}')
                
                if not os.path.exists(output_file):
                    logger.error("Download completed but output file not found")
                    raise Exception("Download failed - output file not found")
                
                logger.debug(f"Video successfully downloaded to: {output_file}")
                return output_file
            except Exception as e:
                logger.error(f"Error downloading video: {str(e)}")
                raise Exception(f"Download failed: {str(e)}")
