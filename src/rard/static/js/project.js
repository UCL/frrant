/* Project specific Javascript goes here. */

$('.rard-toggle-control input').change(function() {
    let checked = $(this).is(':checked');
    let $parent = $(this).closest('.rard-toggle-control');
    let show = $parent.data('on-show');
    let disable = $parent.data('on-disable');
    if (show !== undefined) {
        $(show).toggle(checked);
    }
    if (disable !== undefined) {
        $(disable).attr('disabled', checked);
    }
})