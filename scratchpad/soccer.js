const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, PageOrientation, ShadingType } = require('docx');
const fs = require('fs');

const items = [
  { name: '日焼け止め', icon: '☀️' },
  { name: 'すね当て',   icon: '🛡️' },
  { name: 'ヘアバンド', icon: '🪶' },
  { name: 'ビブス',     icon: '🎽' },
  { name: 'ボール',     icon: '⚽' },
  { name: 'タオル',     icon: '💦' },
  { name: '水筒',       icon: '🥤' },
  { name: '帽子',       icon: '🧢' },
  { name: 'クーラー',   icon: '🧊' },
  { name: '塩分チャージ', icon: '🍬' },
  { name: '帰りの靴',   icon: '👟' },
  { name: 'ユニフォーム', icon: '👕' },
  { name: '椅子',       icon: '🪑' },
  { name: '三脚',       icon: '📷' },
  { name: 'タブレット', icon: '📱' },
];

const matchOnlyStart = 11;
const alwaysCount = matchOnlyStart;
const matchCount = items.length - matchOnlyStart;

const COLOR_A = 'E3F2FD';
const COLOR_B = 'FCE4EC';
const HEADER_A = '1565C0';
const HEADER_B = 'AD1457';

const dateColWidth = 1400;
const itemColWidth = 900;
const cellMargin = { top: 80, bottom: 80, left: 60, right: 60 };
const numRows = 16;

// Row 1: item header row
const headerCells = [
  new TableCell({
    width: { size: dateColWidth, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'FFF3E0' },
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

// Row 2: section label row (between header and check rows)
const sectionRow = new TableRow({
  height: { value: 500, rule: 'atLeast' },
  children: [
    new TableCell({
      width: { size: dateColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'FFFFFF' },
      margins: cellMargin,
      children: [new Paragraph('')],
    }),
    new TableCell({
      width: { size: itemColWidth * alwaysCount, type: WidthType.DXA },
      columnSpan: alwaysCount,
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: HEADER_A },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '⭐ いつも', bold: true, size: 22, color: 'FFFFFF' })] })],
    }),
    new TableCell({
      width: { size: itemColWidth * matchCount, type: WidthType.DXA },
      columnSpan: matchCount,
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: HEADER_B },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '🏆 しあいの日だけ', bold: true, size: 22, color: 'FFFFFF' })] })],
    }),
  ],
});

// Prefilled rows: date + per-item check state (true = checked)
// 7/25 = practice; check everything in "always" EXCEPT 帽子/塩分チャージ/帰りの靴; match items all unchecked
const uncheckedOn725 = new Set(['帽子', '塩分チャージ', '帰りの靴']);
const prefilledRows = [
  {
    date: '7/25 (練習)',
    checks: items.map(it => !uncheckedOn725.has(it.name) && !(items.indexOf(it) >= matchOnlyStart)),
  },
];

const bodyRows = [];
for (let r = 0; r < numRows; r++) {
  const even = r % 2 === 0;
  const bgAlways = even ? COLOR_A : 'FFFFFF';
  const bgMatch = even ? COLOR_B : 'FFFFFF';
  const bgDate = even ? 'FFF8E1' : 'FFFFFF';
  const pre = prefilledRows[r];
  const cells = [
    new TableCell({
      width: { size: dateColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: bgDate },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: pre ? pre.date : '', size: 20, bold: !!pre, color: '5D4037' })] })],
    }),
    ...items.map((_, i) => {
      const isMatch = i >= matchOnlyStart;
      const checked = pre ? pre.checks[i] : false;
      return new TableCell({
        width: { size: itemColWidth, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, color: 'auto', fill: isMatch ? bgMatch : bgAlways },
        margins: cellMargin,
        children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: checked ? '☑' : '☐', size: 30, color: isMatch ? HEADER_B : HEADER_A })] })],
      });
    }),
  ];
  bodyRows.push(new TableRow({ children: cells, height: { value: 640, rule: 'atLeast' } }));
}

const table = new Table({
  columnWidths: [dateColWidth, ...items.map(() => itemColWidth)],
  rows: [
    new TableRow({ children: headerCells, tableHeader: true, height: { value: 860, rule: 'atLeast' } }),
    sectionRow,
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
        children: [new TextRun({ text: 'じゅんびできたら ☐ に ✔ をつけよう！', size: 20, color: '5D4037' })],
      }),
      table,
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/user/claude-skills/scratchpad/soccer_checklist.docx', buf);
  console.log('done');
});
