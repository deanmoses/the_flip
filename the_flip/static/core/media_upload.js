/**
 * Media upload and management functionality.
 *
 * Provides reusable handlers for:
 * - Uploading photos and videos
 * - Deleting media items
 * - Displaying upload feedback
 *
 * Usage:
 *   Include this script and call initMediaUpload() with the container element ID.
 *
 * Required DOM structure:
 *   - #upload-button: Button that triggers file selection
 *   - #media-upload: Hidden file input (accepts image/*,video/*)
 *   - #media-container: Container for media items
 *   - .btn-delete-media[data-media-id]: Delete buttons on each media item
 *   - #no-media-message (optional): Message shown when no media exists
 */

/**
 * Initialize media upload functionality for a container.
 * @param {Object} options Configuration options
 * @param {string} options.uploadButtonId - ID of upload button (default: 'upload-button')
 * @param {string} options.fileInputId - ID of file input (default: 'media-upload')
 * @param {string} options.containerId - ID of media container (default: 'media-container')
 * @param {string} options.noMediaMessageId - ID of "no media" message (default: 'no-media-message')
 */
function initMediaUpload(options = {}) {
  const uploadButtonId = options.uploadButtonId || 'upload-button';
  const fileInputId = options.fileInputId || 'media-upload';
  const containerId = options.containerId || 'media-container';
  const noMediaMessageId = options.noMediaMessageId || 'no-media-message';

  const uploadButton = document.getElementById(uploadButtonId);
  const mediaInput = document.getElementById(fileInputId);
  const mediaContainer = document.getElementById(containerId);

  if (!uploadButton || !mediaInput || !mediaContainer) {
    console.warn('Media upload: Required elements not found');
    return;
  }

  // Update button text if there are existing media items
  const existingMediaCount = mediaContainer.querySelectorAll('.media-item').length;
  if (existingMediaCount > 0) {
    uploadButton.textContent = 'Upload More Photos';
  }

  // Trigger file picker when upload button is clicked
  uploadButton.addEventListener('click', () => mediaInput.click());

  // Handle file selection
  mediaInput.addEventListener('change', async (e) => {
    if (!e.target.files || !e.target.files.length) return;

    const files = Array.from(e.target.files);
    const noMediaMessage = document.getElementById(noMediaMessageId);
    if (noMediaMessage) noMediaMessage.remove();

    for (const file of files) {
      await uploadFile(file, mediaContainer, uploadButton);
    }

    // Reset input to allow re-selecting the same file
    e.target.value = '';
  });

  // Attach delete handlers to existing media items
  mediaContainer.querySelectorAll('.btn-delete-media').forEach(attachDeleteHandler);
}

/**
 * Upload a single file to the server.
 * @param {File} file - The file to upload
 * @param {HTMLElement} container - The media container element
 * @param {HTMLElement} uploadButton - The upload button (to update text)
 */
async function uploadFile(file, container, uploadButton) {
  const formData = new FormData();
  formData.append('action', 'upload_media');
  formData.append('file', file);

  try {
    const response = await fetch(window.location.href, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': getCsrfToken(),
      },
      credentials: 'same-origin',
    });

    const data = await response.json();
    if (data.success) {
      const mediaItem = createMediaElement(data);
      container.appendChild(mediaItem);
      attachDeleteHandler(mediaItem.querySelector('.btn-delete-media'));
      uploadButton.textContent = 'Upload More Photos';
    } else {
      alert('Failed to upload media: ' + (data.error || 'Unknown error'));
    }
  } catch (error) {
    console.error('Upload error:', error);
    alert('Failed to upload media');
  }
}

/**
 * Create a media item DOM element from upload response data.
 * @param {Object} data - Response data from upload
 * @returns {HTMLElement} The created media item element
 */
function createMediaElement(data) {
  const mediaItem = document.createElement('div');
  mediaItem.className = 'media-item';
  mediaItem.dataset.mediaId = data.media_id;

  let content = '';
  if (data.media_type === 'video') {
    if (data.transcode_status === 'ready' && data.media_url) {
      const posterAttr = data.poster_url ? ` poster="${data.poster_url}"` : '';
      content = `
        <video controls${posterAttr} class="media-video">
          <source src="${data.media_url}" type="video/mp4">
          Your browser doesn't support video playback.
        </video>
      `;
    } else if (data.transcode_status === 'failed') {
      content = `<div class="media-status error">Video processing failed.</div>`;
    } else {
      content = `<div class="media-status">Processing video...</div>`;
    }
  } else {
    content = `
      <a href="${data.media_url}" target="_blank" class="media-link">
        <img src="${data.thumbnail_url}" alt="Uploaded photo">
      </a>
    `;
  }

  mediaItem.innerHTML = `
    ${content}
    <button type="button" class="btn-delete-media" data-media-id="${data.media_id}" aria-label="Delete media">&times;</button>
  `;

  return mediaItem;
}

/**
 * Attach a click handler to a delete button.
 * @param {HTMLElement} button - The delete button element
 */
function attachDeleteHandler(button) {
  if (!button) return;

  button.addEventListener('click', async () => {
    const mediaId = button.dataset.mediaId;

    const formData = new FormData();
    formData.append('action', 'delete_media');
    formData.append('media_id', mediaId);

    try {
      const response = await fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': getCsrfToken(),
        },
        credentials: 'same-origin',
      });

      if (response.ok) {
        const mediaItem = button.closest('.media-item');
        mediaItem.remove();
      } else {
        alert('Failed to delete media');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete media');
    }
  });
}
