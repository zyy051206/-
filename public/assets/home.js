(() => {
  'use strict';
  const dialogs = [...document.querySelectorAll('dialog.panel')];
  const openers = new WeakMap();
  const focusable = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

  function closeDialog(dialog) {
    if (dialog.open) dialog.close();
  }

  document.querySelectorAll('[data-dialog]').forEach(button => {
    button.addEventListener('click', () => {
      const dialog = document.getElementById(button.dataset.dialog);
      if (!dialog || dialog.open) return;
      openers.set(dialog, button);
      dialog.showModal();
      document.body.classList.add('dialog-open');
      dialog.querySelector('[data-close]')?.focus();
    });
  });

  dialogs.forEach(dialog => {
    let pointerStartedOutside = false;
    const outside = event => {
      const bounds = dialog.getBoundingClientRect();
      return event.clientX < bounds.left || event.clientX > bounds.right ||
        event.clientY < bounds.top || event.clientY > bounds.bottom;
    };
    dialog.querySelector('[data-close]')?.addEventListener('click', () => closeDialog(dialog));
    dialog.addEventListener('pointerdown', event => { pointerStartedOutside = outside(event); });
    dialog.addEventListener('click', event => {
      if (event.target === dialog && pointerStartedOutside && outside(event)) closeDialog(dialog);
      pointerStartedOutside = false;
    });
    dialog.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      const items = [...dialog.querySelectorAll(focusable)].filter(item => item.getClientRects().length);
      const first = items[0];
      const last = items[items.length - 1];
      if (!first) { event.preventDefault(); return; }
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    });
    // Native modal dialogs handle Escape and keep background content inert.
    dialog.addEventListener('close', () => {
      if (!dialogs.some(item => item.open)) document.body.classList.remove('dialog-open');
      openers.get(dialog)?.focus();
    });
  });
})();
