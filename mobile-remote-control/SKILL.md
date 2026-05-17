---
name: mobile-remote-control
description: スマートフォンからClaude Codeをリモート操作するためのセットアップガイド。「スマホからClaudeCodeを使いたい」「Remote Control」「リモートコントロール」「スマホ接続」「モバイルからClaude Code」などのキーワードが出た場合はこのスキルを参照する。
---

# スマホから Claude Code を使う（Remote Control）

## 概要

Claude Code の **Remote Control** 機能を使うと、自宅PCで動かしているClaude Codeをスマートフォンの Claude アプリから操作できる。

## 必要なもの

- PC（Claude Code がインストール済み）
- スマートフォン（Claude アプリ）
- Claude **Pro プラン**以上（無料プランでは使用不可）

## 基本的な使い方

### Step 1: PCでRemote Controlを有効にして起動

```bash
claude --remote-control
```

セッション名を付ける場合：

```bash
claude --remote-control "自宅PC"
```

起動すると接続用URLが発行される（例: `https://claude.ai/remote/xxxx`）。

### Step 2: スマホのClaudeアプリで接続

1. スマホで Claude アプリを開く
2. 発行されたURLをタップ（またはコピペ）
3. 即時接続完了

### 注意点

- **起動のたびに新しいURLが発行される**。毎回URLを確認する必要がある
- PCとスマホが同じネットワークにある必要はない（インターネット経由で接続）
- レスポンス速度は通常のClaude Codeとほぼ同じ

---

## URL自動通知の設定

毎回URLをコピーするのが面倒な場合、起動時にURLを自動でメール送信する仕組みを作れる。

### 起動スクリプト（メール通知付き）

`start-remote.sh` を適当な場所（例: `~/start-remote.sh`）に作成する：

```bash
#!/bin/bash
# Claude Code をRemote Controlで起動し、発行されたURLをメールで送信する

SESSION_NAME="${1:-自宅PC}"
TO_EMAIL="your-email@example.com"   # ← 自分のメールアドレスに変更

# Remote Control URLをキャプチャしながら起動
claude --remote-control "$SESSION_NAME" 2>&1 | tee >(
    # URLが出力されたら即座にメール送信
    grep -m1 "https://claude.ai/remote/" | while read -r url; do
        echo "Remote Control URL: $url" | mail -s "Claude Code 起動 - $SESSION_NAME" "$TO_EMAIL"
    done
) 
```

```bash
chmod +x ~/start-remote.sh
~/start-remote.sh
```

### Slack通知版

```bash
#!/bin/bash
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
SESSION_NAME="${1:-自宅PC}"

claude --remote-control "$SESSION_NAME" 2>&1 | tee >(
    grep -m1 "https://claude.ai/remote/" | while read -r url; do
        curl -s -X POST "$SLACK_WEBHOOK" \
            -H 'Content-type: application/json' \
            --data "{\"text\":\"Claude Code 起動: $url\"}"
    done
)
```

---

## トラブルシューティング

| 症状 | 原因と対処 |
|------|----------|
| `Remote Control is not available inside a remote session` | すでにリモートセッション内で実行している。ローカルPCのターミナルで実行する |
| スマホアプリに接続項目が表示されない | アプリのバージョンを最新にする |
| 接続できない | ProプランであることをAnthropicサイトで確認する |
| URLが表示されない | `claude --remote-control --debug` で詳細ログを確認する |
