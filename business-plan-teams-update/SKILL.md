---
name: business-plan-teams-update
description: 福田会計の事業計画Excelを毎日更新し、毎月1日にMicrosoft TeamsチャネルへAdaptive Cardで自動投稿するスキル。「事業計画」「Teams投稿」「月次報告」「進捗共有」「目標管理」「KPI」などのキーワードが出た場合は必ずこのスキルを使用する。
---

# 事業計画更新・Teams月次投稿スキル

## 概要

福田会計の事業計画管理を自動化する：

1. 事業計画Excel（月次実績シート）を毎日更新
2. 毎月1日に当月の事業計画サマリーをMicrosoft Teamsチャネルへ投稿
3. 目標対比・進捗を可視化して情報共有

---

## 作業開始前の確認事項

以下をユーザーへ確認する（または会話から特定する）：

- **事業計画Excelパス**: 例 `C:\fukuda\business_plan_2026.xlsx`
- **Teams Incoming Webhook URL**: Teamsチャネルの設定から取得したURL
- **対象月**: 更新・投稿する対象年月（省略時は当月）
- **作業種別**: 「日次更新」か「月次Teams投稿」か（両方の場合も可）

---

## ファイル構成（Excelシート構造）

事業計画Excelは以下のシート構成を想定する。実際の構成に合わせて読み替える。

### 「事業計画」シート（年間目標）

| 列 | 項目 |
|----|------|
| A | 月 |
| B | 売上目標（円） |
| C | 経費予算（円） |
| D | 新規顧問先目標（件） |
| E | 解約予定（件） |
| F | 備考 |

### 「実績」シート（月次実績）

| 列 | 項目 |
|----|------|
| A | 月 |
| B | 売上実績（円） |
| C | 経費実績（円） |
| D | 新規顧問先実績（件） |
| E | 解約実績（件） |
| F | 顧問先合計（件） |
| G | 更新日 |
| H | 備考 |

---

## Step 1: Excelファイルの読み込み

```powershell
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $excel.Workbooks.Open($planFilePath)

# 「事業計画」シートから目標値を取得
$planSheet = $wb.Sheets.Item("事業計画")

# 「実績」シートから実績値を取得
$actualSheet = $wb.Sheets.Item("実績")

# 対象月の行を検索（A列に月が入っている）
$targetMonth = 5  # 例：5月
$planRow = $null
for ($r = 2; $r -le 20; $r++) {
    if ($planSheet.Cells.Item($r, 1).Value2 -eq $targetMonth) {
        $planRow = $r
        break
    }
}

# 目標値の取得
$targetSales      = $planSheet.Cells.Item($planRow, 2).Value2
$targetExpense    = $planSheet.Cells.Item($planRow, 3).Value2
$targetNewClients = $planSheet.Cells.Item($planRow, 4).Value2
```

---

## Step 2: 日次更新（実績入力）

ユーザーから入力された実績値を「実績」シートに書き込む。

```powershell
# 対象月の実績行を検索または新規作成
$actualRow = $null
for ($r = 2; $r -le 20; $r++) {
    if ($actualSheet.Cells.Item($r, 1).Value2 -eq $targetMonth) {
        $actualRow = $r
        break
    }
}
if ($null -eq $actualRow) {
    # 空行を探して追記
    for ($r = 2; $r -le 20; $r++) {
        if ($actualSheet.Cells.Item($r, 1).Value2 -eq "" -or
            $null -eq $actualSheet.Cells.Item($r, 1).Value2) {
            $actualRow = $r
            break
        }
    }
}

# 実績値の書き込み（ユーザーが入力した値を使用）
$actualSheet.Cells.Item($actualRow, 1).Value2 = $targetMonth
$actualSheet.Cells.Item($actualRow, 2).Value2 = $actualSales       # 売上実績
$actualSheet.Cells.Item($actualRow, 3).Value2 = $actualExpense     # 経費実績
$actualSheet.Cells.Item($actualRow, 4).Value2 = $actualNewClients  # 新規顧問先
$actualSheet.Cells.Item($actualRow, 5).Value2 = $actualCanceled    # 解約
$actualSheet.Cells.Item($actualRow, 6).Value2 = $totalClients      # 顧問先合計
$actualSheet.Cells.Item($actualRow, 7).Value2 = (Get-Date -Format "yyyy/MM/dd")  # 更新日
$actualSheet.Cells.Item($actualRow, 2).NumberFormatLocal = "#,##0"
$actualSheet.Cells.Item($actualRow, 3).NumberFormatLocal = "#,##0"

$wb.Save()
Write-Output "実績を更新しました（$targetMonth 月）"
```

---

## Step 3: 進捗率の計算

Teams投稿前に目標対比を計算する。

```powershell
# 売上進捗率
$salesRate = if ($targetSales -gt 0) {
    [math]::Round(($actualSales / $targetSales) * 100, 1)
} else { 0 }

# 達成状況の絵文字判定
$salesEmoji = switch ($true) {
    ($salesRate -ge 100) { "✅" }
    ($salesRate -ge 80)  { "🟡" }
    default              { "🔴" }
}

# 新規顧問先進捗
$clientRate = if ($targetNewClients -gt 0) {
    [math]::Round(($actualNewClients / $targetNewClients) * 100, 1)
} else { 0 }
$clientEmoji = switch ($true) {
    ($clientRate -ge 100) { "✅" }
    ($clientRate -ge 50)  { "🟡" }
    default               { "🔴" }
}

Write-Output "売上進捗: ${salesRate}% ${salesEmoji}"
Write-Output "新規顧問先進捗: ${clientRate}% ${clientEmoji}"
```

---

## Step 4: 毎月1日のTeams投稿

毎月1日に当月の事業計画サマリーをTeamsチャネルへ投稿する。

### 投稿日チェック

```powershell
$today = Get-Date
$isFirstDay = ($today.Day -eq 1)
if (-not $isFirstDay) {
    Write-Output "本日は月初ではないため、Teams投稿をスキップします（今日: $($today.ToString('M月d日'))）"
    # 強制投稿が必要な場合は $isFirstDay = $true に変更
}
```

### Teams Incoming Webhook への投稿

```powershell
$webhookUrl = "YOUR_TEAMS_WEBHOOK_URL"  # ← 実際のWebhook URLに置き換える

$currentYear  = $today.Year
$currentMonth = $today.Month
$prevMonth    = if ($currentMonth -eq 1) { 12 } else { $currentMonth - 1 }
$prevYear     = if ($currentMonth -eq 1) { $currentYear - 1 } else { $currentYear }

# Adaptive Card形式のメッセージ（Teamsに最適化）
$body = @{
    type        = "message"
    attachments = @(
        @{
            contentType = "application/vnd.microsoft.card.adaptive"
            content     = @{
                '$schema' = "http://adaptivecards.io/schemas/adaptive-card.json"
                type      = "AdaptiveCard"
                version   = "1.4"
                body      = @(
                    @{
                        type   = "TextBlock"
                        text   = "📊 福田会計 ${prevYear}年${prevMonth}月 事業計画レポート"
                        size   = "Large"
                        weight = "Bolder"
                        color  = "Accent"
                    },
                    @{
                        type  = "TextBlock"
                        text  = "報告日: ${currentYear}年${currentMonth}月1日"
                        isSubtle = $true
                        spacing = "None"
                    },
                    @{
                        type = "ColumnSet"
                        columns = @(
                            @{
                                type  = "Column"
                                width = "stretch"
                                items = @(
                                    @{
                                        type   = "TextBlock"
                                        text   = "売上"
                                        weight = "Bolder"
                                    },
                                    @{
                                        type = "FactSet"
                                        facts = @(
                                            @{ title = "目標"; value = "¥$([string]::Format('{0:N0}', $targetSales))" },
                                            @{ title = "実績"; value = "¥$([string]::Format('{0:N0}', $actualSales))" },
                                            @{ title = "進捗率"; value = "${salesRate}% ${salesEmoji}" }
                                        )
                                    }
                                )
                            },
                            @{
                                type  = "Column"
                                width = "stretch"
                                items = @(
                                    @{
                                        type   = "TextBlock"
                                        text   = "顧問先"
                                        weight = "Bolder"
                                    },
                                    @{
                                        type = "FactSet"
                                        facts = @(
                                            @{ title = "新規目標"; value = "${targetNewClients}件" },
                                            @{ title = "新規実績"; value = "${actualNewClients}件 ${clientEmoji}" },
                                            @{ title = "解約";     value = "${actualCanceled}件" },
                                            @{ title = "合計";     value = "${totalClients}件" }
                                        )
                                    }
                                )
                            }
                        )
                    },
                    @{
                        type      = "TextBlock"
                        text      = $remarksText  # 備考・コメント（任意）
                        wrap      = $true
                        isVisible = ($remarksText -ne "")
                    }
                )
            }
        }
    )
} | ConvertTo-Json -Depth 20

$response = Invoke-RestMethod -Uri $webhookUrl -Method Post -Body $body -ContentType "application/json; charset=utf-8"
Write-Output "Teams投稿完了: $($today.ToString('yyyy/MM/dd HH:mm'))"
```

---

## Step 5: ファイルを閉じて終了

```powershell
$wb.Close($false)
$excel.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
```

---

## Teams Incoming Webhook の設定手順

1. Teamsで投稿先チャネルを開く
2. チャネル名の横の「…」→「コネクタ」→「受信 Webhook」→「構成」
3. 名前（例：`福田会計 事業計画Bot`）と任意のアイコンを設定
4. 「作成」をクリックしてWebhook URLをコピー
5. スキル内の `$webhookUrl = "YOUR_TEAMS_WEBHOOK_URL"` に貼り付ける

> **注意**: Webhook URLは機密情報のため、Excelファイルや環境変数ファイルに保管し、スクリプトにハードコードしないことを推奨。

---

## 日次自動実行の設定（Windowsタスクスケジューラ）

毎日自動で実行する場合は、Windowsタスクスケジューラで設定する。

```powershell
# タスク登録コマンド（管理者PowerShellで実行）
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-NonInteractive -File C:\fukuda\update_business_plan.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName "福田会計_事業計画更新" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "事業計画の日次更新とTeams月次投稿" -RunLevel Highest
```

---

## エラー対応

| エラー | 原因 | 対処 |
|--------|------|------|
| `401 Unauthorized` | Webhook URLが無効 | Teamsでウェブフック再作成 |
| `COMException` | Excelが別プロセスで開いている | Excelを閉じてから再実行 |
| `対象行が見つからない` | シートの月列の値が不一致 | A列の値（数値/文字列）を確認 |
| Teams投稿は成功するがカード表示が崩れる | JSONの構造エラー | `ConvertTo-Json -Depth` の値を増やす |

---

## 完了報告

実行後にユーザーへ以下を報告する：

1. 更新した月・実績値の概要
2. 目標対比（売上進捗率・顧問先新規獲得進捗）
3. Teams投稿の実施有無（月初の場合は投稿結果）
4. 次回更新推奨日
