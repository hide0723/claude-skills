// 税理士法人 福田会計 顧問契約書 別紙（契約業務内容および報酬内訳）共通フォーム
// 別紙1＝税務・決算申告業務、別紙2＝給与計算代行業務。関与先ごとに記入して使用する。
// 列構成・項目立て・小計区分は福田会計側で編集された様式に準拠。
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, PageBreak,
  WidthType, AlignmentType, BorderStyle, ShadingType, VerticalAlign,
} = require('docx');
const fs = require('fs');

const FONT = 'MS Mincho';

// 番号 / 品番・品名 / 含む / 数量 / 単価 / 金額 / 備考　（合計 = 9639 DXA）
const COL = [480, 3560, 540, 1000, 900, 1300, 1859];
const FULL = COL.reduce((a, b) => a + b, 0);

const B = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const CELL_BORDERS = { top: B, bottom: B, left: B, right: B };

function run(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: opts.size || 17, bold: !!opts.bold });
}

function p(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    spacing: { before: 20, after: 20, line: opts.line || 215 },
    children: Array.isArray(text) ? text : [run(text, opts)],
  });
}

function blank(before) {
  return new Paragraph({ spacing: { before: before || 0, after: 60 }, children: [run('')] });
}

function cell(children, opts = {}) {
  return new TableCell({
    width: { size: opts.width, type: WidthType.DXA },
    columnSpan: opts.span,
    borders: CELL_BORDERS,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 35, bottom: 35, left: 60, right: 60 },
    shading: opts.shade ? { type: ShadingType.CLEAR, fill: opts.shade, color: 'auto' } : undefined,
    children: (Array.isArray(children) ? children : [children]).map((c) =>
      typeof c === 'string' ? p(c, { align: opts.align, bold: opts.bold, size: opts.size }) : c
    ),
  });
}

function headerRow() {
  const h = (t, w) => cell(t, { width: w, shade: 'D9D9D9', align: AlignmentType.CENTER, bold: true });
  return new TableRow({
    tableHeader: true,
    children: [h('', COL[0]), h('品　番　・　品　名', COL[1]), h('含む', COL[2]),
      h('数量', COL[3]), h('単価', COL[4]), h('金額（税抜）', COL[5]), h('備考', COL[6])],
  });
}

// 明細行。金額欄は記入用に空欄とする。
function itemRow(no, name, qty, unit, note, sub) {
  const nameKids = [p(name)];
  if (sub) sub.forEach((s) => nameKids.push(p(s, { size: 15 })));
  return new TableRow({
    children: [
      cell(no, { width: COL[0], align: AlignmentType.CENTER }),
      cell(nameKids, { width: COL[1] }),
      cell(no ? '☐' : '', { width: COL[2], align: AlignmentType.CENTER }),
      cell(qty, { width: COL[3], align: AlignmentType.CENTER, size: 16 }),
      cell(unit, { width: COL[4], align: AlignmentType.RIGHT, size: 16 }),
      cell('', { width: COL[5] }),
      cell(note || '', { width: COL[6], size: 16 }),
    ],
  });
}

// 区分ごとの小計行。単位は区分に応じて月額／年額または年額のみ。
function subtotalRow(label, unit, unitPrice) {
  return new TableRow({
    children: [
      cell('', { width: COL[0], shade: 'F2F2F2' }),
      cell(label, { width: COL[1], shade: 'F2F2F2', bold: true }),
      cell('', { width: COL[2], shade: 'F2F2F2' }),
      cell(unit || '月額／年額', { width: COL[3], shade: 'F2F2F2', align: AlignmentType.CENTER, size: 15 }),
      cell(unitPrice || '', { width: COL[4], shade: 'F2F2F2', align: AlignmentType.CENTER, size: 15 }),
      cell('', { width: COL[5], shade: 'F2F2F2' }),
      cell('', { width: COL[6], shade: 'F2F2F2' }),
    ],
  });
}

// 表末の合計行（ラベルを金額欄の直前まで結合）
function totalRow(label, opts = {}) {
  return new TableRow({
    children: [
      cell(label, {
        width: COL[0] + COL[1] + COL[2] + COL[3] + COL[4], span: 5,
        align: AlignmentType.RIGHT, bold: opts.bold, shade: opts.shade || 'F2F2F2',
      }),
      cell('￥', { width: COL[5], bold: opts.bold, shade: opts.shade || 'F2F2F2' }),
      cell('', { width: COL[6], shade: opts.shade || 'F2F2F2' }),
    ],
  });
}

function totalBlock() {
  return [
    totalRow('小　計（税抜）　　'),
    totalRow('消費税（10％）　　'),
    totalRow('合　計（税込）　　', { bold: true, shade: 'E6E6E6' }),
  ];
}

// 各別紙の前付（表題・甲乙・原契約・前文）
function frontMatter(title, subtitle) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 40 },
      children: [run(title, { bold: true, size: 26 })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 140 },
      children: [run(subtitle, { bold: true, size: 20 })],
    }),
    p('委任者（甲）　　　　　　　　　　　　　　　　　　　　　　　　様', { size: 18 }),
    p('受任者（乙）　税理士法人　福田会計', { size: 18 }),
    p('原契約　　　　　　　年　　　月　　　日付　顧問契約書', { size: 18 }),
    blank(),
    p('本別紙は、甲乙間の顧問契約書（以下「本契約」という。）の一部を構成する。本契約に基づき乙が受任する業務及び報酬は、下表のとおりとする。「含む」欄に☑を付した業務が本契約に含まれる業務であり、☑を付していない業務は本契約に含まれない。', { size: 17 }),
    blank(80),
  ];
}

// ========================= 別紙1　税務・決算申告業務 =========================
const rows1 = [headerRow()];

// ----- 税務業務 -----
rows1.push(itemRow('1', '基本月額報酬', '12　ヶ月', '10,000'));

rows1.push(itemRow('2', '記帳代行報酬：', '12　ケ月', '5,000', '',
  ['会計ソフトの入力処理をご依頼の場合']));

rows1.push(itemRow('', 'なお、年仕訳数1,201件～＠50にて別途請求', '', '', ''));

rows1.push(itemRow('3', '資料預り、打合せ方法：', '　　　ヶ月', '5,000', '来所／オンライン／訪問',
  ['訪問ありの場合は＠5,000', '来所・オンラインはゼロ']));

rows1.push(itemRow('4', '月次経理処理頻度：', '　　　ケ月', '', '年　　　回',
  ['年4回　＠5,000×12か月、年6回　＠10,000×12か月、年6回超　＠15,000×12か月']));

rows1.push(itemRow('5', '事業規模：', '12　ヶ月', '', '　　　　万円想定',
  ['年商　　　　万円（年商5,000万円未満は＠0円、5,000万円超から5,000万円ごとに＠5,000）',
   '※5億円超は一律（+50,000円）']));

rows1.push(itemRow('6', '報酬支払：口座振替以外＠3,000　※請求書発行を行う場合', '　　　ヶ月', '3,000', '振替口座'));

rows1.push(subtotalRow('税務業務　小計'));

// ----- 決算・申告業務 -----
rows1.push(itemRow('7', '決算報酬：法人 ＠120,000　個人＆NPO ＠50,000', '1　事業年度', '', '法人／個人・NPO'));
rows1.push(itemRow('8', '消費税申告：＠50,000', '1　事業年度', '50,000'));
rows1.push(itemRow('9', '申告書控印刷', '　　　部', '30,000'));
rows1.push(itemRow('10', '銀行用申告書印刷', '　　　部', '5,000'));
rows1.push(itemRow('11', '総勘定元帳印刷', '　　　部', '30,000'));
rows1.push(itemRow('12', 'NXPRO使用　決算手数料：年間△50,000（ミロクのクラウドアプリを使用している場合）',
  '　　事業年度', '△50,000'));
rows1.push(itemRow('13', '出精値引き', '　　事業年度', '△'));
rows1.push(itemRow('14', '税理士法第33条の2第1項に規定する書面添付', '1　事業年度', '30,000'));

rows1.push(subtotalRow('決算・申告業務　小計', '年額のみ', '－'));

rows1.push(...totalBlock());

// ========================= 別紙2　給与計算代行業務 =========================
const rows2 = [headerRow()];

rows2.push(itemRow('1', '給与計算：基本月額報酬', '12　ヶ月', '4,000'));
rows2.push(itemRow('2', '給与計算：人数×月＠800×12ヶ月（年＠9,600）', '　　　人', '9,600'));
rows2.push(itemRow('3', '給与計算　勤怠の集計有：人数×月＠400×12ヶ月（年＠4,800）※1', '　　　人', '4,800'));
rows2.push(itemRow('4', '給与明細印刷有：人数×月＠200×12ヶ月（年＠2,400）', '　　　人', '2,400'));
rows2.push(itemRow('5', '納税代行手続き（ダイレクト納付）－住民税＠1,000', '12　ヶ月', '1,000'));
rows2.push(itemRow('6', '労働保険・社会保険手続き一式：＠4,000', '12　ヶ月', '4,000'));
rows2.push(itemRow('7', '労働保険の算定基礎届の作成：＠45,000', '1　回', '45,000'));

rows2.push(subtotalRow('給与計算代行　小計'));

rows2.push(...totalBlock());

const mkTable = (rows) => new Table({
  columnWidths: COL,
  width: { size: FULL, type: WidthType.DXA },
  rows,
});

const NOTE_COMMON = [
  '　「含む」欄に☑を付していない業務は、本契約に含まれない。甲が当該業務を希望する場合は、その都度、事前に甲乙が業務内容及び報酬額を合意のうえ実施し、上表の単価により別途請求する。',
  '　本別紙は本契約の一部を構成する。本別紙の変更は、甲乙双方の書面又は電磁的方法による合意によらなければ、その効力を生じない。',
  '　契約期間の中途において消費税率が改正された場合、消費税額は改正後の税率による。',
];

function notes(extra) {
  const list = extra ? [...extra, ...NOTE_COMMON] : NOTE_COMMON;
  return [
    new Paragraph({ spacing: { before: 140, after: 40 }, children: [run('【注記】', { bold: true, size: 18 })] }),
    ...list.map((t, i) => p(`※${i + 1}${t}`, { size: 16 })),
    blank(160),
    p('以　上', { align: AlignmentType.RIGHT, size: 18 }),
  ];
}

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 18 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 900, bottom: 850, left: 1134, right: 1134 },
      },
    },
    children: [
      ...frontMatter('別　紙　１　　契約業務内容および報酬内訳', '（税務顧問業務・決算申告業務）'),
      mkTable(rows1),
      ...notes(),

      new Paragraph({ children: [new PageBreak()] }),

      ...frontMatter('別　紙　２　　契約業務内容および報酬内訳', '（給与計算代行業務）'),
      mkTable(rows2),
      ...notes(['　出勤簿及びタイムカードの預かり（確認業務含む）の場合は、勤怠の管理有となります。']),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2] || 'form.docx', buf);
  console.log('written');
});
