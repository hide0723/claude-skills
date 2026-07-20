const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, PageOrientation, ShadingType } = require('docx');
const fs = require('fs');

const alwaysItems = [
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
];
const matchItems = [
  { name: '椅子',       icon: '🪑' },
  { name: '三脚',       icon: '📷' },
  { name: 'タブレット', icon: '📱' },
];

const COLOR_A = 'E3F2FD';
const COLOR_B = 'FCE4EC';
const HEADER_A = '1565C0';
const HEADER_B = 'AD1457';

const dateColWidth = 1400;
const itemColWidth = 900;
const cellMargin = { top: 80, bottom: 80, left: 60, right: 60 };
const numRows = 16;

function buildTable(items, palette) {
  const { rowFill, headerFill, headerColor, dateHeaderFill } = palette;

  const headerCells = [
    new TableCell({
      width: { size: dateColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: dateHeaderFill },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '📅 ひづけ', bold: true, size: 22, color: '5D4037' })] })],
    }),
    ...items.map(it => new TableCell({
      width: { size: itemColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: headerFill },
      margins: cellMargin,
      children: [
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.icon, size: 32 })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.name, bold: true, size: 18, color: headerColor })] })
      ],
    })),
  ];

  const bodyRows = [];
  for (let r = 0; r < numRows; r++) {
    const even = r % 2 === 0;
    const bg = even ? rowFill : 'FFFFFF';
    const dateBg = even ? 'FFF8E1' : 'FFFFFF';
    const cells = [
      new TableCell({
        width: { size: dateColWidth, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, color: 'auto', fill: dateBg },
        margins: cellMargin,
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '', size: 22 })] })],
      }),
      ...items.map(() => new TableCell({
        width: { size: itemColWidth, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, color: 'auto', fill: bg },
        margins: cellMargin,
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '☐', size: 30, color: headerColor })] })],
      })),
    ];
    bodyRows.push(new TableRow({ children: cells, height: { value: 640, rule: 'atLeast' } }));
  }

  return new Table({
    columnWidths: [dateColWidth, ...items.map(() => itemColWidth)],
    rows: [new TableRow({ children: headerCells, tableHeader: true, height: { value: 860, rule: 'atLeast' } }), ...bodyRows],
  });
}

const alwaysTable = buildTable(alwaysItems, {
  rowFill: COLOR_A, headerFill: 'BBDEFB', headerColor: HEADER_A, dateHeaderFill: 'FFF3E0',
});
const matchTable = buildTable(matchItems, {
  rowFill: COLOR_B, headerFill: 'F8BBD0', headerColor: HEADER_B, dateHeaderFill: 'FFF3E0',
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
        children: [new TextRun({ text: 'じゅんびできたら ☐ に ✔ をつけよう！', size: 20, color: '5D4037' })],
      }),

      new Paragraph({
        spacing: { before: 100, after: 100 },
        children: [new TextRun({ text: '⭐ いつも もっていく もの', bold: true, size: 24, color: HEADER_A })],
      }),
      alwaysTable,

      new Paragraph({
        spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: '🏆 しあいの日だけ もっていく もの', bold: true, size: 24, color: HEADER_B })],
      }),
      matchTable,
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/user/claude-skills/scratchpad/soccer_checklist.docx', buf);
  console.log('done');
});
