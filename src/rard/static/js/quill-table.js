// this code is based on the code from the quillJS dev branch
// it has been stripped back and adapted for this use case as there is no official release yet
var Module = Quill.import("core/module");

var BlockEmbed = Quill.import("blots/block/embed");
var Block = Quill.import("blots/block");
var Container = Quill.import("blots/container");
var Delta = Quill.import("delta");

function editContents(e) {
  var updateContent = prompt(
    `Update cell content or set blank.`,
    `${e.target.innerText}`
  );
  return (e.target.innerText = updateContent);
}

var currentCell;
function updateCurrentCell(e) {
  currentCell = e.target;
}

class TableCell extends BlockEmbed {
  static blotName = "table-cell";
  static tagName = "TD";

  static create(value) {
    const node = super.create();
    if (value) {
      node.setAttribute("data-row", value);
    } else {
      node.setAttribute("data-row", tableId("cell"));
    }
    node.classList.add("ql-table");
    node.addEventListener("dblclick", editContents);
    node.addEventListener("click", updateCurrentCell);
    return node;
  }

  static formats(domNode) {
    if (domNode.hasAttribute("data-row")) {
      return domNode.getAttribute("data-row");
    }
    return undefined;
  }

  format(name, value) {
    if (name === TableCell.blotName && value) {
      this.domNode.setAttribute("data-row", value);
    } else {
      super.format(name, value);
    }
  }

  table() {
    let cur = this.parent;
    while (cur != null && cur.statics.blotName !== "table-container") {
      cur = cur.parent;
    }
    return cur;
  }
}

class TableRow extends Container {
  static blotName = "table-row";
  static tagName = "TR";
  static create(value) {
    var node = super.create(value);
    node.classList.add("ql-table");
    if (value) {
      node.id = value;
    } else {
      node.id = tableId("row");
    }
    return node;
  }
  optimize(...args) {
    super.optimize(...args);
    this.children.forEach((child) => {
      if (child.next == null) return;
      const childFormats = child.formats();
      const nextFormats = child.next.formats();
      if (childFormats.table !== nextFormats.table) {
        const next = this.splitAfter(child);
        if (next) {
          next.optimize();
        }
        // We might be able to merge with prev now
        if (this.prev) {
          this.prev.optimize();
        }
      }
    });
  }
}

class TableContainer extends BlockEmbed {
  static blotName = "table-container";
  static tagName = "TABLE";
  static create(value) {
    var node = super.create(value);
    node.classList.add("ql-table");
    node.id = value;
    return node;
  }

  balanceCells() {
    const rows = this.querySelectorAll("tr");
    const maxColumns = rows.reduce((max, row) => {
      return Math.max(row.children.length, max);
    }, 0);
    rows.forEach((row) => {
      new Array(maxColumns - row.children.length).fill(0).forEach(() => {
        let value;
        if (row.children.head != null) {
          value = TableCell.formats(row.children.head.domNode);
        }
        const blot = TableCell.create(value);
        row.appendChild(blot);
        blot.optimize(); // Add break blot
      });
    });
  }

  deleteColumn(index) {
    if (
      this == null ||
      this.domNode.firstElementChild.firstElementChild == null
    )
      return;
    Array.from(this.domNode.firstElementChild.children).forEach((row) => {
      const cell = row.children[index];
      if (cell != null) {
        cell.remove();
      }
    });
  }

  insertColumn() {
    if (
      this == null ||
      this.domNode.firstElementChild.firstElementChild == null
    )
      return;
    Array.from(this.domNode.firstElementChild.children).forEach((row) => {
      const value = TableCell.formats(row.firstElementChild);
      const cell = TableCell.create(value);
      // always adds column on the right
      row.appendChild(cell);
    });
  }

  insertRow() {
    if (
      this == null ||
      this.domNode.firstElementChild.firstElementChild == null
    )
      return;
    const id = tableId("row");
    var row = TableRow.create(id);
    Array.from(
      this.domNode.firstElementChild.firstElementChild.children
    ).forEach(() => {
      var cell = TableCell.create();
      row.appendChild(cell);
    });
    // always adds a row at the bottom
    this.domNode.appendChild(row);
  }
}

TableRow.allowedChildren = [TableCell];
TableCell.requiredContainer = TableRow;

function tableId(elem) {
  const id = Math.random().toString(36).slice(2, 6);
  return `${elem}-${id}`;
}

class Table extends Module {
  static register() {
    Quill.register(TableCell, true);
    Quill.register(TableRow, true);
    Quill.register(TableContainer, true);
  }

  constructor(quill, options) {
    super(quill, options);
    this.quill = quill;
    this.toolbar = quill.getModule("toolbar");
    this.toolbar.addHandler("table", this.insertTable.bind(this));
    this.toolbar.addHandler("edit_table", (value) => {
      if (value == "add_row") {
        this.insertRow();
      } else if (value == "add_column") {
        this.insertColumn();
      } else if (value == "delete_row") {
        this.deleteRow();
      } else if (value == "delete_column") {
        this.deleteColumn();
      }
    });
    this.listenBalanceCells();
  }

  deleteColumn() {
    const [table, , row, cell] = this.getTable();
    if (cell == null) return;
    const column = Array.from(row.children).indexOf(cell);
    table.deleteColumn(column);
    this.quill.update(Quill.sources.USER);
  }

  deleteRow() {
    const [, , row] = this.getTable();
    if (row == null || row.nodeName !== "TR") return;
    row.remove();
    this.quill.update(Quill.sources.USER);
  }

  getClosestTable(tables, index) {
    // get table closest to the cursor
    let closestTable;
    let minDistance = Infinity;
    Array.from(tables).forEach((t) => {
      var tableIndex = this.quill.getIndex(t);
      var distance = Math.abs(index - tableIndex);
      if (distance < minDistance) {
        closestTable = t;
        minDistance = distance;
      }
    });
    return closestTable;
  }

  getTable(range = this.quill.getSelection()) {
    if (range == null) {
      return [null, null, null, null, -1];
    }
    let tables = this.quill.scroll.descendants(TableContainer);
    var table = this.getClosestTable(tables, range.index);
    if (table == null || table.domNode.nodeName !== TableContainer.tagName) {
      return [null, null, null, null, -1];
    }
    var body = table.domNode.firstElementChild;
    var cell = currentCell;
    var row = cell.parentElement;

    return [table, body, row, cell, 1];
  }

  insertColumn() {
    var range = this.quill.getSelection();
    const [table, , row, cell] = this.getTable(range);
    if (cell == null) return;
    table.insertColumn();
    this.quill.update(Quill.sources.USER);
    let shift = Array.from(row.parentElement.children).indexOf(row);
    this.quill.setSelection(
      range.index + shift,
      range.length,
      Quill.sources.SILENT
    );
  }

  insertRow() {
    const range = this.quill.getSelection();
    const [table, , row, cell] = this.getTable(range);
    if (cell == null) return;
    table.insertRow();
    this.quill.update(Quill.sources.USER);
    this.quill.setSelection(
      range.index + row.children.length,
      range.length,
      Quill.sources.SILENT
    );
  }

  insertTable() {
    var rows = 3;
    var columns = 3;
    var range = this.quill.getSelection();
    if (range == null) return;

    const tableContainerId = tableId("table");
    this.quill.insertEmbed(range.index, "table-container", tableContainerId);

    var tableElem = document.getElementById(tableContainerId);

    if (tableElem) {
      var tbody = tableElem.appendChild(document.createElement("tbody"));
      for (let i = 0; i < rows; i++) {
        var row = TableRow.create();

        for (let j = 0; j < columns; j++) {
          var cell = TableCell.create();
          row.appendChild(cell);
        }
        tbody.appendChild(row);
      }
    }

    this.quill.setSelection(range.index, Quill.sources.SILENT);
    this.quill.focus();
  }

  listenBalanceCells() {
    this.quill.on(Quill.events.SCROLL_OPTIMIZE, (mutations) => {
      mutations.some((mutation) => {
        if (mutation.target.tagName === "TABLE") {
          this.quill.once(Quill.events.TEXT_CHANGE, (delta, old, source) => {
            if (source !== Quill.sources.USER) return;
            this.quill.scroll.descendants(TableContainer).forEach((table) => {
              table.balanceCells();
            });
          });
          return true;
        }
        return false;
      });
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector("table")) {
    document.querySelectorAll("td.ql-table").forEach((cell) => {
      cell.addEventListener("dblclick", editContents);
      cell.addEventListener("click", updateCurrentCell);
    });
  }
});
Table.register();
Quill.register("modules/table", Table, true);
