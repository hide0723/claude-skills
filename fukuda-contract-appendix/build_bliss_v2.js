// 税理士法人 福田会計 顧問契約書 別紙　株式会社ブリスオーディオ版
// 共通フォーム（別紙1〜3）に見積書 20260725-003 の数値を記入し、但し書きを別紙4にまとめたもの。
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, PageBreak,
  WidthType, AlignmentType, BorderStyle, ShadingType, VerticalAlign,
} = require('docx');
const fs = require('fs');

const FONT = 'MS Mincho';
const KO = '株式会社　ブリスオーディオ';

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
    spacing: { before: opts.before || 20, after: opts.after || 20, line: opts.line || 215 },
    indent: opts.indent,
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

// inc: true = 含むに☑ / false = ☐ / null = チェック欄なし（前行の続き）
function itemRow(no, name, inc, qty, unit, amount, note, sub) {
  const nameKids = [p(name)];
  if (sub) sub.forEach((s) => nameKids.push(p(s, { size: 15 })));
  return new TableRow({
    children: [
      cell(no, { width: COL[0], align: AlignmentType.CENTER }),
      cell(nameKids, { width: COL[1] }),
      cell(inc === null ? '' : (inc ? '☑' : '☐'), { width: COL[2], align: AlignmentType.CENTER }),
      cell(qty, { width: COL[3], align: AlignmentType.CENTER, size: 16 }),
      cell(unit, { width: COL[4], align: AlignmentType.RIGHT, size: 16 }),
      cell(amount, { width: COL[5], align: AlignmentType.RIGHT }),
      cell(note || '', { width: COL[6], size: 16 }),
    ],
  });
}

function subtotalRow(label, unit, unitPrice, amount) {
  const amtKids = (Array.isArray(amount) ? amount : [amount]).map((t) =>
    p(t, { align: AlignmentType.RIGHT, size: 16, bold: true }));
  return new TableRow({
    children: [
      cell('', { width: COL[0], shade: 'F2F2F2' }),
      cell(label, { width: COL[1], shade: 'F2F2F2', bold: true }),
      cell('', { width: COL[2], shade: 'F2F2F2' }),
      cell(unit || '月額／年額', { width: COL[3], shade: 'F2F2F2', align: AlignmentType.CENTER, size: 15 }),
      cell(unitPrice || '', { width: COL[4], shade: 'F2F2F2', align: AlignmentType.CENTER, size: 15 }),
      cell(amtKids, { width: COL[5], shade: 'F2F2F2' }),
      cell('', { width: COL[6], shade: 'F2F2F2' }),
    ],
  });
}

function totalRow(label, amount, opts = {}) {
  return new TableRow({
    children: [
      cell(label, {
        width: COL[0] + COL[1] + COL[2] + COL[3] + COL[4], span: 5,
        align: AlignmentType.RIGHT, bold: opts.bold, shade: opts.shade || 'F2F2F2',
      }),
      cell(amount, { width: COL[5], align: AlignmentType.RIGHT, bold: opts.bold, shade: opts.shade || 'F2F2F2' }),
      cell('', { width: COL[6], shade: opts.shade || 'F2F2F2' }),
    ],
  });
}

function frontMatter(title, subtitle, lead) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 40 },
      children: [run(title, { bold: true, size: 26 })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 140 },
      children: [run(subtitle, { bold: true, size: 20 })],
    }),
    p(`委任者（甲）　${KO}　　様`, { size: 18 }),
    p('受任者（乙）　税理士法人　福田会計', { size: 18 }),
    p('原契約　　　　令和8年4月　　日付　顧問契約書', { size: 18 }),
    p('対象期間　　　令和8年5月1日から令和9年4月30日まで（第12期）', { size: 18 }),
    blank(),
    p(lead, { size: 17 }),
    blank(80),
  ];
}

const LEAD_TABLE = '本別紙は、甲乙間の顧問契約書（以下「本契約」という。）の一部を構成する。本契約に基づき乙が受任する業務及び報酬は、下表のとおりとする。「含む」欄に☑を付した業務が本契約に含まれる業務であり、☑を付していない業務は本契約に含まれない。';

// ================= 別紙1　税務顧問業務・決算申告代行業務 =================
const rows1 = [headerRow()];

rows1.push(itemRow('1', '税務監査、税務相談業務：', true, '12　ヶ月', '10,000', '120,000', '', ['基本月額報酬']));

rows1.push(itemRow('2', '記帳代行報酬：', true, '12　ケ月', '5,000', '60,000', '',
  ['会計ソフトの入力処理をご依頼の場合']));

rows1.push(itemRow('', 'なお、年仕訳数1,201件～＠50にて別途請求', null, '', '', '', ''));

rows1.push(itemRow('3', '資料預り、打合せ方法：', false, '―　ケ月', '5,000', '0', '来所・オンライン',
  ['訪問ありの場合は＠5,000', '来所・オンラインはゼロ']));

rows1.push(itemRow('4', '月次経理処理頻度：', true, '12　ケ月', '5,000', '60,000', '年　4　回',
  ['年4回　＠5,000×12か月、年6回　＠10,000×12か月、年6回超　＠15,000×12か月']));

rows1.push(itemRow('5', '事業規模：', true, '12　ヶ月', '45,000', '540,000', '46,000万円想定',
  ['年商 46,000 万円（年商5,000万円未満は＠0円、5,000万円超から5,000万円ごとに＠5,000）',
   '※5億円超は一律（+50,000円）']));

rows1.push(itemRow('6', '報酬支払：口座振替以外＠3,000　※請求書発行を行う場合',
  false, '―　ケ月', '3,000', '0', '口座振替'));

rows1.push(subtotalRow('税務業務　小計', '月額／年額', '65,000', '780,000'));

rows1.push(itemRow('7', '決算報酬：法人 ＠120,000　個人＆NPO ＠50,000', true, '1　事業年度', '120,000', '120,000', '法人'));
rows1.push(itemRow('8', '消費税申告：＠50,000', true, '1　事業年度', '50,000', '50,000'));
rows1.push(itemRow('9', '申告書控印刷', false, '―　部', '30,000', '0'));
rows1.push(itemRow('10', '銀行用申告書印刷', false, '―　部', '5,000', '0'));
rows1.push(itemRow('11', '総勘定元帳印刷', false, '―　部', '30,000', '0'));
rows1.push(itemRow('12', 'NXPRO使用　決算手数料：年間△50,000（ミロクのクラウドアプリを使用している場合）',
  false, '―　事業年度', '△50,000', '0'));
rows1.push(itemRow('13', '出精値引き', false, '―　事業年度', '△', '0', '下記お値引き欄にて調整'));
rows1.push(itemRow('14', '税理士法第33条の2第1項に規定する書面添付', true, '1　事業年度', '30,000', '30,000'));

rows1.push(subtotalRow('決算・申告代行業務　小計', '年額のみ', '－', '200,000'));

rows1.push(totalRow('小　計（税抜）　　', '980,000'));
rows1.push(totalRow('消費税（10％）　　', '98,000'));
rows1.push(totalRow('お値引き（税込）　※3　　', '△444,400'));
rows1.push(totalRow('合　計（税込）　　', '633,600', { bold: true, shade: 'E6E6E6' }));

// ===================== 別紙3　給与計算代行業務 =====================
const rows3 = [headerRow()];

rows3.push(itemRow('1', '給与計算：基本月額報酬', true, '12　ヶ月', '4,000', '48,000'));
rows3.push(itemRow('2', '給与計算：人数×月＠800×12ヶ月（年＠9,600）', true, '13　人', '9,600', '124,800'));
rows3.push(itemRow('3', '給与計算　勤怠の集計有：人数×月＠400×12ヶ月（年＠4,800）※1', false, '―　人', '4,800', '0'));
rows3.push(itemRow('4', '給与明細印刷有：人数×月＠200×12ヶ月（年＠2,400）', false, '―　人', '2,400', '0'));
rows3.push(itemRow('5', '納税代行手続き（ダイレクト納付）－住民税＠1,000', true, '12　ヶ月', '1,000', '12,000'));
rows3.push(itemRow('6', '労働保険・社会保険手続き一式：＠4,000', false, '―　ヶ月', '4,000', '0', '※2'));
rows3.push(itemRow('7', '労働保険の算定基礎届の作成：＠45,000', false, '―　回', '45,000', '0', '※2'));

rows3.push(subtotalRow('給与計算代行　小計', '月額／年額', '15,400', '184,800'));

rows3.push(totalRow('小　計（税抜）　　', '184,800'));
rows3.push(totalRow('消費税（10％）　　', '18,480'));
rows3.push(totalRow('お値引き（税込）　※3　　', '△63,360'));
rows3.push(totalRow('合　計（税込）　　', '139,920', { bold: true, shade: 'E6E6E6' }));

const mkTable = (rows) => new Table({
  columnWidths: COL, width: { size: FULL, type: WidthType.DXA }, rows,
});

function notes(list) {
  return [
    new Paragraph({ spacing: { before: 140, after: 40 }, children: [run('【注記】', { bold: true, size: 18 })] }),
    ...list.map((t, i) => p(`※${i + 1}　${t}`, { size: 16 })),
    blank(160),
    p('以　上', { align: AlignmentType.RIGHT, size: 18 }),
  ];
}

const NOTES1 = [
  '「含む」欄に☑を付していない業務は、本契約に含まれない。甲が当該業務を希望する場合は、その都度、事前に甲乙が業務内容及び報酬額を合意のうえ実施し、上表の単価により別途請求する。',
  '上表に掲げのない業務のうち、年末調整代行、支払調書の作成代行、償却資産税申告書の作成代行その他の業務の報酬は、別紙2のとおりとする。',
  '本別紙は本契約の一部を構成する。本別紙の変更は、甲乙双方の書面又は電磁的方法による合意によらなければ、その効力を生じない。',
  '契約期間の中途において消費税率が改正された場合、消費税額は改正後の税率による。',
  '本別紙に係る但し書き及び特約は、別紙4のとおりとする。',
];
// ※3 はお値引き欄から参照するため、共通注記より前に差し込む
NOTES1.splice(2, 0, 'お値引きは、従前の顧問契約書（令和6年1月改定。税務顧問報酬 月額 金52,800円（税込））に基づく年額報酬 金633,600円（税込）に本別紙の合計額を据え置くための調整である。お値引き額は税抜 金404,000円（消費税額 金40,400円）に相当する。適用期間は別紙4第11条による。');

const NOTES3 = [
  '出勤簿及びタイムカードの預かり（確認業務含む）の場合は、勤怠の管理有となります。',
  '労働保険・社会保険の手続代行（項目6及び項目7）は、本契約に含まない。甲が別途委託する社会保険労務士が行う。別紙4第10条を参照。',
  '「含む」欄に☑を付していない業務は、本契約に含まれない。甲が当該業務を希望する場合は、その都度、事前に甲乙が業務内容及び報酬額を合意のうえ実施し、上表の単価により別途請求する。',
  '上表に掲げのない業務のうち、年末調整代行、支払調書の作成代行、償却資産税申告書の作成代行その他の業務の報酬は、別紙2のとおりとする。',
  '本別紙は本契約の一部を構成する。本別紙の変更は、甲乙双方の書面又は電磁的方法による合意によらなければ、その効力を生じない。',
  '契約期間の中途において消費税率が改正された場合、消費税額は改正後の税率による。',
  '本別紙に係る但し書き及び特約は、別紙4のとおりとする。',
];
// ※3 はお値引き欄から参照するため、共通注記より前に差し込む
NOTES3.splice(2, 0, 'お値引きは、従前の顧問契約書（令和6年1月改定。給与計算代行 月額 金11,660円（税込））に基づく年額報酬 金139,920円（税込）に本別紙の合計額を据え置くための調整である。お値引き額は税抜 金57,600円（消費税額 金5,760円）に相当する。適用期間は別紙4第11条による。');

// ================= 別紙2　その他業務の報酬（料金表）=================
const RCOL = [4600, 2400, 2639];
const RFULL = RCOL.reduce((a, b) => a + b, 0);

function rateHeaderRow() {
  const h = (t, w) => cell(t, { width: w, shade: 'D9D9D9', align: AlignmentType.CENTER, bold: true });
  return new TableRow({
    tableHeader: true,
    children: [h('項　目', RCOL[0]), h('単　位', RCOL[1]), h('報酬額（税抜）', RCOL[2])],
  });
}
const rateGroupRow = (label) => new TableRow({
  children: [cell(label, { width: RFULL, span: 3, shade: 'F2F2F2', bold: true })],
});
function rateRow(item, unit, fee) {
  const feeKids = (Array.isArray(fee) ? fee : [fee]).map((t, i) =>
    p(t, { align: AlignmentType.RIGHT, size: i === 0 ? 17 : 15 }));
  return new TableRow({
    children: [
      cell(item, { width: RCOL[0] }),
      cell(unit, { width: RCOL[1], align: AlignmentType.CENTER, size: 16 }),
      cell(feeKids, { width: RCOL[2] }),
    ],
  });
}

const rateRows = [rateHeaderRow()];
rateRows.push(rateGroupRow('１　年末調整代行'));
rateRows.push(rateRow('基本料金', '1企業あたり', '￥10,000'));
rateRows.push(rateRow('従業員人数　10人まで', '1人あたり', '￥2,000'));
rateRows.push(rateRow('従業員人数　11人から30人まで', '1人あたり', '￥5,000'));
rateRows.push(rateRow('従業員人数　30人超', '―', '別途見積り'));
rateRows.push(rateGroupRow('２　支払調書の作成代行'));
rateRows.push(rateRow('所得税法第204条第1項報酬　※3', '1件あたり', '￥1,500'));
rateRows.push(rateGroupRow('３　償却資産税申告書の作成代行'));
rateRows.push(rateRow('提出自治体', '一自治体あたり', '￥10,000'));
rateRows.push(rateGroupRow('４　税務調査立会料及び修正申告書作成料'));
rateRows.push(rateRow('税務調査立会料', '1日1人あたり', '￥30,000'));
rateRows.push(rateRow('修正申告書作成料', '1税目1事業年度あたり', '￥30,000'));
rateRows.push(rateGroupRow('５　株式評価（個別お見積もり）'));
rateRows.push(rateRow('初回', '1回', '￥100,000～'));
rateRows.push(rateRow('2回目以降', '1回', '￥50,000～'));
rateRows.push(rateGroupRow('６　所得税・贈与税申告書の作成代行'));
rateRows.push(rateRow('〈所得税〉確定申告書　第1表・第2表（基本料金）', '1件', '￥20,000'));
rateRows.push(rateRow('〈所得税〉収支内訳書　又は　青色申告決算書（損益計算書のみ）', '1件', '￥30,000'));
rateRows.push(rateRow('〈所得税〉青色申告決算書（貸借対照表あり）', '―', '別紙１に含む'));
rateRows.push(rateRow('〈所得税〉消費税申告書', '1件', '￥30,000'));
rateRows.push(rateRow('〈所得税〉その他の付表・明細（株式譲渡明細を含む）', '1種類につき', '￥10,000'));
rateRows.push(rateRow('〈所得税〉土地・建物の譲渡所得の申告', '1事業年度あたり', '￥100,000'));
rateRows.push(rateRow('〈所得税〉給与所得以外の所得の収入金額が300万円以下の場合', '1件', '△￥10,000'));
rateRows.push(rateRow('〈贈与税〉贈与税申告書の作成・贈与契約書の作成', '贈与者・受贈者1組につき', '￥10,000'));
rateRows.push(rateGroupRow('７　税額控除に係る報酬'));
rateRows.push(rateRow('法人税額の特別控除額に対する報酬　※4', '1事業年度',
  ['特別控除額×5％', '（上限 ￥500,000／事業年度）']));
rateRows.push(rateGroupRow('８　試算表の提出頻度又は訪問の追加'));
rateRows.push(rateRow('別紙1の項目3及び項目4で合意した頻度・方法を超える場合　※5', '都度',
  ['別紙1の当該項目の単価による']));

const rateTable = new Table({
  columnWidths: RCOL, width: { size: RFULL, type: WidthType.DXA }, rows: rateRows,
});

const RATE_NOTES = [
  '年末調整を行わず、法定調書合計表の作成のみを行う場合の報酬は、￥10,000とする。',
  '償却資産税申告書について、該当する資産がない場合は請求しない。',
  '所得税法第204条第1項報酬とは、弁護士・税理士・デザイナー等の一定の職業に該当する者への支払について、支払者が源泉徴収を要する報酬・料金をいう。',
  '税額控除に係る報酬は、法人税申告書別表一「3」欄（法人税額の特別控除額の合計を記載する欄）の金額に5％を乗じた額とし、1事業年度あたり￥500,000（税抜）を上限とする。詳細は別紙4第1条に定めるところによる。',
  '試算表の提出頻度及び資料の預り・打合せの方法について、別紙1の項目3及び項目4で合意した頻度・方法を超えて実施する場合は、別紙1の当該項目の単価により算定し、その都度、事前に甲乙が合意する。',
  '本別紙に掲げのない業務を甲が委任する場合は、その都度、事前に甲乙が業務内容及び報酬額を合意のうえ実施する。',
  '本別紙は本契約の一部を構成する。本別紙の変更は、甲乙双方の書面又は電磁的方法による合意によらなければ、その効力を生じない。',
  '契約期間の中途において消費税率が改正された場合、消費税額は改正後の税率による。',
  '本別紙に係る但し書き及び特約は、別紙4のとおりとする。',
];

// ========================= 別紙4　特約事項 =========================
function art(title) {
  return new Paragraph({
    spacing: { before: 140, after: 30, line: 215 },
    children: [run(title, { bold: true, size: 18 })],
  });
}
function cl(text) {
  return new Paragraph({
    spacing: { before: 10, after: 10, line: 215 },
    indent: { left: 240, hanging: 240 },
    children: [run(text, { size: 16 })],
  });
}

const besshi4 = [
  art('第1条（税額控除に係る報酬）'),
  cl('1　別紙2の区分7（本契約第8項）に定める税額控除に係る報酬の上限￥500,000（税抜）は、1事業年度あたりの上限とする。'),
  cl('2　前項の報酬の算定基礎は、法定申告期限時点で有効な最終の確定申告書の別表一「3」欄の金額とする。その後の修正申告又は更正等により控除額が増加した場合においても、追加の報酬は生じない。ただし、乙の責めに帰すべき事由により当該金額が過大であった場合は、適正額を基礎として精算する。'),
  cl('3　第1項の報酬には、税額控除の適用に通常必要となる資料の確認、要件の検討、適用の判定、計算、関係別表及び明細の作成、申告書への反映並びに申告後の通常の照会対応までを含むものとし、名称のいかんを問わず重ねて請求しない。ただし、甲が行うことを合意した基礎資料の集計は含まない。'),

  art('第2条（追加報酬の取扱い）'),
  cl('1　附属明細書の作成、年末調整代行及び償却資産税申告書の作成に係る報酬は、別紙2に定めるところによる。'),
  cl('2　本契約第2項に定める1事業年度あたり4,800仕訳を超える部分の単価は、1仕訳あたり￥50（税抜）とする。'),
  cl('3　本契約及び別紙において「別途請求」「別途協議」又は「当事務所規定」による旨を定める報酬は、いずれも本契約第9項に定める手続及び上限に従うものとする。'),

  art('第3条（損害賠償）'),
  cl('1　本契約の損害賠償に関する定めのうち「本契約締結の前後を問わず」の文言は、これを削除する。'),
  cl('2　賠償額の上限に関する定めは、本契約の効力発生日以後の乙の行為又は不作為に起因する損害についてのみ適用し、効力発生日前の事由、行為又は不作為に起因する損害には適用しない。'),
  cl('3　前項の上限は、乙の故意又は重大な過失による場合には適用しない。'),

  art('第4条（契約内容の変更）'),
  cl('契約内容の変更は、甲乙双方が書面又はChatwork等の電磁的方法により合意した場合に限り、その効力を生じる。本条は、解約の3か月前予告に関する定めとは別個のものとする。'),

  art('第5条（契約終了時の取扱い）'),
  cl('1　乙は、本契約の終了時、甲から預託を受けた資料の原本を現物により甲に返還する。'),
  cl('2　乙は、会計・税務データ、申告書及び届出書の控え、電子申告の受信通知並びに税務官公署との応答記録等を、契約終了日から14日以内に、一般的に利用可能な電磁的形式により無償で甲に提供する。'),
  cl('3　乙は、期限のある業務について、合理的な範囲で引継ぎに協力する。'),
  cl('4　前2項の提供にあたり特別な加工を要する場合の報酬は、本契約第9項に定める手続に従う。'),

  art('第6条（打合せの記録）'),
  cl('乙は、打合せの録音、録画又は文字起こしを作成した場合、当該打合せの日から少なくとも1年間これを保存し、甲の求めがあったときは、当該求めから10営業日以内に、保有する原データ及び文字起こしの写しを一般的に利用可能な電磁的形式により甲に提供する。'),

  art('第7条（AIサービス等の利用）'),
  cl('1　乙は、AIサービス提供者及び業務委託先の選定、利用及び監督について責任を負い、これらの者の行為について、乙が自ら行った場合と同様の責任を負う。'),
  cl('2　乙は、情報漏えいその他の事故（そのおそれがある場合を含む。）を認識したときは、速やかに甲に通知する。'),

  art('第8条（契約期間及び従前の合意との関係）'),
  cl('1　本契約の期間は、令和8年5月1日から令和9年4月30日までとする。'),
  cl('2　同一の委任業務に関する従前の料金の合意と本契約の内容とが矛盾する場合は、その矛盾する範囲に限り、本契約が優先する。'),

  art('第9条（条項の引用）'),
  cl('本契約第6項及び第7項における「(4)」及び「(5)」は、委任業務の範囲を定める号を指すものとする。'),

  art('第10条（労働・社会保険の手続代行）'),
  cl('1　労働保険及び社会保険の手続代行は、本契約に含まない。別紙3の項目6及び項目7のとおり、当該業務は乙の受任範囲外とし、甲が別途委託する社会保険労務士が行う。'),
  cl('2　本契約第6項に「必要な労働・社会保険の手続代行を含む」旨の記載がある場合は、前項により読み替えるものとする。'),
  cl('3　甲が将来これらの業務を乙に委任することを希望する場合は、別紙3の項目6及び項目7の単価により、その都度、事前に甲乙が合意のうえ実施する。'),

  art('第11条（お値引き）'),
  cl('1　別紙1及び別紙3のお値引きは、従前の顧問契約書（令和6年1月改定）に基づく年額報酬（税務顧問報酬 金633,600円（税込）及び給与計算代行 金139,920円（税込）。合計 金773,520円（税込））に、本別紙の合計額を据え置くための調整である。'),
  cl('2　前項のお値引きは、本契約の期間（令和8年5月1日から令和9年4月30日まで）に限り適用する。次期以降の取扱いは、甲乙協議のうえ決定する。'),
  cl('3　本契約期間の中途において委任業務の範囲又は数量に変更が生じた場合のお値引き額の取扱いは、甲乙協議のうえ決定する。'),
];

// ============================== 文書 ==============================
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
      ...frontMatter('別　紙　１　　契約業務内容および報酬内訳', '（税務顧問業務・決算申告代行業務）', LEAD_TABLE),
      mkTable(rows1),
      ...notes(NOTES1),

      new Paragraph({ children: [new PageBreak()] }),

      ...frontMatter('別　紙　２　　その他業務の報酬', '（年末調整代行業務・償却資産申告業務ほか料金表）',
        '本別紙は、甲乙間の顧問契約書（以下「本契約」という。）の一部を構成する。下表の業務は別紙1及び別紙3の月額報酬に含まれない。甲が委任を希望する場合は、その都度、事前に甲乙が業務内容を合意のうえ実施し、下表の報酬額により別途請求する。'),
      rateTable,
      ...notes(RATE_NOTES),

      new Paragraph({ children: [new PageBreak()] }),

      ...frontMatter('別　紙　３　　契約業務内容および報酬内訳', '（給与計算代行業務）', LEAD_TABLE),
      mkTable(rows3),
      ...notes(NOTES3),

      new Paragraph({ children: [new PageBreak()] }),

      ...frontMatter('別　紙　４　　特　約　事　項', '（別紙1から別紙3までに係る但し書き）',
        '本別紙は、甲乙間の顧問契約書（以下「本契約」という。）の一部を構成する。本契約及び別紙1から別紙3までの定めと本別紙の定めとが異なる場合は、本別紙が優先する。'),
      ...besshi4,
      blank(160),
      p('以　上', { align: AlignmentType.RIGHT, size: 18 }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2] || 'bliss_v2.docx', buf);
  console.log('written');
});
