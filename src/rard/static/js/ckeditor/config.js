/**
 * @license Copyright (c) 2003-2023, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function (config) {
  // %REMOVE_START%
  // The configuration options below are needed when running CKEditor from source files.
  config.plugins =
    "dialogui,dialog,about,a11yhelp,basicstyles,blockquote,notification,button,toolbar,clipboard,panel,floatpanel,menu,contextmenu,resize,elementspath,enterkey,entities,popup,filetools,filebrowser,floatingspace,listblock,richcombo,format,horizontalrule,htmlwriter,wysiwygarea,image,indent,indentlist,fakeobjects,link,list,magicline,maximize,pastetext,xml,ajax,pastetools,pastefromgdocs,pastefromlibreoffice,pastefromword,removeformat,showborders,sourcearea,specialchar,menubutton,scayt,stylescombo,tab,table,tabletools,tableselection,undo,lineutils,widgetselection,widget,notificationaggregator,uploadwidget,uploadimage,footnotes,textwatcher,autocomplete,textmatch,mentions";
  config.skin = "moono-lisa";
  // %REMOVE_END%

  // Define changes to default configuration here.
  // For complete reference see:
  // https://ckeditor.com/docs/ckeditor4/latest/api/CKEDITOR_config.html

  // The toolbar groups arrangement, optimized for two toolbar rows.
  config.toolbarGroups = [
    { name: "clipboard", groups: ["clipboard", "undo"] },
    { name: "editing", groups: ["find", "selection", "spellchecker"] },
    { name: "links" },
    { name: "insert" },
    { name: "forms" },
    { name: "tools" },
    { name: "document", groups: ["mode", "document", "doctools"] },
    { name: "others" },
    "/",
    { name: "basicstyles", groups: ["basicstyles", "cleanup"] },
    {
      name: "paragraph",
      groups: ["list", "indent", "blocks", "align", "bidi"],
    },
    { name: "styles" },
    { name: "colors" },
    { name: "about" },
  ];

  // Remove some buttons provided by the standard plugins, which are
  // not needed in the Standard(s) toolbar.
  //   config.removeButtons = "Underline,Subscript,Superscript";

  // Set the most common block elements.
  config.format_tags = "p;h1;h2;h3;pre";

  // Simplify the dialog windows.
  config.removeDialogTabs = "image:advanced;link:advanced";

  config.uiColor = "#F7E5D0";

  config.toolbar = [
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
    { name: "styles", items: ["Styles", "Format", "Font", "FontSize"] },
    { name: "colors", items: ["TextColor", "BGColor"] },
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
    { name: "insert", items: ["Image", "Table"] },
    {
      name: "others",
      items: ["vinculumOn", "vinculumOff", "-", "underdotOn", "underdotOff"],
    },

    { name: "tools", items: ["ShowBlocks"] },
  ];

  config.extraPlugins = "vinculum,underdot,floating-tools";
  if (enableFootnotes) {
    config.extraPlugins += ",footnotes";
    config.toolbar[8].items.push("Footnotes");
  }

  if (enableMentions || enableApparatusCriticus) {
    config.extraPlugins += ",mentions, mentionsWidget";
    config.mentions = [];
    if (enableMentions) {
      config.mentions.push({
        feed: `${g_mention_url}?q={encodedQuery}`,
        marker: "@",
        output: "<span class='mention'>$1</span>",
        minChars: 0,
        pattern: /@([a-zA-Z]{2}):.*/,
        followingSpace: true,
        itemTemplate: "<li data-id='{id}'>{value}</li>",
        outputTemplate: `<span class='mention'
			data-target={target}
			data-id={id}>
		<span contenteditable="false">
		<span>@</span>
		{citation}
		</span>
	</span>`,
      });
    }
    if (enableApparatusCriticus) {
      config.mentions.push({
        marker: "#",
        minChars: 0,
        feed: appCriticusFeed, // defined in text-editor.js
        itemTemplate: "<li data-id='{id}'>{list_display}</li>",
        outputTemplate: `<span class='mention'
			data-denotation-char='#'
			data-target='{target}'
			data-id='{id}'
			data-index='0'
			data-original-text='{originalText}'
			data-parent='{parent}'
			data-value='{value}'>
		<span contenteditable='false'>
		<span>#</span>
		{value}
		</span>\ufeff
	</span>`,
      });
    }
  }

  config.extraAllowedContent = `span(mention)[data-target,data-id, data-value, data-original-text, data-parent, data-index, data-denotation-char];
	sup[data-footnote-id];
	section(footnotes);
	li[data-footnote-id];
	a[href]`;
};
