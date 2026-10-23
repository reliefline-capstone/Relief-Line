// PSWDO 'New Distribution' pop-up: the 2-step form to schedule a food pack delivery
// (step 1: choose the approved request, step 2: delivery details).
document.addEventListener('DOMContentLoaded', function () {
    var modal = document.getElementById('new-distribution-modal');
    var form = document.getElementById('new-distribution-form');
    if (!modal || !form) return;

    var openBtn = document.querySelector('[data-open-modal="new-distribution-modal"]');
    var panel1 = modal.querySelector('[data-step-panel="1"]');
    var panel2 = modal.querySelector('[data-step-panel="2"]');
    var stepDots = modal.querySelectorAll('[data-step-dot]');
    var muniTiles = modal.querySelectorAll('.nd-muni-tile');
    var requestOptions = modal.querySelectorAll('.nd-request-option');
    var selectedMuniLabel = document.getElementById('nd-selected-muni');
    var hiddenAllocationId = document.getElementById('nd-allocation-id');
    var submitBtn = document.getElementById('nd-submit-btn');
    var stockWarning = document.getElementById('nd-stock-warning');

    // Shows step 1 or step 2 of the 'New Distribution' form and updates the step dots.
    function goToStep(step) {
        panel1.hidden = step !== 1;
        panel2.hidden = step !== 2;
        stepDots.forEach(function (dot) {
            dot.classList.toggle('is-active', dot.dataset.stepDot === String(step));
        });
    }

    // Clears the form and goes back to step 1 (when the pop-up is closed or reopened).
    function resetWizard() {
        goToStep(1);
        form.reset();
        hiddenAllocationId.value = '';
        submitBtn.disabled = true;
        stockWarning.hidden = true;
        requestOptions.forEach(function (opt) { opt.classList.remove('is-selected'); });
    }

    if (openBtn) openBtn.addEventListener('click', resetWizard);

    muniTiles.forEach(function (tile) {
        tile.addEventListener('click', function () {
            var muni = tile.dataset.municipality;
            selectedMuniLabel.textContent = muni;
            requestOptions.forEach(function (opt) {
                opt.hidden = opt.dataset.municipality !== muni;
            });
            goToStep(2);
        });
    });

    modal.querySelectorAll('[data-step-back]').forEach(function (btn) {
        btn.addEventListener('click', function () { goToStep(1); });
    });

    requestOptions.forEach(function (opt) {
        var radio = opt.querySelector('input[type="radio"]');
        opt.addEventListener('click', function () {
            radio.checked = true;
            requestOptions.forEach(function (o) { o.classList.remove('is-selected'); });
            opt.classList.add('is-selected');
            hiddenAllocationId.value = radio.value;

            var stockOk = opt.dataset.stockOk === 'true';
            submitBtn.disabled = !stockOk;
            stockWarning.hidden = stockOk;
        });
    });
});
