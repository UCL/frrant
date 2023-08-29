console.log(modalUrl);

async function getModalTemplate() {
  try {
    var currentPage = window.location.pathname;
    const response = await fetch(`${modalUrl}?sourcePage=${currentPage}`);
    return response.text();
  } catch (error) {
    console.error("Error fetching modal template:", error);
    return null;
  }
}

function addSymbolPickerToModal() {
  var symbolPicker = document.body.querySelector("#myForm");
  var modal = document.getElementById("editContentModal");
  modal.appendChild(symbolPicker);
}

function replaceSymbolPickerInBody() {
  var originalSymbolPickerContainer =
    document.body.querySelector(".container.mt-5");
  var modalPicker = document
    .getElementById("editContentModal")
    .querySelector("#myForm");
  originalSymbolPickerContainer.appendChild(modalPicker);
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
    initRichTextEditor($("#modal-content-editor"));
    setTimeout(() => {
      if (modalContainer.querySelector(".ql-editor")) {
        var modalQlEditor = modalContainer.querySelector(".ql-editor");

        modalContainer
          .querySelector(".ql-toolbar")
          .querySelector("button.ql-footnote").style.display = "none";

        modalQlEditor.innerHTML = content;
        modalQlEditor.focus();
        addSymbolPickerToModal();
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
      replaceSymbolPickerInBody();
      $(this).remove(); // Remove the modal from the DOM
      resolve(content);
    });
  });
}
