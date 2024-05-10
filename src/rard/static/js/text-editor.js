// CKEDITOR.editorConfig = function (config) {
//   config.uiColor = "#AADC6E";
//   config.toolbar = [
//     {
//       name: "clipboard",
//       items: [
//         "Cut",
//         "Copy",
//         "Paste",
//         "PasteText",
//         "PasteFromWord",
//         "-",
//         "Undo",
//         "Redo",
//       ],
//     },
//     {
//       name: "editing",
//       items: ["Find", "Replace", "-", "SelectAll", "-", "Scayt"],
//     },
//     "/",
//     {
//       name: "basicstyles",
//       items: [
//         "Bold",
//         "Italic",
//         "Underline",
//         "Strike",
//         "Subscript",
//         "Superscript",
//         "-",
//         "RemoveFormat",
//       ],
//     },
//     {
//       name: "paragraph",
//       items: [
//         "NumberedList",
//         "BulletedList",
//         "-",
//         "Outdent",
//         "Indent",
//         "-",
//         "Blockquote",
//       ],
//     },
//     { name: "links", items: ["Link", "Unlink"] },
//     { name: "insert", items: ["Image", "SpecialChar", "Table", "Footnote"] },
//     { name: "styles", items: ["Styles", "Format", "Font", "FontSize"] },
//     { name: "colors", items: ["TextColor", "BGColor"] },
//     { name: "tools", items: ["ShowBlocks"] },
//     {
//       name: "others",
//       items: ["vinculumOn", "vinculumOff", "-", "underdotOn", "underdotOff"],
//     },
//   ];

//   config.extraPlugins =
//     "vinculumOn,vinculumOff,underdotOn,underdotOff,footnotes,mentions";
// };
CKEDITOR.plugins.add("vinculumOn", {
  icons: "V\u0305",
  init: function (editor) {
    editor.ui.addButton("vinculumOn", {
      label: "V\u0305",
      command: "addVinculum",
    });

    editor.addCommand("addVinculum", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var combinedText = selectedText + "\u0305";

        editor.insertText(combinedText);
      },
    });
  },
});
CKEDITOR.plugins.add("vinculumOff", {
  icons: "V",
  init: function (editor) {
    editor.ui.addButton("vinculumOff", {
      label: "V",
      command: "removeVinculum",
    });

    editor.addCommand("removeVinculum", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var hasOverline = selectedText.includes("\u0305");

        if (hasOverline) {
          var newText = selectedText.replace("\u0305", "");
          editor.insertText(newText);
        } else {
          // If the selected text does not contain the overline character, do nothing
        }
      },
    });
  },
});
CKEDITOR.plugins.add("underdotOn", {
  icons: "U\u0323",
  init: function (editor) {
    editor.ui.addButton("underdotOn", {
      label: "U\u0323",
      command: "addUnderdot",
    });

    editor.addCommand("addUnderdot", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var combinedText = selectedText + "\u0323";

        editor.insertText(combinedText);
      },
    });
  },
});
CKEDITOR.plugins.add("underdotOff", {
  icons: "U",
  init: function (editor) {
    editor.ui.addButton("underdotOff", {
      label: "U",
      command: "removeUnderdot",
    });

    editor.addCommand("removeUnderdot", {
      exec: function (editor) {
        var selection = editor.getSelection();
        var selectedText = selection.getSelectedText();

        var hasOverline = selectedText.includes("\u0323");

        if (hasOverline) {
          var newText = selectedText.replace("\u0305", "");
          editor.insertText(newText);
        } else {
          // If the selected text does not contain the underdot character, do nothing
        }
      },
    });
  },
});
CKEDITOR.plugins.addExternal("footnotes", "./footnotes/plugin.js");

CKEDITOR.replace("ckeditortest", {
  uiColor: "#AADC6E",
  toolbar: [
    {
      name: "clipboard",
      items: [
        "Cut",
        "Copy",
        "Paste",
        "PasteText",
        "PasteFromWord",
        "-",
        "Undo",
        "Redo",
      ],
    },
    {
      name: "editing",
      items: ["Find", "Replace", "-", "SelectAll", "-", "Scayt"],
    },
    "/",
    {
      name: "basicstyles",
      items: [
        "Bold",
        "Italic",
        "Underline",
        "Strike",
        "Subscript",
        "Superscript",
        "-",
        "RemoveFormat",
      ],
    },
    {
      name: "paragraph",
      items: [
        "NumberedList",
        "BulletedList",
        "-",
        "Outdent",
        "Indent",
        "-",
        "Blockquote",
      ],
    },
    { name: "links", items: ["Link", "Unlink"] },
    { name: "insert", items: ["Image", "SpecialChar", "Table", "Footnote"] },
    { name: "styles", items: ["Styles", "Format", "Font", "FontSize"] },
    { name: "colors", items: ["TextColor", "BGColor"] },
    { name: "tools", items: ["ShowBlocks"] },
    {
      name: "others",
      items: ["vinculumOn", "vinculumOff", "-", "underdotOn", "underdotOff"],
    },
  ],

  extraPlugins: "vinculumOn,vinculumOff,underdotOn,underdotOff,mentions",
  //todo: add footnotes manually
});

function initRichTextEditor(elem) {
  console.log(elem);
  CKEDITOR.replace(elem);
}
