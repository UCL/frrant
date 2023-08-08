var Module = Quill.import("core/module");
var BlockEmbed = Quill.import("blots/block/embed");
var Parchment = Quill.import("parchment");

// create custom blot for superscript footnote indicator
class FootnoteIndicator extends BlockEmbed {
  static blotName = "footnote-indicator";
  static scope = Parchment.Scope.INLINE;
  static tagName = "SUP";

  static create(value) {
    const number = value.trim();
    const node = super.create(value);
    node.classList.add("footnote-indicator");
    node.id = `footnote-indicator-${number}`;
    node.textContent = value;
    node.setAttribute("data-toggle", "tooltip");
    node.setAttribute("data-placement", "top");
    node.setAttribute("contenteditable", "false");
    return node;
  }
  static value(node) {
    return node.textContent;
  }
}
class FootnoteArea extends BlockEmbed {
  static blotName = "footnote-area";
  static scope = Parchment.Scope.BLOCK;
  static tagName = "div";

  static create(value) {
    const node = super.create(value);
    node.id = "footnote-area"; // edit styling in CSS
    node.textContent = value;
    node.innerHTML = "<hr>";
    return node;
  }
  static value(node) {
    return node.textContent;
  }
}

Quill.register("formats/footnote-indicator", FootnoteIndicator, true);
Quill.register("formats/footnote-area", FootnoteArea, true);

class Footnote extends Module {
  constructor(quill, options) {
    super(quill, options);
    this.quill = quill;
    this.toolbar = quill.getModule("toolbar");
    this.toolbar.addHandler("footnote", this.insertFootnote.bind(this));

    const observer = new MutationObserver(this.handleDeletion.bind(this));
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
      // insert a superscripted indicator in the text editor, space after is intended
      this.quill.insertEmbed(index, "footnote-indicator", `${footnoteNumber} `);

      // this.quill.setSelection(index + 1);
      const cursorPosition = index + 1; // Set the desired cursor position
      this.quill.setSelection(cursorPosition);

      // Add the ql-cursor class to the selected range to style the cursor
      const range = this.quill.getSelection();
      range.length = 0; // Remove the selection
      range.index = cursorPosition; // Set the index to the cursor position
      this.quill.setSelection(range);

      // create the content of the footnote in the footnote area
      const footnoteElement = document.createElement("p");
      footnoteElement.classList = "footnote";
      footnoteElement.id = `footnote-${footnoteNumber}`;
      footnoteElement.textContent = `${footnoteNumber}. ${footnoteContent}`;

      // insert it in the correct location in the list
      var nextFootnoteIndicator = this.findNextIndicator(footnoteNumber);
      if (nextFootnoteIndicator) {
        const footnoteID = nextFootnoteIndicator.id.match(/\d+/)[0];
        const nextFootNoteItem = document.getElementById(
          `footnote-${footnoteID}`
        );
        this.footnoteArea.insertBefore(footnoteElement, nextFootNoteItem);
      } else this.footnoteArea.appendChild(footnoteElement);

      // add tooltip content
      var indicatorElement = document.getElementById(
        `footnote-indicator-${footnoteNumber}`
      );
      indicatorElement.setAttribute("title", footnoteContent);
      // add highlight and edit listeners
      footnoteElement.addEventListener("mouseenter", this.addHighlight);
      footnoteElement.addEventListener("mouseleave", this.removeHighlight);
      footnoteElement.addEventListener("click", this.editNote);

      indicatorElement.addEventListener("mouseenter", this.addHighlight);
      indicatorElement.addEventListener("mouseleave", this.removeHighlight);

      this.cleanFootnoteNumbers();
      footnoteNumber++;
      $('[data-toggle="tooltip"]').tooltip(); //enable tooltips
    }
  }

  removeFootnote(node) {
    let footnoteID = node.id.match(/\d+/)[0];
    let footnoteElement = document.getElementById(`footnote-${footnoteID}`);
    if (footnoteElement) {
      footnoteElement.remove();
      return true;
    }
  }

  hasIndicatorChildren(node) {
    if (node.children) {
      for (var child of Array.from(node.children)) {
        if (child.classList && child.classList.contains("footnote-indicator")) {
          return true;
        }
      }
    }
    return false;
  }

  processMutations(mutationsList) {
    for (const mutation of mutationsList) {
      if (mutation.type === "childList" && mutation.removedNodes.length > 0) {
        let node = mutation.removedNodes[0];
        if (
          (node.classList && node.classList.contains("footnote-indicator")) ||
          this.hasIndicatorChildren(node) == true
        ) {
          this.removeFootnote(node);
        }
      }
    }
    return true;
  }

  handleDeletion(mutationsList) {
    let hasFinished = this.processMutations(mutationsList);
    if (hasFinished) {
      this.cleanFootnoteNumbers();
    }
  }

  cleanFootnoteNumbers() {
    var footnotes = document.querySelectorAll("p.footnote");
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
          footnoteIndicator.textContent = `${expectedNumber} `;
          footnoteIndicator.setAttribute("title", footnote.textContent);
          footnoteIndicator.setAttribute(
            "data-original-title",
            footnote.textContent
          );
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
    // if it's the last indicator in the editor, return null
    var allIndicators = document.querySelectorAll(".footnote-indicator");
    if (newIndicator == allIndicators[allIndicators.length - 1]) {
      return null;
    }

    var index = Array.from(allIndicators).indexOf(newIndicator);
    return allIndicators[index + 1];
  }

  addHighlight(e) {
    var noteID = e.target.id.match(/\d+/)[0];
    var indicator = document.getElementById(`footnote-indicator-${noteID}`);
    var footnote = document.getElementById(`footnote-${noteID}`);
    // add a highlight class to the elements - ensure this is in your CSS file
    if (footnote && indicator) {
      footnote.classList.add("highlighted-note-valid");
      indicator.classList.add("highlighted-note-valid");
    } else {
      if (footnote) {
        footnote.classList.add("highlighted-note-missing");
      }
      if (indicator) {
        indicator.classList.add("highlighted-note-missing");
      }
    }
  }
  removeHighlight(e) {
    var noteID = e.target.id.match(/\d+/)[0];
    var indicator = document.getElementById(`footnote-indicator-${noteID}`);
    var footnote = document.getElementById(`footnote-${noteID}`);
    if (footnote && indicator) {
      footnote.classList.remove("highlighted-note-valid");
      indicator.classList.remove("highlighted-note-valid");
    } else {
      if (footnote) {
        footnote.classList.remove("highlighted-note-missing");
      }
      if (indicator) {
        indicator.classList.remove("highlighted-note-missing");
      }
    }
  }

  editNote(e) {
    var regex = /^(\d+)\.\s*(.*)/;

    var noteContent = e.target.textContent.match(regex)[2];
    var updateContent = prompt(
      `Update footnote: ${noteContent}\n If you'd like to remove it, delete the contents.`,
      `${noteContent}`
    );
    if (updateContent !== null) {
      let id = e.target.id.match(/\d+/)[0];
      if (updateContent.trim() !== "") {
        e.target.innerText = `${id}. ${updateContent}`;
        document
          .getElementById(`footnote-indicator-${id}`)
          .setAttribute("title", updateContent);
        document
          .getElementById(`footnote-indicator-${id}`)
          .setAttribute("data-original-title", updateContent);
      } else {
        // delete the note and indicator if they remove the content
        e.target.remove();
        document.getElementById(`footnote-indicator-${id}`).remove();
        this.cleanFootnoteNumbers();
      }
    } else return e.target.innerText;
  }
}

Quill.register("modules/footnote", Footnote, true);
