/**
 * Machine pill side effects — toast messages, mobile button sync, confetti.
 *
 * Listens for `pill:updated` events dispatched by settable_pill.js and
 * handles machine-specific side effects:
 *   - operational_status: toast with styled pill, mobile button class sync
 *   - location: toast (with confetti for "Floor" celebration)
 *
 * Used on both machine_feed.html and machine_edit.html. The mobile button
 * sync is a no-op on pages that don't have a `.status-btn` element.
 *
 * Depends on globals from core.js: showMessage(), escapeHtml(), launchConfetti().
 * Depends on readPillStyling() from settable_pill.js.
 */
(function () {
  'use strict';

  // Mobile button class map (no DOM source — btn classes differ from pill classes)
  const STATUS_BTN_MAP = {
    good: 'btn--status-good',
    fixing: 'btn--status-fixing',
    broken: 'btn--status-broken',
  };

  if (typeof document !== 'undefined') {
    document.addEventListener('pill:updated', (event) => {
      const { field, value, label, data } = event.detail;
      const machineName = escapeHtml(
        document.querySelector('.sidebar__title')?.textContent?.trim() || 'Machine'
      );

      if (field === 'operational_status') {
        const { pillClass, iconClass } = readPillStyling('operational_status');

        // Sync mobile button styling (only on feed page, no-op on edit page)
        const mobileBtn = document.querySelector('.status-btn');
        if (mobileBtn) {
          const btnIconEl = mobileBtn.querySelector('.status-icon');
          mobileBtn.className =
            'btn btn--dropdown status-btn ' + (STATUS_BTN_MAP[value] || 'btn--secondary');
          if (btnIconEl) {
            btnIconEl.className = 'fa-solid status-icon ' + (iconClass || 'fa-circle-question');
          }
        }

        const iconHtml = iconClass ? `<i class="fa-solid ${iconClass} meta"></i> ` : '';
        const pillHtml = `<span class="pill ${pillClass}">${iconHtml}${escapeHtml(label)}</span>`;
        showMessage('success', `Status of ${machineName} set to ${pillHtml}`);
      } else if (field === 'location') {
        const pillHtml = `<span class="pill pill--neutral"><i class="fa-solid fa-location-dot meta"></i> ${escapeHtml(label)}</span>`;
        if (data.celebration) {
          showMessage('success', `🎉🎊 ${machineName} moved to ${pillHtml}! 🎊🎉`);
          launchConfetti();
        } else {
          showMessage('success', `Location of ${machineName} set to ${pillHtml}`);
        }
      }
    });
  }
})();
