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
  return new Promise((resolve) => {
    var modalContainer = document.createElement("div");
    // var modalHTML = await getModalTemplate();
    // modalContainer.innerHTML = modalHTML;
    getModalTemplate().then((modalHTML) => {
      modalContainer.innerHTML = modalHTML;
    });
    document.body.appendChild(modalContainer);
    $(modalContainer).find(".modal").modal({
      backdrop: "static",
    }); // init the modal
    // init the editor
    initRichTextEditor($("#content-editor"));
    setTimeout(() => {
      if (modalContainer.querySelector(".ql-editor")) {
        var modalQlEditor = modalContainer.querySelector(".ql-editor");
        modalQlEditor.innerText = content;
      }
    }, 50);

    modalContainer
      .querySelector("#update-content-button")
      .addEventListener("click", () => {
        content = modalContainer.querySelector(".ql-editor").innerText;
        $("#editContentModal").modal("hide");
      });

    // listen for when it's closed
    $("#editContentModal").on("hidden.bs.modal", function (e) {
      $(this).remove(); // Remove the modal from the DOM
      console.log(content);
      return content;
    });
  });
}
