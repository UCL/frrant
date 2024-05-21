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
  CKEDITOR.replace(elem);
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

function setupApparatusCriticusInlineEditors() {
  console.log("Setting up inline App crit editors");
  document.querySelectorAll(".edit-app-crit-toggle").forEach((item) => {
    item.addEventListener("click", () => {
      var isEditingEnabled = this.getAttribute("data-editing");
      if (isEditingEnabled) {
        // Editing is enabled, so save the line
        var id = this.getAttribute("data-id");
        var line = document.getElementById("appcrit" + id);
        // Save the line
        const csrftoken = document.querySelector(
          "[name=csrfmiddlewaretoken]"
        ).value;
        var data = {
          line_id: id,
          content: line.innerHTML,
        };
        var url = '{% url "update_apparatus_criticus_line" %}';
        fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify(data),
        })
          .then((response) => {
            // change button and disable editing
            this.innerHTML = "Edit";
            this.removeAttribute("data-editing");
            line.setAttribute("contenteditable", false);
            CKEDITOR.instances["appcrit" + id].destroy();
            this.parentNode.querySelector(".cancelBtn").remove();
            document
              .querySelectorAll(".edit-app-crit-toggle")
              .forEach(function (item) {
                item.style.display = "block";
              });
          })
          .catch((error) => console.error("Error:", error));
      } else {
        // Enable editing
        var id = this.getAttribute("data-id");
        var line = document.getElementById("appcrit" + id);
        line.setAttribute("contenteditable", true);
        line.focus();
        var original_content = line.innerHTML;
        this.innerHTML = "Save";
        this.setAttribute("data-editing", true);
        document
          .querySelectorAll(".edit-app-crit-toggle")
          .forEach(function (item) {
            item.style.display = "none";
          });
        this.style.display = "block";
        var editor = CKEDITOR.inline("appcrit" + id, {
          toolbar: [
            {
              name: "basicstyles",
              items: ["Bold", "Italic", "Underline"],
            },
          ],
          setFocus: true,
        });
        editor;
        // Add cancel button
        cancelBtn = document.createElement("button");
        cancelBtn.textContent = "Cancel";
        cancelBtn.classList.add(
          "cancelBtn",
          "btn",
          "btn-link",
          "text-primary",
          "btn-sm"
        );
        item.parentNode.insertBefore(
          cancelBtn,
          item.parentNode.querySelector(".delete-apparatus-criticus-line")
        );
        console.log("added button");
        cancelBtn.addEventListener("click", () => {
          line.setAttribute("contenteditable", false);
          editor.destroy();
          line.innerHTML = original_content;
          this.innerHTML = "Edit";
          this.removeAttribute("data-editing");
          cancelBtn.remove();
          document
            .querySelectorAll(".edit-app-crit-toggle")
            .forEach(function (item) {
              item.style.display = "block";
            });
        });
      }
    });
  });
}

addEventListener("DOMContentLoaded", (evt) => {
  setupApparatusCriticusInlineEditors();
});
