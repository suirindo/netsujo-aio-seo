# Anthropic コミュニティマーケットプレイス申請手順

**作成日**: 2026-05-30 / **最終更新**: 2026-05-31
**対象 repo**: https://github.com/suirindo/netsujo-aio-seo
**申請先カタログ**: `anthropics/claude-plugins-community`（公式コミュニティカタログ）

---

## 0. 事前 smoke test 結果（2026-05-31 実施）

ローカル marketplace 経由でのインストール検証は **OK**。Claude Code v2.1.158 で確認。

```bash
$ claude plugin marketplace add /Users/tomohiro/netsujo/netsujo-aio-seo
✔ Successfully added marketplace: netsujo-aio-seo

$ claude plugin install netsujo-aio@netsujo-aio-seo --scope user
✔ Successfully installed plugin: netsujo-aio@netsujo-aio-seo

$ claude plugin details netsujo-aio
netsujo-aio 0.1.0
  Component inventory
    Skills (3)  gsc-weekly-audit, jsonld-faqpage, llms-txt-generator
  Projected token cost
    Always-on:   ~563 tok added to every session

$ claude plugin tag --dry-run ./plugins/netsujo-aio
✔ Would create tag netsujo-aio--v0.1.0 at HEAD
```

`plugin.json` / `marketplace.json` の整合性、SKILL.md フロントマター、トークンコスト試算すべて妥当。

---

## 1. 申請方法（飯田さん手動・2026-05-31 時点）

公式ドキュメントによれば、コミュニティマーケットプレイス審査申請は以下のいずれかのアプリ内フォームから行う。

| 経由 | URL |
|---|---|
| Claude.ai | https://claude.ai/settings/plugins/submit |
| Console | https://platform.claude.com/plugins/submit |

承認されたプラグインは `anthropics/claude-plugins-community` カタログ内の特定コミット SHA に固定され、リポジトリに新しいコミットを push すると CI がピンを自動更新する。

---

## 2. フォームに貼り付ける内容

下記をコピペ:

```
Plugin name:         netsujo-aio
Repository URL:      https://github.com/suirindo/netsujo-aio-seo
Author name:         Tomohiro Iida (Netsujo Inc.)
Author email:        t-iida@netsujo.jp
Author website:      https://netsujo.jp
License:             MIT
Category:            seo

Description:
Production-tested AIO/SEO toolkit for Next.js + Strapi + Japanese sites. Battle-tested on miyakodeit.com (564 community members, 155+ events) and netsujo.jp. Includes GSC weekly audit (8 checks), JSON-LD generation with Schema.org validation, llms.txt generator for AI search optimization (GEO), and 3-gate review workflow (CTO/Designer/CEO subagents). Specialized for Japanese (CJK) sites with H1 mobile breaking rules, half-width space detection, and inLanguage:ja JSON-LD.

Differentiation from claude-seo (AgriciDaniel):
- claude-seo focuses on generic SEO auditing (any framework)
- netsujo-aio focuses on Next.js 15 App Router + Strapi v5 implementation patterns
- Together they are complementary: use claude-seo for diagnosis, netsujo-aio for implementation

Battle-tested incidents (documented in BATTLE_TESTED.md):
- 2026-05-10 fake sitemap entry incident
- 2026-05-11 duplicate title from layout template
- 2026-05-22 cross-page FAQ duplication
- 2026-05-24 Discovered, not indexed for 9 new routes
- 2026-05-26 Japanese H1 mobile break
- 2026-05-27 half-width space between ASCII and CJK

Initial release: v0.1.0 (3 skills MVP)
v0.2.0 planned: 12 skills including full JSON-LD suite + GA4 wiring
```

---

## 3. 申請前ローカル検証コマンド

公式ドキュメントは「申請前に `claude plugin validate` を実行」と書いてあるが、Claude Code v2.1.158 時点で当該サブコマンドは未実装。代替として下記を実行する。

```bash
# (a) plugin.json と marketplace entry の整合性チェック
claude plugin tag --dry-run ./plugins/netsujo-aio

# (b) ローカル marketplace 経由インストールテスト
claude plugin marketplace add $(pwd)
claude plugin install netsujo-aio@netsujo-aio-seo --scope user
claude plugin details netsujo-aio
# Component inventory が想定通り（skills 3 個）なら OK

# (c) JSON マニフェストの構文確認
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
python3 -c "import json; json.load(open('plugins/netsujo-aio/plugin.json'))"

# (d) SKILL.md フロントマター必須フィールド検査
for f in plugins/netsujo-aio/skills/*/SKILL.md; do
  head -10 "$f" | grep -q '^name: ' || echo "Missing name in $f"
  head -10 "$f" | grep -q '^description: ' || echo "Missing description in $f"
done
```

GitHub Actions の `Smoke test` ワークフロー（`.github/workflows/test.yml`）が (c) (d) を CI で毎 push 実行している。

---

## 4. 代替案 — GitHub PR 経由（非推奨）

`anthropics/claude-plugins-community` リポジトリへ直接 PR を出す方法もあるが、現時点では推奨されていない。フォーム経由が正規ルート。

将来的にフォーム以外で出す場合の構造想定:

```
external_plugins/netsujo-aio/
├── .claude-plugin/
│   └── plugin.json
└── README.md
```

---

## 5. 申請後の流れ（推定）

Anthropic team の審査項目:
- 品質チェック（SKILL.md の妥当性、scripts の動作）
- セキュリティチェック（外部通信、認証情報の扱い）
- ライセンス確認（MIT OK）
- ドキュメント整備度（README / SETUP / BATTLE_TESTED 揃いあり）

審査期間: 既存例から推定 **2-4 週間**。

承認されると `anthropics/claude-plugins-community` カタログに追加され、世界中のユーザーが下記でインストール可能になる:

```
/plugin install netsujo-aio@claude-plugins-community
```

---

## 6. 申請のタイミング — v0.1.0 で出すか v0.2.0 まで待つか

| 観点 | v0.1.0 で出す | v0.2.0 まで待つ |
|---|---|---|
| 第一印象 | 3 skills のみ → 「まだ薄い」と見られるリスク | 12 skills → 十分なボリューム |
| ユーザーフィードバック | 早期にもらえる | 遅れる |
| 審査やり直しコスト | 0.1.0 で承認 → 0.2.0 で再審査の可能性 | 1 回で済む |
| 競合プラグイン状況 | claude-seo はすでに 2.0 / 早めに棚に並ぶ価値 | 後出しになる |

**推奨**: v0.1.0 で申請し、審査期間中に v0.2.0 を開発。承認後 v0.2.0 push でカタログピン自動更新（マニフェストの CI 説明と整合）。

---

## 7. 並行で実施すべきこと（審査期間中）

1. **v0.1.0 を miyakodeit / netsujo.jp で dogfooding**
   - 既存スクリプトを skill 経由で再実行して整合性確認
   - 不足機能を v0.2.0 ロードマップに追加
2. **対外発信**
   - X / note / Zenn で公開告知
   - PR TIMES「Netsujo、京都発の AIO/SEO Claude Code Plugin を公開」
   - みやこでITイベントで紹介 LT
3. **v0.2.0 開発**（残り 9 skills）
   - JSON-LD 系 5（organization / article / event / breadcrumb / speakable）
   - GA4 配線系 2（custom-dimensions / tracking-wiring）
   - 品質ゲート系 3（h1-mobile-check / jp-ascii-space-fix / three-gate-review）
4. **README 英文校正**（国際展開を考慮）

---

## 8. v0.1.0 タグ作成手順（飯田さん承認後に実施）

```bash
cd /Users/tomohiro/netsujo/netsujo-aio-seo
claude plugin tag --push ./plugins/netsujo-aio
# → netsujo-aio--v0.1.0 タグ作成 + origin に push
```

GitHub Releases で `netsujo-aio--v0.1.0` を選んで Release 化すると、コミュニティカタログ CI が SHA ピンを更新しやすくなる。

---

## 9. 承認されない場合の対策

- Anthropic からのフィードバックを反映して再申請
- 独立 marketplace として運用継続（`suirindo/netsujo-aio-seo` 単独で `/plugin marketplace add suirindo/netsujo-aio-seo`）
- claude-seo / opkod-france と同様、コミュニティ marketplace として並立

OSS として広く使われれば公式入りしなくても価値は十分。

---

## 10. 申請後の追跡

- フォーム送信後、確認メール（または GitHub Issue / PR）が届く想定 → スレッド管理
- 1 ヶ月応答なければリマインド
- 承認されたら Discord 通知 + 飯田さんに即報告
- README に「Anthropic コミュニティカタログ掲載」バッジ追加（例: `![Claude Plugins Community](https://img.shields.io/badge/claude--plugins--community-listed-blue)`）

---

## 11. 飯田さんアクションサマリ

1. **このリポジトリの最終目視確認**: README / SETUP / BATTLE_TESTED / plugin.json / 3 SKILL.md
2. **v0.1.0 で出すか v0.2.0 まで待つかの判断**（§6 推奨は v0.1.0）
3. （v0.1.0 で出す場合）**v0.1.0 タグ作成指示**: 秘書に「`claude plugin tag --push` 実行して」
4. **申請フォーム送信**: §1 の URL のうちどちらか → §2 のテキストを貼り付け
5. 送信完了したら秘書に共有 → Discord 通知 + 観測スケジュール登録
