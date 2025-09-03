document.addEventListener('DOMContentLoaded', function() {
    const downloadForm = document.getElementById('downloadForm');
    const videoUrl = document.getElementById('videoUrl');
    const errorAlert = document.getElementById('errorAlert');
    const videoPreview = document.getElementById('videoPreview');
    const downloadProgress = document.getElementById('downloadProgress');
    const progressBar = downloadProgress.querySelector('.progress-bar');
    const formatSelect = document.getElementById('formatSelect');
    const downloadBtn = document.getElementById('downloadBtn');

    downloadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        resetUI();

        try {
            const response = await fetch('/get-info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `url=${encodeURIComponent(videoUrl.value)}`
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch video information');
            }

            displayVideoInfo(data);
        } catch (error) {
            showError(error.message);
        }
    });

    downloadBtn.addEventListener('click', async function() {
        const format = formatSelect.value;
        if (!format) return;

        try {
            downloadProgress.classList.remove('d-none');
            downloadBtn.disabled = true;

            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `url=${encodeURIComponent(videoUrl.value)}&format=${format}`
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Download failed');
            }

            // Get the filename from the Content-Disposition header if available
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `video.${format}`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (match && match[1]) {
                    filename = match[1].replace(/['"]/g, '');
                }
            }

            const reader = response.body.getReader();
            const contentLength = +response.headers.get('Content-Length');
            
            // Create a new ReadableStream
            const stream = new ReadableStream({
                async start(controller) {
                    let receivedLength = 0;
                    
                    while(true) {
                        const {done, value} = await reader.read();
                        
                        if (done) {
                            controller.close();
                            break;
                        }
                        
                        receivedLength += value.length;
                        const progress = (receivedLength / contentLength) * 100;
                        progressBar.style.width = progress + '%';
                        
                        controller.enqueue(value);
                    }
                }
            });
            
            // Create response from stream
            const newResponse = new Response(stream);
            const blob = await newResponse.blob();
            
            if (blob.size === 0) {
                throw new Error('Downloaded file is empty');
            }
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `video.${format}`;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }, 100);

        } catch (error) {
            showError(error.message);
        } finally {
            downloadProgress.classList.add('d-none');
            downloadBtn.disabled = false;
            progressBar.style.width = '0%';
        }
    });

    function displayVideoInfo(data) {
        document.getElementById('thumbnailImg').src = data.thumbnail;
        document.getElementById('videoTitle').textContent = data.title;
        document.getElementById('videoDuration').textContent = 
            `Duration: ${formatDuration(data.duration)}`;

        formatSelect.innerHTML = '';
        data.formats.forEach(format => {
            const option = document.createElement('option');
            option.value = format.ext;
            option.textContent = `${format.ext.toUpperCase()} - ${format.quality}`;
            formatSelect.appendChild(option);
        });

        videoPreview.classList.remove('d-none');
        downloadBtn.disabled = false;
    }

    function formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    function showError(message) {
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
    }

    function resetUI() {
        errorAlert.classList.add('d-none');
        videoPreview.classList.add('d-none');
        downloadProgress.classList.add('d-none');
        progressBar.style.width = '0%';
        downloadBtn.disabled = true;
    }
});
