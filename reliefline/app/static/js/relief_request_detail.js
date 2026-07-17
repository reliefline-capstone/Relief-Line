document.addEventListener('DOMContentLoaded', function () {
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
