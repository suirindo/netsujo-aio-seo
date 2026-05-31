# Japanese Line Break Rules (禁則処理 + 文節分離防止)

Reference for the `h1-mobile-check` skill. Covers JIS X 4051 kinsoku rules, particle
classification, bunsetsu segmentation heuristics, and the `<br />` insertion algorithm.

## 1. 禁則処理 (Kinsoku)

Kinsoku is the Japanese typesetting rule that bans certain characters from appearing
at the start (gyoutou, 行頭) or end (gyoumatsu, 行末) of a wrapped line.

### 1.1 行頭禁則文字 (cannot start a line)

Closing brackets, punctuation, small kana, and prolonged sound mark:

```
、 。 ， ． ） 〕 ］ ｝ 〉 》 」 』 】 〗 〙 〛
ゝ ゞ ヽ ヾ ー ァ ィ ゥ ェ ォ ッ ャ ュ ョ ヮ
ぁ ぃ ぅ ぇ ぉ っ ゃ ゅ ょ ゎ
々 ? ! ： ；
```

### 1.2 行末禁則文字 (cannot end a line)

Opening brackets:

```
「 『 （ 【 ［ 〈 《 〔 ｛ 〘 〚
```

These are handled by browsers automatically via `word-break: keep-all` semantics,
but they do not cover the rules below.

## 2. 助詞分離防止 (particle-head ban)

Browsers do **not** enforce particle-head bans by default. This is the leading cause
of awkward Japanese H1 wraps and is the rule that this skill exists to enforce.

### 2.1 Banned line-head particles (Critical)

| Particle | Role | Example bad wrap |
|---|---|---|
| を | direct object marker | `京都でIT勉強会` ↵ `を探している` |
| が | subject marker | `天気` ↵ `が良い` |
| に | locative/dative | `京都` ↵ `に住む` |
| で | instrumental/locative | `Vercel` ↵ `でデプロイ` |
| と | conjunction/quotative | `田中さん` ↵ `と話した` |
| は | topic marker | `この記事` ↵ `はまとめ` |
| から | source/since | `昨日` ↵ `から始めた` |
| まで | terminus | `明日` ↵ `までに完成` |
| より | comparison | `想定` ↵ `よりも速い` |
| へ | direction | `京都` ↵ `へ向かう` |
| の | genitive (only when followed by noun) | `京都` ↵ `のIT` |

### 2.2 Soft-banned line-head particles (Warning)

`や`, `も`, `ね`, `よ`, `わ`, `か` — context dependent. Flag as Warning, not Critical.

## 3. 動詞分離防止 (verb stem/ending ban)

Verb stems must not be split from their inflectional endings. Common offenders:

| Stem | Endings |
|---|---|
| もたら | す, した, して, される |
| はじま | る, った, って |
| つく | る, った, って, られる |
| う | ける, けた |
| まと | める, まった |
| はじめ | る, た, て |

The 2026-04-08 incident broke `もたら` from `す` and is the canonical example.

## 4. 文節 (bunsetsu) segmentation heuristic

A bunsetsu is the minimal meaning-bearing unit in Japanese — one content word plus
its trailing particles/auxiliaries. Full morphological analysis (MeCab/Sudachi) is
overkill for headlines; a rule-based segmenter works for inputs under 40 chars.

### 4.1 Rule

Scan left to right. A bunsetsu boundary occurs **after**:

1. A particle from the head-ban list (§2.1) when followed by a content character
2. A punctuation mark (`・`, `、`, `〜`, `—`, `:`, `｜`)
3. A katakana → kanji transition (`ブロックチェーン` | `企業`)
4. A kanji → hiragana transition where the hiragana is a known particle (§2)

### 4.2 Worked example

Input: `AI×ブロックチェーンが企業にもたらす5つの変革`

Boundaries detected:

| Position | Reason |
|---|---|
| after `AI×ブロックチェーン` (10) | katakana → particle `が` |
| after `が` (11) | particle followed by kanji |
| after `企業` (13) | kanji → particle `に` |
| after `に` (14) | particle followed by hiragana verb |
| after `もたらす` (18) | verb stem+ending complete, followed by digit |

Bunsetsu list: `AI×ブロックチェーンが` / `企業に` / `もたらす` / `5つの` / `変革`

## 5. `<br />` 挿入位置決定アルゴリズム

Given heading H, viewport-implied max line length M (defaults to 15 chars):

```
def suggest_break(H, M=15):
  bunsetsu = segment_bunsetsu(H)
  cumulative = []  # prefix lengths after each bunsetsu
  acc = 0
  for b in bunsetsu:
    acc += len(b)
    cumulative.append(acc)

  candidates = []
  for i, left_len in enumerate(cumulative[:-1]):
    right_len = len(H) - left_len
    # Hard constraints
    if left_len > M or right_len > M:
      continue
    if H[left_len] in HEAD_BAN_PARTICLES:
      continue
    if ends_with_tail_ban(H[:left_len]):
      continue
    if splits_verb(H, left_len):
      continue
    # Score: prefer balance
    balance = abs(left_len - right_len)
    candidates.append((balance, i, left_len, right_len))

  candidates.sort()  # lowest balance first
  return [(H[:l], H[l:], (l, r)) for _, _, l, r in candidates[:3]]
```

### 5.1 Worked example continued

For `AI×ブロックチェーンが企業にもたらす5つの変革` (20 chars, M=15):

| Boundary after | Left | Right | Balance | Particle head? | Verb split? | Verdict |
|---|---|---|---|---|---|---|
| `…が` (11) | 11 | 9 | 2 | no (`企業` starts with kanji) | no | **OK, balance 2** |
| `企業に` (14) | 14 | 6 | 8 | no (`もたらす` starts with hira verb) | no | OK, balance 8 |
| `もたらす` (18) | 18 | 2 | 16 | rejected — left > M | — | reject |

Top candidate: `AI×ブロックチェーンが<br />企業にもたらす5つの変革`. The skill ranks
this above the `企業に` boundary because of better balance.

## 6. CLS considerations

`<br />` insertions change the rendered height of H1 on mobile and can shift LCP/CLS.
After adding a `<br />`, re-measure with Lighthouse or `claude-seo:seo-technical`.
A 2-line H1 at 32px base font typically adds ~40px height, which is acceptable when
the H1 sits above the fold image (no CLS impact since it pushes content, not media).

## 7. References

- JIS X 4051:2004 — 日本語文書の組版方法
- W3C JLREQ — https://www.w3.org/TR/jlreq/
- CSS `line-break: strict` — enforces kinsoku but not particle-head bans
- netsujo monorepo `CLAUDE.md` — 見出し改行ルール (project-level enforcement)
