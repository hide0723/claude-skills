// 税理士法人 福田会計 顧問契約書 別紙1（契約業務内容および報酬内訳）生成スクリプト
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, BorderStyle, ShadingType, VerticalAlign, HeadingLevel,
} = require('docx');
const fs = require('fs');

const FONT = 'MS Mincho';
const PAGE_W = 9639; // A4 portrait usable width in DXA (A4 11906 - margins)

// 列幅（合計 = PAGE_W）
const COL = [624, 4200, 700, 900, 3215];

const B = { style: BorderStyle.SINGLE, size: 4, color: '000000' };
const CELL_BORDERS = { top: B, bottom: B, left: B, right: B };

function run(text, opts = {}) {
  return new TextRun({
    text,
    font: FONT,
    size: opts.size || 17, // half-points (8.5pt)
    bold: !!opts.bold,
    ...opts,
  });
}

function p(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.LEFT,
    spacing: { before: opts.before || 20, after: opts.after || 20, line: opts.line || 220 },
    indent: opts.indent,
    children: Array.isArray(text) ? text : [run(text, opts)],
  });
}

function cell(children, opts = {}) {
  return new TableCell({
    width: { size: opts.width, type: WidthType.DXA },
    columnSpan: opts.span,
    borders: CELL_BORDERS,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    shading: opts.shade
      ? { type: ShadingType.CLEAR, fill: opts.shade, color: 'auto' }
      : undefined,
    children: (Array.isArray(children) ? children : [children]).map((c) =>
      typeof c === 'string' ? p(c, { align: opts.align, bold: opts.bold }) : c
    ),
  });
}

// ---- 見出し行 -------------------------------------------------------------
function headerRow() {
  return new TableRow({
    tableHeader: true,
    children: [
      cell('', { width: COL[0], shade: 'D9D9D9' }),
      cell('業　務　項　目', { width: COL[1], shade: 'D9D9D9', align: AlignmentType.CENTER, bold: true }),
      cell('含む', { width: COL[2], shade: 'D9D9D9', align: AlignmentType.CENTER, bold: true }),
      cell('含まない', { width: COL[3], shade: 'D9D9D9', align: AlignmentType.CENTER, bold: true }),
      cell('摘　要（報酬・単価／税抜）', { width: COL[4], shade: 'D9D9D9', align: AlignmentType.CENTER, bold: true }),
    ],
  });
}

// ---- 区分見出し行（全幅） --------------------------------------------------
function sectionRow(label, note) {
  const kids = [p(label, { bold: true, size: 18 })];
  if (note) kids.push(p(note, { size: 15 }));
  return new TableRow({
    children: [
      cell(kids, { width: COL.reduce((a, b) => a + b, 0), span: 5, shade: 'F2F2F2' }),
    ],
  });
}

// ---- 明細行 ---------------------------------------------------------------
// inc: 'y' = 含むにレ点 / 'n' = 含まないにレ点 / null = 空欄（選択記入）
function itemRow(no, name, inc, remark, sub) {
  const nameKids = [p(name)];
  if (sub) sub.forEach((s) => nameKids.push(p(s, { size: 15 })));
  const remarkKids = (Array.isArray(remark) ? remark : [remark]).map((r) => p(r, { size: 15 }));
  return new TableRow({
    children: [
      cell(no, { width: COL[0], align: AlignmentType.CENTER }),
      cell(nameKids, { width: COL[1] }),
      cell(inc === 'y' ? '☑' : '☐', { width: COL[2], align: AlignmentType.CENTER }),
      cell(inc === 'n' ? '☑' : '☐', { width: COL[3], align: AlignmentType.CENTER }),
      cell(remarkKids, { width: COL[4] }),
    ],
  });
}

// ---- 全幅の注記行 ---------------------------------------------------------
function noteRow(text) {
  return new TableRow({
    children: [cell([p(text, { size: 15 })], { width: COL.reduce((a, b) => a + b, 0), span: 5 })],
  });
}

const rows = [];
rows.push(headerRow());

// =========================== Ⅰ 月額顧問報酬 ================================
rows.push(sectionRow(
  'Ⅰ　月額顧問報酬に含まれる業務（毎月）',
  '※ 下記のうち「含む」に☑を付した業務が、第1条の月額顧問報酬の対象業務である。'
));

rows.push(itemRow('(1)', '基本業務（税務・会計に関する相談、指導及び助言、月次データの確認）', 'y',
  ['基本月額報酬　＠10,000／月']));

rows.push(itemRow('(2)', '記帳代行（会計ソフトへの入力処理）', null,
  ['＠5,000／月',
   '1事業年度あたり4,800仕訳までを月額顧問報酬に含む。',
   '超過分は本契約第2項に基づき1仕訳＠50円で精算する。'],
  ['□ 依頼する　　□ 依頼しない（自計化）']));

rows.push(itemRow('(3)', '月次試算表の作成及び提出', null,
  ['年4回　　　＠5,000／月',
   '年6回　　　＠10,000／月',
   '年6回超　　＠15,000／月'],
  ['提出頻度：□ 年4回　□ 年6回　□ 年12回']));

rows.push(itemRow('(4)', '資料の預り・返却及び打合せ', null,
  ['来所　　　　＠0',
   'オンライン　＠0',
   '訪問　　　　＠5,000／月'],
  ['方法：□ 来所　□ オンライン　□ 訪問']));

rows.push(itemRow('(5)', '夏季源泉所得税の手続〈納期の特例〉', 'y', ['―']));

rows.push(itemRow('(6)', '納税代行手続（ダイレクト納付）－住民税', null, ['＠1,000／月'],
  ['□ 依頼する　　□ 依頼しない']));

rows.push(itemRow('(7)', '給与計算（基本）', null, ['＠4,000／月'],
  ['□ 依頼する　　□ 依頼しない']));

rows.push(itemRow('(8)', '給与計算（対象者数に応じた加算）', null,
  ['対象者1名につき ＠800／月（年＠9,600）'],
  ['対象者　　　　　名']));

rows.push(itemRow('(9)', '給与計算（勤怠の集計を含む場合の加算）', null,
  ['対象者1名につき ＠400／月（年＠4,800）'],
  ['対象者　　　　　名　※注4']));

rows.push(itemRow('(10)', '給与明細の印刷', null,
  ['対象者1名につき ＠200／月（年＠2,400）'],
  ['対象者　　　　　名']));

rows.push(itemRow('(11)', '労働保険・社会保険手続一式', null, ['＠4,000／月'],
  ['□ 依頼する　　□ 依頼しない']));

rows.push(itemRow('(12)', '報酬の支払方法', null,
  ['口座振替　　　　　　　　＠0',
   '口座振替以外（請求書発行）＠3,000／月'],
  ['□ 口座振替　□ 口座振替以外']));

rows.push(noteRow('月額顧問報酬　小計（税抜）　　　　　　　　　　　　　　　　　　　　￥　　　　　　　　　／月　　（消費税額　￥　　　　　　　　）'));

// =========================== Ⅱ 決算・申告業務 ==============================
rows.push(sectionRow(
  'Ⅱ　決算・申告業務（事業年度ごと。税務顧問報酬に含む）',
  '※ 本区分の業務は、事業年度ごとに1回、決算月の翌月以降に別途請求する。'
));

rows.push(itemRow('(13)', '決算報酬（決算書の作成、法人税・地方税の確定申告書の作成及び提出）', null,
  ['法人　　　　　＠120,000／事業年度',
   '個人・NPO　　 ＠50,000／事業年度'],
  ['□ 法人　　□ 個人・NPO']));

rows.push(itemRow('(14)', '消費税確定申告報酬', null, ['＠50,000／事業年度'],
  ['□ 課税事業者　□ 免税事業者（該当なし）']));

rows.push(itemRow('(15)', '書面添付（税理士法第33条の2第1項に規定する書面の添付）', 'y',
  ['決算報酬に含む。本項につき別途の報酬は請求しない。',
   '※注5'],
  null));

rows.push(itemRow('(16)', '申告書控の印刷・製本', null, ['＠30,000／部'], ['　　　　　部']));
rows.push(itemRow('(17)', '銀行提出用申告書の印刷', null, ['＠5,000／部'], ['　　　　　部']));
rows.push(itemRow('(18)', '総勘定元帳の印刷・製本', null, ['＠30,000／部'], ['　　　　　部']));

rows.push(itemRow('(19)', 'NXPRO（ミロク社クラウドアプリ）使用による減額', null,
  ['△50,000／事業年度'],
  ['□ 使用する　　□ 使用しない']));

rows.push(itemRow('(20)', '出精値引き', null, ['△　　　　　　　／事業年度'], null));

rows.push(noteRow('決算・申告報酬　小計（税抜）　　　　　　　　　　　　　　　　　　　￥　　　　　　　／事業年度　（消費税額　￥　　　　　　　　）'));

// =========================== Ⅲ 選択的追加業務 ==============================
rows.push(sectionRow(
  'Ⅲ　選択的追加業務（月額顧問報酬及び決算・申告報酬に含まない）',
  '※ 本区分の業務は、利用の都度、業務内容及び報酬額について事前に甲乙が合意したうえで実施する。'
));

rows.push(itemRow('(21)', '労働保険の年度更新（算定基礎届）の作成', 'n', ['＠45,000／回']));
rows.push(itemRow('(22)', '冬季源泉所得税の手続〈年末調整〉及び法定調書等の提出手続', 'n', ['別紙2「報酬規定」による。']));
rows.push(itemRow('(23)', '税務調査立会料及び修正申告書作成料', 'n', ['別紙2「報酬規定」による。']));
rows.push(itemRow('(24)', 'その他の届出書作成', 'n', ['別紙2「報酬規定」による。']));
rows.push(itemRow('(25)', '自計化支援（会計ソフトの導入・操作指導）', 'n', ['別紙2「報酬規定」による。']));
rows.push(itemRow('(26)', '資産税関連業務（相続税申告・贈与税申告・譲渡申告・相続対策・事業承継・自社株対策）', 'n',
  ['本契約には一切含まれない。',
   '相談内容に応じ別紙2「報酬規定」により別途請求する。']));
rows.push(itemRow('(27)', '試算表の提出頻度又は訪問の追加（第Ⅰ区分(3)(4)で合意した頻度・方法を超える場合）', 'n',
  ['別紙2「報酬規定」による。都度、事前に合意する。']));
rows.push(itemRow('(28)', '商業登記・建設業許可・社会保険労務関連業務', 'n',
  ['提携する司法書士・社会保険労務士事務所の報酬規定による。']));

const table = new Table({
  columnWidths: COL,
  width: { size: COL.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  rows,
});

// =========================== 文書本体 ======================================
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 18 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1000, bottom: 900, left: 1134, right: 1134 },
      },
    },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [run('別　紙　１　　契約業務内容および報酬内訳', { bold: true, size: 26 })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
        children: [run('（顧問契約書　第1条関係）', { size: 18 })],
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 60 },
        children: [run('（消費税率10％）', { bold: true, size: 18 })],
      }),
      p([run('委任者（甲）', { size: 17 }), run('　　　　　　　　　　　　　　　　　　　　　　　様', { size: 17 })]),
      p([run('受任者（乙）　税理士法人　福田会計', { size: 17 })]),
      new Paragraph({ spacing: { after: 80 }, children: [run('')] }),
      p('本別紙は、甲乙間の顧問契約書（以下「本契約」という。）の一部を構成する。本契約に基づき乙が受任する業務の範囲及び報酬は、下表のとおりとする。', { size: 17 }),
      new Paragraph({ spacing: { after: 100 }, children: [run('')] }),
      table,
      new Paragraph({ spacing: { before: 160, after: 60 }, children: [run('【注記】', { bold: true, size: 18 })] }),
      p('注1　本別紙及び別紙2「報酬規定」は、いずれも本契約の一部を構成する。これらの変更は、甲乙双方の書面又は電磁的方法による合意によらなければ、その効力を生じない。', { size: 16 }),
      p('注2　業務量の基準は年間仕訳数によるものとし、甲の売上高（事業規模）を基準とする報酬の加算は行わない。記帳代行に係る報酬は、第Ⅰ区分(2)のとおり、1事業年度4,800仕訳までを月額顧問報酬に含め、これを超える部分について1仕訳＠50円により精算する。', { size: 16 }),
      p('注3　試算表の提出頻度及び資料の預り・打合せの方法は、甲の売上高とは切り離し、第Ⅰ区分(3)及び(4)のとおり本契約上のサービス内容として定める。これを超える頻度・方法を希望する場合は、第Ⅲ区分(27)により、その都度事前に甲乙が合意する。', { size: 16 }),
      p('注4　出勤簿及びタイムカードの預り（確認業務を含む。）を乙が行う場合は、第Ⅰ区分(9)の「勤怠の集計を含む場合」に該当する。', { size: 16 }),
      p('注5　書面添付（税理士法第33条の2第1項）は、税務調査への備え及び申告内容の信頼性を高める趣旨から、第Ⅱ区分(15)のとおり決算業務に含めるものとし、別途の報酬は請求しない。', { size: 16 }),
      p('注6　本表に記載のない業務は、本契約に含まれない。当該業務を乙に委任する場合は、別紙2「報酬規定」に基づき、その都度事前に甲乙が業務内容及び報酬額を合意する。', { size: 16 }),
      p('注7　契約期間の中途において消費税率が改正された場合、消費税額は改正後の税率による。', { size: 16 }),
      new Paragraph({ spacing: { before: 200 }, children: [run('')] }),
      p('　　　　　　年　　　月　　　日', { align: AlignmentType.RIGHT, size: 18 }),
      new Paragraph({ spacing: { before: 100 }, children: [run('')] }),
      p('（甲）　所在地　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　', { size: 18 }),
      p('　　　　商　号　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　㊞', { size: 18 }),
      new Paragraph({ spacing: { before: 120 }, children: [run('')] }),
      p('（乙）　所在地　　群馬県桐生市東一丁目13番39号', { size: 18 }),
      p('　　　　商　号　　税理士法人　福田会計　　　　　　　　　　　　　　　　　　㊞', { size: 18 }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(process.argv[2] || 'fukuda_besshi1.docx', buf);
  console.log('written');
});
