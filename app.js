const fileInput = document.getElementById("positions");
const reset = document.querySelector(".reset");
let tableCount = 0;

function handleFileSelect(event) {
  processFile(event.target.files[0])
}

function handleFileLoad(event) {
  console.log(event);
  document.getElementById('QB').textContent = event.target.result;
}

function convertCSV(textData) {
  let arrayOne = textData.split("\r\n");
  let header = arrayOne[0].split(",");
  let noOfRow = arrayOne.length;
  let noOfCol = header.length;
  let jsonData = []  
  let i = 0;
  let j = 0;

  // for loop (rows)
  for (i = 1; i < noOfRow - 1; i++) {
      let obj = {};
      let myNewLine = arrayOne[i].split(",");
      // nested for loop (columns)
      for (j = 0; j < noOfCol; j++) {
          obj[header[j]] = myNewLine[j];
      };
      // generate JSON
      jsonData.push(obj);
  };
  return jsonData
}

function readFileAsync(file) {
  return new Promise((resolve, reject) => {
    let reader = new FileReader();

    reader.onload = () => {
      resolve(reader.result);
    }

    reader.onerror = reject;

    reader.readAsText(file);
  })
}

const _tr_ = document.createElement('tr'),
  _th_ = document.createElement('th'),
  _td_ = document.createElement('td');

// Builds the HTML Table out of myList json data from Ivy restful service.
function buildHtmlTable(tierList, tableID) {
  const table = document.createElement("table"),
    columns = addAllColumnHeaders(tierList, table);
  table.id = tableID
  table.classList.add("positionTable")
  table.setAttribute("oncontextmenu", "return false;")
  for (let i = 0, maxi = tierList.length; i < maxi; ++i) {
    const tr = _tr_.cloneNode(false);
    tr.addEventListener("click", colorRow);
    tr.addEventListener("contextmenu", resetRow);
    for (var j = 0, maxj = columns.length; j < maxj; ++j) {
      var td = _td_.cloneNode(false);
      var cellValue = tierList[i][columns[j]];
      td.appendChild(document.createTextNode(tierList[i][columns[j]] || ''));
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
  sortTable(table)
  return table;
}

// Adds a header row to the table and returns the set of columns.
// Need to do union of keys from all records as some records may not contain
// all records
function addAllColumnHeaders(tierList, table) {
  var columnSet = [],
    tr = _tr_.cloneNode(false);
  for (var i = 0, l = tierList.length; i < l; i++) {
    for (var key in tierList[i]) {
      if (tierList[i].hasOwnProperty(key) && columnSet.indexOf(key) === -1) {
        columnSet.push(key);
        var th = _th_.cloneNode(false);
        th.appendChild(document.createTextNode(key));
        tr.appendChild(th);
      }
    }
  }
  table.appendChild(tr);
  return columnSet;
}

async function processFile(file) {
  try {
    const tableID = file.name.slice(0,2);
    let textData = await readFileAsync(file);
    let jsonData = convertCSV(textData);
    let tableGroup;
    const newPosition = buildElements(tableID, jsonData);
    if (tableCount === 0 ) {
      const collapse = document.createElement("button");
      collapse.textContent = "Collapse";
      collapse.classList.add("collapsible");
      collapse.addEventListener("click", collapseDiv);
      document.getElementById("tierLists").appendChild(collapse)
      tableGroup = document.createElement("div");
      tableGroup.classList.add("tableGroup");
      document.getElementById("tierLists").appendChild(tableGroup);
    } else {
      const tableGroups = document.querySelectorAll(".tableGroup")
      tableGroup = [].slice.call(tableGroups).pop()
    }
    tableGroup.appendChild(newPosition);
    tableCount += 1
    if (tableCount === 2) tableCount = 0;
  } catch (err) {
    console.log(err)
  }
}

function buildElements(tableID, jsonData) {
  const newPosition = document.createElement("div");
  newPosition.classList.add("positionDiv");
  const title = document.createElement("h1");
  title.textContent = tableID;
  newPosition.appendChild(title);
  newPosition.appendChild(buildHtmlTable(jsonData, tableID));
  return newPosition
}

function collapseDiv() {
  if (!(this.nextElementSibling.style.display === "none")) {
    this.nextElementSibling.style.display = "none";
  } else {
    this.nextElementSibling.style.display = "";
  }
}

function colorRow() {
  if (this.id === "") {
    this.id = "red";
  } else if (this.id === "red") {
    this.classList.add("hidden");
  }
}

function resetRow() {
  this.id = "";
  this.classList.remove("hidden");
}

function sortTable(table) {
  var rows, switching, i, x, y, shouldSwitch;
  switching = true;
  /* Make a loop that will continue until
  no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /* Loop through all table rows (except the
    first, which contains table headers): */
    for (i = 1; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
      one from current row and one from the next: */
      x = rows[i].getElementsByTagName("TD")[4];
      y = rows[i + 1].getElementsByTagName("TD")[4];
      // Check if the two rows should switch place:
      if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
        // If so, mark as a switch and break the loop:
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}

reset.addEventListener("click", () => {
  const hidden = document.querySelectorAll(".hidden");
  hidden.forEach(element => {
    element.classList.remove("hidden");
  })
})

fileInput.addEventListener('change', handleFileSelect);