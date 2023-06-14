var bookSelectElems = document.querySelectorAll("select[name=book]");

bookSelectElems.forEach((select) => {
  select.onchange = (e) => {
    var target = e.target;
    var value = target.selectedOptions[0].innerText;
    var parentElem = target.closest(".book-details");
    var definiteBookToggle = parentElem.querySelector("#id_definite_book");

    if (value.toString().toLowerCase().includes("unknown")) {
      definiteBookToggle.disabled = true;
      definiteBookToggle.checked = false;
    } else definiteBookToggle.disabled = false;
  };
});
