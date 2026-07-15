#!/usr/bin/env python3
"""
Build static marketing pages for huloglobal.com/vendure-plugins/

Layout:
  /vendure-plugins/                  — catalog + comparison table + FAQ
  /vendure-plugins/<slug>/           — product page (hero + sticky pricing + features + install + FAQ)
  /vendure-plugins/<slug>/install.sh — runnable install script
  /vendure-plugins/<slug>/docs/      — user manual (generated separately)

Drop dist/vendure-plugins into /var/www/huloglobal/current/dist/client/.
"""
from pathlib import Path
import html
import json
import subprocess
import textwrap


def fetch_npm_version(pkg: str) -> str | None:
    """Best-effort fetch of the latest version on the public npm registry.

    Falls back to the hardcoded value in the PLUGINS table when the
    network is unavailable, so the build still works offline."""
    try:
        out = subprocess.check_output(
            ['npm', 'view', pkg, 'version'],
            stderr=subprocess.DEVNULL, timeout=8,
        )
        v = out.decode().strip()
        return v or None
    except Exception:
        return None

HERE = Path(__file__).parent
OUT = HERE / 'dist' / 'vendure-plugins'

ASTRO_CSS = '/_astro/index@_@astro.CpJRZGi5.css'
BUY_BASE = 'https://elite.charity/licence/buy'
CHECKOUT_URL = 'https://elite.charity/licence/checkout'

CURRENCIES = {
    'GBP': {'monthly': '£9.95',  'lifetime': '£199', 'symbol': '£',  'label': 'GBP — British pound'},
    'USD': {'monthly': '$12.99', 'lifetime': '$249', 'symbol': '$',  'label': 'USD — US dollar'},
    'EUR': {'monthly': '€11.95', 'lifetime': '€229', 'symbol': '€',  'label': 'EUR — Euro'},
    'AUD': {'monthly': 'A$19.95','lifetime': 'A$379','symbol': 'A$', 'label': 'AUD — Australian dollar'},
    'CAD': {'monthly': 'C$17.95','lifetime': 'C$339','symbol': 'C$', 'label': 'CAD — Canadian dollar'},
}

PLUGINS = [
    {
        'slug': 'email-tracking',
        'pkg': '@huloglobal/vendure-plugin-email-tracking',
        'class': 'EmailTrackingPlugin',
        'version': '0.8.2',
        'title': 'Email Tracking',
        'tagline': 'Per-link transactional email tracking with human-vs-machine classification, sensitive-link redaction and a per-order activity timeline.',
        'description': (
            'Drop-in tracker for every email your Vendure server sends. Wraps the '
            '`@vendure/email-plugin` pipeline plus a service for ad-hoc sends. '
            'Records every send, open and click as a raw event — never deduped — '
            'so the underlying audit trail is always intact. Each link in each '
            'email gets its own opaque token so the click handler can identify '
            '**exactly which link was clicked** (invoice view, order view, '
            'password reset, footer terms link) rather than merely "a link was '
            'clicked". Password-reset and invoice-access links are flagged '
            'sensitive so the raw destination never lands in the event log. '
            'Every open + click is classified `human_likely` / `machine_likely` '
            '/ `unknown` with reason codes (Gmail image proxy, Apple Mail Privacy '
            'Protection, Microsoft Safe Links, Proofpoint, Mimecast, Barracuda, '
            'datacentre, VPN, bot UA, …) so you can tell a real customer from a '
            'security scanner.'
        ),
        'features': [
            ('Per-link tokenisation', 'Every clickable link in every email gets a random 32-byte token; the destination is stored server-side. The click endpoint identifies exactly which link was clicked — link_type, link_label, link_text, link_index, template_section, destination host + path — and records it on the event row.'),
            ('Sensitive-link redaction', 'Flag password-reset, invoice-access-token and licence-key URLs with `isSensitive: true`. The raw destination is replaced with `[sensitive: <host>]` in the event log; only the URL hash + host are stored. The redirect still works — the raw destination just never lands on an admin-visible row.'),
            ('Human / machine / unknown classification', 'Every open and click is scored with the SDK\'s built-in classifier. Reason chips surface why an event was flagged machine-likely: `gmail-proxy`, `ampp` (Apple Mail Privacy Protection), `safelinks`, `outlook-proxy`, `proofpoint`, `mimecast`, `barracuda`, `symantec`, `datacentre`, `vpn`, `tor`, `bot-ua`, `headless`, `prefetch`, `scanner-ua`. Raw event count still recorded — the classification is advisory, never the sole basis for a decision.'),
            ('IP enrichment (ip-api.com or ipinfo)', 'Every event ingested triggers an async geo lookup (country, region, city, ASN, organisation, timezone, proxy / VPN / datacentre / mobile flags). Provider is pluggable via `HULO_IP_ENRICHMENT_PROVIDER`. Skips private / loopback / link-local. Never blocks event recording — enrichment happens fire-and-forget.'),
            ('Provider webhook receiver', 'Ingest delivered / bounced / deferred / dropped / complaint / open / click events from Postmark, SendGrid, Mailgun and Amazon SES. Each provider\'s signature scheme is verified; unconfigured providers 401; unknown slugs 404. Idempotent within 24h so retries don\'t double-count.'),
            ('Full open + click history per email', 'Raw events are never deduplicated. Multiple pixel fires from the same recipient create multiple rows; the admin UI groups for display but the underlying audit trail stays intact.'),
            ('Suppression list', 'Hard bounces and complaints auto-add to the suppression table. Subsequent sends are silently skipped and logged as `status=suppressed`.'),
            ('Per-template analytics', 'Open rate, CTR, click-to-open ratio and bounce rate per email type — order-confirmation, OTP, invoice, password-reset and your custom types.'),
            ('Bounce + complaint webhook', 'POST DSN events to `/email-track/bounce` from your postmaster integration for legacy setups.'),
            ('Admin UI: Email Log + per-customer Emails tab', 'Filter by recipient, customer, order, status, type, date range. Expand any row for the full event timeline.'),
            ('Order Activity History panel', 'On every order-detail page: chronological timeline of every transactional email event with classification badges, filters (opens only / clicks only / payment / admin notes), IP-derived location with cautionary banner, CSV export, PDF Evidence Report via short-lived signed URLs, and elevated-permission full-export for legal evidence preservation. Pagination for high-volume customers — 100 events per page with a "Load more" button.'),
            ('CSV + JSON + PDF export', 'CSV (redacted) for daily browsing, JSON via GraphQL for machine processing, PDF Evidence Report ("Order Activity and Delivery Evidence Report") for legal preservation. Sensitive fields respect the redaction rules; full export requires elevated permission.'),
            ('Works with any SMTP transport', 'Gmail, SES, SendGrid, Postmark, Mailgun, raw SMTP. Just plug `TrackingEmailSender()` into your email-plugin config.'),
            ('Graceful degradation', 'No runtime import from invoice / support-ticket / order plugins. Hosts that don\'t have those simply never pass the id; entity foreign-id columns are plain nullable ints. If a table isn\'t there yet, persistence fails silently and the redirect still works via signature verification.'),
        ],
        'endpoints': [
            ('GET',  '/email-track/open/:id.gif',     'Pixel — logs an open then serves a 1×1 GIF'),
            ('GET',  '/email-track/click/:id?u=<url>&s=<sig>', 'Click redirector — verifies HMAC signature, logs event with per-link metadata + classification, then 302s'),
            ('POST', '/email-track/bounce',           'Bounce / complaint webhook — DSN bridge'),
            ('POST', '/email-events/webhook/postmark',  'Postmark event webhook (Basic Auth verified)'),
            ('POST', '/email-events/webhook/sendgrid',  'SendGrid event webhook (ECDSA signature verified)'),
            ('POST', '/email-events/webhook/mailgun',   'Mailgun event webhook (HMAC-SHA256 verified)'),
            ('POST', '/email-events/webhook/ses',       'Amazon SES via SNS (topic ARN allowlist)'),
            ('GET',  '/email-track/log',              'Admin: paginated log with filters'),
            ('GET',  '/email-track/log/summary',      'Admin: status totals tile'),
            ('GET',  '/email-track/log/:id',          'Admin: full detail (incl. opens + clicks arrays)'),
            ('GET',  '/email-track/log/stats/by-template', 'Admin: per-template aggregates (open / click rate, CTR)'),
            ('GET',  '/email-track/log/export.csv',   'Admin: CSV export'),
            ('GET',  '/email-track/suppression',      'Admin: list suppression entries'),
            ('POST', '/email-track/suppression',      'Admin: manually add a recipient'),
            ('DELETE', '/email-track/suppression/:recipient', 'Admin: lift a suppression'),
        ],
    },
    {
        'slug': 'geo-block',
        'pkg': '@huloglobal/vendure-plugin-geo-block',
        'class': 'GeoBlockPlugin',
        'version': '0.6.0',
        'title': 'Geo Block',
        'tagline': '37 region presets, soft-block mode, IP allowlist, audit log, "what-if" simulator.',
        'description': (
            'Per-channel geo-restrictions you can actually understand. Pick from '
            '37 hand-curated region presets (EU, EEA, Schengen, GCC, ANZAC, NATO, '
            'OECD, Commonwealth, English-speaking, MENA, ASEAN, Nordic, …) or '
            'add countries manually. Soft-block mode for "browse-only" markets. '
            'IP allowlist for offices and payment processors. Every block decision '
            'is logged for the admin Stats panel.'
        ),
        'features': [
            ('37 region presets', 'One-click setups: EU, EEA, EFTA, Schengen, Nordic, DACH, Benelux, Balkans, GCC, MENA, ASEAN, APAC, East Asia, South Asia, LATAM, North America, Caribbean, Oceania, ANZ, G7, G20, BRICS, OECD, NATO, Five Eyes, Commonwealth, English-speaking, and more.'),
            ('Per-channel rules', 'Each Vendure channel gets its own rules — perfect for multi-storefront installs (e.g. one UK-only channel, one EU channel).'),
            ('Soft-block (browse-only)', 'Mode toggle: full block hides the storefront entirely; soft mode renders it with a banner explaining you don\'t ship to their country and hiding checkout.'),
            ('IP allowlist with CIDR', 'IPs or IPv4 ranges (`203.0.113.0/24`) that bypass every rule. For your office, oncall, monitoring probes, payment processors.'),
            ('Audit log + stats', 'Every block decision logged with country, region, IP, UA, channel and reason. Admin Stats tab shows top blocked countries, daily series, and reason breakdown.'),
            ('"What-if" simulator', 'Test exactly what your rules will do for a hypothetical visitor — country, UK region, IP — before saving anything to production.'),
            ('Custom block page', 'Per-channel message, optional redirect URL and optional logo URL. Or fall back to sensible defaults per block reason.'),
            ('UK sub-region filter', 'When GB is allowed, optionally restrict to ENG / WLS / SCT / NIR. Driven from the standard ISO subdivision codes.'),
            ('Proxy-aware', 'Reads `cf-ipcountry` / Akamai / Fastly region headers when present. Saves a MaxMind lookup per request.'),
            ('Scheduled maintenance window', 'Plugin option for a date-range lockdown — every visitor is blocked (except the IP allowlist) until the window closes.'),
        ],
        'endpoints': [
            ('GET',  '/geo-block/site-config',     'Public: channel rules the storefront polls'),
            ('GET',  '/geo-block/check',           'Public: per-request decision + reason (logs to audit)'),
            ('GET',  '/geo-block/presets',         'Public: the preset catalogue (37 entries)'),
            ('GET',  '/geo-block/admin/channels',  'Admin: list channels with current rules'),
            ('POST', '/geo-block/admin/save',      'Admin: save a channel\'s rules'),
            ('GET',  '/geo-block/admin/stats',     'Admin: block totals + top countries + daily series'),
            ('POST', '/geo-block/admin/simulate',  'Admin: dry-run a visitor against current rules'),
            ('POST', '/geo-block/admin/gc',        'Admin: prune old audit rows'),
        ],
    },
    {
        'slug': 'visitor-analytics',
        'pkg': '@huloglobal/vendure-plugin-visitor-analytics',
        'class': 'VisitorAnalyticsPlugin',
        'version': '0.8.1',
        'title': 'Visitor Analytics',
        'tagline': 'Self-hosted visitor journey, cart abandonment, product recommendations, search analytics — one plugin, one database, no third party.',
        'description': (
            'Self-hosted analytics that reaches all the way from a visitor\'s '
            'first pageview to a recovered abandoned cart. Journey drawer with '
            'parsed UA + MaxMind geo + heuristic intent labels; cart abandonment '
            'detection with signed recovery links and Slack notifications; '
            'co-view product recommendations (also-viewed, personal, trending); '
            'site-search analytics (top queries, zero-result gaps, search-to-cart '
            'conversion); rage-click and dead-click hot-spot lists. Privacy-first '
            'defaults: DNT respected, IPs anonymised, optional consent gate. '
            'Ships a drop-in storefront JS helper at `/ees/hulo.js` — one script '
            'tag and every event type is wired.'
        ),
        'features': [
            ('Cart abandonment', 'Detects sessions with `cart_snapshot` events but no `checkout_completed` in the abandonment window (default 30 min). Auto-promotes to `converted` when a matching checkout later lands. Signed recovery-link tokens (time-bounded, non-reusable) — `/ees/abandoned-carts/:id/recovery-link` returns a URL you drop into a recovery email. Slack notification for high-value drops.'),
            ('Product recommendations', 'Denormalised `ProductCoView` table rebuilt every 6 hours from `product_view` events, bounded per session to 20 events so bot sessions can\'t skew the table. Three endpoints: `also-viewed` for a product-page rail, `personal` for a homepage/cart rail based on a returning visitor\'s last 10 product views, `trending` for a most-viewed-in-window rail.'),
            ('Site search analytics', 'Zero-schema-cost queries over `search` events. Top queries by volume with average results count, zero-result queries (direct catalogue-gap intel), search-to-cart conversion rate.'),
            ('Journey drawer buffs', 'Rage-click + dead-click hot-spot lists per URL. Per-session heuristic `intent` label (`purchase` / `abandon` / `frustrate` / `consider` / `browse` / `bounce`) — one glance per session in the visitor drawer.'),
            ('Drop-in storefront helper', 'Ships `/ees/hulo.js` — one script tag and every event helper (`cartSnapshot`, `productView`, `search`, `checkoutCompleted`) is on `window.hulo`. Handles batching, `sendBeacon`, auto rage-click + dead-click detection.'),
            ('Configurable conversion goals', 'CRUD a goal with a URL glob (`/checkout/thank-you/*`) and a value. Live matcher tags every pageview that hits the pattern. Dashboard shows completions per goal.'),
            ('Full visitor journey', 'Page views, time-on-page, exit pages, configurable funnel, UTM attribution, bot detection. Per-visitor profile drawer with parsed UA + MaxMind GeoLite2 geo. Survives login — guest and signed-in events share the same visitor id.'),
            ('Privacy-first defaults', 'DNT respected, IPs anonymised to /24 (IPv4) / /48 (IPv6), optional `requireConsent` gate. All three opt-outable per install.'),
            ('Live-now SSE widget', 'Real-time tile on the admin dashboard showing visitors active right now (by country).'),
            ('CSV export', '`/ees/visitors/export.csv?days=N` and `/ees/abandoned-carts/export.csv` for raw event / abandoned-cart data.'),
            ('Admin dashboards', 'Angular admin pages for Abandoned Carts (KPIs, filters, recovery-link mint, CSV export) and Analytics Insights (trending, also-viewed lookup, search analytics, rage/dead-click hot spots).'),
        ],
        'endpoints': [
            ('POST', '/ees/track',                 'Public: ingest a batch of events'),
            ('GET',  '/ees/hulo.js',               'Public: drop-in storefront helper JS (0.8.1)'),
            ('GET',  '/ees/recover-cart?t=…',      'Public: resolve a recovery-link token → cart items'),
            ('GET',  '/ees/recommendations/also-viewed?productId=…', 'Public: co-view recommendations for one product'),
            ('GET',  '/ees/recommendations/personal?visitorId=…',    'Public: personalised recs from visitor history'),
            ('GET',  '/ees/recommendations/trending?hours=…',        'Public: most-viewed products in the window'),
            ('GET',  '/ees/abandoned-carts',       'Admin: paginated list with filters'),
            ('GET',  '/ees/abandoned-carts/summary','Admin: totals + recovery rate + lost value'),
            ('GET',  '/ees/abandoned-carts/:id',   'Admin: detail incl. parsed items'),
            ('POST', '/ees/abandoned-carts/:id/recovery-link', 'Admin: mint signed recovery URL'),
            ('POST', '/ees/abandoned-carts/:id/status', 'Admin: mark recovered / dismissed'),
            ('GET',  '/ees/abandoned-carts/export.csv', 'Admin: CSV export'),
            ('GET',  '/ees/search-analytics/top',   'Admin: top search queries'),
            ('GET',  '/ees/search-analytics/no-results', 'Admin: zero-result queries'),
            ('GET',  '/ees/search-analytics/conversion', 'Admin: search→cart conversion'),
            ('GET',  '/ees/journey/rage-clicks',    'Admin: rage-click hot spots'),
            ('GET',  '/ees/journey/dead-clicks',    'Admin: dead-click hot spots'),
            ('GET',  '/ees/journey/session-summary?visitorId=…', 'Admin: per-session intent labels'),
            ('GET',  '/ees/visitors/summary',      'Admin: top-line counters + daily series'),
            ('GET',  '/ees/visitors/sources',      'Admin: top sources by visits / sessions'),
            ('GET',  '/ees/visitors/top-pages',    'Admin: most-visited URLs'),
            ('GET',  '/ees/visitors/funnel',       'Admin: configurable funnel with drop-offs'),
            ('GET',  '/ees/visitors/exit-pages',   'Admin: top exit pages'),
            ('GET',  '/ees/visitors/live',         'Admin: SSE live-now stream'),
            ('GET',  '/ees/visitors/journey/:visitorId', 'Admin: per-visitor timeline'),
            ('GET',  '/ees/visitors/export.csv',   'Admin: CSV export'),
            ('POST', '/ees/goals',                 'Admin: create a conversion goal'),
            ('GET',  '/ees/goals/stats',           'Admin: per-goal completion stats'),
        ],
    },
]


HEADER = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#0f1419">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/svg+xml" href="/vendure-plugins/logos/hulo-global.svg?v=1">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Hulo Global">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://huloglobal.com/og-image.png">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="https://huloglobal.com/og-image.png">
<meta name="robots" content="index, follow">
<link rel="stylesheet" href="''' + ASTRO_CSS + '''">
<style>
/* Global focus indicator — accessibility */
.vp-section a:focus-visible, .vp-card a:focus-visible, .vp-hero a:focus-visible, .vp-faq summary:focus-visible, button:focus-visible {{
  outline: 2px solid var(--color-accent-500, #f59e0b);
  outline-offset: 3px;
  border-radius: 4px;
}}
/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }}
}}
.vp-hero {{ position: relative; background: linear-gradient(to bottom, var(--color-ink-50, #f8fafc) 0%, #fff 100%); }}
.vp-hero::before {{ content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .35; background-image: radial-gradient(ellipse 70% 50% at 50% 0%, var(--color-accent-100, #fde68a), transparent 60%); }}
/* Corporate brand mark — sits at the top of every hero. Small,
   text-anchored to the logotype so it reads as a clickable badge. */
.vp-brand {{ display: inline-flex; align-items: center; gap: 10px; text-decoration: none; margin-bottom: 24px; }}
.vp-brand svg {{ width: 40px; height: 40px; display: block; border-radius: 10px; box-shadow: 0 1px 3px rgba(15,23,42,.10), 0 2px 8px rgba(15,23,42,.06); }}
.vp-brand-txt {{ font-weight: 700; letter-spacing: -0.01em; color: var(--color-ink-900, #0f172a); font-size: 15px; }}
.vp-brand:hover .vp-brand-txt {{ color: var(--color-accent-600, #d97706); }}
.vp-pill {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 999px; border: 1px solid var(--color-ink-200, #e2e8f0); background: #fff; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: var(--color-ink-600, #475569); }}
.vp-pill::before {{ content: ""; width: 6px; height: 6px; border-radius: 999px; background: var(--color-accent-500, #f59e0b); }}
.vp-section {{ padding: 88px 0; }}
@media (max-width: 768px) {{ .vp-section {{ padding: 56px 0; }} }}
.vp-grid-2 {{ display: grid; grid-template-columns: 1fr; gap: 48px; }}
@media (min-width: 1024px) {{ .vp-grid-2 {{ grid-template-columns: minmax(0, 1fr) 380px; gap: 64px; align-items: start; }} }}
.vp-pricing-aside {{ position: sticky; top: 104px; }}
@media (max-width: 1023px) {{ .vp-pricing-aside {{ position: static; top: auto; margin-top: 8px; }} }}
.vp-price-card {{ border: 1px solid var(--color-ink-100, #e2e8f0); border-radius: 18px; padding: 28px; background: #fff; box-shadow: 0 1px 3px rgba(15,23,42,.05), 0 8px 24px rgba(15,23,42,.04); }}
.vp-price-card + .vp-price-card {{ margin-top: 18px; }}
.vp-price-card.featured {{ border: 2px solid var(--color-accent-500, #f59e0b); padding: 27px; }}
@media (max-width: 767px) {{
    .vp-price-card {{ padding: 22px; }}
    .vp-price-card.featured {{ padding: 21px; }}
    .vp-price-num {{ font-size: 36px !important; }}
    /* Pricing cards side-by-side on small screens so both are above the fold */
    .vp-pricing-aside {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .vp-pricing-aside > .vp-price-card + .vp-price-card {{ margin-top: 0; }}
    .vp-pricing-aside > p {{ grid-column: 1 / -1; }}
}}
@media (max-width: 480px) {{
    .vp-pricing-aside {{ grid-template-columns: 1fr; }}
    .vp-pricing-aside > .vp-price-card + .vp-price-card {{ margin-top: 16px; }}
}}
.vp-price-num {{ font-size: 40px; font-weight: 800; color: var(--color-ink-900, #0f172a); line-height: 1; letter-spacing: -0.025em; }}
.vp-price-num small {{ font-size: 15px; font-weight: 500; color: var(--color-ink-500, #64748b); margin-left: 6px; }}
.vp-trial-num {{ color: var(--color-accent-600, #d97706); }}
.vp-email-input {{
    width: 100%; box-sizing: border-box;
    padding: 12px 14px; min-height: 44px;
    border: 1px solid var(--color-ink-200, #e2e8f0);
    border-radius: 8px;
    font-size: 16px;
    background: #fff;
    color: var(--color-ink-900);
}}
.vp-email-input:focus-visible {{ outline: 2px solid var(--color-accent-500, #f59e0b); outline-offset: 2px; border-color: transparent; }}
.vp-tiny-note {{ font-size: 12px; color: var(--color-ink-500); margin-top: 10px; text-align: center; }}
.vp-feat {{ display: grid; grid-template-columns: 28px 1fr; gap: 16px; padding: 18px 0; border-top: 1px solid var(--color-ink-100, #e2e8f0); }}
.vp-feat:first-of-type {{ border-top: 0; padding-top: 4px; }}
.vp-feat-tick {{ width: 28px; height: 28px; border-radius: 999px; background: var(--color-accent-50, #fffbeb); display: grid; place-items: center; color: var(--color-accent-600, #d97706); }}
.vp-feat h3 {{ font-size: 16px; font-weight: 600; color: var(--color-ink-900); margin: 2px 0 0; line-height: 1.4; }}
.vp-feat p {{ font-size: 14px; color: var(--color-ink-600, #475569); margin: 8px 0 0; line-height: 1.6; }}
.vp-step {{ counter-increment: step; margin-top: 48px; }}
.vp-step:first-of-type {{ margin-top: 56px; }}
.vp-step h3::before {{ content: counter(step); display: inline-block; min-width: 32px; height: 32px; padding: 0 8px; margin-right: 14px; background: var(--color-ink-900); color: #fff; border-radius: 999px; font-size: 15px; font-weight: 700; text-align: center; line-height: 32px; vertical-align: middle; }}
.vp-step h3 {{ font-size: 22px !important; line-height: 1.4; }}
.vp-step > p {{ margin: 12px 0 14px 46px; }}
.vp-code {{ background: #0f172a; color: #f1f5f9; padding: 22px 24px; border-radius: 12px; font-size: 13.5px; line-height: 1.75; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; overflow-x: auto; margin-left: 46px; }}
.vp-code .vp-comment {{ color: #94a3b8; }}
.vp-code .vp-key {{ color: #fbbf24; }}
.vp-code .vp-str {{ color: #86efac; }}
.vp-faq summary {{ font-weight: 600; padding: 22px 0; cursor: pointer; list-style: none; display: flex; justify-content: space-between; align-items: center; font-size: 16px; }}
.vp-faq summary::after {{ content: "+"; font-size: 26px; color: var(--color-ink-400, #94a3b8); transition: transform .15s; }}
.vp-faq details[open] summary::after {{ content: "−"; }}
.vp-faq details {{ border-bottom: 1px solid var(--color-ink-100); }}
.vp-faq details:first-of-type {{ border-top: 1px solid var(--color-ink-100); }}
.vp-faq details p {{ padding: 4px 0 22px; color: var(--color-ink-600); line-height: 1.7; font-size: 15px; }}
.vp-endpoint {{ display: grid; grid-template-columns: 90px 1.2fr 2fr; gap: 16px; padding: 14px 16px; border-top: 1px solid var(--color-ink-100); font-size: 14px; align-items: center; }}
.vp-endpoint:first-of-type {{ border-top: 0; }}
.vp-endpoint .vp-method {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 700; padding: 4px 10px; border-radius: 5px; text-align: center; font-size: 11px; }}
.vp-method.GET {{ background: #dbeafe; color: #1e3a8a; }}
.vp-method.POST {{ background: #dcfce7; color: #14532d; }}
.vp-method.PUT {{ background: #fef3c7; color: #78350f; }}
.vp-method.DELETE {{ background: #fee2e2; color: #7f1d1d; }}
.vp-endpoint code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--color-ink-900); font-size: 13px; }}
.vp-endpoint .vp-desc {{ color: var(--color-ink-600); font-size: 13px; }}
.vp-cards-grid {{ display: grid; grid-template-columns: 1fr; gap: 28px; }}
@media (min-width: 768px) {{ .vp-cards-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
.vp-card {{ display: flex; flex-direction: column; border: 1px solid var(--color-ink-100, #e2e8f0); border-radius: 18px; padding: 32px; background: #fff; box-shadow: 0 1px 3px rgba(15,23,42,.05); transition: transform .15s, box-shadow .15s; }}
.vp-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(15,23,42,.08); }}
.vp-card h3 {{ font-size: 24px; font-weight: 700; color: var(--color-ink-900); line-height: 1.2; margin: 0; }}
.vp-card .vp-card-tagline {{ font-size: 15px; color: var(--color-ink-600); line-height: 1.65; margin: 14px 0 0; }}
.vp-card ul {{ list-style: none; padding: 0; margin: 24px 0 0; }}
.vp-card li {{ display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; font-size: 14px; color: var(--color-ink-700); line-height: 1.5; }}
.vp-card .vp-card-actions {{ margin-top: 28px; padding-top: 24px; border-top: 1px solid var(--color-ink-100); display: flex; align-items: center; gap: 12px; }}

/* Currency picker — proper tap target + visible focus */
.sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }}
.ccy-picker-wrap {{ display: inline-flex; align-items: center; gap: 8px; }}
.ccy-label {{ font-size: 13px; font-weight: 500; color: var(--color-ink-600, #475569); }}
.ccy-select {{
    appearance: none; -webkit-appearance: none;
    padding: 10px 32px 10px 14px;
    min-height: 44px;
    border: 1px solid var(--color-ink-200, #e2e8f0);
    border-radius: 8px;
    background: #fff;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23475569' stroke-width='2.5'><polyline points='6 9 12 15 18 9'/></svg>");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 12px;
    font-size: 14px; font-weight: 500; color: var(--color-ink-700, #334155);
    cursor: pointer;
    line-height: 1.2;
}}
.ccy-select:focus-visible {{
    outline: 2px solid var(--color-accent-500, #f59e0b);
    outline-offset: 2px;
}}
.ccy-select:hover {{ border-color: var(--color-ink-300, #cbd5e1); }}
.ccy-select-mobile {{ font-size: 13px; padding: 8px 28px 8px 12px; min-height: 40px; }}

.mobile-controls {{ display: flex; align-items: center; gap: 12px; }}
.mobile-nav-link {{
    padding: 10px 14px; min-height: 44px;
    display: inline-flex; align-items: center;
    border-radius: 8px;
    background: var(--color-ink-50, #f8fafc);
    color: var(--color-ink-800, #1e293b);
    font-size: 14px; font-weight: 600; text-decoration: none;
    border: 1px solid var(--color-ink-200, #e2e8f0);
}}
.mobile-nav-link:focus-visible {{ outline: 2px solid var(--color-accent-500, #f59e0b); outline-offset: 2px; }}

/* Compatibility matrix */
.vp-compat-wrap {{ overflow-x: auto; }}
.vp-compat {{ border-collapse: collapse; }}
.vp-compat th, .vp-compat td {{ padding: 14px 18px; font-size: 14px; border-top: 1px solid var(--color-ink-100, #e2e8f0); }}
.vp-compat thead th {{ border-top: 0; font-weight: 600; color: var(--color-ink-500, #64748b); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; white-space: nowrap; }}
.vp-compat tbody th {{ font-weight: 600; color: var(--color-ink-900, #0f172a); }}
.vp-compat tbody th a {{ color: inherit; text-decoration: none; }}
.vp-compat tbody th a:hover {{ color: var(--color-accent-600, #d97706); text-decoration: underline; }}
.vp-compat tbody tr:hover {{ background: var(--color-ink-50, #f8fafc); }}
.vp-compat td {{ color: var(--color-ink-700, #334155); }}
.vp-compat-ver {{ font-size: 13px; color: var(--color-ink-900, #0f172a); }}
.vp-compat-ok {{ display: inline-block; padding: 3px 10px; border-radius: 999px; background: #ecfdf5; color: #047857; font-size: 12px; font-weight: 600; white-space: nowrap; }}

/* Catalog comparison: table on desktop, stacked cards on mobile */
.vp-compare-table {{ display: block; }}
.vp-compare-cards {{ display: none; }}
@media (max-width: 767px) {{
    .vp-compare-table {{ display: none; }}
    .vp-compare-cards {{ display: grid; gap: 16px; }}
    .vp-compare-card {{
        background: #fff;
        border: 1px solid var(--color-ink-100, #e2e8f0);
        border-radius: 14px;
        padding: 20px;
        min-width: 0;
    }}
    .vp-cmp-row {{
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 12px;
        align-items: start;
        padding: 10px 0;
        border-top: 1px solid var(--color-ink-100, #e2e8f0);
        min-width: 0;
    }}
    .vp-cmp-key {{
        font-size: 13px;
        color: var(--color-ink-600, #475569);
        word-wrap: break-word;
        overflow-wrap: anywhere;
        min-width: 0;
    }}
    .vp-cmp-val {{
        font-size: 13px;
        font-weight: 600;
        color: var(--color-ink-900);
        text-align: right;
        word-wrap: break-word;
        overflow-wrap: anywhere;
        max-width: 55%;
    }}
}}

/* Responsive table wrapper — momentum scroll on iOS, visible scrollbar */
.table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: 12px; }}
.table-wrap::-webkit-scrollbar {{ height: 8px; }}
.table-wrap::-webkit-scrollbar-thumb {{ background: var(--color-ink-300, #cbd5e1); border-radius: 4px; }}
</style>
</head>
<body>
<a href="#main" class="skip-link">Skip to content</a>
<header class="sticky top-0 z-40 border-b border-ink-100 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70">
<div class="container-page flex items-center justify-between py-4">
<a href="/" class="flex items-center gap-2.5 group" aria-label="Hulo Global — home">
<span aria-hidden="true" class="grid size-9 place-items-center rounded-lg bg-ink-900 text-white font-bold tracking-tight text-sm group-hover:bg-ink-800 transition-colors">HG</span>
<span class="font-bold text-ink-900 tracking-tight text-lg">Hulo Global</span>
</a>
<nav aria-label="Primary" class="hidden md:flex md:items-center md:gap-6">
<ul class="flex items-center gap-6 text-sm font-medium text-ink-700">
<li><a href="/" class="hover:text-ink-900 transition-colors py-3 px-2 inline-block">Home</a></li>
<li><a href="/vendure-plugins/" class="hover:text-ink-900 transition-colors py-3 px-2 inline-block">Vendure plugins</a></li>
<li><a href="/#contact" class="hover:text-ink-900 transition-colors py-3 px-2 inline-block">Contact</a></li>
</ul>
<div class="ccy-picker-wrap">
<label for="ccy-picker" class="ccy-label">Currency:</label>
<select id="ccy-picker" name="currency" class="ccy-select">
<option value="GBP">£ GBP</option>
<option value="USD">$ USD</option>
<option value="EUR">€ EUR</option>
<option value="AUD">A$ AUD</option>
<option value="CAD">C$ CAD</option>
</select>
</div>
</nav>
<div class="mobile-controls md:hidden">
<a href="/vendure-plugins/" class="mobile-nav-link" aria-label="Vendure plugins">Plugins</a>
<div class="ccy-picker-wrap">
<label for="ccy-picker-mobile" class="sr-only">Currency</label>
<select id="ccy-picker-mobile" name="currency" class="ccy-select ccy-select-mobile">
<option value="GBP">£ GBP</option>
<option value="USD">$ USD</option>
<option value="EUR">€ EUR</option>
<option value="AUD">A$ AUD</option>
<option value="CAD">C$ CAD</option>
</select>
</div>
</div>
<div id="ccy-live" class="sr-only" aria-live="polite" aria-atomic="true"></div>
</div>
</header>
<main id="main">
'''

CURRENCY_JS = '''
<script>
(function() {
  var PRICES = ''' + str(CURRENCIES).replace("'", '"') + ''';
  function pickInitial() {
    try {
      var url = new URLSearchParams(location.search).get('currency');
      if (url && PRICES[url.toUpperCase()]) return url.toUpperCase();
      var stored = localStorage.getItem('hulo-currency');
      if (stored && PRICES[stored]) return stored;
      var loc = (navigator.language || 'en-GB').toUpperCase();
      if (loc.indexOf('US') !== -1) return 'USD';
      if (loc.indexOf('AU') !== -1) return 'AUD';
      if (loc.indexOf('CA') !== -1) return 'CAD';
      if (/-(DE|FR|ES|IT|NL|IE|AT|BE|PT|FI|GR|LU)$/.test(loc)) return 'EUR';
    } catch (e) {}
    return 'GBP';
  }
  var live = document.getElementById('ccy-live');
  var initialised = false;
  function apply(ccy) {
    var p = PRICES[ccy] || PRICES.GBP;
    document.querySelectorAll('[data-monthly-price]').forEach(function(el) { el.textContent = p.monthly; });
    document.querySelectorAll('[data-lifetime-price]').forEach(function(el) { el.textContent = p.lifetime; });
    document.querySelectorAll('[data-currency-input]').forEach(function(el) { el.value = ccy; });
    try { localStorage.setItem('hulo-currency', ccy); } catch (e) {}
    if (live && initialised) {
      live.textContent = 'Currency changed to ' + ccy + '. Monthly ' + p.monthly + ', lifetime ' + p.lifetime + '.';
    }
    initialised = true;
  }
  var initial = pickInitial();
  ['ccy-picker', 'ccy-picker-mobile'].forEach(function(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.value = initial;
    el.addEventListener('change', function() {
      apply(el.value);
      // keep both pickers in sync
      var other = document.getElementById(id === 'ccy-picker' ? 'ccy-picker-mobile' : 'ccy-picker');
      if (other) other.value = el.value;
    });
  });
  apply(initial);
})();
</script>
'''

VERSION_REFRESH_JS = '''
<script>
/*
 * Keep every [data-hulo-pkg] version chip in sync with what npm currently
 * publishes. The HTML is built with the last-known-good version baked in
 * (so JS-off users still see the right thing and search engines index a
 * concrete number). This runs on load and rewrites the chip if npm has
 * shipped a newer version since the last build.
 *
 * Strategy:
 *   1. Fetch /vendure-plugins/versions.json (regenerated on every build,
 *      served from our own CDN — no cross-origin, no rate-limit).
 *   2. If that fails (older build without the file), fall back to the
 *      public npm registry directly. CORS on the registry is permissive.
 *   3. Never throw. A stale chip is fine; a broken page is not.
 */
(function () {
  var chips = document.querySelectorAll('[data-hulo-pkg]');
  if (!chips.length) return;
  var wanted = {};
  chips.forEach(function (el) { wanted[el.getAttribute('data-hulo-pkg')] = true; });
  function apply(versions) {
    chips.forEach(function (el) {
      var pkg = el.getAttribute('data-hulo-pkg');
      var v = versions[pkg];
      if (!v) return;
      var prefix = el.getAttribute('data-hulo-version-prefix') || '';
      var next = prefix + v;
      if (el.textContent !== next) el.textContent = next;
    });
  }
  fetch('/vendure-plugins/versions.json', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(apply)
    .catch(function () {
      // Fall back to the public registry — one request per package.
      Object.keys(wanted).forEach(function (pkg) {
        var url = 'https://registry.npmjs.org/' + encodeURIComponent(pkg).replace('%40', '@') + '/latest';
        fetch(url, { cache: 'no-cache' })
          .then(function (r) { return r.ok ? r.json() : null; })
          .then(function (j) {
            if (j && j.version) { var o = {}; o[pkg] = j.version; apply(o); }
          })
          .catch(function () { /* silent */ });
      });
    });
})();
</script>
'''

FOOTER = CURRENCY_JS + VERSION_REFRESH_JS + '''
</main>
<footer class="border-t border-ink-100 bg-ink-50 mt-20">
<div class="container-page py-10 grid gap-8 sm:grid-cols-3">
<div>
<p class="text-sm text-ink-700">Hulo Global Limited</p>
<p class="text-xs text-ink-600 mt-1">UK Companies House 17134928</p>
<p class="text-xs text-ink-600 mt-1">Unit A, 82 James Carter Road,<br>Mildenhall, IP28 7DE, UK</p>
</div>
<div>
<p class="text-xs uppercase tracking-wider text-ink-500 font-semibold mb-3">Vendure plugins</p>
<ul class="space-y-1.5 text-sm text-ink-700">
<li><a href="/vendure-plugins/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">All plugins</a></li>
<li><a href="/vendure-plugins/email-tracking/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Email Tracking</a></li>
<li><a href="/vendure-plugins/geo-block/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Geo Block</a></li>
<li><a href="/vendure-plugins/visitor-analytics/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Visitor Analytics</a></li>
</ul>
</div>
<div>
<p class="text-xs uppercase tracking-wider text-ink-500 font-semibold mb-3">Customers</p>
<ul class="space-y-1.5 text-sm text-ink-700">
<li><a href="https://elite.charity/licence/forgot" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Lost your key?</a></li>
<li><a href="https://elite.charity/licence/privacy" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Your data &amp; privacy</a></li>
<li><a href="mailto:hello@huloglobal.com" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">hello@huloglobal.com</a></li>
</ul>
</div>
</div>
</footer>
</body>
</html>
'''


def header(title, canonical, description):
    return HEADER.format(title=html.escape(title), canonical=canonical, description=html.escape(description))


TICK_SVG = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'


def index_page():
    short_features = {
        'email-tracking': [
            'Per-link tokenised open + click tracking',
            'Human / machine event classification (Gmail proxy, Safe Links, …)',
            'IP enrichment + provider webhooks (Postmark / SendGrid / Mailgun / SES)',
            'Order Activity History panel + PDF Evidence Report',
        ],
        'geo-block': [
            '37 region presets (EU, EEA, GCC, NATO, …)',
            'Soft-block (browse-only) mode',
            'IP allowlist with CIDR',
            '"What-if" simulator + stats panel',
        ],
        'visitor-analytics': [
            'Page views + funnel + exit pages',
            'Conversion goals with URL globs',
            'Bot detection + privacy-first defaults',
            'Live-now SSE widget',
        ],
    }
    cards = []
    for p in PLUGINS:
        feats_html = '\n'.join(
            f'<li><span class="text-accent-600 shrink-0" style="margin-top:2px">{TICK_SVG}</span><span>{html.escape(f)}</span></li>'
            for f in short_features[p['slug']]
        )
        cards.append(f'''
<article class="vp-card">
  <h3>{html.escape(p['title'])}</h3>
  <p class="vp-card-tagline">{html.escape(p['tagline'])}</p>
  <ul>{feats_html}</ul>
  <div class="vp-card-actions">
    <a href="/vendure-plugins/{p['slug']}/" class="btn btn-primary text-sm" style="padding:.6rem 1.2rem">Learn more →</a>
    <!--email_off--><span class="text-xs text-ink-500 font-mono ml-auto" data-hulo-pkg="{html.escape(p['pkg'])}" data-hulo-version-prefix="v">v{p['version']}</span><!--/email_off-->
  </div>
</article>''')

    comparison_rows = [
        ['Drop-in install (one yarn add)', 'yes', 'yes', 'yes'],
        ['Channel-aware', 'yes', 'yes', 'yes'],
        ['Admin UI included', 'yes', 'yes', 'yes'],
        ['Database entities', '2', '1', '2'],
        ['Public HTTP endpoints', '4', '3', '1'],
        ['Admin HTTP endpoints', '7', '5', '15'],
        ['Privacy controls', 'IP hash', 'IP allowlist', 'DNT, IP anonymisation, consent gate'],
        ['Offline licence verification', 'yes', 'yes', 'yes'],
        ['Self-hosted (no calls home at runtime)', 'yes', 'yes', 'yes'],
    ]
    def fmt_cell(c, plain=False):
        if c == 'yes': return '<span class="text-accent-600 font-bold">✓</span>' if not plain else '✓'
        if c == 'no': return '<span class="text-ink-400">—</span>' if not plain else '—'
        return html.escape(c)
    rows_html = '\n'.join(
        '<tr>' +
        f'<th class="p-4 font-semibold text-ink-800 border-t border-ink-100" style="font-size:14px; text-align:left">{html.escape(r[0])}</th>' +
        ''.join(
            f'<td class="p-4 border-t border-ink-100 text-sm {"text-ink-900 font-medium" if c not in ("yes","no") else ""}" style="text-align:center; vertical-align:middle">{fmt_cell(c)}</td>'
            for c in r[1:]
        ) +
        '</tr>'
        for r in comparison_rows
    )
    # Mobile fallback: render the same data as three cards, one per plugin
    plugin_titles = ['Email Tracking', 'Geo Block', 'Visitor Analytics']
    mobile_cards = []
    for idx, title in enumerate(plugin_titles):
        rows_for_card = '\n'.join(
            f'<div class="vp-cmp-row">'
            f'<span class="vp-cmp-key">{html.escape(r[0])}</span>'
            f'<span class="vp-cmp-val">{fmt_cell(r[idx + 1])}</span>'
            f'</div>'
            for r in comparison_rows
        )
        mobile_cards.append(
            f'<article class="vp-compare-card">'
            f'<h3 class="font-bold text-lg text-ink-900 mb-1">{title}</h3>'
            f'<div>{rows_for_card}</div>'
            f'</article>'
        )

    # Compatibility matrix — one row per plugin. Vendure range comes
    # from each plugin's declared peer dependency; "Verified on" is the
    # newest Vendure release we build + smoke-test against before
    # publishing. Kept as data so a plugin version bump (which flows in
    # via versions.json) keeps the "Latest" column honest.
    VERIFIED_VENDURE = '3.7.1'
    compat = {
        'email-tracking':    ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'geo-block':         ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
        'visitor-analytics': ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'),
    }
    compat_rows_html = ''
    for p in PLUGINS:
        vendure_range, node_range, ts_range = compat.get(
            p['slug'], ('3.5 – 3.7', '20 LTS+', '5.4 – 6.x'))
        compat_rows_html += (
            '<tr>'
            f'<th style="text-align:left"><a href="/vendure-plugins/{p["slug"]}/">{html.escape(p["title"])}</a></th>'
            f'<td style="text-align:center"><!--email_off--><span class="vp-compat-ver font-mono" data-hulo-pkg="{html.escape(p["pkg"])}" data-hulo-version-prefix="v">v{p["version"]}</span><!--/email_off--></td>'
            f'<td style="text-align:center">{vendure_range}</td>'
            f'<td style="text-align:center">{node_range}</td>'
            f'<td style="text-align:center">{ts_range}</td>'
            f'<td style="text-align:center"><span class="vp-compat-ok">✓ {VERIFIED_VENDURE}</span></td>'
            '</tr>'
        )

    faqs = [
        ('How are the plugins licensed?', 'Each plugin is licensed individually. Monthly subscription with a <strong>7-day free trial</strong> (then £9.95/mo, cancel any time), or one-off lifetime (£199, never expires, 12 months of updates included). Both options give you a JWT licence key you set as an env var.'),
        ('How does the free trial work?', 'Pick the monthly plan and enter your email. We collect a payment method via Stripe but don\'t charge for 7 days — and we\'ll send a reminder email 2 days before the trial ends so you can cancel if you change your mind. Trials are limited to one per customer; we detect repeat attempts by the card fingerprint, not just the email.'),
        ('How do I manage / cancel my subscription?', 'Every receipt email includes a Stripe Customer Portal link — click it to update your payment method, see invoices, or cancel. No need to email us. Lifetime customers have nothing to manage; reply to your receipt if you need a VAT invoice.'),
        ('I lost my licence key — what now?', 'Re-send every active key on file at <a class="underline underline-offset-2" href="https://elite.charity/licence/forgot">elite.charity/licence/forgot</a>. We always show the same confirmation regardless of whether the email is on file (anti-enumeration), so check spam if nothing arrives. Limited to 5 requests per email per day.'),
        ('Can I export or delete my data?', 'Yes — under UK GDPR you have a right to see, export and erase the personal data we hold. Visit <a class="underline underline-offset-2" href="https://elite.charity/licence/privacy">elite.charity/licence/privacy</a> and we\'ll email you a magic link to do both.'),
        ('Do the plugins call home?', 'No — licence verification is offline. Each plugin verifies the JWT at boot against an embedded public key. A revocation list is polled once a week (cached, soft-fail), so a brief outage at our end never disables your store. Nothing else leaves your server.'),
        ('Where does customer data live?', 'On your Vendure server — same DB as the rest of your data. No third-party analytics provider. The visitor-analytics plugin\'s ingest endpoint is on your domain.'),
        ('What if I don\'t buy a licence?', 'Plugins still boot in a degraded "evaluation" mode — install, configure, browse data, and the admin UI is functional. The public storefront endpoints are limited (geo-block always reports `enabled:false`; visitor-analytics dashboards return 403). Buy a key when you\'re ready.'),
        ('Can I see the source?', 'Yes — all three are on GitHub under <a class="underline underline-offset-2" href="https://github.com/exceeded">github.com/exceeded</a>. MIT-style licence on the code itself, separate paid licence for production use.'),
        ('Do they work on Vendure 2.x?', 'They target Vendure 3.x (3.0+). Vendure 2.x isn\'t supported because we use some of the 3.x customField improvements.'),
    ]
    faq_html = '\n'.join(f'<details><summary>{html.escape(q)}</summary><p>{a}</p></details>' for q, a in faqs)

    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-24 pb-16 md:pt-32 md:pb-24">
<!-- HG monogram — corporate mark on every marketing page hero.
     Same rounded-navy frame as every plugin logo so the family
     reads consistently. Inline SVG so it doesn't add a network
     round-trip on first render. -->
<a href="/vendure-plugins/" class="vp-brand" aria-label="Hulo Global home">
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
<rect width="64" height="64" rx="14" fill="#0f1419"/>
<path d="M14 16 h5 v13 h11 v-13 h5 v32 h-5 v-14 h-11 v14 h-5 z" fill="#ffffff"/>
<path d="M50 24 A11 11 0 1 0 50 42 L50 34 L44 34 L44 30" fill="none" stroke="#ffffff" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="50" cy="33" r="2.5" fill="#f59e0b"/>
</svg>
<span class="vp-brand-txt">Hulo Global</span>
</a>
<span class="vp-pill mb-6">Vendure plugins by Hulo Global</span>
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">
Production-grade plugins for your Vendure store.
</h1>
<p class="mt-7 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">
Battle-tested in our own UK e-commerce stack. One <code class="font-mono text-sm bg-ink-100 px-1.5 py-0.5 rounded">yarn add</code>, one config line, ready in 5 minutes.
</p>
</div>
</section>

<section class="vp-section" style="background:#fff">
<div class="container-page">
<div class="vp-cards-grid">
{''.join(cards)}
</div>
</div>
</section>

<section class="vp-section" style="background:var(--color-ink-50,#f8fafc)">
<div class="container-page">
<div class="max-w-2xl mx-auto text-center" style="margin-bottom:56px">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">At a glance</p>
<h2 class="mt-4 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Same shape, focused on different problems.</h2>
</div>
<!-- Desktop / wide tablet: full comparison table -->
<div class="vp-compare-table rounded-2xl border border-ink-100 bg-white table-wrap" role="region" aria-label="Plugin comparison" tabindex="0">
<table class="w-full" style="min-width:640px">
<thead>
<tr>
<th class="p-4 font-medium text-sm text-ink-500" style="text-align:left"></th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Email Tracking</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Geo Block</th>
<th class="p-4 font-semibold text-ink-900" style="text-align:center">Visitor Analytics</th>
</tr>
</thead>
<tbody>{rows_html}</tbody>
</table>
</div>
<!-- Mobile: stacked cards, one per plugin -->
<div class="vp-compare-cards" aria-hidden="false">
{''.join(mobile_cards)}
</div>
</div>
</section>

<section class="vp-section" id="compatibility" style="background:#fff">
<div class="container-page">
<div class="max-w-2xl mx-auto text-center" style="margin-bottom:48px">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Compatibility</p>
<h2 class="mt-4 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Verified against the latest Vendure.</h2>
<p class="mt-4 text-ink-600 leading-relaxed">Every plugin is built and smoke-tested against the newest Vendure release before publishing. The table below is the current support surface — installs cleanly with <code class="font-mono text-sm bg-ink-100 px-1.5 py-0.5 rounded">yarn</code> or <code class="font-mono text-sm bg-ink-100 px-1.5 py-0.5 rounded">npm</code>.</p>
</div>
<div class="vp-compat-wrap rounded-2xl border border-ink-100 bg-white table-wrap" role="region" aria-label="Compatibility matrix" tabindex="0">
<table class="vp-compat w-full" style="min-width:680px">
<thead>
<tr>
<th style="text-align:left">Plugin</th>
<th style="text-align:center">Latest</th>
<th style="text-align:center">Vendure&nbsp;core</th>
<th style="text-align:center">Node</th>
<th style="text-align:center">TypeScript</th>
<th style="text-align:center">Verified&nbsp;on</th>
</tr>
</thead>
<tbody>{compat_rows_html}</tbody>
</table>
</div>
<p class="mt-6 text-sm text-ink-500 max-w-3xl mx-auto text-center">
A boot-time check emits a non-fatal warning if <code class="font-mono text-xs bg-ink-100 px-1 py-0.5 rounded">@vendure/core</code> is outside the tested range, so a future 3.x upgrade is always safe to try. Vendure 4.0 will be tested and re-declared once its changelog lands. Node 20 LTS or newer recommended.
</p>
</div>
</section>

<section class="vp-section" style="background:var(--color-ink-50,#f8fafc)">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">FAQ</p>
<h2 class="mt-4 text-3xl md:text-4xl font-bold tracking-tight text-ink-900" style="margin-bottom:40px">Common questions.</h2>
<div class="vp-faq">{faq_html}</div>
</div>
</section>
'''
    return header('Vendure plugins by Hulo Global',
                  'https://huloglobal.com/vendure-plugins/',
                  'Production-grade Vendure plugins by Hulo Global — email tracking, geo-blocking, visitor analytics. Drop-in, self-hosted, licensed.') + body + FOOTER


def plugin_page(p):
    feats_html = '\n'.join(
        f'<div class="vp-feat"><div class="vp-feat-tick" aria-hidden="true">{TICK_SVG}</div><div><h3>{html.escape(t)}</h3><p>{html.escape(d)}</p></div></div>'
        for t, d in p['features']
    )
    endpoints_html = '\n'.join(
        f'<div class="vp-endpoint"><span class="vp-method {m}">{m}</span><code>{html.escape(path)}</code><span class="vp-desc">{html.escape(desc)}</span></div>'
        for m, path, desc in p['endpoints']
    )
    env_var_name = 'HULO_LICENCE_KEY_' + p['slug'].upper().replace('-', '_')

    config_block = f'''<span class="vp-comment"># vendure-config.ts</span>
import {{ <span class="vp-key">{p['class']}</span> }} from <span class="vp-str">'{p['pkg']}'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="vp-key">{p['class']}</span>.init({{
      publicBaseUrl: <span class="vp-str">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="vp-key">{env_var_name}</span>,
    }}),
    <span class="vp-comment">// ... your other plugins</span>
  ],
}};'''

    short_id = p['slug']
    pkg_short = p['pkg'].split('/')[-1]
    faqs = [
        ('How do I get a licence key?',
         f'<a class="underline underline-offset-2" href="{BUY_BASE}/{pkg_short}">Buy here</a> — Stripe Checkout, monthly or lifetime. You\'ll receive the JWT key by email; set it as <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">{env_var_name}</code> in your <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">.env</code>.'),
        ('Does it work without a key?',
         'Yes — the plugin boots in a degraded "evaluation" mode. You can install, configure, and inspect the admin UI before committing.'),
        ('Where is data stored?',
         'In your Vendure database. The plugin adds its own tables via a migration — your data never leaves your server.'),
        ('Will it survive a Vendure upgrade?',
         f'Tested against Vendure <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">&gt;=3.5.0 &lt;4.0.0</code> — 3.5, 3.6 and 3.7 are all covered by CI. A boot-time compatibility check emits a non-fatal warning if <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">@vendure/core</code> is outside that range, so upgrades to a future 3.x are safe to try. The 4.0 line will be tested and re-declared once its changelog lands.'),
    ]
    faq_html = '\n'.join(f'<details><summary>{html.escape(q)}</summary><p>{a}</p></details>' for q, a in faqs)

    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-12 pb-10 md:pt-16 md:pb-14">
<a href="/vendure-plugins/" class="vp-brand" aria-label="Hulo Global home">
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true">
<rect width="64" height="64" rx="14" fill="#0f1419"/>
<path d="M14 16 h5 v13 h11 v-13 h5 v32 h-5 v-14 h-11 v14 h-5 z" fill="#ffffff"/>
<path d="M50 24 A11 11 0 1 0 50 42 L50 34 L44 34 L44 30" fill="none" stroke="#ffffff" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="50" cy="33" r="2.5" fill="#f59e0b"/>
</svg>
<span class="vp-brand-txt">Hulo Global</span>
</a>
<nav class="mb-5 text-sm text-ink-600">
<a href="/vendure-plugins/" class="hover:text-ink-900">Vendure plugins</a>
<span class="mx-2 text-ink-400">/</span>
<span class="text-ink-900 font-medium">{html.escape(p['title'])}</span>
</nav>
<h1 class="max-w-3xl text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-ink-900 leading-[1.04]">{html.escape(p['title'])}</h1>
<p class="mt-6 max-w-2xl text-lg md:text-xl text-ink-600 leading-relaxed">{html.escape(p['tagline'])}</p>
<div class="mt-8 flex flex-wrap items-center gap-3">
<a href="{BUY_BASE}/{pkg_short}" class="btn btn-primary">Buy a licence →</a>
<a href="#install" class="btn btn-secondary">Install</a>
<a href="/vendure-plugins/{short_id}/docs/" class="btn btn-secondary">Read the manual</a>
<!--email_off--><span class="text-xs text-ink-500 font-mono ml-auto" data-hulo-pkg="{html.escape(p['pkg'])}" data-hulo-version-prefix="v">v{p['version']}</span><!--/email_off-->
</div>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page">
<div class="vp-grid-2">
<div>
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">What it does</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Built for production from day one.</h2>
<p class="mt-5 text-lg text-ink-700 leading-relaxed">{html.escape(p['description'])}</p>
<div class="mt-10">
{feats_html}
</div>
</div>
<aside class="vp-pricing-aside">
<div class="vp-price-card">
<p class="text-xs uppercase tracking-wider text-accent-600 font-semibold">Monthly · 7 days free</p>
<p class="vp-price-num mt-2"><span class="vp-trial-num">7</span><small>days free</small></p>
<p class="mt-2 text-sm text-ink-700">Then <span data-monthly-price>£9.95</span>/month. Cancel anytime before day 8 and pay nothing.</p>
<a href="{BUY_BASE}/{pkg_short}?plan=monthly" class="btn btn-secondary w-full mt-5" style="text-align:center">Start 7-day free trial →</a>
<p class="vp-tiny-note">Card required. One trial per customer.</p>
</div>
<div class="vp-price-card featured">
<p class="text-xs uppercase tracking-wider text-accent-600 font-semibold">Lifetime · Best value</p>
<p class="vp-price-num mt-2" data-lifetime-price>£199</p>
<p class="mt-2 text-sm text-ink-600">One-off. Never expires. 12 months of updates.</p>
<a href="{BUY_BASE}/{pkg_short}?plan=lifetime" class="btn btn-primary w-full mt-5" style="text-align:center">Buy lifetime →</a>
</div>
<p class="mt-4 text-xs text-ink-500 leading-relaxed">Payments processed by Stripe. VAT applied where applicable. 30-day refund if it doesn't fit your stack. By proceeding you accept our <a href="/legal/terms/" class="underline">Terms</a> and <a href="/legal/privacy/" class="underline">Privacy Policy</a>.</p>
</aside>
</div>
</div>
</section>

<section id="install" class="vp-section bg-ink-50">
<div class="container-page max-w-3xl" style="counter-reset: step;">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">Install</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Three steps, five minutes.</h2>

<div class="vp-step mt-10">
<h3 class="text-xl font-semibold text-ink-900 flex items-center">Add the package</h3>
<p class="mt-2 text-ink-600">Or run the one-line installer that does steps 1–3 for you:</p>
<div class="vp-code mt-3">curl -sSL https://huloglobal.com/vendure-plugins/{short_id}/install.sh | bash</div>
<p class="mt-3 text-sm text-ink-500">Prefer to do it by hand?</p>
<div class="vp-code mt-2">yarn add {p['pkg']}</div>
</div>

<div class="vp-step mt-10">
<h3 class="text-xl font-semibold text-ink-900 flex items-center">Register it</h3>
<p class="mt-2 text-ink-600">In your <code class="font-mono text-sm bg-white px-1.5 py-0.5 rounded border border-ink-200">vendure-config.ts</code>:</p>
<div class="vp-code mt-3">{config_block}</div>
</div>

<div class="vp-step mt-10">
<h3 class="text-xl font-semibold text-ink-900 flex items-center">Run the migration</h3>
<p class="mt-2 text-ink-600">The plugin adds its own table(s). Generate + run the migration like any other:</p>
<div class="vp-code mt-3">yarn migration:generate Add{p['class']}Tables
yarn migration:run</div>
</div>

<div class="mt-10 rounded-lg border border-ink-200 bg-white p-6">
<p class="text-sm text-ink-700"><strong>That's it.</strong> The admin UI tab appears immediately. Without a licence key the plugin runs in a degraded evaluation mode — fine for trying things out. <a href="{BUY_BASE}/{pkg_short}" class="text-accent-600 underline underline-offset-2">Buy a key →</a></p>
</div>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">HTTP endpoints</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Every route exposed.</h2>
<div class="mt-8 rounded-lg border border-ink-100 bg-white table-wrap" role="region" aria-label="HTTP endpoints" tabindex="0">
<div style="min-width:560px;padding:6px 12px">
{endpoints_html}
</div>
</div>
</div>
</section>

<section class="vp-section bg-ink-50">
<div class="container-page max-w-3xl">
<p class="text-sm font-semibold uppercase tracking-wider text-accent-600">FAQ</p>
<h2 class="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-ink-900 mb-8">Common questions.</h2>
<div class="vp-faq">{faq_html}</div>
</div>
</section>

<section class="vp-section bg-white">
<div class="container-page max-w-2xl text-center">
<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-ink-900">Ready to ship?</h2>
<p class="mt-5 text-lg text-ink-600 leading-relaxed">Buy a key, drop the plugin in, ship today.</p>
<div class="mt-8 flex flex-wrap items-center justify-center gap-3">
<a href="{BUY_BASE}/{pkg_short}" class="btn btn-primary">Buy a licence →</a>
<a href="mailto:hello@huloglobal.com?subject=Vendure%20plugin%20enquiry" class="btn btn-secondary">Email us</a>
</div>
</div>
</section>
'''
    return header(f"{p['title']} — Vendure plugin by Hulo Global",
                  f"https://huloglobal.com/vendure-plugins/{p['slug']}/",
                  p['tagline']) + body + FOOTER


INSTALL_SH = '''#!/usr/bin/env bash
# {title} — installer
# Run this from the root of your Vendure project (where vendure-config.ts lives).

set -euo pipefail

PKG="{pkg}"
CLASS="{class_name}"
ENV_VAR="{env_var}"

cd "$(dirname "$(pwd)/vendure-config.ts")" 2>/dev/null || true
if [[ ! -f "src/vendure-config.ts" && ! -f "vendure-config.ts" ]]; then
  echo "✗ Couldn't find vendure-config.ts in $(pwd). Run from your Vendure project root." >&2
  exit 1
fi
CONFIG=$( [[ -f "src/vendure-config.ts" ]] && echo "src/vendure-config.ts" || echo "vendure-config.ts" )

echo "→ Installing $PKG"
if [[ -f "yarn.lock" ]]; then
  yarn add "$PKG"
elif [[ -f "pnpm-lock.yaml" ]]; then
  pnpm add "$PKG"
else
  npm install "$PKG"
fi

if ! grep -q "$PKG" "$CONFIG"; then
  echo
  echo "→ Add the following to $CONFIG:"
  echo
  cat <<EOF
import {{ $CLASS }} from '$PKG';

// inside your VendureConfig.plugins[]:
$CLASS.init({{
  publicBaseUrl: process.env.VENDURE_PUBLIC_URL || 'http://localhost:3000',
  licenceKey: process.env.$ENV_VAR,
}}),
EOF
  echo
  echo "→ Then add the UI extension to your compile-admin-ui.ts (if you have one):"
  echo "  extensions: [..., $CLASS.uiExtensions]"
else
  echo "✓ $PKG already referenced in $CONFIG"
fi

echo
echo "→ Generate + run the migration:"
echo "  yarn migration:generate Add${{CLASS}}Tables"
echo "  yarn migration:run"
echo
echo "→ Set your licence key:"
echo "  echo '$ENV_VAR=...' >> .env"
echo
echo "✓ Done. Restart Vendure to pick up the plugin."
echo "  Buy a key:  https://elite.charity/licence/buy/{pkg_short}"
echo "  Manual:     https://huloglobal.com/vendure-plugins/{slug}/docs/"
'''


def install_sh(p):
    return INSTALL_SH.format(
        title=p['title'],
        pkg=p['pkg'],
        class_name=p['class'],
        env_var='HULO_LICENCE_KEY_' + p['slug'].upper().replace('-', '_'),
        pkg_short=p['pkg'].split('/')[-1],
        slug=p['slug'],
    )


def main():
    # Refresh the version numbers from npm. Falls back to the hardcoded
    # value when offline so the build always works.
    for p in PLUGINS:
        latest = fetch_npm_version(p['pkg'])
        if latest:
            if latest != p['version']:
                print(f"  {p['pkg']}: {p['version']} → {latest} (npm)")
            p['version'] = latest

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(index_page(), encoding='utf-8')
    # Emit a flat versions map the client-side updater fetches on load —
    # so version chips always show the current npm version even if the
    # HTML itself was baked hours ago.
    versions_map = {p['pkg']: p['version'] for p in PLUGINS}
    versions_map['_generated_at_utc'] = subprocess.check_output(
        ['date', '-u', '+%Y-%m-%dT%H:%M:%SZ']).decode().strip()
    (OUT / 'versions.json').write_text(
        json.dumps(versions_map, indent=2) + '\n', encoding='utf-8')
    for p in PLUGINS:
        d = OUT / p['slug']
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(plugin_page(p), encoding='utf-8')
        sh = d / 'install.sh'
        sh.write_text(install_sh(p), encoding='utf-8')
        sh.chmod(0o755)

    # Mirror the static/vendure-plugins tree into the dist output so
    # `deploy.sh` — which only tar/rsyncs `dist/vendure-plugins` —
    # picks up brand assets like the plugin logos. Deliberately copies
    # every file so future additions (favicons, OG images, etc.) land
    # under the same URL prefix without needing another wiring change.
    import shutil
    src_static = HERE / 'static' / 'vendure-plugins'
    if src_static.is_dir():
        for sub in src_static.iterdir():
            dest = OUT / sub.name
            if sub.is_dir():
                shutil.copytree(sub, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(sub, dest)

    print(f'Wrote {len(PLUGINS) + 1} pages + {len(PLUGINS)} install scripts + versions.json to {OUT}')


if __name__ == '__main__':
    main()
