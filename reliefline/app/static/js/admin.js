// System Admin pages (Add/Edit User forms).
// Shows the 'Office' field for PSWDO/CSWDO roles and the 'Barangay' field for barangay users.
document.addEventListener('DOMContentLoaded', function () {
    // Shows only the fields that match the selected role:
    // the Office field for PSWDO/CSWDO admins, the Barangay field for barangay users.
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
