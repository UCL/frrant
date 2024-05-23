var enableMentions;
var enableFootnotes;
var enableApparatusCriticus;
var appCriticusFeed;

CKEDITOR.plugins.add("mentionsWidget", {
  requires: "widget",
  init: function (editor) {
    editor.widgets.add("mentionWidget", {
      template: '<span class="mention"></span>',
      upcast: function (element) {
        return element.name == "span" && element.hasClass("mention");
      },
    });
  },
});

function initRichTextEditor(elem) {
  let container = document.querySelector(`#${elem}`);
  if (container.classList.contains("enableFootnotes")) {
    enableFootnotes = true;
  }
  if (container.classList.contains("enableMentions")) {
    enableMentions = true;
  }
  if (container.classList.contains("enableApparatusCriticus")) {
    enableApparatusCriticus = true;
    let object_id = container.getAttribute("data-object");
    let object_class = container.getAttribute("data-class") || "originaltext";
    appCriticusFeed = `${g_apparatus_criticus_url}?q={encodedQuery}&object_id=${object_id}&object_class=${object_class}`;
  }

  if (container.classList.contains("CKEditorBasic")) {
    var editor = CKEDITOR.replace(elem, {
      toolbar: [
        {
          name: "basicstyles",
          items: ["Bold", "Italic"],
        },
      ],
      height: 50,
    });
  } else {
    var editor = CKEDITOR.replace(elem);
  }

  document.addEventListener("htmx:configRequest", function (event) {
    var param = document.getElementById(elem).getAttribute("name");
    // directly send the updated content from editor since htmx prevents regular submit
    // works for intros and commentaries
    var html = editor.getData();
    event.detail.parameters[param] = html;
  });
}

function initRichTextEditors() {
  var elements = document.querySelectorAll(".enableCKEditor");
  elements.forEach((element) => {
    console.log("Initialising rich text editor...", element);
    initRichTextEditor(element.id);
  });
}

initRichTextEditors();

// If swapping form containing rich text editor with htmx
// we need to initialise it
document.addEventListener("htmx:afterSettle", function (evt) {
  var verb = evt.detail.requestConfig.verb;
  //
  if (
    evt.detail.target.classList.contains("rich-text-form-container") &&
    verb == "get"
  ) {
    initRichTextEditors();
  }
  if (verb == "post" && evt.detail.successful) {
    $(".htmx-get-button").show(); // Show edit button again
    $('[data-toggle="tooltip"]').tooltip(); // Enable tooltips in updated content
  }
});

setupApparatusCriticusInlineEditors();
