var bookSelectElems = document.querySelectorAll("select[name=book]");

bookSelectElems.forEach((select) => {
  select.onchange = (e) => {
    var target = e.target;
    var value = target.selectedOptions[0].innerText;
    var parentElem = target.closest(".book-details");
    var definiteBookToggle = parentElem.querySelector("#id_definite_book");

    if (value.toString().toLowerCase().includes("unknown")) {
      console.log("Unknown book selected!");
      definiteBookToggle.disabled = true;
    } else definiteBookToggle.disabled = false;
  };
});
