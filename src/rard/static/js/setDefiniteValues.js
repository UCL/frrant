function setValues(e, fieldName) {
  console.log(e.target.value, e.target.checked);
  var checkboxValue = e.target.closest("input[type='checkbox']").checked;
  document.querySelectorAll(`input[name=${fieldName}]`).forEach((input) => {
    input.checked = checkboxValue;
    input.value = checkboxValue;
  });
}
