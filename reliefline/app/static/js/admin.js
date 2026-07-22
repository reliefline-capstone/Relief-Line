document.addEventListener('DOMContentLoaded', function () {
    function syncRoleFields(select) {
        var form = select.closest('form');
        if (!form) return;
        var role = select.value;
        form.querySelectorAll('[data-role-field]').forEach(function (field) {
            var roles = field.dataset.roleField.split(',');
            field.classList.toggle('is-visible', roles.indexOf(role) !== -1);
        });
    }

    document.querySelectorAll('select[data-role-select]').forEach(function (select) {
        syncRoleFields(select);
        select.addEventListener('change', function () { syncRoleFields(select); });
    });
});
