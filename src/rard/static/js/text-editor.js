var enableMentions;
var enableFootnotes;
var enableApparatusCriticus;
var appCriticusFeed;

CKEDITOR.plugins.add("vinculumOn", {
  icons: "V\u0305",
  init: function (editor) {
    editor.ui.addButton("vinculumOn", {
      label: "V\u0305",
      command: "addVinculum",
    });

    editor.addCommand("addVinculum", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var combinedText = selectedText + "\u0305";

        editor.insertText(combinedText);
      },
    });
  },
});
CKEDITOR.plugins.add("vinculumOff", {
  icons: "V",
  init: function (editor) {
    editor.ui.addButton("vinculumOff", {
      label: "V",
      command: "removeVinculum",
    });

    editor.addCommand("removeVinculum", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var hasOverline = selectedText.includes("\u0305");

        if (hasOverline) {
          var newText = selectedText.replace("\u0305", "");
          editor.insertText(newText);
        } else {
          // If the selected text does not contain the overline character, do nothing
        }
      },
    });
  },
});
CKEDITOR.plugins.add("underdotOn", {
  icons: "U\u0323",
  init: function (editor) {
    editor.ui.addButton("underdotOn", {
      label: "U\u0323",
      command: "addUnderdot",
    });

    editor.addCommand("addUnderdot", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var combinedText = selectedText + "\u0323";

        editor.insertText(combinedText);
      },
    });
  },
});
CKEDITOR.plugins.add("underdotOff", {
  icons: "U",
  init: function (editor) {
    editor.ui.addButton("underdotOff", {
      label: "U",
      command: "removeUnderdot",
    });

    editor.addCommand("removeUnderdot", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var hasOverline = selectedText.includes("\u0323");

        if (hasOverline) {
          var newText = selectedText.replace("\u0305", "");
          editor.insertText(newText);
        } else {
          // If the selected text does not contain the underdot character, do nothing
        }
      },
    });
  },
});
CKEDITOR.plugins.add("mentionsWidget", {
  requires: 'widget',
  init: function (editor) {
    editor.widgets.add('mentionWidget', {
      template: '<span class="mention"></span>',
      upcast: function (element) {
        return element.name == 'span' && element.hasClass('mention');
      }
    })
  }
})

function initRichTextEditor(elem) {
  let container = document.querySelector(`#${elem}`);
  if (container.classList.contains("enableFootnotes")) {
    enableFootnotes = true;
  }
  enableFootnotes = true;
  if (container.classList.contains("enableMentions")) {
    enableMentions = true;
  }
  enableMentions = true;
  if (container.classList.contains("enableApparatusCriticus")) {
    enableApparatusCriticus = true;
    let object_id = container.getAttribute("data-object");
    let object_class = container.getAttribute("data-class") || "originaltext";
    appCriticusFeed = `${g_apparatus_criticus_url}?q={encodedQuery}&object_id=${object_id}&object_class=${object_class}`;
  }
  CKEDITOR.replace(elem)
}

function initRichTextEditors() {
  var elements = document.querySelectorAll(".enableCKEditor");
  elements.forEach((element) => {
    console.log("Initialising rich text editor...", element)
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


function setupApparatusCriticusInlineEditors() {
  console.log("Setting up inline App crit editors");
  document.querySelectorAll(".edit-app-crit-toggle").forEach(function (item) {
    item.addEventListener('click', function () {
      var isEditingEnabled = this.getAttribute('data-editing');
      if (isEditingEnabled) {
        // Editing is enabled, so save the line
        var id = this.getAttribute('data-id');
        var line = document.getElementById('appcrit' + id);
        // Save the line
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        var data = {
          //'csrfmiddlewaretoken': csrftoken,
          'line_id': id,
          'content': line.innerHTML
        };
        var url = '{% url "update_apparatus_criticus_line" %}';
        fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
          },
          body: JSON.stringify(data),
        })
          .then(response => {
            // change button and disable editing
            this.innerHTML = 'Edit';
            this.removeAttribute('data-editing');
            line.setAttribute('contenteditable', false);
            CKEDITOR.instances["appcrit" + id].destroy();
            this.parentNode.querySelector(".cancelBtn").remove();
            document.querySelectorAll(".edit-app-crit-toggle").forEach(function (item) {
              item.style.display = "block";
            })
          })
          .catch(error => console.error('Error:', error));
      } else {
        // Enable editing
        var id = this.getAttribute('data-id');
        var line = document.getElementById('appcrit' + id);
        line.setAttribute('contenteditable', true);
        line.focus();
        var original_content = line.innerHTML;
        this.innerHTML = 'Save';
        this.setAttribute('data-editing', true);
        document.querySelectorAll(".edit-app-crit-toggle").forEach(function (item) {
          item.style.display = "none";
        })
        this.style.display = "block";
        var editor = CKEDITOR.inline('appcrit' + id, {
          toolbar: [
            {
              name: "basicstyles",
              items: [
                "Bold",
                "Italic",
                "Underline"
              ]
            }
          ],
          setFocus: true
        });
        // Add cancel button
        cancelBtn = document.createElement("button");
        cancelBtn.textContent = "Cancel";
        cancelBtn.classList.add("cancelBtn", "btn", "btn-link", "text-primary", "btn-sm");
        item.parentNode.insertBefore(cancelBtn, item.parentNode.querySelector(".delete-apparatus-criticus-line"));
        console.log("added button");
        cancelBtn.addEventListener("click", () => {
          line.setAttribute('contenteditable', false);
          editor.destroy()
          line.innerHTML = original_content;
          this.innerHTML = "Edit";
          this.removeAttribute('data-editing');
          cancelBtn.remove();
          document.querySelectorAll(".edit-app-crit-toggle").forEach(function (item) {
            item.style.display = "block";
          })
        })
      }
    });
  });
}

addEventListener("DOMContentLoaded", (evt) => { setupApparatusCriticusInlineEditors() });
