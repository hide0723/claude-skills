const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, HeadingLevel, AlignmentType, PageOrientation, ShadingType, BorderStyle } = require('docx');
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

const dateColWidth = 1400;
const itemColWidth = 900;

// HSL -> hex helpers for row gradients
function hslToRgb(h, s, l) {
  h /= 360; s /= 100; l /= 100;
  const a = s * Math.min(l, 1 - l);
  const f = n => {
    const k = (n + h * 12) % 12;
    return Math.round(255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))));
  };
  return [f(0), f(8), f(4)];
}
function hex(rgb) { return rgb.map(v => v.toString(16).padStart(2, '0')).join('').toUpperCase(); }

// Each row: horizontal gradient from startHue -> endHue (pastel)
const rowThemes = [
  [340, 20],   // pink -> peach
  [45, 90],    // yellow -> lime
  [170, 210],  // aqua -> sky
  [260, 300],  // lavender -> pink-purple
  [10, 45],    // coral -> amber
  [140, 180],  // mint -> teal
];

function rowGradientColors(themeIdx, n) {
  const [h1, h2] = rowThemes[themeIdx % rowThemes.length];
  const colors = [];
  for (let i = 0; i < n; i++) {
    const t = i / Math.max(1, n - 1);
    const h = h1 + (h2 - h1) * t;
    colors.push(hex(hslToRgb(h, 75, 88)));
  }
  return colors;
}

const cellMargin = { top: 80, bottom: 80, left: 60, right: 60 };

const headerCells = [
  new TableCell({
    width: { size: dateColWidth, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'FFE082' },
    margins: cellMargin,
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '📅 ひづけ', bold: true, size: 24, color: '5D4037' })] }),
    ],
  }),
  ...items.map(it => new TableCell({
    width: { size: itemColWidth, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, color: 'auto', fill: 'FFECB3' },
    margins: cellMargin,
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.icon, size: 36 })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: it.name, bold: true, size: 18, color: '5D4037' })] }),
    ],
  })),
];

const numRows = 16;
const bodyRows = [];
for (let r = 0; r < numRows; r++) {
  const colors = rowGradientColors(r, items.length + 1);
  const cells = [
    new TableCell({
      width: { size: dateColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: colors[0] },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '', size: 22 })] })],
    }),
    ...items.map((_, i) => new TableCell({
      width: { size: itemColWidth, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: colors[i + 1] },
      margins: cellMargin,
      children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: '☐', size: 32, color: 'FFFFFF' })] })],
    })),
  ];
  bodyRows.push(new TableRow({ children: cells, height: { value: 700, rule: 'atLeast' } }));
}

const table = new Table({
  columnWidths: [dateColWidth, ...items.map(() => itemColWidth)],
  rows: [new TableRow({ children: headerCells, tableHeader: true, height: { value: 900, rule: 'atLeast' } }), ...bodyRows],
});

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: 'Yu Gothic' } },
    },
  },
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
          new TextRun({ text: '⚽ ', size: 48 }),
          new TextRun({ text: 'サッカー もちものチェック', bold: true, size: 44, color: 'E91E63' }),
          new TextRun({ text: ' 🌈', size: 48 }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: 'じゅんびできたら ☐ に ✔ をつけよう！', size: 22, color: '7B1FA2' })],
      }),
      table,
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/home/user/claude-skills/scratchpad/soccer_checklist.docx', buf);
  console.log('done');
});
