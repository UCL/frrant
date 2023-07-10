const Module = Quill.import("core/module");
const BlockEmbed = Quill.import("blots/block/embed");
const Parchment = Quill.import("parchment");

// create custom blot for superscript footnote indicator
class FootnoteIndicator extends BlockEmbed {
  static create(value) {
    const number = value.substring(1);
    const node = super.create(value);
    node.classList.add("footnote-indicator");
    node.id = `data-footnote-indicator-id-${number}`;
    node.textContent = value;
    return node;
  }
  static value(node) {
    return node.textContent;
  }
}
FootnoteIndicator.blotName = "footnote-indicator";
FootnoteIndicator.scope = Parchment.Scope.INLINE;
FootnoteIndicator.tagName = "sup";
// FootnoteIndicator.className = "footnote-indicator";

class FootnoteArea extends BlockEmbed {
  static create(value) {
    const node = super.create(value);
    node.classList = "pt-1 mt-2";
    node.id = "footnote-area";
    node.textContent = value;
    node.innerHTML = "<hr>";
    return node;
  }
  static value(node) {
    return node.textContent;
  }
}
FootnoteArea.blotName = "footnote-area";
FootnoteArea.scope = Parchment.Scope.BLOCK;
FootnoteArea.tagName = "div";

Quill.register("formats/footnote-indicator", FootnoteIndicator, true);
Quill.register("formats/footnote-area", FootnoteArea, true);

class Footnote extends Module {
  constructor(quill, options) {
    super(quill, options);
    this.quill = quill;
    this.toolbar = quill.getModule("toolbar");
    this.toolbar.addHandler("footnote", this.insertFootnote.bind(this));
    const observer = new MutationObserver(this.deleteFootnote.bind(this));
    observer.observe(this.quill.root, { childList: true, subtree: true });
  }

  setEditorSelectionWithinFootnoteArea() {
    const footnoteArea = document.getElementById("footnote-area");

    // Set the selection to encompass the whole footnote-area block
    const range = this.quill.getSelection();
    range.index = 0;
    range.length = footnoteArea.textContent.length;
    this.quill.setSelection(index);
  }

  countFootnotes() {
    var footnoteCounter;
    if (document.querySelector(".footnote-indicator")) {
      var indicators = document.querySelectorAll(".footnote-indicator");
      console.log(indicators.length);
      return (footnoteCounter = indicators.length + 1);
    } else return (footnoteCounter = 1); // if no indicators
  }

  insertFootnote() {
    var footnoteNumber = this.countFootnotes();
    const range = this.quill.getSelection();
    const index = range ? range.index : this.quill.getLength();

    if (!document.getElementById("footnote-area")) {
      // create the footnote area inside the ql-editor if it doesn't exist
      this.quill.insertEmbed(this.quill.getLength(), "footnote-area", "");
    }
    this.footnoteArea = document.getElementById("footnote-area");

    const footnoteContent = prompt("Enter footnote content:");
    if (footnoteContent) {
      // insert a superscripted indicator in the text editor
      this.quill.insertEmbed(index, "footnote-indicator", `•${footnoteNumber}`);
      this.quill.setSelection(index + 3);
      // create the content of the footnote in the footnote area
      const footnoteElement = document.createElement("p");
      footnoteElement.classList = "footnote pb-1";
      footnoteElement.id = `data-footnote-id-${footnoteNumber}`;
      footnoteElement.textContent = `${footnoteNumber}. ${footnoteContent}`;

      this.footnoteArea.appendChild(footnoteElement);
      this.cleanFootnoteNumbers();
      footnoteNumber++;
    }
  }

  deleteFootnote(mutationsList) {
    for (const mutation of mutationsList) {
      if (mutation.type === "childList" && mutation.removedNodes.length > 0) {
        // Check if any removed nodes are footnote indicators
        const removedFootnoteIDs = [];
        mutation.removedNodes.forEach((node) => {
          if (node.classList && node.classList.contains("footnote-indicator")) {
            const footnoteID = node.id.replace(
              "data-footnote-indicator-id-",
              ""
            );
            removedFootnoteIDs.push(footnoteID);
          }
        });

        // Delete the corresponding footnote
        removedFootnoteIDs.forEach((footnoteID) => {
          const footnoteElement = document.getElementById(
            `data-footnote-id-${footnoteID}`
          );
          if (footnoteElement) {
            footnoteElement.remove();
          }
          // ensure footnotes are in correct ascending order
          this.cleanFootnoteNumbers();
        });
      }
    }
  }

  cleanFootnoteNumbers() {
    var footnoteArea = document.getElementById("footnote-area");
    var footnotes = footnoteArea.querySelectorAll("p.footnote");
    var footnoteIndicators = document.querySelectorAll(
      "sup.footnote-indicator"
    );
    var expectedNumber = 1;
    // loop through all the elements and assign the numbers
    if (footnotes) {
      for (var i = 0; i < footnotes.length; i++) {
        var footnote = footnotes[i];
        var footnoteIndicator = footnoteIndicators[i];

        // update the footnote number if the element is still there
        if (footnote) {
          var originalText = footnote.textContent;
          var newText = `${expectedNumber}.${originalText
            .split(".")
            .slice(1)
            .join(".")}`;
          footnote.id = `data-footnote-id-${expectedNumber}`;
          footnote.textContent = newText;
        }

        // update the indicator if the element is still there
        if (footnoteIndicator) {
          footnoteIndicator.id = `data-footnote-indicator-id-${expectedNumber}`;
          footnoteIndicator.textContent = `•${expectedNumber}`;
        }

        expectedNumber++;
      }
    }
  }
}

Quill.register("modules/footnote", Footnote, true);
