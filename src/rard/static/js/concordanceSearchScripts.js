var workSelectElem;

document.addEventListener("DOMContentLoaded", function () {
  document.addEventListener("htmx:configRequest", function (event) {
    document.getElementById("loader").style.visibility = "visible";
  });

  document.addEventListener("htmx:beforeSwap", function (event) {
    if (event.detail.target.id === "concordance-search__results") {
      document.getElementById("loader").style.visibility = "hidden";
    }
  });

  document
    .getElementById("id_antiquarian")
    .addEventListener("change", enableWork);

  workSelectElem = document.getElementById("id_work");
  const workObserver = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.type === "childList") {
        updateLabel(workSelectElem);
      }
    });
  });
  partSelectElem = document.getElementById("id_identifier");
  const partObserver = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (mutation.type === "childList") {
        updateLabel(partSelectElem);
      }
    });
  });

  const config = {
    childList: true,
    subtree: false,
  };
  // watch the work and identifier dropdowns for changes to update the badges (these get updated via requests)
  workObserver.observe(workSelectElem, config);
  partObserver.observe(partSelectElem, config);
});

function enableWork() {
  if (document.getElementById("id_antiquarian").value) {
    workSelectElem.disabled = false;
  }
}

function disableWork() {
  workSelectElem.disabled = true;
  workSelectElem.innerHTML = "";
}

function updateLabel(elem) {
  var optionCount = 0;
  var options = elem.querySelectorAll("option");
  optionCount = options.length;
  optionCount = optionCount - 1; // don't include the blank
  optionCount = optionCount < 0 ? 0 : optionCount; // if no parts, don't show as -1
  var label = document.querySelector(`label[for="${elem.id}"]>span`);
  label.textContent = optionCount;

  if (optionCount == 0) {
    elem.disabled = true;
  } else {
    elem.disabled = false;
  }
}
