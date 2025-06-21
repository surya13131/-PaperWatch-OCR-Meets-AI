document.addEventListener('DOMContentLoaded', () => {
  const scanBtn = document.getElementById('scanBtn');
  const video = document.getElementById('video');
  const canvas = document.createElement('canvas');
  const statusText = document.getElementById('statusText');
  const uploadForm = document.getElementById('uploadForm');
  const fileInput = document.getElementById('fileInput');
  const scannerBar = document.getElementById('scannerBar');
  const cameraWrapper = document.getElementById('cameraWrapper');

  function showStatus(message, showSpinner = true) {
    if (statusText) {
      statusText.innerHTML = showSpinner ? `<div class="spinner"></div> ${message}` : message;
      statusText.style.display = 'flex';
    }
  }

  function hideStatus() {
    if (statusText) {
      statusText.style.display = 'none';
    }
  }

  function reloadPageAndRebind(htmlContent) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');
    document.body.innerHTML = doc.body.innerHTML;

    setTimeout(() => {
      document.dispatchEvent(new Event('DOMContentLoaded'));
    }, 100);
  }

  // Upload flow
  if (uploadForm) {
    uploadForm.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!fileInput || fileInput.files.length === 0) return;
      showStatus('Verifying the document...');

      const formData = new FormData(uploadForm);
      fetch('/', {
        method: 'POST',
        body: formData
      })
      .then(res => res.text())
      .then(html => {
        reloadPageAndRebind(html);
      });
    });
  }

  // Scan Now flow
  if (scanBtn) {
    scanBtn.addEventListener('click', () => {
      showStatus('Opening camera...');
      if (cameraWrapper) cameraWrapper.style.display = 'block';
      if (scannerBar) scannerBar.style.display = 'block';

      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          video.srcObject = stream;

          video.onloadedmetadata = () => {
            video.play();

            setTimeout(() => {
              showStatus('Capturing document...');

              canvas.width = video.videoWidth;
              canvas.height = video.videoHeight;
              canvas.getContext('2d').drawImage(video, 0, 0);

              // Stop camera
              stream.getTracks().forEach(track => track.stop());

              // Hide scanner bar after capture
              if (scannerBar) scannerBar.style.display = 'none';

              // Send image to server
              canvas.toBlob(blob => {
                const formData = new FormData();
                formData.append('doc', blob, 'scanned.jpg');

                showStatus('Verifying the document...');
                fetch('/', {
                  method: 'POST',
                  body: formData
                })
                .then(res => res.text())
                .then(html => {
                  reloadPageAndRebind(html);
                });
              }, 'image/jpeg');
            }, 2500); // wait for scan effect
          };
        })
        .catch(err => {
          showStatus(`Camera not accessible: ${err.message || err}`, false);
          if (scannerBar) scannerBar.style.display = 'none';
        });
    });
  }
});
