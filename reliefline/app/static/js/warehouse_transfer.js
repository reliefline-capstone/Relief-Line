// Stock Transfer page: choosing the 'from' and 'to' warehouses (they must be different)
// and showing each warehouse's stock as you type the quantity.
document.addEventListener('DOMContentLoaded', function () {
    var fromSelect = document.getElementById('from_office_id');
    var toSelect = document.getElementById('to_office_id');
    var quantityInput = document.getElementById('quantity');
    if (!fromSelect || !toSelect || !quantityInput) return;

    var fromHint = document.getElementById('from-hint');
    var toHint = document.getElementById('to-hint');
    var preview = document.getElementById('transfer-preview');
    var fromValue = document.getElementById('from-preview-value');
    var toValue = document.getElementById('to-preview-value');

    // The chosen warehouse's name, stock and location.
    function selectedData(select) {
        var opt = select.options[select.selectedIndex];
        if (!opt || !opt.value) return null;
        return {
            name: opt.text,
            qty: parseInt(opt.dataset.qty, 10) || 0,
            location: opt.dataset.location || '',
        };
    }

    // Formats a number with commas (e.g. 12,345).
    function formatNumber(n) {
        return n.toLocaleString('en-US');
    }

    // Hides the warehouse already chosen on the other side,
    // so 'from' and 'to' can't be the same warehouse.
    function excludeOtherSelection(select, otherValue) {
        var wrap = select.closest('.csel-wrap');
        var list = wrap ? wrap.cselList : null;
        var resetNeeded = false;
        Array.prototype.forEach.call(select.options, function (opt) {
            if (!opt.value) return;
            var blocked = otherValue !== '' && opt.value === otherValue;
            opt.disabled = blocked;
            if (blocked && select.value === opt.value) resetNeeded = true;
            if (list) {
                var li = list.querySelector('.csel-option[data-value="' + opt.value + '"]');
                if (li) {
                    if (blocked) li.setAttribute('aria-disabled', 'true');
                    else li.removeAttribute('aria-disabled');
                }
            }
        });
        if (resetNeeded) {
            select.value = '';
            var wrapForRefresh = select.closest('.csel-wrap');
            var valueEl = wrapForRefresh && wrapForRefresh.querySelector('.csel-trigger .csel-value');
            if (valueEl) {
                valueEl.textContent = select.options[0] ? select.options[0].textContent : '';
                valueEl.classList.add('csel-placeholder');
            }
            if (list) {
                list.querySelectorAll('.csel-option').forEach(function (o) { o.classList.remove('is-selected'); });
            }
        }
    }

    // Keeps the 'from' and 'to' warehouses different.
    function syncExclusions() {
        excludeOtherSelection(toSelect, fromSelect.value);
        excludeOtherSelection(fromSelect, toSelect.value);
    }

    // Updates the hints under each field (stock available, location)
    // and the preview when the form changes.
    function update() {
        syncExclusions();
        var from = selectedData(fromSelect);
        var to = selectedData(toSelect);
        var qty = parseInt(quantityInput.value, 10) || 0;

        fromHint.textContent = from ? (formatNumber(from.qty) + ' packs available · ' + from.location) : 'Select a warehouse';
        toHint.textContent = to ? (formatNumber(to.qty) + ' packs current · ' + to.location) : 'Select a warehouse';

        if (from && to && qty > 0) {
            var fromAfter = from.qty - qty;
            fromValue.textContent = formatNumber(fromAfter);
            fromValue.className = fromAfter < 0 ? 'text-red' : '';
            toValue.textContent = formatNumber(to.qty + qty);
            preview.hidden = false;
        } else {
            preview.hidden = true;
        }
    }

    [fromSelect, toSelect, quantityInput].forEach(function (el) {
        el.addEventListener('input', update);
        el.addEventListener('change', update);
    });

    update();
});
