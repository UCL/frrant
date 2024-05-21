CKEDITOR.plugins.add("vinculum", {
  icons: "vinculum_on,vinculum_off",
  init: function (editor) {
    editor.ui.addButton("vinculumOn", {
      label: "add vinculum",
      command: "addVinculum",
      toolbar: "insert",
      icon: this.path + "icons/vinculum_on.png",
    });

    editor.addCommand("addVinculum", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();
        var combinedText = selectedText
          .split("")
          .map((char) => char + "\u0305")
          .join("");
        editor.insertText(combinedText);
      },
    });

    editor.ui.addButton("vinculumOff", {
      label: "remove vinculum",
      command: "removeVinculum",
      toolbar: "insert",
      icon: this.path + "icons/vinculum_off.png",
    });

    editor.addCommand("removeVinculum", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();
        var newText = selectedText.replace(/\u0305/g, "");
        editor.insertText(newText);
      },
    });
  },
});
