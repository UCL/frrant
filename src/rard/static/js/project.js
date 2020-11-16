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

$('.submit-on-change').change(function(e){
    // submit the form it belongs to
    $(this).closest('form').submit();
});

$('.work-form').submit(function(e){
    // disable any volume controls on the page
    $('select[name="volume"]').prop('disabled', true);
});


$('#id_year_type').change(function(e) {
    $('.range-only').toggle($(this).val() === 'range')
});

$('#id_year_type').trigger('change', true);

// initialise any checkbox-driven toggle areas on initialising page
$('.rard-toggle-control input').trigger('change', true);

$('form').click(function(event) {
    // store the clicked button when submitting forms
    // for cross-browser determination of the clicked button
  $(this).data('clicked',$(event.target))
});

// confirm delete of objects when forms submitted
$('body').on("submit", "form", function (e) {
    var $clicked= $(this).data('clicked');
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

// store scroll position on save and reload - useful for inline posts not
// returning the user to the top of the page
document.addEventListener("DOMContentLoaded", function (event) {
    var scrollpos = sessionStorage.getItem('scrollpos');
    if (scrollpos) {
        window.scrollTo(0, scrollpos);
        sessionStorage.removeItem('scrollpos');
    }
});

window.addEventListener("beforeunload", function (e) {
    sessionStorage.setItem('scrollpos', window.scrollY);
});
