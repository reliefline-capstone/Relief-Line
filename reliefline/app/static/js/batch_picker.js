// Batch picker on every 'send stock' form.
// Lets the user send food packs automatically (soonest-to-expire first) or pick the batches by hand.
(function () {
    if (window.__batchPickerLoaded) return;
    window.__batchPickerLoaded = true;

    // Sets up one batch picker on a form (runs only once per picker).
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

        // True if the user chose to pick the batches by hand.
        function isManual() {
            var r = bp.querySelector('input[name="batch_mode"]:checked');
            return r && r.value === 'manual';
        }
        // The batch list for the warehouse currently chosen on the form.
        function activeOffice() {
            if (!officeSelect) return bp.querySelector('[data-bp-office]');
            return bp.querySelector('[data-bp-office="' + officeSelect.value + '"]');
        }
        var totalBar = bp.querySelector('.bp-total');
        // Updates the picker: shows or hides the batch list,
        // and totals the packs chosen from each batch so it matches the quantity being sent.
        function refresh() {
            var manual = isManual();
            body.hidden = !manual;
            if (totalBar) totalBar.hidden = !manual;
            bp.querySelectorAll('.bp-seg').forEach(function (seg) {
                seg.classList.toggle('is-on', seg.querySelector('input').checked);
            });
            bp.querySelectorAll('.bp-batch').forEach(function (card) {
                var q = card.querySelector('.bp-qty');
                card.classList.toggle('is-taken', !!q && (parseInt(q.value, 10) || 0) > 0);
            });
            var active = activeOffice();
            var pickHint = bp.querySelector('[data-bp-pick-office]');
            if (pickHint) pickHint.hidden = !manual || !!active;
            bp.querySelectorAll('[data-bp-office]').forEach(function (g) {
                var on = manual && g === active;
                g.hidden = !on;
                g.querySelectorAll('.bp-qty').forEach(function (inp) { inp.disabled = !on; });
            });
            var total = 0;
            if (active) active.querySelectorAll('.bp-qty').forEach(function (inp) { total += parseInt(inp.value, 10) || 0; });
            var target = qtyInput ? parseInt(qtyInput.value, 10) || 0 : 0;
            totalEl.textContent = total.toLocaleString();
            targetEl.textContent = target ? 'of ' + target.toLocaleString() + ' packs' : '';
            var mismatch = manual && total !== target;
            bp.classList.toggle('bp-mismatch', mismatch);
            if (qtyInput) qtyInput.setCustomValidity(mismatch ? 'The packs chosen from batches must add up to this quantity.' : '');
        }
        bp.addEventListener('input', refresh);
        bp.addEventListener('change', refresh);
        if (officeSelect) officeSelect.addEventListener('change', refresh);
        if (qtyInput) qtyInput.addEventListener('input', refresh);
        refresh();
    }

    // Sets up every batch picker on the page.
    function initAll() { document.querySelectorAll('[data-bp]').forEach(init); }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initAll);
    else initAll();
})();
