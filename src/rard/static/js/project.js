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

$('[data-toggle="tooltip"]').tooltip()

$('.submit-on-change').change(function(e){
    // submit the form it belongs to
    $(this).closest('form').submit();
});

$('.work-form').submit(function(e){
    // disable any book/volume controls on the page
    $('select[name="volume"]').prop('disabled', true);
});


$('#id_year_type').change(function(e) {
    $('.range-only').toggle($(this).val() === 'range')
});

$('#id_year_type').trigger('change', true);

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
        // resetCss: true,
        autogrow: true,
        removeformatPasted: true,
        // tagsToRemove: ['script', 'span'],
        tagsToKeep: ['img'],
        btns: [
            ['characters'],
            ['vinculum_on', 'vinculum_off'], 
            ['undo', 'redo'],
            ['superscript', 'subscript', 'removeformat'],
        ],
       langs: {
            en: {
                fontFamily: 'Alphabetum'
            },
       }
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

if (!String.prototype.HTMLDecode) {
    String.prototype.HTMLDecode = function () {
        var str = this.toString(),
            //Create an element for decoding            
            decoderEl = document.createElement('p');

        //Bail if empty, otherwise IE7 will return undefined when 
        //OR-ing the 2 empty strings from innerText and textContent
        if (str.length == 0) {
            return str;
        }

        //convert newlines to <br's> to save them
        str = str.replace(/((\r\n)|(\r)|(\n))/gi, " <br/>");            

        decoderEl.innerHTML = str;
        /*
        We use innerText first as IE strips newlines out with textContent.
        There is said to be a performance hit for this, but sometimes
        correctness of data (keeping newlines) must take precedence.
        */
        str = decoderEl.innerText || decoderEl.textContent;

        //clean up the decoding element
        decoderEl = null;

        //replace back in the newlines
        return str.replace(/<br((\/)|( \/))?>/gi, "\r\n");
    };
}

$('.alphabetum.insert').click(function(e) {
    let code = $(this).data('code');
    let dummyInput = $('#clipboard_input');
    let str = `\\u${code}`
    let to_parse = '"'+str+'"';
    let val = decodeURIComponent(JSON.parse(to_parse));
    dummyInput.val(dummyInput.val()+val);
});

$('#copy_to_clipboard').click(function(e) {
    let dummyInput = $('#clipboard_input');
    dummyInput.select();
    document.execCommand('copy');
    dummyInput.blur();

});

$('#clear_copy_to_clipboard').click(function(e) {
    let dummyInput = $('#clipboard_input');
    dummyInput.val('');

});

$('#symbol-palette-select').change(function(e) {
    let target = $(this).val();
    $('.symbol-palette').hide();
    $(`#${target}`).show();
});

$('#symbol-palette-select').trigger('change', true);
