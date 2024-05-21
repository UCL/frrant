const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value;

$("body").on("click", ".show-apparatus-criticus-form", function () {
  // alert('todo: show the form beneath this')
  $(".show-apparatus-criticus-form").show();
  let inserting_at = $(this).data("index");
  let $new_area = $("#new_apparatus_criticus_line_area");
  $new_area.insertAfter($(this));
  $("#id_new_apparatus_criticus_line_editor").find(".ql-editor").html("");
  $("#update-apparatus-criticus-line").hide();
  $("#submit-new-apparatus-criticus-line").show();
  $("#submit-new-apparatus-criticus-line").attr("data-index", inserting_at);

  $(".line-action").hide();
  $new_area.show();
  setUpNewApparatusCriticusLineEditor();
});

$("body").on("click", ".delete-apparatus-criticus-line", function () {
  if (
    !confirm(
      "Are you sure you want to delete this line? This cannot be undone."
    )
  ) {
    return;
  }
  let index = $(this).data("index");
  let line_id = $(this).data("id");
  let action_url = $(this).data("action");

  // submit the form via ajax then re-render the apparatus criticus area
  let data = {
    index: index,
    line_id: line_id,
  };
  let headers = {};
  headers["X-CSRFToken"] = csrftoken;

  $.ajax({
    url: action_url,
    type: "POST",
    data: data,
    headers: headers,
    context: document.body,
    dataType: "json",
    success: function (data, textStatus, jqXHR) {
      let $builder_area = $("#apparatus_criticus_builder_area");

      $builder_area.replaceWith(data.html);
      $("body").css("cursor", "default");
      try {
        cache_forms();
      } catch (err) {}
      $('[data-toggle="tooltip"]').tooltip();
      $builder_area.find(".rich-editor").each(function () {
        initRichTextEditor($(this));
      });
    },
    error: function (e) {
      console.log(e);
      alert("Sorry, an error occurred.");
    },
  });
});

function setupApparatusCriticusInlineEditors() {
  // add listeners to all the edit buttons
  document.querySelectorAll(".edit-app-crit-toggle").forEach((item) => {
    item.addEventListener("click", () => {
      var isEditingEnabled = item.getAttribute("data-editing");

      var id = item.getAttribute("data-id");
      var line = document.getElementById("appcrit" + id);
      if (isEditingEnabled) {
        // Editing is enabled, so save the line
        var data = {
          line_id: id,
          content: line.innerHTML,
        };
        fetch(g_update_apparatus_criticus_url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify(data),
        })
          .then((response) => {
            // change button and disable editing
            item.innerHTML = "Edit";
            item.removeAttribute("data-editing");
            line.setAttribute("contenteditable", false);
            CKEDITOR.instances["appcrit" + id].destroy();
            item.parentNode.querySelector(".cancelBtn").remove();
            document
              .querySelectorAll(".edit-app-crit-toggle")
              .forEach(function (item) {
                item.style.display = "block";
              });
          })
          .catch((error) => console.error("Error:", error));
      } else {
        // Enable editing
        line.setAttribute("contenteditable", true);
        line.focus();
        var original_content = line.innerHTML;
        item.innerHTML = "Save";
        item.setAttribute("data-editing", true);
        document
          .querySelectorAll(".edit-app-crit-toggle")
          .forEach(function (item) {
            item.style.display = "none";
          });
        item.style.display = "block";
        var editor = CKEDITOR.inline(line, {
          toolbar: [
            {
              name: "basicstyles",
              items: [
                "Bold",
                "Italic",
                "Underline",
                "Superscript",
                "Subscript",
              ],
            },
          ],
          setFocus: true,
        });
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
        cancelBtn.addEventListener("click", () => {
          line.setAttribute("contenteditable", false);
          editor.destroy();
          line.innerHTML = original_content;
          item.innerHTML = "Edit";
          item.removeAttribute("data-editing");
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

function setUpNewApparatusCriticusLineEditor() {
  var newLine = document.getElementById("id_new_apparatus_criticus_line");
  var newLineArea = document.getElementById("new_apparatus_criticus_line_area");

  const builderArea = document.getElementById(
    "apparatus_criticus_builder_area"
  );

  var editor = CKEDITOR.replace(newLine, {
    toolbar: [
      {
        name: "basicstyles",
        items: ["Bold", "Italic", "Underline", "Superscript", "Subscript"],
      },
    ],
    setFocus: true,
    height: 100,
  });
  // ensure cancel deletes editor
  const cancelBtn = document.getElementById(
    "cancel-new-apparatus-criticus-line"
  );
  cancelBtn.classList.add("cancelBtn", "btn", "btn-sm");
  cancelBtn.addEventListener("click", () => {
    editor.destroy();
    document.querySelectorAll(".edit-app-crit-toggle").forEach(function (item) {
      item.style.display = "block";
    });
    newLine.remove();
    newLineArea.remove();
  });

  const submitBtn = document.getElementById(
    "submit-new-apparatus-criticus-line"
  );

  submitBtn.addEventListener("click", () => {
    let html = editor.getData();

    let action_url = submitBtn.dataset.action;
    let insert_at = submitBtn.dataset.index;
    let parent_id = submitBtn.dataset.parent;

    let data = {
      content: html,
      insert_at: insert_at,
      parent_id: parent_id,
    };
    fetch(action_url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        editor.destroy();
        builderArea.outerHTML = data.html;
        setupApparatusCriticusInlineEditors();
        try {
          cache_forms();
        } catch (err) {}
        $('[data-toggle="tooltip"]').tooltip();
      })
      .catch((error) => console.error("Error:", error));
  });
}
