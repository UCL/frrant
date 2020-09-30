/* Project specific Javascript goes here. */

$('.rard-toggle-control input').change(function(e, init) {
    let checked = $(this).is(':checked');
    let $parent = $(this).closest('.rard-toggle-control');
    let show = $parent.data('on-show');
    let disable = $parent.data('on-disable');
    if (show !== undefined) {
        $(show).toggle(checked);
    }
    if (disable !== undefined) {
        $(disable).attr('disabled', checked);
        if (init !== true) {
            $(disable).removeClass('is-invalid');
        }
    }
})

// initialise any checkbox-driven toggle areas on initialising page
$('.rard-toggle-control input').trigger('change', true);

// confirm delete of objects when forms submitted
$('body').on("submit", "form", function(e){
    // get clicked button
    var $clicked = $(document.activeElement);
    if ($clicked.hasClass('confirm-delete')) {
        let what = $clicked.data('what') || 'object';
        return confirm("Are you sure you want to delete this "+what+'? This cannot be undone.');
    }
    return true; // proceed as normal
});
