// Behaviour for the batch_picker macro (templates/_macros.html). The macro
// can render several times on one page (one per review modal) and each copy
// includes this file, so it wires every picker once and then never again.
(function () {
    if (window.__batchPickerLoaded) return;
    window.__batchPickerLoaded = true;

    function init(bp) {
        if (bp.__bpReady) return;
        bp.__bpReady = true;
        var form = bp.closest('form');
        var body = bp.querySelector('.bp-body');
        var totalEl = bp.querySelector('[data-bp-total]');
        var targetEl = bp.querySelector('[data-bp-target]');
        var selectName = bp.getAttribute('data-bp-office-select');
        var officeSelect = selectName && form ? form.querySelector('[name="' + selectName + '"]') : null;
        var qtyInput = form ? form.querySelector('[name="quantity"]') : null;

        function isManual() {
            var r = bp.querySelector('input[name="batch_mode"]:checked');
            return r && r.value === 'manual';
        }
        function activeOffice() {
            if (!officeSelect) return bp.querySelector('[data-bp-office]');
            return bp.querySelector('[data-bp-office="' + officeSelect.value + '"]');
        }
        function refresh() {
            var manual = isManual();
            body.hidden = !manual;
            var active = activeOffice();
            bp.querySelectorAll('[data-bp-office]').forEach(function (g) {
                var on = manual && g === active;
                g.hidden = !on;
                // Only the shown warehouse's boxes are submitted.
                g.querySelectorAll('.bp-qty').forEach(function (inp) { inp.disabled = !on; });
            });
            var total = 0;
            if (active) active.querySelectorAll('.bp-qty').forEach(function (inp) { total += parseInt(inp.value, 10) || 0; });
            var target = qtyInput ? parseInt(qtyInput.value, 10) || 0 : 0;
            totalEl.textContent = total.toLocaleString();
            targetEl.textContent = target ? 'of ' + target.toLocaleString() + ' packs' : '';
            var mismatch = manual && total !== target;
            bp.classList.toggle('bp-mismatch', mismatch);
            // Blocks submitting until the chosen batches add up (the server
            // checks again regardless).
            if (qtyInput) qtyInput.setCustomValidity(mismatch ? 'The packs chosen from batches must add up to this quantity.' : '');
        }
        bp.addEventListener('input', refresh);
        bp.addEventListener('change', refresh);
        if (officeSelect) officeSelect.addEventListener('change', refresh);
        if (qtyInput) qtyInput.addEventListener('input', refresh);
        refresh();
    }

    function initAll() { document.querySelectorAll('[data-bp]').forEach(init); }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initAll);
    else initAll();
})();
