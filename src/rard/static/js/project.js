/* Project specific Javascript goes here. */
$.event.addProp('dataTransfer');

// The show detail mechanism:

// NB values stored as strings in the session storage
let show_detail = sessionStorage.getItem('show_detail') !== 'false';
$('#toggle-elements').prop('checked', show_detail ? 'checked': '');

function toggleElements(show) {
    if (show) {
        $('.toggle-element').removeClass('hidden')
        $('.toggle-element-button').addClass('open')
    } else {
        $('.toggle-element').addClass('hidden')
        $('.toggle-element-button').removeClass('open')
    }
    sessionStorage.setItem('show_detail', show);
}

toggleElements(show_detail);

// if no toggleable elements on screen then hide the control
// to avoid confusion (could also disable it)

if ($('.toggle-element').length == 0) {
    // $('#toggle-elements').prop('disabled', 'disabled');
    $('.toggle-switch').hide();
} else {
    $('.toggle-switch').show();
}


$('body').on('click', '.toggle-element-button', function(e) {
    $(this).toggleClass('open');
    let show = $(this).hasClass('open');
    if (show) {
        $(this).closest('li').find('.toggle-element').removeClass('hidden')
    } else {
        $(this).closest('li').find('.toggle-element').addClass('hidden')
    }
})

$('#toggle-elements').click(function() {
    let show_detail = $(this).is(':checked');
    toggleElements(show_detail);
})

// End of show detail mechanism

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
    // disable any book/volume/submit controls on the page
    $('[name="book"]').prop('disabled', true);
    $('[name="definite"]').prop('disabled', true);
    $('button[type="submit"]').prop('disabled', true);
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
});


Quill.register('modules/mention', quillMention);
var icons = Quill.import("ui/icons");
// import fontawesome icons for the undo/redo buttons
icons['undo'] = '<i class="fa fa-undo fa-xs align-text-top" aria-hidden="true"></i>';
icons['redo'] = '<i class="fa fa-redo fa-xs align-text-top" aria-hidden="true"></i>';
// and for the vinculum buttons
icons['vinculum_on'] = 'V\u0305'
icons['vinculum_off'] = 'V'

async function suggestPeople(searchTerm) {

    // call backend synchonously here and wait
    let matches = []
    await $.ajax({
        url: `${g_mention_url}?q=${searchTerm}`,
        type: "GET",
        context: document.body,
        dataType: 'json',
        async: false,
        success: function (data, textStatus, jqXHR) {
            matches = data;
        },
        error: function (e) {
        }
    });
    return matches;
};

async function getApparatusCriticusLines(searchTerm, object_id, object_class) {

    // call backend synchonously here and wait
    let matches = []
    await $.ajax({
        url: `${g_apparatus_criticus_url}?q=${searchTerm}&object_id=${object_id}&object_class=${object_class}`,
        type: "GET",
        context: document.body,
        dataType: 'json',
        async: false,
        success: function (data, textStatus, jqXHR) {
            console.log('success '+data)
            matches = data;
        },
        error: function (e) {
            console.log('error '+e)
        }
    });
    return matches;
};


function initRichTextEditor($item) {

    let config = {
        theme: 'snow',
        history: {
            delay: 1000,
            maxStack: 1000,
            userOnly: false
        },
        modules: {
            toolbar: {
                container: [
                    [{ undo: 'undo' }, { redo: 'redo' }],
                    [ 'bold', 'italic', 'underline', 'strike' ],
                    [{ vinculum_on: 'vinculum_on' }, { vinculum_off: 'vinculum_off' }],
                    [{ 'script': 'super' }, { 'script': 'sub' }],
                    [{ 'list': 'ordered' }, { 'list': 'bullet'}],
                    [ { 'align': [] }],
                    [ 'clean' ]
                ],
                handlers: {
                    undo: function (value) {
                        this.quill.history.undo();
                    },
                    redo: function (value) {
                        this.quill.history.redo();
                    },
                    vinculum_on: function (value) {
                        var range = this.quill.getSelection();
                        if (range) {
                            if (range.length > 0) {
                                var text = this.quill.getText(range.index, range.length);
                                let html = '';
                                for (let i = 0; i < text.length; i++) {
                                    html += text[i] + '\u0305'
                                }
                                this.quill.deleteText(range.index, range.length)
                                this.quill.insertText(range.index, html)
                            }
                        }
                    },
                    vinculum_off: function (value) {
                        var range = this.quill.getSelection();
                        if (range) {
                            if (range.length > 0) {
                                var text = this.quill.getText(range.index, range.length);

                                let html = '';
                                for (let i = 0; i < text.length; i++) {
                                    if (text[i] != '\u0305') {
                                        html += text[i];
                                    }
                                }
                                this.quill.deleteText(range.index, range.length)
                                this.quill.insertText(range.index, html)
                            }
                        }
                    }
                }
            }
        }
    };

    if ($item.hasClass('enable-mentions') || $item.hasClass('enable-apparatus-criticus')) {
        let delimiters = [];
        let dataAttributes = ['id', 'value', 'denotationChar', 'link', 'target'];
        if ($item.hasClass('enable-mentions') ) {
            delimiters.push('@')
        }
        if ($item.hasClass('enable-apparatus-criticus') ) {
            delimiters.push('#');
            dataAttributes.push('originalText');  // also need to keep track of original text owner for app crit
            dataAttributes.push('parent');  // and the parent object e.g. fragment
        }
        config['modules']['mention'] = {
            allowedChars: /^[0-9A-Za-z\sÅÄÖåäö]*$/,
            mentionDenotationChars: delimiters,
            dataAttributes: dataAttributes,
            source: async function(searchTerm, renderList, mentionChar) {

                if (mentionChar == '@') {
                    const matchedPeople = await suggestPeople(searchTerm);
                    renderList(matchedPeople);

                } else if (mentionChar == '#') {
                    let object_id = $item.data('object');
                    let object_class = $item.data('class') || 'originaltext';
                    const lines = await getApparatusCriticusLines(searchTerm, object_id, object_class);
                    console.log('lines:')
                    console.dir(lines)
                    renderList(lines);
                    
                }
            },
            renderItem(item, searchTerm) {
                // allows you to control how the item is displayed
                let list_display = item.list_display || item.value;
                console.log('list_display:')
                console.log(list_display)
                return `${list_display}`;

            }
        }
    }
    
    new Quill('#'+$item.attr('id'), config);

    var for_id = $item.data('for');
    var $for = $(`#${for_id}`);

    var html = $for.text();
    $item.find('.ql-editor').html(html);
    $for.hide();

    $('body').on("submit", "form", function (e) {
        let html = $item.find('.ql-editor').html();
        $for.text(html);
    });
}

function initRichTextEditors() {

    $('.rich-editor').each(function() {

        let $elem = $(this);
        initRichTextEditor($elem);

    });
}

initRichTextEditors();

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

function insertAtCaret(input, text) {
    var caretPos = input.selectionStart;

    var front = (input.value).substring(0, caretPos);
    var back = (input.value).substring(input.selectionEnd, input.value.length);
    input.value = front + text + back;
    caretPos = caretPos + text.length;
    input.selectionStart = caretPos;
    input.selectionEnd = caretPos;
    input.focus();
}

$('.alphabetum.insert').click(function(e) {
    let code = $(this).data('code');
    let dummyInput = $('#clipboard_input');
    let str = `\\u${code}`
    let to_parse = '"'+str+'"';
    let val = decodeURIComponent(JSON.parse(to_parse));

    insertAtCaret(dummyInput.get(0), val)
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

function togglePicker() {
    $('.picker').toggleClass('open');
}

function openForm() {
  document.getElementById("myForm").style.display = "block";
}

function closeForm() {
  document.getElementById("myForm").style.display = "none";
}


function allowDrop(ev) {
    ev.preventDefault();
    $(ev.target).addClass('over')
}

function dragleave(ev) {
  ev.preventDefault();
    $(ev.target).removeClass('over')
}

function dragend(ev) {
  ev.preventDefault();
  $('.drop-target').hide();
  $('.ordered-list-item').attr('draggable', 'false')
}

$('body').on('mousedown', '.drag-handle', function(ev) {
    // ev.preventDefault();
    let item = $(this).closest('.ordered-list-item');
    if (item) {
        item.attr('draggable', 'true')
    }
});

$('body').on('mouseup', '.drag-handle', function(ev) {
    // ev.preventDefault();
    let item = $(this).closest('.ordered-list-item');
    if (item) {
        item.attr('draggable', 'false')
    }
})

function drag(ev) {
    let src_pos = $(ev.target).data('pos');
    let object_type = $(ev.target).data('objecttype');
    let pos = parseInt(src_pos);
    ev.dataTransfer.setData("Text", ev.target.id); 
    // Only show drop targets belonging to the same work
    let work_div = $(ev.target).parent().closest('.parent-ordering-group');
    // if we manipulate the DOM on drag start we need
    // to do it within a setTimeout. Apparently
  setTimeout(function(){ 
        work_div.find('.drop-target').filter('[data-objecttype="'+object_type+'"]').show();
        let not_allowed = [pos, pos+1];
        for (let i=0; i < not_allowed.length; i++) {
            let index = not_allowed[i];
            $('.drop-target').filter('[data-pos="'+index+'"]').hide();
        }
    }, 10);

}

function drop(ev) {
  ev.preventDefault();
  var dragged_id = ev.dataTransfer.getData("Text");

    let item = $('#'+dragged_id);
    let object_type = $(item).data('objecttype');
    let target_pos = parseInt($(ev.target).data('pos'));
    let old_pos = parseInt( $(item).data('pos') );
    let new_pos = target_pos;
    // if moving down, subtract 1
    if (target_pos > old_pos) {
        new_pos = target_pos - 1;
    }
    let antiquarian_id = $(item).data('antiquarian');

    let data = {};
    if (object_type == 'topic') {
        let topic_id = $(item).data('topic');
        data = {'topic_id': topic_id};
        data['move_to'] = new_pos;
        // also need the page number
        let page_index = $('.ordered-list').data('page');
        data['page_index'] = page_index;
        moveTopicTo(data)
    } else if (object_type == 'work') {
        let work_id = $(item).data('work');
        data = {'work_id': work_id};
        data['antiquarian_id'] = antiquarian_id;
        data['move_to'] = new_pos;
        moveLinkTo(data)
    } else {
        let link_id = $(item).data('link');
        data = {'link_id': link_id, 'object_type': object_type};
        data['antiquarian_id'] = antiquarian_id;
        data['move_to_by_work'] = new_pos;
        moveLinkTo(data)
    }

    dragend(ev);

}


$('body').on('click', 'button[name="topic_down"]', function() {

    let pos = $(this).data('pos');
    let new_pos = pos + 1;
    let topic_id = $(this).data('topic');
    let page_index = $('.ordered-list').data('page');
    let data = {'topic_id': topic_id, 'move_to': new_pos, 'page_index': page_index};
    moveTopicTo(data)

})


$('body').on('click', 'button[name="topic_up"]', function() {

    let pos = $(this).data('pos');
    // let object_type = $(this).data('objecttype');
    let new_pos = pos - 1;
    let topic_id = $(this).data('topic');
    let page_index = $('.ordered-list').data('page');
    let data = {'topic_id': topic_id, 'move_to': new_pos, 'page_index': page_index};
    moveTopicTo(data)

})

$('body').on('click', 'button[name="work_down"]', function() {

    let pos = $(this).data('pos');
    // let object_type = $(this).data('objecttype');
    let new_pos = pos + 1;
    let work_id = $(this).data('work');
    let antiquarian_id = $(this).data('antiquarian');
    let data = {'work_id': work_id};
    data['antiquarian_id'] = antiquarian_id;
    data['move_to'] = new_pos;
    moveLinkTo(data)

})


$('body').on('click', 'button[name="work_up"]', function() {

    let pos = $(this).data('pos');
    // let object_type = $(this).data('objecttype');
    let new_pos = pos - 1;
    let work_id = $(this).data('work');
    let antiquarian_id = $(this).data('antiquarian');
    let data = {'work_id': work_id};
    data['antiquarian_id'] = antiquarian_id;
    data['move_to'] = new_pos;
    moveLinkTo(data)

})

$('body').on('click', 'button[name="down_by_work"]', function() {

    let pos = $(this).data('pos');
    let object_type = $(this).data('objecttype');
    let new_pos = pos + 1;
    let link_id = $(this).data('link');
    let antiquarian_id = $(this).data('antiquarian');
    let data = {'link_id': link_id, 'object_type': object_type};
    data['antiquarian_id'] = antiquarian_id;
    data['move_to_by_work'] = new_pos;
    moveLinkTo(data)
})

$('body').on('click', 'button[name="up_by_work"]', function() {

    let pos = $(this).data('pos');
    let object_type = $(this).data('objecttype');
    let new_pos = pos - 1;
    let link_id = $(this).data('link');
    let antiquarian_id = $(this).data('antiquarian');
    let data = {'link_id': link_id, 'object_type': object_type};
    data['antiquarian_id'] = antiquarian_id;
    data['move_to_by_work'] = new_pos;
    moveLinkTo(data)
})

$('body').on('drop', '.drop-target', function(event) {
    drop(event);
});

$('body').on('dragleave', '.drop-target', function(event) {
    dragleave(event)
});

$('body').on('dragover', '.drop-target', function(event) {
    allowDrop(event)
});

$('body').on('dragstart', '.drag-item', function(event) {
    drag(event);
});
 
$('body').on('dragend', '.drag-item', function(event) {
    dragend(event)
});


function moveLinkTo(post_data) {
  runMoveAction(post_data, g_move_link_url)
}

function moveTopicTo(post_data) {
    runMoveAction(post_data, g_move_topic_url)
}

function runMoveAction(post_data, post_url) {

    let sel = '.ordered-list'
    let $list_area = $(sel).first();
    
    let data = post_data;

    let csrf = document.querySelector("meta[name='token']").getAttribute('content');
    let headers = {};
    let that = this;
    headers['X-CSRFToken'] = csrf;

    // TODO set the UI for the list_area to disabled to prevent multiple submits at once
    $('.ordered-list a').css('pointer-events', 'none')
    $('.ordered-list button').css('pointer-events', 'none')
    $('.ordered-list').css('opacity', '0.5');
    $("body").css("cursor", "progress");

    $.ajax({
        url: post_url,
        type: "POST",
        data: data,
        headers: headers,
        context: document.body,
        dataType: 'json',
        success: function (data, textStatus, jqXHR) {

            $list_area.replaceWith(data.html);
            $("body").css("cursor", "default");
            try {
                cache_forms();
            }
            catch(err) {
            }
            toggleElements(show_detail);
            $('[data-toggle="tooltip"]').tooltip()
        },
        error: function (e) {
            console.log(e)
            alert('Sorry, an error occurred.')
        }
    });
};



$('body').on('click', '.show-apparatus-criticus-form', function() {

    // alert('todo: show the form beneath this')
    $('.show-apparatus-criticus-form').show();
    let inserting_at = $(this).data('index');
    let $new_area = $('#new_apparatus_criticus_line_area');
    $new_area.insertAfter($(this));
    $('#id_new_apparatus_criticus_line_editor').find('.ql-editor').html('');
    $('#update-apparatus-criticus-line').hide();
    $('#submit-new-apparatus-criticus-line').show();
    $('#submit-new-apparatus-criticus-line').attr('data-index', inserting_at);
    
    $('.line-action').hide();
    $new_area.show();
});

$('body').on('click', '.edit-apparatus-criticus-line', function() {

    // alert('todo: show the form beneath this')
    $('.edit-apparatus-criticus-line').show();
    let $new_area = $('#new_apparatus_criticus_line_area');
    let item_id = $(this).data('id');
    let content_html = $(this).data('content');
    $new_area.insertAfter($(this));
    // quill needs to put things in <p> tags so make it easy for it otherwise we get
    // unwanted automatic entering of newlines :/
    $('#id_new_apparatus_criticus_line_editor').find('.ql-editor').html(`<p>${content_html}</p>`);
    $('#submit-new-apparatus-criticus-line').hide();
    $('#update-apparatus-criticus-line').show();
    $('#update-apparatus-criticus-line').attr('data-id', item_id);
    
    $('.line-action').hide();
    $new_area.show();
});


function refreshOriginalTextApparatusCriticus() {
    // now refresh content of editable area on the page
    $('.rich-editor.enable-apparatus-criticus').each(function() {
        let $editor = $(this).find('.ql-editor');

        let html = $editor.html();

        let csrf = document.querySelector("meta[name='token']").getAttribute('content');
        let headers = {};
        headers['X-CSRFToken'] = csrf;

        // any text within the original text editor on the same
        // page might have become stale due to a change in the apparatus criticus
        // so we send it to the server to re-index any app crit links within it.
        // nb this doesn't save anything, just refreshes the text in the editor
        // so that it appears correct to the user. It would be all handled correctly
        // on saving anyway, but this is a cosmetic update so the user doesn't become confused!
        $.ajax({
            url: g_refresh_original_text_content_url,
            type: "POST",
            data: {'content': html},
            headers: headers,
            context: document.body,
            dataType: 'json',
            success: function (data, textStatus, jqXHR) {
                $editor.html(data.html);
            },
            error: function (e) {
                console.log(e)
            }
        });


    });

}

$('body').on('click', '#submit-new-apparatus-criticus-line', function() {

    let html = $('#id_new_apparatus_criticus_line_editor').find('.ql-editor').html();
    let action_url = $(this).data('action');
    let insert_at = $(this).data('index');
    let parent_id = $(this).data('parent');

    // submit the form via ajax then re-render the apparatus criticus area

    let data = {
        'content': html,
        'insert_at': insert_at,
        'parent_id': parent_id,
    }
    let csrf = document.querySelector("meta[name='token']").getAttribute('content');
    let headers = {};
    let that = this;
    headers['X-CSRFToken'] = csrf;

    $.ajax({
        url: action_url,
        type: "POST",
        data: data,
        headers: headers,
        context: document.body,
        dataType: 'json',
        success: function (data, textStatus, jqXHR) {

            let $builder_area = $('#apparatus_criticus_builder_area');

            $builder_area.replaceWith(data.html);
            $("body").css("cursor", "default");
            try {
                cache_forms();
            }
            catch(err) {
            }
            $('[data-toggle="tooltip"]').tooltip()
            $builder_area.find('.rich-editor').each(function() {
                initRichTextEditor($(this)) ;
            });
            refreshOriginalTextApparatusCriticus();
        },
        error: function (e) {
            console.log(e)
            alert('Sorry, an error occurred.')
        }
    });


});

$('body').on('click', '#cancel-new-apparatus-criticus-line', function() {
    let $new_area = $('#new_apparatus_criticus_line_area');
    $('.line-action').show();
    $new_area.hide();

});

$('body').on('click', '.delete-apparatus-criticus-line', function() {

    
    if (!confirm("Are you sure you want to delete this line? This cannot be undone.")) {
        return;
    }

    let index = $(this).data('index');
    let line_id = $(this).data('id');
    let action_url = $(this).data('action');

    // submit the form via ajax then re-render the apparatus criticus area
    let data = {
        'index': index,
        'line_id': line_id,
    }
    let csrf = document.querySelector("meta[name='token']").getAttribute('content');
    let headers = {};
    let that = this;
    headers['X-CSRFToken'] = csrf;

    $.ajax({
        url: action_url,
        type: "POST",
        data: data,
        headers: headers,
        context: document.body,
        dataType: 'json',
        success: function (data, textStatus, jqXHR) {
            let $builder_area = $('#apparatus_criticus_builder_area');

            $builder_area.replaceWith(data.html);
            $("body").css("cursor", "default");
            try {
                cache_forms();
            }
            catch(err) {
            }
            $('[data-toggle="tooltip"]').tooltip();
            $builder_area.find('.rich-editor').each(function() {
                initRichTextEditor($(this)) ;
            });
            refreshOriginalTextApparatusCriticus();
        },
        error: function (e) {
            console.log(e)
            alert('Sorry, an error occurred.')
        }
    });


});


$('body').on('click', '#update-apparatus-criticus-line', function() {

    
    let line_id = $(this).data('id');
    let action_url = $(this).data('action');
    let html = $('#id_new_apparatus_criticus_line_editor').find('.ql-editor').html();

    // submit the form via ajax then re-render the apparatus criticus area
    let data = {
        'line_id': line_id,
        'content': html
    }
    let csrf = document.querySelector("meta[name='token']").getAttribute('content');
    let headers = {};
    let that = this;
    headers['X-CSRFToken'] = csrf;

    $.ajax({
        url: action_url,
        type: "POST",
        data: data,
        headers: headers,
        context: document.body,
        dataType: 'json',
        success: function (data, textStatus, jqXHR) {
            let $builder_area = $('#apparatus_criticus_builder_area');

            $builder_area.replaceWith(data.html);
            $("body").css("cursor", "default");
            try {
                cache_forms();
            }
            catch(err) {
            }
            $('[data-toggle="tooltip"]').tooltip();
            $builder_area.find('.rich-editor').each(function() {
                initRichTextEditor($(this)) ;
            });
            // don't need to update the text editor as the index will not have changed
        },
        error: function (e) {
            console.log(e)
            alert('Sorry, an error occurred.')
        }
    });


});