// 税理士法人 福田会計 顧問契約書 別紙（契約業務内容および報酬内訳）
// 株式会社ブリスオーディオ版 ─ 見積書 20260725-003 の項目順・項目名にそのまま準拠
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, BorderStyle, ShadingType, VerticalAlign,
} = require('docx');
const fs = require('fs');

const FONT = 'MS Mincho';

// 番号 / 品番・品名 / 含む / 含まない / 数量 / 単価 / 金額　（合計 = 9639 DXA）
const COL = [500, 4020, 560, 760, 1000, 1000, 1799];
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
      h('含まない', COL[3]), h('数量', COL[4]), h('単価', COL[5]), h('金額（税抜）', COL[6])],
  });
}

// inc: 'y' = 含む / 'n' = 含まない
function itemRow(no, name, inc, qty, unit, amount, sub) {
  const nameKids = [p(name)];
  if (sub) sub.forEach((s) => nameKids.push(p(s, { size: 15 })));
  return new TableRow({
    children: [
      cell(no, { width: COL[0], align: AlignmentType.CENTER }),
      cell(nameKids, { width: COL[1] }),
      cell(inc === 'y' ? '☑' : '☐', { width: COL[2], align: AlignmentType.CENTER }),
      cell(inc === 'n' ? '☑' : '☐', { width: COL[3], align: AlignmentType.CENTER }),
      cell(qty, { width: COL[4], align: AlignmentType.CENTER, size: 16 }),
      cell(unit, { width: COL[5], align: AlignmentType.RIGHT, size: 16 }),
      cell(amount, { width: COL[6], align: AlignmentType.RIGHT }),
    ],
  });
}

function totalRow(label, amount, opts = {}) {
  return new TableRow({
    children: [
      cell(label, { width: COL[0] + COL[1] + COL[2] + COL[3] + COL[4] + COL[5], span: 6,
        align: AlignmentType.RIGHT, bold: opts.bold, shade: opts.shade }),
      cell(amount, { width: COL[6], align: AlignmentType.RIGHT, bold: opts.bold, shade: opts.shade }),
    ],
  });
}

const rows = [headerRow()];

// ===== 見積書 20260725-003 の記載順・記載どおり =====
rows.push(itemRow('1', '基本月額報酬　＠10,000', 'y', '12　ヶ月', '10,000', '120,000'));

rows.push(itemRow('2', '記帳代行報酬：会計ソフトの入力処理をご依頼の場合＠5,000',
  'y', '12　ケ月', '5,000', '60,000'));

rows.push(itemRow('3', '年仕訳数1,201件～＠50　※1', 'y', '4,325　件', '50', '216,250',
  ['R8.4月期年間仕訳数　5,525件（5,525件－1,200件＝4,325件）']));

rows.push(itemRow('4', '資料預り、打合せ方法：訪問ありの場合＠5,000×12か月、来所・オンラインはゼロ',
  'n', '―　ヶ月', '5,000', '0', ['本契約における方法：来所・オンライン（訪問なし）']));

rows.push(itemRow('5', '月次経理処理頻度　年〇回：年4回　＠5,000×12か月、年6回　＠10,000×12か月、年6回超　＠15,000×12か月',
  'y', '12　ケ月', '5,000', '60,000', ['本契約における頻度：年4回']));

rows.push(itemRow('6', '事業規模　年商46,000万円（年商5,000万円未満は＠0円、5,000万円超から5,000万円ごとに＠5,000）※5億円超は一律（+50,000円）',
  'y', '12　ヶ月', '45,000', '540,000'));

rows.push(itemRow('7', '報酬支払：口座振替以外＠3,000　※請求書発行を行う場合',
  'n', '―　ヶ月', '3,000', '0', ['本契約における支払方法：口座振替']));

rows.push(itemRow('8', '給与計算：基本月額報酬', 'y', '12　ヶ月', '4,000', '48,000'));

rows.push(itemRow('9', '給与計算：人数×月＠800×12ヶ月（年＠9,600）', 'y', '13　人', '9,600', '124,800'));

rows.push(itemRow('10', '給与計算　勤怠の集計有：人数×月＠400×12ヶ月（年＠4,800）※2',
  'y', '13　人', '4,800', '62,400'));

rows.push(itemRow('11', '給与明細印刷有：人数×月＠200×12ヶ月（年＠2,400）', 'y', '13　人', '2,400', '31,200'));

rows.push(itemRow('12', '納税代行手続き（ダイレクト納付）－住民税＠1,000', 'y', '12　ヶ月', '1,000', '12,000'));

rows.push(itemRow('13', '労働保険・社会保険手続き一式：＠4,000', 'y', '12　ヶ月', '4,000', '48,000'));

rows.push(itemRow('14', '労働保険の算定基礎届の作成：＠45,000', 'y', '1　回', '45,000', '45,000'));

rows.push(itemRow('15', '決算報酬：法人 ＠120,000　個人＆NPO ＠50,000',
  'y', '1　事業年度', '120,000', '120,000', ['本契約における区分：法人']));

rows.push(itemRow('16', '消費税申告：＠50,000', 'y', '1　事業年度', '50,000', '50,000'));

rows.push(itemRow('17', '申告書控印刷', 'n', '―　部', '30,000', '0'));

rows.push(itemRow('18', '銀行用申告書印刷', 'n', '―　部', '5,000', '0'));

rows.push(itemRow('19', '総勘定元帳印刷', 'n', '―　部', '30,000', '0'));

rows.push(itemRow('20', 'NXPRO使用　決算手数料：年間△50,000（ミロクのクラウドアプリを使用している場合）',
  'n', '―　事業年度', '△50,000', '0'));

rows.push(itemRow('21', '出精値引き', 'n', '―　事業年度', '―', '0'));

rows.push(itemRow('22', '税理士法第33条の2第1項に規定する書面添付', 'y', '1　事業年度', '30,000', '30,000'));

rows.push(totalRow('小　計　　', '1,567,650', { shade: 'F2F2F2' }));
rows.push(totalRow('消費税（10％）　　', '156,765', { shade: 'F2F2F2' }));
rows.push(totalRow('合　計　　', '1,724,415', { bold: true, shade: 'F2F2F2' }));

const table = new Table({
  columnWidths: COL,
  width: { size: FULL, type: WidthType.DXA },
  rows,
});

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
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [run('別　紙　　契約業務内容および報酬内訳', { bold: true, size: 26 })],
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 80 },
        children: [run('（消費税率10％）', { bold: true, size: 18 })],
      }),
      p('委任者（甲）　株式会社　ブリスオーディオ　　様', { size: 18 }),
      p('受任者（乙）　税理士法人　福田会計', { size: 18 }),
      p('対象　　　　　令和8年4月期（見積番号 20260725-003 に基づく）', { size: 18 }),
      new Paragraph({ spacing: { after: 60 }, children: [run('')] }),
      p('本別紙は、甲乙間の顧問契約書（以下「本契約」という。）の一部を構成する。本契約に基づき乙が受任する業務及び報酬は、下表のとおりとする。「含む」欄に☑を付した業務が本契約に含まれる業務であり、「含まない」欄に☑を付した業務は本契約に含まれない。', { size: 17 }),
      new Paragraph({ spacing: { after: 80 }, children: [run('')] }),
      table,
      new Paragraph({ spacing: { before: 140, after: 40 }, children: [run('【注記】', { bold: true, size: 18 })] }),
      p('※1　年間仕訳数1,200件を超える際は、1仕訳＠50をいただきます。', { size: 16 }),
      p('※2　出勤簿及びタイムカードの預かり（確認業務含む）の場合は、勤怠の管理有となります。', { size: 16 }),
      p('※3　「含まない」欄に☑を付した業務を甲が希望する場合は、その都度、事前に甲乙が業務内容及び報酬額を合意のうえ実施し、上表の単価により別途請求する。', { size: 16 }),
      p('※4　本別紙は本契約の一部を構成する。本別紙の変更は、甲乙双方の書面又は電磁的方法による合意によらなければ、その効力を生じない。', { size: 16 }),
      p('※5　契約期間の中途において消費税率が改正された場合、消費税額は改正後の税率による。', { size: 16 }),
      new Paragraph({ spacing: { before: 180 }, children: [run('')] }),
      p('　　　　　　年　　　月　　　日', { align: AlignmentType.RIGHT, size: 18 }),
      new Paragraph({ spacing: { before: 80 }, children: [run('')] }),
      p('（甲）　所在地　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　', { size: 18 }),
      p('　　　　商　号　　株式会社　ブリスオーディオ　　　　　　　　　　　　　　　㊞', { size: 18 }),
      new Paragraph({ spacing: { before: 100 }, children: [run('')] }),
      p('（乙）　所在地　　群馬県桐生市東一丁目13番39号', { size: 18 }),
      p('　　　　商　号　　税理士法人　福田会計　　　　　　　　　　　　　　　　　　㊞', { size: 18 }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2] || 'bliss.docx', buf);
  console.log('written');
});
