var states = [];
let saving;
function cache_forms() {
  states = [];
  $('form').each(function () {
    var initial_form_state = $(this).serialize();
    states.push(initial_form_state);
  });

}

cache_forms();

$('form').submit(function () {
  var initial_form_state = $(this).serialize();
  var index = $("form").index($(this));
  saving = index;
});

$(window).bind('beforeunload', function (e) {
  var index = 0;
  var changes = false;
  $('form').each(function () {
    var form_state = $(this).serialize();
    if (saving !== index && states[index] != form_state) {
      changes = true;
    }
    index += 1;
  });
  if (changes) {
    var message = "You may have unsaved changes on this page. Do you want to leave this page and discard your changes or stay on this page?";
    e.returnValue = message; // Cross-browser compatibility (src: MDN)
    return message;
  }
});

