const Module = Quill.import("core/module");
const BlockEmbed = Quill.import("blots/block/embed");
const Parchment = Quill.import("parchment");

// create custom blot for superscript footnote indicator
class FootnoteIndicator extends BlockEmbed {
  static create(value) {
    const number = value.trim();
    const node = super.create(value);
    node.classList.add("footnote-indicator");
    node.id = `footnote-indicator-${number}`;
    node.textContent = value;
    node.setAttribute("data-toggle", "tooltip");
    node.setAttribute("data-placement", "top");
    node.setAttribute("data-html", "true");
    return node;
  }
  static value(node) {
    return node.textContent;
  }
}
FootnoteIndicator.blotName = "footnote-indicator";
FootnoteIndicator.scope = Parchment.Scope.INLINE;
FootnoteIndicator.tagName = "sup";

class FootnoteArea extends BlockEmbed {
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
      // insert a superscripted indicator in the text editor, space after is intended
      this.quill.insertEmbed(index, "footnote-indicator", `${footnoteNumber} `);

      this.quill.setSelection(index + 1);

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
      indicatorElement.setAttribute("title", footnoteElement.textContent);
      // add highlight and edit listeners
      footnoteElement.addEventListener("mouseenter", this.addHighlight);
      footnoteElement.addEventListener("mouseleave", this.removeHighlight);
      footnoteElement.addEventListener("click", this.editNote);

      indicatorElement.addEventListener("mouseenter", this.addHighlight);
      indicatorElement.addEventListener("mouseleave", this.removeHighlight);

      this.cleanFootnoteNumbers();
      footnoteNumber++;
      $('[data-toggle="tooltip"]').tooltip();
    }
  }

  deleteFootnote(mutationsList) {
    for (const mutation of mutationsList) {
      if (mutation.type === "childList" && mutation.removedNodes.length > 0) {
        // Check if any removed nodes are footnotes or indicators
        let node = mutation.removedNodes[0];
        if (
          (node.classList && node.classList.contains("footnote")) ||
          (node.classList && node.classList.contains("footnote-indicator"))
        ) {
          let footnoteID = node.id.match(/\d+/)[0];

          // Delete the corresponding footnote/indicator
          let footnoteElement = document.getElementById(
            `footnote-${footnoteID}`
          );
          let indicatorElement = document.getElementById(
            `footnote-indicator-${footnoteID}`
          );
          if (footnoteElement) {
            footnoteElement.remove();
          }
          if (indicatorElement) {
            indicatorElement.remove();
          }

          // ensure footnotes are in correct ascending order
          this.cleanFootnoteNumbers();
        }
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
          footnoteIndicator.textContent = `${expectedNumber} `;
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
    var newIndicatorIndex = Array.from(parentElement.children).indexOf(
      newIndicator
    );
    var siblingElement = parentElement.children[newIndicatorIndex + 1];
    var cousinElement = parentSibling.firstElementChild;
    // check parent first
    while (siblingElement) {
      if (
        siblingElement !== newIndicator &&
        siblingElement.tagName.toLowerCase() === "sup" &&
        siblingElement.classList.contains("footnote-indicator")
      ) {
        return siblingElement;
      }
      siblingElement = siblingElement.nextElementSibling;
    }
    if (!siblingElement) {
      console.log("no siblings");
      console.log(cousinElement);
      // if not in parent, check parent sibling
      if (!cousinElement) {
        cousinElement = parentSibling.nextElementSibling.firstElementChild;
      }
      while (cousinElement) {
        if (
          cousinElement !== newIndicator &&
          cousinElement.tagName.toLowerCase() === "sup" &&
          cousinElement.classList.contains("footnote-indicator")
        ) {
          return cousinElement;
        }
        if (cousinElement.nextElementSibling) {
          console.log("another to check");
          cousinElement = cousinElement.nextElementSibling;
        }
        // and then parent sibling sibling
        else
          cousinElement =
            cousinElement.parentElement.parentSibling.firstElementChild;
        console.log(cousinElement);
      }
    }
    return null;
  }

  addHighlight(e) {
    var noteID = e.target.id.match(/\d+/)[0];
    var indicator = document.getElementById(`footnote-indicator-${noteID}`);
    var footnote = document.getElementById(`footnote-${noteID}`);
    // add a highlight class to the elements - ensure this is in your CSS file
    footnote.classList.add("highlighted-note");
    indicator.classList.add("highlighted-note");
  }
  removeHighlight(e) {
    var noteID = e.target.id.match(/\d+/)[0];
    var indicator = document.getElementById(`footnote-indicator-${noteID}`);
    var footnote = document.getElementById(`footnote-${noteID}`);
    footnote.classList.remove("highlighted-note");
    indicator.classList.remove("highlighted-note");
  }

  editNote(e) {
    var updateContent = prompt(
      `Update footnote: ${e.target.innerText}\n If you'd like to remove it, delete the contents.`,
      `${e.target.innerText}`
    );
    if (updateContent !== null) {
      if (updateContent.trim() !== "") {
        e.target.innerText = updateContent;
      } else {
        let id = e.target.id.match(/\d+/)[0];
        e.target.remove();
        document.getElementById(`footnote-indicator-${id}`).remove();
      }
    } else return e.target.innerText;
  }
}

Quill.register("modules/footnote", Footnote, true);
