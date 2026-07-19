document.addEventListener('DOMContentLoaded', function () {
    var fromSelect = document.getElementById('from_office_id');
    var toSelect = document.getElementById('to_office_id');
    var quantityInput = document.getElementById('quantity');
    if (!fromSelect || !toSelect || !quantityInput) return;

    var fromHint = document.getElementById('from-hint');
    var toHint = document.getElementById('to-hint');
    var preview = document.getElementById('transfer-preview');
    var fromLabel = document.getElementById('from-preview-label');
    var toLabel = document.getElementById('to-preview-label');
    var fromValue = document.getElementById('from-preview-value');
    var toValue = document.getElementById('to-preview-value');

    function selectedData(select) {
        var opt = select.options[select.selectedIndex];
        if (!opt || !opt.value) return null;
        return {
            name: opt.text,
            qty: parseInt(opt.dataset.qty, 10) || 0,
            location: opt.dataset.location || '',
        };
    }

    function formatNumber(n) {
        return n.toLocaleString('en-US');
    }

    function update() {
        var from = selectedData(fromSelect);
        var to = selectedData(toSelect);
        var qty = parseInt(quantityInput.value, 10) || 0;

        fromHint.textContent = from ? (formatNumber(from.qty) + ' packs available · ' + from.location) : 'Select a warehouse';
        toHint.textContent = to ? (formatNumber(to.qty) + ' packs current · ' + to.location) : 'Select a warehouse';

        if (from && to && qty > 0) {
            fromLabel.textContent = from.name.toUpperCase() + ' AFTER TRANSFER';
            toLabel.textContent = to.name.toUpperCase() + ' AFTER TRANSFER';
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
