var Module = Quill.import("core/module");
var BlockEmbed = Quill.import("blots/block/embed");
var Parchment = Quill.import("parchment");

function identifier() {
  var id = Math.random().toString(36).slice(2, 6);
  return id;
}
const footnoteAreaID = identifier();

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
    node.setAttribute("data-html", "true");
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
    node.id = `footnote-area-${footnoteAreaID}`;
    node.classList.add("footnote-area"); // edit styling in CSS
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

    this.editorArea = this.quill.container;

    const observer = new MutationObserver(this.handleDeletion.bind(this));
    observer.observe(this.quill.root, { childList: true, subtree: true });
  }

  countFootnotes() {
    var footnoteCounter;
    if (this.editorArea.querySelector(".footnote-indicator")) {
      var indicators = this.editorArea.querySelectorAll(".footnote-indicator");
      return (footnoteCounter = indicators.length + 1);
    } else return (footnoteCounter = 1); // if no indicators
  }

  async insertFootnote() {
    console.log("inserting footnote");
    var footnoteNumber = this.countFootnotes();
    const range = this.quill.getSelection();
    const index = range ? range.index : this.quill.getLength();
    if (!this.editorArea.querySelector(`.footnote-area`)) {
      // create the footnote area inside the ql-editor if it doesn't exist
      console.log("adding footnote area");
      this.quill.insertEmbed(this.quill.getLength(), "footnote-area", "");
    }
    this.footnoteArea = this.editorArea.querySelector(`.footnote-area`);

    const footnoteContent = await addModal("");
    if (footnoteContent) {
      // insert a superscripted indicator in the text editor, space after is intended
      this.quill.insertEmbed(index, "footnote-indicator", `${footnoteNumber} `);

      const cursorPosition = index + 1;
      this.quill.setSelection(cursorPosition);

      const range = this.quill.getSelection();
      range.length = 0; // Remove the selection
      range.index = cursorPosition; // Set the index to the cursor position
      this.quill.setSelection(range);

      // create the content of the footnote in the footnote area
      const footnoteElement = document.createElement("article");
      footnoteElement.classList = "footnote";
      footnoteElement.id = `footnote-${footnoteNumber}`;
      footnoteElement.innerHTML = `<span class="footnote-number">${footnoteNumber}. </span>${footnoteContent}`;

      // insert it in the correct location in the list
      var nextFootnoteIndicator = this.findNextIndicator(footnoteNumber);
      if (nextFootnoteIndicator) {
        const footnoteID = nextFootnoteIndicator.id.match(/\d+/)[0];
        const nextFootNoteItem = this.editorArea.querySelector(
          `#footnote-${footnoteID}`
        );
        this.footnoteArea.insertBefore(footnoteElement, nextFootNoteItem);
      } else this.footnoteArea.appendChild(footnoteElement);

      // add tooltip content
      var indicatorElement = this.editorArea.querySelector(
        `#footnote-indicator-${footnoteNumber}`
      );
      indicatorElement.setAttribute(
        "data-original-title",
        footnoteElement.innerHTML.trim()
      );
      // add highlight and edit listeners
      footnoteElement.addEventListener("mouseenter", this.addHighlight);
      footnoteElement.addEventListener("mouseleave", this.removeHighlight);
      footnoteElement.addEventListener("click", this.editNote);

      this.cleanFootnoteNumbers();
      footnoteNumber++;
      $('[data-toggle="tooltip"]').tooltip(); //enable tooltips
    }
  }

  removeFootnote(node) {
    let footnoteID = node.id.match(/\d+/)[0];
    let footnoteElement = this.editorArea.querySelector(
      `#footnote-${footnoteID}`
    );
    if (footnoteElement) {
      footnoteElement.remove();
      return true;
    } else return true;
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
    for (var mutation of mutationsList) {
      if (mutation.type === "childList" && mutation.removedNodes.length > 0) {
        let node = mutation.removedNodes[0];

        if (
          (node.classList && node.classList.contains("footnote")) ||
          (node.classList && node.classList.contains("footnote-indicator")) ||
          this.hasIndicatorChildren(node) == true
        ) {
          return this.removeFootnote(node);
        }
      }
      if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
        for (const addedNode of mutation.addedNodes) {
          if (
            addedNode.classList &&
            addedNode.classList.contains("footnote-area")
          ) {
            // add highlight and edit listeners to existing notes
            if (this.editorArea.querySelector(`.footnote-area`)) {
              this.editorArea
                .querySelector(`.footnote-area`)
                .querySelectorAll(".footnote")
                .forEach((footnote) => {
                  footnote.addEventListener("mouseenter", this.addHighlight);
                  footnote.addEventListener("mouseleave", this.removeHighlight);
                  footnote.addEventListener("click", this.editNote);
                });
            }
          }
        }
      }
    }
  }

  handleDeletion(mutationsList) {
    let hasFinished = this.processMutations(mutationsList);
    if (hasFinished) {
      return this.cleanFootnoteNumbers();
    }
  }

  cleanFootnoteNumbers() {
    var footnotes = this.editorArea.querySelectorAll("article.footnote");
    var footnoteIndicators = this.editorArea.querySelectorAll(
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
          var footnoteNumber = footnote.querySelector(".footnote-number");
          footnoteNumber.textContent = `${expectedNumber}. `;
          footnote.id = `footnote-${expectedNumber}`;
        }

        // update the indicator if the element is still there
        if (footnoteIndicator) {
          footnoteIndicator.id = `footnote-indicator-${expectedNumber}`;
          footnoteIndicator.textContent = `${expectedNumber} `;
          footnoteIndicator.setAttribute(
            "data-original-title",
            footnote.innerHTML.trim()
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
    var newIndicator = this.editorArea.querySelector(
      `#footnote-indicator-${footnoteNumber}`
    );
    // if it's the last indicator in the editor, return null
    var allIndicators = this.editorArea.querySelectorAll(".footnote-indicator");
    if (newIndicator == allIndicators[allIndicators.length - 1]) {
      return null;
    }

    var index = Array.from(allIndicators).indexOf(newIndicator);
    return allIndicators[index + 1];
  }

  addHighlight(e) {
    var footnoteArea = e.target.parentElement;
    var editorArea = footnoteArea.parentElement;

    var noteID = e.target.id.match(/\d+/)[0];
    var indicator = editorArea.querySelector(`#footnote-indicator-${noteID}`);
    var footnote = footnoteArea.querySelector(`#footnote-${noteID}`);
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
    var footnoteArea = e.target.parentElement;
    var editorArea = footnoteArea.parentElement;

    var noteID = e.target.id.match(/\d+/)[0];
    var indicator = editorArea.querySelector(`#footnote-indicator-${noteID}`);
    var footnote = footnoteArea.querySelector(`#footnote-${noteID}`);
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

  async editNote(e) {
    var selectedFootnote = e.target.closest(".footnote");
    var footnoteArea = selectedFootnote.parentElement;
    var editorArea = footnoteArea.parentElement;
    var noteContent = selectedFootnote.innerHTML.replace(
      /<span class="footnote-number">.*<\/span>\s*/,
      ""
    );
    var updateContent = await addModal(noteContent);

    var regex = /<p[^>]*>/i;
    let id = selectedFootnote.id.match(/\d+/)[0];
    if (updateContent !== null) {
      if (updateContent == "delete") {
        selectedFootnote.remove();
        editorArea.querySelector(`#footnote-indicator-${id}`).remove();
      } else {
        selectedFootnote.innerHTML = updateContent
          .replace(regex, `<span class="footnote-number">${id}. </span>$&`)
          .trim();
        editorArea
          .querySelector(`#footnote-indicator-${id}`)
          .setAttribute(
            "data-original-title",
            selectedFootnote.innerHTML.trim()
          );
      }
    } else return selectedFootnote.innerHTML;
  }
}

Quill.register("modules/footnote", Footnote, true);
