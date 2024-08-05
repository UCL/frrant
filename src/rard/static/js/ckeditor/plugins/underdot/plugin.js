CKEDITOR.plugins.add("underdot", {
  icons: "underdot_on,underdot_off",
  init: function (editor) {
    editor.ui.addButton("underdotOn", {
      label: "add underdot",
      command: "addUnderdot",
      toolbar: "insert",
      icon: this.path + "icons/underdot_on.png",
    });

    editor.addCommand("addUnderdot", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();
        var combinedText = selectedText
          .split("")
          .map((char) => char + "\u0323")
          .join("");
        editor.insertText(combinedText);
      },
    });

    editor.ui.addButton("underdotOff", {
      label: "remove underdot",
      command: "removeUnderdot",
      toolbar: "insert",
      icon: this.path + "icons/underdot_off.png",
    });

    editor.addCommand("removeUnderdot", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();
        var newText = selectedText.replace(/\u0323/g, "");
        editor.insertText(newText);
      },
    });
  },
});
