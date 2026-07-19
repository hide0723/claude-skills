const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, HeadingLevel, AlignmentType, PageOrientation, BorderStyle } = require('docx');
const fs = require('fs');

const items = ['日焼け止め','すね当て','ヘアバンド','ビブス','ボール','タオル','水筒','帽子','クーラーボックス','ユニフォーム','塩分チャージ','帰りの靴','椅子','三脚','タブレット'];

const dateColWidth = 1200;
const itemColWidth = 900;
const totalWidth = dateColWidth + items.length * itemColWidth;

// landscape A4 approx: portrait dims passed, engine swaps
const pageSize = { width: 11906, height: 16838 };

const headerCells = [
  new TableCell({
    width: { size: dateColWidth, type: WidthType.DXA },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '日付', bold: true })] })],
  }),
  ...items.map(item => new TableCell({
    width: { size: itemColWidth, type: WidthType.DXA },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: item, bold: true })] })],
  })),
];

const numRows = 20;
const bodyRows = [];
for (let i = 0; i < numRows; i++) {
  const cells = [
    new TableCell({ width: { size: dateColWidth, type: WidthType.DXA }, children: [new Paragraph('')] }),
    ...items.map(() => new TableCell({ width: { size: itemColWidth, type: WidthType.DXA }, children: [new Paragraph('')] })),
  ];
  bodyRows.push(new TableRow({ children: cells, height: { value: 500, rule: 'atLeast' } }));
}

const table = new Table({
  columnWidths: [dateColWidth, ...items.map(() => itemColWidth)],
  rows: [new TableRow({ children: headerCells, tableHeader: true }), ...bodyRows],
});

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: pageSize.width, height: pageSize.height, orientation: PageOrientation.LANDSCAPE },
        margin: { top: 720, right: 720, bottom: 720, left: 720 },
      },
    },
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'サッカー 持ち物チェックリスト', bold: true })] }),
      new Paragraph(''),
      table,
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/user/claude-skills/scratchpad/soccer_checklist.docx', buf);
  console.log('done');
});
