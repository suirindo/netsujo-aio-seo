# Anthropic コミュニティマーケットプレイス申請手順

**作成日**: 2026-05-30 / **最終更新**: 2026-05-31(v0.2.0 12/12 skills 達成)
**対象 repo**: https://github.com/suirindo/netsujo-aio-seo
**申請先カタログ**: `anthropics/claude-plugins-community`（公式コミュニティカタログ）

---

## 0. 事前 smoke test 結果（2026-05-31 実施・v0.2.0 12 skills）

ローカル marketplace 経由でのインストール検証は **OK**。Claude Code v2.1.158 で確認。

```bash
$ claude plugin marketplace add /Users/tomohiro/netsujo/netsujo-aio-seo
✔ Successfully added marketplace: netsujo-aio-seo

$ claude plugin install netsujo-aio@netsujo-aio-seo --scope user
✔ Successfully installed plugin: netsujo-aio@netsujo-aio-seo

$ claude plugin details netsujo-aio
netsujo-aio 0.2.0
  Component inventory
    Skills (12)  ga4-custom-dimensions, ga4-tracking-wiring, gsc-weekly-audit,
                 h1-mobile-check, jp-ascii-space-fix, jsonld-article,
                 jsonld-breadcrumb, jsonld-event, jsonld-faqpage,
                 jsonld-organization, jsonld-speakable, llms-txt-generator
  Projected token cost
    Always-on:   ~2,521 tok added to every session

$ claude plugin tag --dry-run ./plugins/netsujo-aio
✔ Would create tag netsujo-aio--v0.2.0 at HEAD
```

`plugin.json` / `marketplace.json` の整合性、SKILL.md フロントマター(12/12)、トークンコスト試算、Python syntax(12/12 scripts)すべて妥当。

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
Version:             0.2.0

Description:
Production-tested AIO/SEO toolkit (12 skills) for Next.js + Strapi + Japanese sites. Battle-tested on miyakodeit.com (564 community members, 155+ events) and netsujo.jp.

Audit & diagnosis:
- gsc-weekly-audit: Google Search Console comprehensive audit (8 checks, GitHub Actions weekly cron)

Structured data (JSON-LD, full suite):
- jsonld-faqpage: FAQPage with cross-page duplicate detection
- jsonld-organization: Organization with sameAs auto-expansion + logo dimension validation
- jsonld-article: Article / BlogPosting / NewsArticle subtype auto-detect + batch generation
- jsonld-event: Event with Online/Offline/Mixed attendance modes
- jsonld-breadcrumb: BreadcrumbList with Next.js App Router auto-derivation + XSS-safe inline JSON
- jsonld-speakable: WebPage + SpeakableSpecification with llms.txt consistency verification

AI search optimization (GEO):
- llms-txt-generator: generate + verify llms.txt across 5 surfaces (Speakable, connpass, X bio)

GA4 wiring:
- ga4-custom-dimensions: register 12 standard dimensions via Admin API (idempotent)
- ga4-tracking-wiring: scaffold trackCTAClick / trackOutboundLink / trackScrollDepth / trackReadComplete

Japanese-specific quality gates:
- h1-mobile-check: 375px H1 break detection with bunsetsu-aware <br /> suggestion
- jp-ascii-space-fix: context-aware ASCII↔CJK half-width space remover

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
- 2026-05-27 half-width space between ASCII and CJK (178 files, 1500+ replacements)

Release timeline:
- v0.1.0 (2026-05): 3 skills MVP
- v0.2.0 (2026-05): 12 skills shipped — this submission
- v0.3.x (2026-07+): three-gate-review / gsc-url-inspect / sitemap-resubmit
- v1.0.0 (2026-10): netsujo-aio-strapi sub-package

Token cost: ~2,521 tokens always-on per session (12 skills); on-invoke 2-3k per skill.
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

## 6. 申請タイミング — **v0.2.0 達成・申請可能**(2026-05-31)

| マイルストーン | 状態 | 日付 |
|---|---|---|
| v0.1.0 MVP(3 skills) | ✅ 完了 | 2026-05-30 |
| v0.2.0 phase 1(7/12 skills) | ✅ merge 済 | 2026-05-31 |
| **v0.2.0 phase 2(12/12 skills)** | ✅ **merge 済** | 2026-05-31 |
| plugin.json/marketplace.json v0.2.0 bump | ✅ 本 PR | 2026-05-31 |
| v0.2.0 git tag 作成 | ⏸ 飯田指示待ち | — |
| 申請フォーム送信 | ⏸ 飯田手動 | — |

申請に必要な要素はすべて揃っています。残るは git tag 作成と飯田さん手動でのフォーム送信のみ。

---

## 7. (旧 v0.2.0 開発ロードマップ — 完了済のため削除)

v0.2.0 で実装した skills は §2 Description 内に記載。残り skills(three-gate-review / gsc-url-inspect / sitemap-resubmit)は v0.3.x にスライド。

---

## 8. v0.2.0 タグ作成手順（申請直前）

v0.2.0 が完成し、申請テキストを書き換えた後に実行:

```bash
cd /Users/tomohiro/netsujo/netsujo-aio-seo
# (1) plugin.json と marketplace.json の version を 0.2.0 に書き換え
# (2) コミット
# (3) タグ作成 + push
claude plugin tag --push ./plugins/netsujo-aio
# → netsujo-aio--v0.2.0 タグ作成 + origin に push
```

GitHub Releases で `netsujo-aio--v0.2.0` を選んで Release 化すると、コミュニティカタログ CI が SHA ピンを更新しやすくなる。

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

## 11. 飯田さんアクションサマリ(申請可能ステータス)

### 即実行可能
1. **本 PR (release/v0.2.0-prep) merge**: plugin.json/marketplace.json v0.2.0 bump + SUBMISSION.md 最新化を本番反映(「merge して」明示で OK)
2. **v0.2.0 タグ作成指示**: merge 完了後、秘書に「`claude plugin tag --push` 実行して」 → `netsujo-aio--v0.2.0` 作成 + origin push
3. **GitHub Release 作成**: GitHub UI で `netsujo-aio--v0.2.0` を選んで Release 化(任意・推奨)

### 飯田さん手動(秘書では実行不可)
4. **§2 Description 最終目視**: §2 の v0.2.0 申請テキストを最終確認
5. **申請フォーム送信**: 下記いずれかにログインして §2 のテキストを貼り付け
   - https://claude.ai/settings/plugins/submit
   - https://platform.claude.com/plugins/submit
6. **送信完了報告**: 秘書に共有 → Discord 通知 + 観測スケジュール登録(月次リマインド)
