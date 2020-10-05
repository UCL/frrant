/* Project specific Javascript goes here. */

$('.rard-toggle-control input').change(function (e, init) {
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
$('body').on("submit", "form", function (e) {
    // get clicked button
    var $clicked = $(document.activeElement);
    if ($clicked.hasClass('confirm-delete')) {
        let what = $clicked.data('what') || 'object';
        return confirm("Are you sure you want to delete this " + what + '? This cannot be undone.');
    }
    return true; // proceed as normal
})

// prevent double-submit either from RTN or button press
$('body').on("submit", "form", function (e) {
    if ($(this).data('submitted')) {
        return false;
    }
    $(this).data('submitted', true);

    $('.rich-editor').each(function() {
        // copy each rich editor's content to its related control
        var for_id = $(this).data('for');
        var html = $(this).trumbowyg('html');
        $(`#${for_id}`).html(html);
    })
});

$('.rich-editor').trumbowyg(
    {
        resetCss: true,
        autogrow: true,
        // removeformatPasted: true,
        // tagsToRemove: ['script', 'span'],
        tagsToKeep: ['img'],
        btns: [
            ['characters'],
            ['vinculum_on', 'vinculum_off'], 
            ['undo', 'redo'],
            ['superscript', 'subscript', 'removeformat'],
        ],
    }
).on('tbwinit', function(e, a)
    {
        // set our initial html from the related control
        var for_id = $(this).data('for');
        var $for = $(`#${for_id}`);
        var html = $for.text();
        $for.hide();
        $(this).trumbowyg('html', html);

        // set the tooltip of the characters in the list and blank their content
        // as background images are set in css
        $('.trumbowyg-dropdown-characters > button').each(function() {
            $(this).attr('title', $(this).text());
            $(this).text('')
        });
    }
).on('tbwchange', function() {
}).on('keyup', function(e) {
});
