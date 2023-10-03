var bookSelectElems = document.querySelectorAll("select[name=book]");
var workSelectElems = document.querySelectorAll("select[name=work]");

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

workSelectElems.forEach((select) => {
  select.onchange = (e) => {
    var target = e.target;
    var value = target.selectedOptions[0].innerText;
    var parentElem = target.closest(".work-details");
    var definiteBookToggle = parentElem.querySelector("#id_definite_work");

    if (value.toString().toLowerCase().includes("unknown")) {
      definiteBookToggle.disabled = true;
      definiteBookToggle.checked = false;
    } else definiteBookToggle.disabled = false;
  };
});

// const observer = new MutationObserver((mutationsList, observer) => {
//   for (const mutation of mutationsList) {
//       if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
//           const selectedValue = selectElement.value;
//           console.log(`Selected value changed to: ${selectedValue}`);
//       }
//   }
// });

// // Configure the observer to monitor attribute changes on the 'value' attribute
// observer.observe(selectElement, { attributes: true, attributeFilter: ['value'] });
