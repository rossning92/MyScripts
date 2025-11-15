import * as mo from "movy";

export function addTable(
  /** @type {{ headers: string[]; data: string[] }} */ data,
  {
    tableWidth = 14,
    cellWidth,
    cellHeight = 0.6,
    fontSize = 0.2,
    striped = true,
    borderWidth = 0.03,
    borderColor = "#404040",
  } = {}
) {
  const columns = data.headers.length;
  const rows = data.data.length + 1;

  let columnWidths;

  if (cellWidth === undefined) {
    const maxValues = Array.from({ length: columns }, (_, columnIndex) => {
      let maxLength = String(data.headers[columnIndex] ?? "").length;
      data.data.forEach((row) => {
        const length = String(row[columnIndex] ?? "").length;
        if (length > maxLength) {
          maxLength = length;
        }
      });
      return maxLength;
    });
    const totalMax = maxValues.reduce((total, value) => total + value, 0);
    if (totalMax === 0) {
      columnWidths = Array(columns).fill(tableWidth / columns);
    } else {
      columnWidths = maxValues.map(
        (maxValue) => (maxValue / totalMax) * tableWidth
      );
      const widthSum = columnWidths.reduce((sum, width) => sum + width, 0);
      columnWidths[columnWidths.length - 1] += tableWidth - widthSum;
    }
  } else if (Array.isArray(cellWidth)) {
    columnWidths = cellWidth.slice(0, columns);
  } else {
    columnWidths = Array(columns).fill(cellWidth);
  }

  const totalTableWidth = columnWidths.reduce((sum, width) => sum + width, 0);
  const startX = -totalTableWidth / 2;
  const startY = (rows * cellHeight) / 2;

  for (let i = 0; i <= rows; i++) {
    const y = startY - i * cellHeight;
    mo.addLine(
      [
        [startX, y],
        [startX + totalTableWidth, y],
      ],
      { lineWidth: borderWidth, color: borderColor, z: 0.1 }
    ).drawLine({ t: "<0.1", ease: "power2.inOut", duration: 1 });
  }

  const renderRow = ({ cells, rowIndex }) => {
    let xCursor = startX;
    cells.forEach((text, columnIndex) => {
      const width = columnWidths[columnIndex] ?? 0;
      const x = xCursor + width / 2;
      const y = startY - rowIndex * cellHeight - cellHeight / 2;
      mo.addText(String(text), { x, y, fontSize, z: 0.1 }).fadeIn({
        t: "<0.05",
        duration: 0.5,
        ease: "linear",
      });
      xCursor += width;
    });
  };

  function addBackground({ color, rowIndex }) {
    mo.addRect({
      x: startX + totalTableWidth / 2,
      y: startY - rowIndex * cellHeight - cellHeight / 2,
      sx: totalTableWidth,
      sy: cellHeight,
      color,
    }).fadeIn({ t: "<" });
  }

  addBackground({ color: "#444444", rowIndex: 0 });
  renderRow({ cells: data.headers, rowIndex: 0 });

  data.data.forEach((row, index) => {
    const rowIndex = index + 1;
    if (striped && index % 2 === 0) {
      addBackground({ color: "#222222", rowIndex });
    }

    renderRow({ cells: row, rowIndex });
  });
}
