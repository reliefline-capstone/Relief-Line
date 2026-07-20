function openReportModal(reportId) {
    var overlay = document.getElementById('report-modal-' + reportId);
    if (!overlay) return;
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
}

function closeReportModal(reportId) {
    var overlay = document.getElementById('report-modal-' + reportId);
    if (!overlay) return;
    overlay.hidden = true;
    document.body.style.overflow = '';
}

function switchModalTab(reportId, paneKey) {
    var overlay = document.getElementById('report-modal-' + reportId);
    if (!overlay) return;

    overlay.querySelectorAll('.da-modal-tab').forEach(function (btn) {
        btn.classList.toggle('active', btn.dataset.pane === paneKey);
    });
    overlay.querySelectorAll('.da-modal-pane').forEach(function (pane) {
        pane.classList.toggle('active', pane.dataset.pane === paneKey);
    });
}

document.addEventListener('click', function (e) {
    if (e.target.classList && e.target.classList.contains('da-modal-overlay')) {
        e.target.hidden = true;
        document.body.style.overflow = '';
    }
});

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.da-modal-overlay:not([hidden])').forEach(function (overlay) {
            overlay.hidden = true;
        });
        document.body.style.overflow = '';
    }
});
