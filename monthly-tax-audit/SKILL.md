---
name: monthly-tax-audit
description: 法人税の月次税務監査を支援するスキル。仕訳日記帳CSV（Shift-JIS）と前期の監査不明点ファイル（xlsx）を照合し、同様・再発の指摘事項を特定して当期の監査不明点一覧表（xlsx）に月別シートとして自動転記する。「月次監査」「税務監査」「記帳検査」「仕訳日記帳」「監査不明点」「法人税監査」「指摘事項」「監査レビュー」などのキーワードが出た場合、または仕訳日記帳CSVと前期指摘事項の照合作業が必要な場合は必ずこのスキルを使用する。
---

# 月次税務監査レビュースキル

## 概要

税理士法人での法人税月次税務監査において、以下を自動化する：

1. 仕訳日記帳CSV（Shift-JIS）から要確認仕訳を抽出
2. 前期の監査不明点ファイルと照合し、再発・類似案件を特定
3. 当期の監査不明点一覧表（xlsx）に月別シートとして転記

## ファイル構成の確認

作業開始前にユーザーへ以下を確認する（または会話から特定する）：

- **対象CSVパス**: 仕訳日記帳（Shift-JIS形式）
- **書き込み先xlsxパス**: 当期の監査不明点一覧表
- **前期参照xlsxパス**: 前期の監査不明点一覧表（指摘パターン把握用）
- **対象期間**: 何月から何月分か

---

## Step 1: 前期指摘事項の読み込み

PowerShellのExcel COMで前期の不明点xlsxを全シート読み込み、指摘パターンを把握する。

```powershell
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$wb = $excel.Workbooks.Open($prevFilePath)
$sheetNames = @()
foreach ($sh in $wb.Sheets) { $sheetNames += $sh.Name }

foreach ($shName in $sheetNames) {
    $ws = $wb.Sheets.Item($shName)
    $rows = $ws.UsedRange.Rows.Count
    $cols = $ws.UsedRange.Columns.Count
    for ($r = 1; $r -le $rows; $r++) {
        $rowData = @()
        for ($c = 1; $c -le $cols; $c++) { $rowData += $ws.Cells.Item($r,$c).Text }
        $line = ($rowData -join "`t").TrimEnd()
        if ($line.Trim() -ne "") { Write-Output "[$shName] $line" }
    }
}
$wb.Close($false)
$excel.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
```

前期の指摘事項から以下を把握する：
- 繰り返し発生しているパターン（再発リスク高）
- 「修正確認済み」と記録されているが今期も発生しうる事項
- 資料提出依頼が必要だった事項・科目

---

## Step 2: 仕訳日記帳CSVの読み込み

CSVはShift-JIS（Windows既定エンコーディング = `-Encoding Default`）で読み込む。UTF-8で読むと文字化けする。

```powershell
$lines = Get-Content -Path $csvPath -Encoding Default
Write-Output "総行数: $($lines.Count)"
```

---

## Step 3: 要確認仕訳の抽出

以下のキーワードでCSVを検索し、要確認候補を抽出する。

```powershell
# 福利厚生費
$lines | Select-String -Pattern "福利厚生|弁当"
# 修繕費
$lines | Select-String -Pattern "修繕費"
# 建設仮勘定
$lines | Select-String -Pattern "建設仮勘定"
# 外注加工費
$lines | Select-String -Pattern "外注加工"
# 地代家賃
$lines | Select-String -Pattern "地代家賃"
# 寄付金
$lines | Select-String -Pattern "寄付金"
# 出資金・匿名投資組合
$lines | Select-String -Pattern "出資金|匿名"
# 大口消耗品費（100万円超）
$lines | Select-String -Pattern "消耗品費" | Where-Object { $_ -match "[0-9]{1,3},[0-9]{3},[0-9]{3}" }
```

---

## Step 4: 判断ルール

抽出した仕訳を以下のルールで指摘要否を判定する。

### 消費税区分

| 摘要のキーワード | 正しい税区分 | 指摘要否 |
|-----------------|------------|---------|
| 「弁当代」 | 課対仕入8%（軽減税率） | 10%なら指摘 |
| 「食事代」「会議費」（外食） | 課対仕入10% | 8%（軽）なら指摘 |
| 地代家賃（事業所貸付） | 課対仕入10% | 非課税扱いなら指摘 |

### 修繕費

| 状況 | 判断 | 指摘要否 |
|------|------|---------|
| 摘要に「修理代」を含む | 修繕費処理で正しい | なし |
| 摘要が「製作＋交換」「新設」等で資本的支出が疑われる | 請求書確認・資本的支出の判断が必要 | あり |
| 同一金額・同一内容の仕訳が異なる部門・伝票で複数計上 | 重複計上の疑い | あり |
| 摘要のみでは内容が判断できない大口修繕費 | 確認不要 | なし |

### 建設仮勘定・外注加工費

| 状況 | 判断 | 指摘要否 |
|------|------|---------|
| 建設仮勘定→外注加工費（製造費）への振替 | 固定資産への振替が適切か確認が必要 | あり |
| 建設仮勘定→機械装置・構築物への振替 | 正しい処理 | なし |
| 建設仮勘定の大口計上（売買代金等） | 内容・処理方針の確認が必要 | あり |

### 寄付金・出資金

| 状況 | 判断 | 指摘要否 |
|------|------|---------|
| 小額の寄付金（概ね50,000円未満） | 確認不要 | なし |
| 大口の寄付金 | 資料確認が必要 | あり |
| 匿名投資組合の分配金・損益計上 | 損益分配報告書の確認が必要 | あり |

---

## Step 5: 前期指摘との照合

- 前期に「修正確認済み」と記録されているが、今期も同様の計上がある → **再発**として指摘（前期何月の指摘と同様である旨を明記）
- 前期から継続して確認が必要な事項 → 継続指摘として記録
- 今期初めて発見した事項 → 新規指摘として記録

---

## Step 6: 監査不明点xlsxへのシート追加

### シート書式

既存シートの書式に合わせて月別シートを追加する。

**列構成（A～J列）：**

| 列 | 項目 |
|----|------|
| A | No. |
| B | 済 |
| C | 日付 |
| D | 借方科目 |
| E | 貸方科目 |
| F | 金額（#,##0形式） |
| G | 摘要 |
| H | 修正・確認依頼 |
| I | 次回監査時以降変更内容 |
| J | 備考 |

**行構成：**
- 行1：会社名
- 行2：「月次確認・修正依頼一覧表」
- 行3：年・月・監査日
- 行4：ヘッダー行
- 行5～19：指摘事項（No.1～15）
- 行20：合計行
- 行21：その他

### Excel COM スニペット

```powershell
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open($outputPath)

# 既存シートの先頭に挿入する場合
$refSheet = $wb.Sheets.Item(1)
$ws = $wb.Sheets.Add([System.Reflection.Missing]::Value, $refSheet)
$ws.Name = "R8.1月"  # シート名：期・月を明記

# 列幅設定
$ws.Columns.Item(1).ColumnWidth = 5   # No.
$ws.Columns.Item(3).ColumnWidth = 10  # 日付
$ws.Columns.Item(4).ColumnWidth = 20  # 借方科目
$ws.Columns.Item(5).ColumnWidth = 18  # 貸方科目
$ws.Columns.Item(6).ColumnWidth = 14  # 金額
$ws.Columns.Item(7).ColumnWidth = 30  # 摘要
$ws.Columns.Item(8).ColumnWidth = 40  # 修正・確認依頼

# ヘッダー
$ws.Cells.Item(1,1).Value2 = "株式会社　○○"
$ws.Cells.Item(2,1).Value2 = "月次確認・修正依頼一覧表"
$ws.Cells.Item(3,3).Value2 = "2026年"
$ws.Cells.Item(3,4).Value2 = "1月分"
$ws.Cells.Item(3,9).Value2 = "監査日"

# データ行（1件あたり）
$row = 5
$ws.Cells.Item($row,1).Value2 = 1            # No.
$ws.Cells.Item($row,3).Value2 = "1月31日"   # 日付
$ws.Cells.Item($row,4).Value2 = "[製]修繕費（成鶏部門）"  # 借方科目
$ws.Cells.Item($row,5).Value2 = ""           # 貸方科目
$ws.Cells.Item($row,6).Value2 = 1808356      # 金額
$ws.Cells.Item($row,6).NumberFormatLocal = "#,##0"
$ws.Cells.Item($row,7).Value2 = "吉澤電気：換気扇盤製作＋交換"  # 摘要
$ws.Cells.Item($row,8).Value2 = "請求書をご確認ください。資本的支出に該当しないでしょうか。"
$ws.Rows.Item($row).RowHeight = 45
$ws.Cells.Item($row,8).WrapText = $true

# No.6～15（空白行）
for ($n = 6; $n -le 15; $n++) { $ws.Cells.Item(4+$n,1).Value2 = $n }

# 合計行
$ws.Cells.Item(20,1).Value2 = "計　"
$ws.Cells.Item(20,6).Value2 = 1808356
$ws.Cells.Item(20,6).NumberFormatLocal = "#,##0"
$ws.Cells.Item(21,1).Value2 = "その他"

$wb.Save()
$wb.Close($false)
$excel.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
```

### 注意事項

- `$ws.Cells.Item($row,$col).HorizontalAlignment` の設定はCOMエラーが出ることがあるため省略してよい
- 文字列の設定には `Value2` を使う。配列のインデックスアクセスは型エラーになりやすいため、変数に一旦代入してから設定する
- 行削除は後ろの行から実施する（前から削除すると行番号がずれる）

---

## Step 7: 確認依頼文のテンプレート

| 状況 | 確認依頼文の例 |
|------|--------------|
| 資本的支出の可能性 | 「請求書をご確認ください。また内容から資本的支出に該当しないでしょうか。（前期○月にも同様の指摘あり）」 |
| 重複計上の疑い | 「同一内容・同一金額が別伝票（No.○○）でも計上されています。仕訳の経緯をご確認ください。」 |
| 資料提出依頼 | 「資料をご提出ください。」 |
| 前期指摘の再発 | 「前期令和○年○月に同様の指摘（修正確認済み）がありますが、今期も同様に計上されています。ご確認ください。」 |
| 固定資産計上の判断 | 「建設仮勘定から○○費への振替ですが、設備への取付工事として固定資産（機械装置・構築物）への振替が適切ではないでしょうか。請求書をご確認ください。」 |
| 匿名投資組合 | 「○○の損益分配報告書をご提出ください。また源泉税の法人税等計上処理の根拠をご確認させてください。」 |

---

## Step 8: 完了報告

監査後にユーザーへ以下を報告する：

1. 各月の指摘件数と合計金額
2. 前期から再発している指摘事項（件数・内容）
3. 新規に発見した指摘事項（件数・内容）
4. xlsxファイルへの転記完了確認
