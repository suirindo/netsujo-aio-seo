# Netsujo AIO/SEO Skills for Claude Code

> Production-tested AIO/SEO toolkit for **Next.js App Router + Strapi v5 + Japanese (CJK) sites**.
> Battle-tested on [miyakodeit.com](https://www.miyakodeit.com) and [netsujo.jp](https://netsujo.jp).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://claude.ai/claude-code)
![Version](https://img.shields.io/badge/version-0.2.0--dev-orange)
![Skills](https://img.shields.io/badge/skills-7%2F12-blue)

## What this is

`netsujo-aio-seo` is a Claude Code plugin marketplace that packages the AIO/SEO patterns developed and dogfooded at [Netsujo Inc.](https://netsujo.jp) over 6+ months on production sites with real Google Search Console signals and ChatGPT citation evidence.

Unlike generic SEO plugins, this one is opinionated for:
- **Next.js 15 App Router** + Server/Client Component patterns
- **Strapi v5** Document Service API
- **Japanese sites** (H1 mobile 375px breaking rules, half-width space between ASCII and CJK, JSON-LD `inLanguage: "ja"`)
- **AIO/GEO** for ChatGPT / Perplexity / Gemini / Google AI Overviews

## Why use this

| Problem | This plugin's answer |
|---|---|
| "Our FAQ schema isn't appearing as rich result" | `jsonld-faqpage` validates against Schema.org spec + Google constraints, including the often-missed "no duplicate questions across pages" rule |
| "We want ChatGPT to recommend our site" | `llms-txt-generator` enforces consistency across llms.txt, Speakable JSON-LD, connpass description, X bio — the 5 surfaces ChatGPT actually reads |
| "GSC says Discovered, not indexed for 30 URLs" | `gsc-weekly-audit` catches this in the first scan, with battle-tested patterns from real incidents (see [BATTLE_TESTED.md](BATTLE_TESTED.md)) |
| "Our Japanese H1 breaks oddly on mobile" | `h1-mobile-check` (coming v0.2) enforces the 15-char H1 limit with `<br />` placement validation |
| "Different SEO advisors give different scores" | `three-gate-review` runs CTO / Designer / CEO subagents in parallel for objective approval |

## Installation

### Via Claude Code marketplace (recommended)

```
/plugin marketplace add suirindo/netsujo-aio-seo
/plugin install netsujo-aio@netsujo-aio-seo
```

### Verify installation

```
/plugin list
```

You should see `netsujo-aio` in the list.

## Quick start

After installation, in a Next.js project:

```
/aio-audit https://your-site.com
```

This runs:
1. GSC weekly audit (requires GSC credentials, see [SETUP.md](SETUP.md))
2. JSON-LD validation across all pages
3. llms.txt consistency check
4. CTR low pages report

## Skills included (7 skills shipped / 5 planned)

### Audit & diagnosis

- **`gsc-weekly-audit`** — Google Search Console comprehensive audit (8 checks)
- **`gsc-url-inspect`** *(v0.2 planned)* — One-shot URL inspection for new routes
- **`sitemap-resubmit`** *(v0.2 planned)* — Submit sitemap.xml via Sitemaps API

### Structured data (JSON-LD)

- **`jsonld-faqpage`** — FAQPage JSON-LD with cross-page duplicate detection
- **`jsonld-organization`** — Organization JSON-LD with sameAs auto-completion (logo dimension validation, Google rich results)
- **`jsonld-article`** — Article / BlogPosting / NewsArticle JSON-LD (subtype auto-detect, ISO 8601 enforcement, batch generation)
- **`jsonld-event`** *(v0.2 planned)* — Event JSON-LD (Online/Offline/Mixed)
- **`jsonld-breadcrumb`** *(v0.2 planned)* — BreadcrumbList generation
- **`jsonld-speakable`** *(v0.2 planned)* — WebPage + SpeakableSpecification

### AIO/GEO

- **`llms-txt-generator`** — Generate + verify llms.txt for AI search citation

### GA4 *(v0.2 planned)*

- **`ga4-custom-dimensions`** — Register 12 standard custom dimensions
- **`ga4-tracking-wiring`** — Wire `trackCTAClick` / `trackOutboundLink`

### Quality gates

- **`h1-mobile-check`** — 375px H1 break validation with bunsetsu-aware `<br />` suggestion
- **`jp-ascii-space-fix`** — Context-aware remover of half-width spaces between ASCII and CJK (skips code blocks, HTML attributes)
- **`three-gate-review`** *(v0.2 planned)* — CTO / Designer / CEO subagent review

## Roadmap

- **v0.1.0** (2026-05): 3 skills MVP — gsc-weekly-audit / jsonld-faqpage / llms-txt-generator
- **v0.2.0 phase 1** (2026-06, current): 7 skills total — adds jsonld-organization / jsonld-article / h1-mobile-check / jp-ascii-space-fix
- **v0.2.0 phase 2** (2026-07): 12 skills total — adds 5 remaining (jsonld-event / jsonld-breadcrumb / jsonld-speakable / ga4-custom-dimensions / ga4-tracking-wiring / three-gate-review / gsc-url-inspect / sitemap-resubmit)
- **v0.2.0 release** (2026-07): Anthropic claude-plugins-community submission
- **v1.0.0** (2026-10): Production-ready with `netsujo-aio-strapi` sub-package

## Relationship to other plugins

This plugin **complements** rather than competes with:

- [**claude-seo**](https://github.com/AgriciDaniel/claude-seo) (AgriciDaniel) — Use `/seo audit` for broad SEO; use `netsujo-aio:gsc-weekly-audit` for GSC-specific deep diagnostics + Japanese site rules
- [**security-guidance**](https://github.com/anthropics/claude-plugins-official) (Anthropic) — Use for security review of API integrations
- [**strapi-plugin-dev**](https://github.com/opkod-france/opkod-claude-code-plugins) (OPKOD France) — Use for Strapi v5 plugin scaffolding; this plugin handles the SEO side of Strapi-rendered pages

## Battle-tested incidents

This plugin codifies lessons from real production incidents. Examples:

- **2026-05-10**: Fake sitemap entry `/blog/meetup-anxiety` shipped. Caught 7 days late → now caught in first scan
- **2026-05-11**: `/blog` title double-applied from layout template → now cross-checked
- **2026-05-22**: `/faq` and `/guides/kyoto-mokumoku` had duplicate FAQ questions → now detected by `jsonld-faqpage --check-duplicates`
- **2026-05-24**: New routes `Discovered, not indexed` → solved with weekly URL Inspection automation

See [BATTLE_TESTED.md](BATTLE_TESTED.md) for the full incident log and how the skill prevents recurrence.

## Authentication setup

Most skills require API credentials. See [SETUP.md](SETUP.md):

- Google Cloud project with Search Console API enabled
- Service account JSON at `~/.config/gcloud/gsc-credentials.json`
- (Optional) Discord webhook for notifications
- (Optional) GA4 property ID + measurement ID

## Contributing

Pull requests welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) (TBA v0.2).

For issues with specific skills, open an issue with:
- Skill name and version
- Reproduction site (or sanitized example)
- Expected vs actual behavior
- Claude Code version (`claude --version`)

## License

MIT © 2026 [Netsujo Inc.](https://netsujo.jp)

## About Netsujo Inc.

Netsujo is a Kyoto-based BizDev company specializing in Web3, AI, and software implementation. We run [みやこでIT](https://www.miyakodeit.com), Kyoto's largest IT engineer community (564 members, 155+ events).

This plugin packages the patterns we developed to keep our own sites GSC-clean and AI-citable. We hope it helps yours too.

- Website: https://netsujo.jp
- Community: https://www.miyakodeit.com
- Contact: [t-iida@netsujo.jp](mailto:t-iida@netsujo.jp)
