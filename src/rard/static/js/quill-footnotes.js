const Module = Quill.import("core/module");
const BlockEmbed = Quill.import("blots/block/embed");
const Parchment = Quill.import("parchment");

// create custom blot for superscript footnote indicator
class FootnoteIndicator extends BlockEmbed {
  static create(value) {
    const number = value.substring(1);
    const node = super.create(value);
    node.classList.add("footnote-indicator");
    node.id = `footnote-indicator-${number}`;
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
    document.addEventListener("DOMContentLoaded", () => {
      // add highlight and edit listeners to existing notes
      if (document.getElementById("footnote-area")) {
        document.querySelectorAll(".footnote").forEach((footnote) => {
          footnote.addEventListener("mouseenter", this.addHighlight);
          footnote.addEventListener("mouseleave", this.removeHighlight);
          footnote.addEventListener("click", this.editNote);
        });
      }
    });
  }

  countFootnotes() {
    var footnoteCounter;
    if (document.querySelector(".footnote-indicator")) {
      var indicators = document.querySelectorAll(".footnote-indicator");
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
      var editLink = document.createElement("a");
      editLink.textContent = "Edit note";
      editLink.classList = "";
      const footnoteElement = document.createElement("p");
      footnoteElement.classList = "footnote pb-1 btn btn-sm btn-text";
      footnoteElement.id = `footnote-${footnoteNumber}`;
      footnoteElement.textContent = `${footnoteNumber}. ${footnoteContent}`;

      // insert it in the correct location in the list
      var nextFootnoteIndicator = this.findNextIndicator(footnoteNumber);
      if (nextFootnoteIndicator) {
        const footnoteID = nextFootnoteIndicator.id.replace(
          "footnote-indicator-",
          ""
        );
        const nextFootNoteItem = document.getElementById(
          `footnote-${footnoteID}`
        );
        this.footnoteArea.insertBefore(footnoteElement, nextFootNoteItem);
      } else this.footnoteArea.appendChild(footnoteElement);

      // add highlight and edit listeners
      footnoteElement.addEventListener("mouseenter", this.addHighlight);
      footnoteElement.addEventListener("mouseleave", this.removeHighlight);
      footnote.addEventListener("click", this.editNote);

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
            const footnoteID = node.id.replace("footnote-indicator-", "");
            removedFootnoteIDs.push(footnoteID);
          }
        });

        // Delete the corresponding footnote
        removedFootnoteIDs.forEach((footnoteID) => {
          const footnoteElement = document.getElementById(
            `footnote-${footnoteID}`
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
          footnote.id = `footnote-${expectedNumber}`;
          footnote.textContent = newText;
        }

        // update the indicator if the element is still there
        if (footnoteIndicator) {
          footnoteIndicator.id = `footnote-indicator-${expectedNumber}`;
          footnoteIndicator.textContent = `•${expectedNumber}`;
        }

        expectedNumber++;
      }
    }
  }

  findNextIndicator(footnoteNumber) {
    // When inserting a new footnote and there are other footnotes
    // this will find the next indicator and return it so the note
    // is inserted in the correct place
    var newIndicator = document.getElementById(
      `footnote-indicator-${footnoteNumber}`
    );
    var parentElement = newIndicator.parentElement;
    var parentSibling = parentElement.nextElementSibling;
    var cousinElement = parentSibling.firstElementChild;

    while (cousinElement) {
      if (
        cousinElement !== newIndicator &&
        cousinElement.tagName.toLowerCase() === "sup" &&
        cousinElement.classList.contains("footnote-indicator")
      ) {
        return cousinElement;
      }
      cousinElement = cousinElement.nextElementSibling;
    }
    return null;
  }

  addHighlight(e) {
    var noteID = e.target.id.replace("footnote-", "");
    var correspondingIndicator = document.getElementById(
      `footnote-indicator-${noteID}`
    );
    // add a highlight class to the elements - ensure this is in your CSS file
    e.target.classList.add("highlighted-note");
    correspondingIndicator.classList.add("highlighted-note");
  }
  removeHighlight(e) {
    var noteID = e.target.id.replace("footnote-", "");
    var correspondingIndicator = document.getElementById(
      `footnote-indicator-${noteID}`
    );
    e.target.classList.remove("highlighted-note");
    correspondingIndicator.classList.remove("highlighted-note");
  }
  editNote(e) {
    var updatedContent = prompt(
      `Update footnote:${e.target.innerText}`,
      `${e.target.innerText}`
    );
    e.target.innerText = updatedContent;
  }
}

Quill.register("modules/footnote", Footnote, true);
