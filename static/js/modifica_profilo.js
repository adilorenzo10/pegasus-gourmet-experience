$("#toggle-modifica-password").on('change', function() {
    const isChecked = this.checked;

    $(".sez-modifica-password").toggleClass("d-none", !isChecked);
    $(".sez-modifica-password input[type=password]")
        .toggleClass("disabled", !isChecked)
        .prop("required", isChecked);
});
