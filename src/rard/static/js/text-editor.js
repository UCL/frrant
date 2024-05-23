var enableMentions;
var enableFootnotes;
var enableApparatusCriticus;
var appCriticusFeed;

CKEDITOR.plugins.add("mentionsWidget", {
  requires: "widget",
  init: function (editor) {
    editor.widgets.add("mentionWidget", {
      template: '<span class="mention bg-light"></span>',
      upcast: function (element) {
        return element.name == "span" && element.hasClass("mention");
      },
    });
  },
});

function initRichTextEditor(elem) {
  let container = document.querySelector(`#${elem}`);
  let pluginNames = [];
  if (container.classList.contains("enableFootnotes")) {
    enableFootnotes = true;
    pluginNames.push("Footnotes");
  }
  if (container.classList.contains("enableMentions")) {
    enableMentions = true;
    pluginNames.push("Mentions");
  }
  if (container.classList.contains("enableApparatusCriticus")) {
    enableApparatusCriticus = true;
    pluginNames.push("Apparatus Criticus");
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

    editor.on("instanceReady", function (event) {
      var editor = event.editor;
      const pluginElement = document.createElement("div");
      editor.container.$.parentElement.parentElement.insertBefore(
        pluginElement,
        editor.container.$.parentElement.nextSibling
      );
      pluginElement.id = "plugin-info";
      pluginNames.forEach((pname) => {
        if (pname === "Mentions") {
          pluginElement.innerHTML += `<small class="text-muted"
          data-toggle="tooltip"
          data-html="true"
          title="
            Content type codes: </br>
            @aq - Antiquarian</br>
            @wk - Work</br>
            @bi - Bibliography Item</br>
            @tp - Topic</br>
            @fr - Fragment</br>
            @tt - Testimonium</br>
            @af - Anonymous Fragment</br>
            @uf - Unlinked Fragment"
          >@mentions are enabled <i class="bi bi-info-circle"></i></small>`;
        } else if (pname === "Apparatus Criticus") {
          pluginElement.innerHTML += `<span class="text-muted"><small>Type # for apparatus criticus items.</small></span>`;
        } else {
          pluginElement.innerHTML += `<small class="text-muted">${pname} are enabled</small>`;
        }
        pluginElement.innerHTML += `<br>`;
      });
      $('[data-toggle="tooltip"]').tooltip();
    });
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

{
}
