/**
 * Checkbox Toggle Module
 *
 * Enables interactive task list checkboxes in [data-text-card] containers.
 * Checkboxes rendered outside data-text-card remain disabled (read-only).
 *
 * Auto-initializes on elements with [data-text-card] attribute.
 *
 * Behavior:
 * 1. Finds all checkboxes with [data-checkbox-index] inside [data-text-card]
 * 2. Removes their "disabled" attribute to make them interactive
 * 3. On click: toggles the Nth checkbox marker in the raw markdown textarea
 * 4. POSTs the updated text via the existing update_text action
 * 5. On failure: reverts the checkbox and shows error status
 *
 * Limitation: 4-space indented code blocks are not detected. Task markers
 * inside indented code blocks will cause index mismatch with rendered
 * checkboxes. Use fenced code blocks (``` or ~~~) instead.  We decided that
 * supporting this is too complex and nobody uses indented code blocks anyway.
 */
(function () {
  'use strict';

  function getCsrfToken() {
    var cookie = document.cookie.match(/csrftoken=([^;]+)/);
    return cookie ? cookie[1] : '';
  }

  /**
   * Toggle the Nth task list marker in raw markdown text.
   *
   * Finds the Nth occurrence of list item checkbox markers and toggles
   * between checked/unchecked. Supports all markdown list types:
   * - Unordered: "- [ ]", "* [ ]", "+ [ ]"
   * - Ordered: "1. [ ]", "2. [ ]", etc.
   * - Inside blockquotes: "> - [ ]"
   *
   * Skips markers inside fenced code blocks (``` or ~~~).
   * Note: 4-space indented code blocks are NOT detected - use fenced blocks.
   *
   * @param {string} text - Raw markdown text
   * @param {number} index - Zero-based checkbox index
   * @returns {string} Updated markdown text
   */
  function toggleCheckboxInMarkdown(text, index) {
    // Split text into segments: outside code blocks vs inside
    // Code blocks start and end with ``` or ~~~ on their own line
    var segments = text.split(/^((?:```|~~~)[\s\S]*?^(?:```|~~~))/gm);
    var count = 0;
    // Match task list markers for all list types: -, *, +, or numbered (1., 2., etc.)
    // Also handles blockquote prefixes (> ) which can appear before the list marker
    var pattern = /^((?:>\s*)*\s*(?:[-*+]|\d+\.) )\[( *|[xX])\]/gm;

    var result = segments.map(function (segment, i) {
      // Odd indices are inside code blocks (captured groups)
      if (i % 2 === 1) {
        return segment;
      }

      // Process segments outside code blocks
      return segment.replace(pattern, function (match, prefix, checkChar) {
        if (count++ !== index) {
          return match;
        }
        // Toggle: empty or spaces -> x, x/X -> single space
        var newChar = checkChar.trim() === '' ? 'x' : ' ';
        return prefix + '[' + newChar + ']';
      });
    });

    return result.join('');
  }

  function initTextCard(card) {
    var textarea = card.querySelector('[data-text-textarea]');
    var statusEl = card.querySelector('[data-text-status]');
    if (!textarea) return;

    var checkboxes = card.querySelectorAll('input[data-checkbox-index]');
    if (checkboxes.length === 0) return;

    // Enable checkboxes (they render disabled by default for list views)
    checkboxes.forEach(function (cb) {
      cb.disabled = false;
    });

    // Attach click handler to each checkbox
    checkboxes.forEach(function (cb) {
      cb.addEventListener('change', function () {
        var index = parseInt(cb.getAttribute('data-checkbox-index'), 10);
        var newText = toggleCheckboxInMarkdown(textarea.value, index);
        textarea.value = newText;

        // POST the update
        var formData = new FormData();
        formData.append('action', 'update_text');
        formData.append('text', newText);
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        fetch(window.location.href, {
          method: 'POST',
          body: formData,
        })
          .then(function (response) {
            if (!response.ok) {
              // Revert checkbox on failure
              cb.checked = !cb.checked;
              textarea.value = toggleCheckboxInMarkdown(textarea.value, index);
              if (statusEl) {
                statusEl.textContent = 'Error saving';
                statusEl.className = 'status-indicator error';
              }
            }
          })
          .catch(function () {
            // Revert on network error
            cb.checked = !cb.checked;
            textarea.value = toggleCheckboxInMarkdown(textarea.value, index);
            if (statusEl) {
              statusEl.textContent = 'Error saving';
              statusEl.className = 'status-indicator error';
            }
          });
      });
    });
  }

  function init() {
    document.querySelectorAll('[data-text-card]').forEach(initTextCard);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
