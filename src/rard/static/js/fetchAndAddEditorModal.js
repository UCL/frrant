async function getModalTemplate() {
  try {
    const response = await fetch("/render-editor-modal-template/");
    return response.text();
  } catch (error) {
    console.error("Error fetching modal template:", error);
    return null;
  }
}

async function addModal(content) {
  var modalContainer = document.createElement("div");
  var modalHTML = await getModalTemplate();
  modalContainer.innerHTML = modalHTML;
  return new Promise((resolve) => {
    document.body.appendChild(modalContainer);
    $(modalContainer).find(".modal").modal({
      backdrop: "static",
    }); // init the modal
    // init the editor
    initRichTextEditor($("#content-editor"));
    setTimeout(() => {
      if (modalContainer.querySelector(".ql-editor")) {
        var modalQlEditor = modalContainer.querySelector(".ql-editor");
        modalQlEditor.innerHTML = content;
        modalQlEditor.focus();
      }
    }, 15);

    modalContainer
      .querySelector("#update-content-button")
      .addEventListener("click", () => {
        // update content on save
        content = modalContainer.querySelector(".ql-editor").innerHTML;
        $("#editContentModal").modal("hide");
      });
    modalContainer
      .querySelector("#delete-content")
      .addEventListener("click", () => {
        // update content on save
        content = "delete";
        $("#editContentModal").modal("hide");
      });

    // listen for when it's closed
    $("#editContentModal").on("hidden.bs.modal", function (e) {
      $(this).remove(); // Remove the modal from the DOM
      resolve(content);
    });
  });
}
