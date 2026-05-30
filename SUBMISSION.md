# Anthropic公式プラグインディレクトリ申請手順

**作成日**: 2026-05-30
**対象 repo**: https://github.com/suirindo/netsujo-aio-seo
**申請先**: anthropics/claude-plugins-official

---

## 申請方法(2026-05-30 時点)

Anthropic公式は2つの申請ルートを提供:

### 推奨:申請フォーム経由(飯田さん手動)

```
https://clau.de/plugin-directory-submission
```

### フォームに記入する内容

下記をコピーして貼り付けてください:

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

## 代替案: GitHub PR 経由

将来的に直接 PR を提出する場合の構造:

`anthropics/claude-plugins-official` に `external_plugins/netsujo-aio/` を追加:

```
external_plugins/netsujo-aio/
├── .claude-plugin/
│   └── plugin.json
└── README.md (or symlink)
```

`plugin.json` の中身:

```json
{
  "name": "netsujo-aio",
  "description": "Production-tested AIO/SEO toolkit for Next.js + Strapi + Japanese sites. GSC audit, JSON-LD generation, llms.txt for AI search, 3-gate review. Battle-tested on miyakodeit.com and netsujo.jp.",
  "author": {
    "name": "Netsujo Inc.",
    "url": "https://netsujo.jp"
  },
  "source": {
    "source": "github",
    "repo": "suirindo/netsujo-aio-seo"
  }
}
```

ただし第三者がforkして直接PRを出すのが正規ルートかは公式に明記されていないため、**まず申請フォーム経由**が安全。

---

## 申請後の流れ(推定)

Anthropic team の審査:
- 品質チェック(SKILL.md の妥当性、scripts の動作)
- セキュリティチェック(外部通信、認証情報の扱い)
- ライセンス確認(MIT OK)
- ドキュメント整備度

審査期間: 既存例から推定で **2-4週間**

承認されると `external_plugins/netsujo-aio/` に追加され、世界中の Claude Code ユーザーが下記でインストール可能になる:

```
/plugin install netsujo-aio@claude-plugins-official
```

---

## 並行で実施すべきこと

審査期間中も以下を進める:

1. **v0.1.0 を miyakodeit / netsujo.jp で dogfooding**
   - 既存スクリプトを skill 経由で再実行して整合性確認
   - 不足機能を v0.2.0 ロードマップに追加
2. **対外発信**
   - X / note / Zenn で公開告知
   - PR TIMES「Netsujo、京都発のAIO/SEO Claude Code Plugin を公開」
   - みやこでITイベントで紹介LT
3. **v0.2.0 開発**
   - 残り JSON-LD 系 5 skill
   - GA4 配線系 3 skill
   - 品質ゲート系 4 skill
4. **README英文校正**(国際展開を考慮)

---

## 承認されない場合の対策

仮に審査NGの場合:
- Anthropic からのフィードバックを反映
- 独立 marketplace として運用継続(`suirindo/netsujo-aio-seo` 単独)
- claude-seo / opkod-france と同様、コミュニティ marketplace として並立

OSS として広く使われればAnthropic公式に入らなくても価値は十分。

---

## 申請後の追跡

- フォーム送信後、確認メールが届く想定 → スレッド管理
- 1ヶ月応答なければリマインド
- 承認されたら Discord 通知 + 飯田さんに即報告
- README に「Anthropic公式ディレクトリ掲載」バッジ追加
