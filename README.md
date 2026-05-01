# Claude Code スキル集

税理士法人業務で使用するClaude Codeスキルのリポジトリです。

## スキル一覧

### monthly-tax-audit（月次税務監査レビュー）

法人税の月次税務監査を支援するスキル。

**機能：**
- 仕訳日記帳CSV（Shift-JIS）から要確認仕訳を自動抽出
- 前期の監査不明点ファイルと照合し、再発・類似案件を特定
- 当期の監査不明点一覧表（xlsx）に月別シートとして自動転記

**対応チェック項目：**
- 福利厚生費（弁当代・食事代の消費税区分）
- 修繕費（資本的支出の可能性・重複計上の疑い）
- 建設仮勘定（固定資産計上の判断・資料確認）
- 外注加工費（固定資産計上の妥当性）
- 寄付金・出資金・匿名投資組合

**判断ルール（確認済み）：**
- 弁当代 → 軽減税率8%（食事代・外食は10%）
- 地代家賃（事業所貸付）→ 課対仕入10%で正しい
- 摘要に「修理代」とあるものは修繕費処理でOK
- 摘要のみでは判断できない大口修繕費は指摘不要
- 小額の寄付金（概ね50,000円未満）は指摘不要

### business-plan-teams-update（事業計画書PPT更新・Teams月次投稿）

福田会計の事業計画書PPTをAsanaのタスク進捗と連携しながら毎日更新し、毎月1日にMicrosoft TeamsチャネルへサマリーをIncoming Webhookで投稿するスキル。

**機能：**
- AsanaのプロジェクトからタスクKPI・進捗率を取得
- 事業計画書PPTの指定スライドを毎日自動更新（python-pptx）
- 毎月1日にTeams Incoming WebhookへAdaptive Card形式でサマリーを投稿
- Windowsタスクスケジューラによる日次自動実行をサポート

**使用技術：**
- python-pptx（PPT操作）
- Asana REST API
- Microsoft Teams Incoming Webhook

## インストール方法

スキルファイルを `~/.claude/skills/` 配下に配置してください。

```bash
cp -r monthly-tax-audit ~/.claude/skills/
cp -r business-plan-teams-update ~/.claude/skills/
```
