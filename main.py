import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from downloader import VideoDownloader
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a-very-secret-key")

# Create temporary directory for downloads
temp_dir = tempfile.mkdtemp()
video_downloader = VideoDownloader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    logger.debug(f"Received URL for info: {url}")
    
    if not url:
        logger.error("No URL provided")
        return jsonify({'error': 'No URL provided'}), 400

    try:
        logger.debug("Attempting to get video info...")
        info = video_downloader.get_video_info(url)
        logger.debug(f"Successfully retrieved video info: {info}")
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    format_ext = request.form.get('format')
    logger.debug(f"Download request - URL: {url}, Format: {format_ext}")

    if not url or not format_ext:
        logger.error("Missing URL or format in download request")
        return jsonify({'error': 'Missing URL or format'}), 400

    try:
        # Create a unique temporary directory for this download
        temp_download_dir = tempfile.mkdtemp(prefix='video_download_')
        file_path = os.path.join(temp_download_dir, f'video.{format_ext}')
        
        try:
            # Download the video
            logger.debug(f"Starting video download to: {file_path}")
            file_path = video_downloader.download_video(url, format_ext)
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Downloaded file not found at: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError("Downloaded file is empty")
                
            logger.debug(f"Video downloaded successfully, size: {file_size} bytes")
            
            # Set up the response with appropriate headers
            mime_type = 'video/mp4' if format_ext == 'mp4' else 'video/webm'
            
            def generate():
                with open(file_path, 'rb') as video_file:
                    while True:
                        chunk = video_file.read(8192)
                        if not chunk:
                            break
                        yield chunk
                        
            response = app.response_class(
                generate(),
                mimetype=mime_type,
                direct_passthrough=True
            )
            
            response.headers.update({
                'Content-Length': file_size,
                'Content-Type': mime_type,
                'Content-Disposition': f'attachment; filename="video.{format_ext}"',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            })
            
            logger.debug("Starting file streaming...")
            return response
            
        except Exception as e:
            logger.error(f"Error processing download: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
        finally:
            # Cleanup temporary files
            try:
                if os.path.exists(temp_download_dir):
                    import shutil
                    shutil.rmtree(temp_download_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_download_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary files: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in download process: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
