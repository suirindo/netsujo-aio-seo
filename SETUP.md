# Setup

Authentication and prerequisites for `netsujo-aio-seo` skills.

## Prerequisites

- **Python 3.10+**(needed by audit scripts)
- **pnpm or npm**(needed by Next.js helpers)
- **gh CLI**(needed for some GitHub-integrated workflows)

## Google Search Console API

Required by: `gsc-weekly-audit`, `gsc-url-inspect`, `sitemap-resubmit`

### Steps

1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable **Search Console API** for the project
3. Create a service account: IAM → Service Accounts → Create
4. Generate a JSON key and download it
5. Save the JSON at `~/.config/gcloud/gsc-credentials.json`(or set `GSC_CREDENTIALS_PATH` env var)
6. In Search Console, add the service account email as **Owner** or **Full user** for your property

### Verify

```bash
python3 -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build
creds = service_account.Credentials.from_service_account_file('~/.config/gcloud/gsc-credentials.json'.replace('~', __import__('os').path.expanduser('~')), scopes=['https://www.googleapis.com/auth/webmasters.readonly'])
svc = build('searchconsole', 'v1', credentials=creds)
print(svc.sites().list().execute())
"
```

You should see a list of your verified properties.

## Discord webhook(optional)

Required by:`--discord` flag on audit scripts

### Steps

1. In Discord, open the channel where you want notifications
2. Channel settings → Integrations → Webhooks → New Webhook
3. Copy the URL
4. Set as env var:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

Or pass via CLI:

```bash
python3 scripts/gsc-weekly-audit.py --discord-webhook "https://discord.com/api/webhooks/..."
```

## GA4 setup(for ga4-* skills, v0.2)

Required by: `ga4-custom-dimensions`, `ga4-tracking-wiring`

### Steps

1. Note your GA4 Measurement ID(format: `G-XXXXXXXXXX`)from GA4 Admin → Data Streams
2. Note your Property ID(format: 9-10 digits)from GA4 Admin → Property Settings
3. Enable Google Analytics Admin API in your GCS project
4. Add the same service account from GSC setup to GA4: Admin → Property Access Management → Add user with `Viewer` role

### Env vars

```bash
export GA4_MEASUREMENT_ID="G-XXXXXXXXXX"
export GA4_PROPERTY_ID="123456789"
```

## Site-specific config

Each skill can read from `.aio-config.json` in your project root:

```json
{
  "site": "sc-domain:example.com",
  "siteUrl": "https://example.com",
  "language": "ja",
  "criticalCanonicalPaths": ["/blog", "/events", "/faq"],
  "discordWebhook": "https://discord.com/api/webhooks/...",
  "topUrlsFile": "docs/seo/top-urls.txt"
}
```

The skills auto-detect this file. CLI flags override.

## Troubleshooting

### "Search Console API has not been used"

Enable the API in GCS console:
https://console.developers.google.com/apis/api/searchconsole.googleapis.com/overview

Wait 1-2 minutes for activation, then retry.

### "URL is unknown to Google"

Normal for new URLs. Run `gsc-url-inspect` after the sitemap is resubmitted. URLs typically transition to `Discovered → Indexed` within hours when sitemap is healthy.

### "Permission denied"on credentials file

```bash
chmod 600 ~/.config/gcloud/gsc-credentials.json
```

### Python version too old

```bash
brew install pyenv
pyenv install 3.12.7
pyenv global 3.12.7
python3 --version  # Should show 3.12.7
```
