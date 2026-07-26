document.addEventListener('DOMContentLoaded', function () {
    // Generic conditional-field toggle (e.g. "Source: Donation" revealing a
    // Donor Name field) — same pattern as admin.js's role-field toggle, scoped
    // here to whatever form the triggering select lives in.
    function syncToggleFields(select) {
        var form = select.closest('form');
        if (!form) return;
        var value = select.value;
        form.querySelectorAll('[data-toggle-field]').forEach(function (field) {
            var values = field.dataset.toggleField.split(',');
            field.classList.toggle('is-visible', values.indexOf(value) !== -1);
        });
    }

    document.querySelectorAll('select[data-toggle-select]').forEach(function (select) {
        syncToggleFields(select);
        select.addEventListener('change', function () { syncToggleFields(select); });
    });

    document.querySelectorAll('[data-open-modal]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var modal = document.getElementById(btn.dataset.openModal);
            if (modal) modal.hidden = false;
        });
    });

    document.querySelectorAll('.rd-modal-overlay').forEach(function (overlay) {
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) overlay.hidden = true;
        });
        overlay.querySelectorAll('[data-close-modal]').forEach(function (btn) {
            btn.addEventListener('click', function () { overlay.hidden = true; });
        });
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.rd-modal-overlay').forEach(function (overlay) {
                overlay.hidden = true;
            });
        }
    });
});
