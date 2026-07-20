const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, PageOrientation, ShadingType } = require('docx');
const fs = require('fs');

const items = [
  { name: '日焼け止め', icon: '☀️' },
  { name: 'すね当て',   icon: '🛡️' },
  { name: 'ヘアバンド', icon: '🎀' },
  { name: 'ビブス',     icon: '🦺' },
  { name: 'ボール',     icon: '⚽' },
  { name: 'タオル',     icon: '🧻' },
  { name: '水筒',       icon: '🥤' },
  { name: '帽子',       icon: '🧢' },
  { name: 'クーラー',   icon: '🧊' },
  { name: 'ユニフォーム', icon: '👕' },
  { name: '塩分チャージ', icon: '🍬' },
  { name: '帰りの靴',   icon: '👟' },
  { name: '椅子',       icon: '🪑' },
  { name: '三脚',       icon: '📷' },
  { name: 'タブレット', icon: '📱' },
];

// Two-color print scheme
const COLOR_A = 'E3F2FD'; // light blue
const COLOR_B = 'FCE4EC'; // light pink
const HEADER_A = '1565C0'; // deep blue
const HEADER_B = 'AD1457'; // deep pink
const DATE_HEADER = 'FFF3E0';

const matchOnlyStart = 12; // items index 12..14 (椅子/三脚/タブレット) are match-day only

const dateColWidth = 1400;
const itemColWidth = 900;
const cellMargin = { top: 80, bottom: 80, left: 60, right: 60 };

// Section header row: "いつも" / "試合の日だけ"
const sectionRow = new TableRow({
  tableHeader: true,
  height: { value: 500, rule: 'atLeast' },
  children: [
    new TableCell({
      width: { size: dateColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'FFFFFF' },
      margins: cellMargin,
      children: [new Paragraph('')],
    }),
    new TableCell({
      width: { size: itemColWidth * matchOnlyStart, type: WidthType.DXA },
      columnSpan: matchOnlyStart,
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: HEADER_A },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '⭐ いつも もっていく もの', bold: true, size: 24, color: 'FFFFFF' })] })],
    }),
    new TableCell({
      width: { size: itemColWidth * (items.length - matchOnlyStart), type: WidthType.DXA },
      columnSpan: items.length - matchOnlyStart,
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: HEADER_B },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '🏆 しあいの日だけ', bold: true, size: 24, color: 'FFFFFF' })] })],
    }),
  ],
});

// Item header row
const headerCells = [
  new TableCell({
    width: { size: dateColWidth, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, color: 'auto', fill: DATE_HEADER },
    margins: cellMargin,
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '📅 ひづけ', bold: true, size: 22, color: '5D4037' })] })],
  }),
  ...items.map((it, i) => {
    const isMatch = i >= matchOnlyStart;
    return new TableCell({
      width: { size: itemColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: isMatch ? 'F8BBD0' : 'BBDEFB' },
      margins: cellMargin,
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.icon, size: 32 })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.name, bold: true, size: 18, color: isMatch ? HEADER_B : HEADER_A })] }),
      ],
    });
  }),
];

const numRows = 16;
const bodyRows = [];
for (let r = 0; r < numRows; r++) {
  const even = r % 2 === 0;
  const rowFillCommon = even ? COLOR_A : 'FFFFFF';
  const rowFillMatch = even ? COLOR_B : 'FFFFFF';
  const dateFill = even ? 'FFF8E1' : 'FFFFFF';
  const cells = [
    new TableCell({
      width: { size: dateColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: dateFill },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '', size: 22 })] })],
    }),
    ...items.map((_, i) => {
      const isMatch = i >= matchOnlyStart;
      return new TableCell({
        width: { size: itemColWidth, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, color: 'auto', fill: isMatch ? rowFillMatch : rowFillCommon },
        margins: cellMargin,
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '☐', size: 30, color: isMatch ? HEADER_B : HEADER_A })] })],
      });
    }),
  ];
  bodyRows.push(new TableRow({ children: cells, height: { value: 700, rule: 'atLeast' } }));
}

const table = new Table({
  columnWidths: [dateColWidth, ...items.map(() => itemColWidth)],
  rows: [
    sectionRow,
    new TableRow({ children: headerCells, tableHeader: true, height: { value: 900, rule: 'atLeast' } }),
    ...bodyRows,
  ],
});

const doc = new Document({
  styles: { default: { document: { run: { font: 'Yu Gothic' } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838, orientation: PageOrientation.LANDSCAPE },
        margin: { top: 500, right: 500, bottom: 500, left: 500 },
      },
    },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: '⚽ ', size: 40 }),
          new TextRun({ text: 'サッカー もちものチェック', bold: true, size: 40, color: HEADER_A }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 150 },
        children: [
          new TextRun({ text: 'じゅんびできたら ☐ に ✔ をつけよう！ ', size: 20, color: '5D4037' }),
          new TextRun({ text: '（ピンクの列は しあいの日だけ）', size: 18, color: HEADER_B, bold: true }),
        ],
      }),
      table,
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/user/claude-skills/scratchpad/soccer_checklist.docx', buf);
  console.log('done');
});
