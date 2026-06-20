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
import textwrap

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
        'version': '0.3.0',
        'title': 'Email Tracking',
        'tagline': 'See exactly what every transactional email does — opens, clicks, bounces, suppressions.',
        'description': (
            'Drop-in tracker for every email your Vendure server sends. Wraps the '
            '`@vendure/email-plugin` pipeline plus a service for ad-hoc sends. '
            'Logs every send, click and open with full history. Suppression list '
            'auto-handles hard bounces and complaints. Per-template open rates, '
            'CSV export, device + client detection on every open.'
        ),
        'features': [
            ('Open + click pixel-and-redirect tracking', 'Per-event 1×1 pixel for opens, per-link redirector for clicks. Bot UAs are flagged separately.'),
            ('Full open + click history per email', 'Last 50 opens and clicks per row with timestamp, IP, user-agent and parsed client (Gmail web, Outlook desktop, Apple Mail iOS …).'),
            ('Suppression list', 'Hard bounces and complaints auto-add to the suppression table. Subsequent sends are silently skipped and logged as `status=suppressed`.'),
            ('Per-template analytics', 'Open rate, CTR, click-to-open ratio and bounce rate per email type — order-confirmation, OTP, invoice, password-reset and your custom types.'),
            ('Bounce + complaint webhook', 'POST DSN events to `/email-track/bounce` from your postmaster integration. Both bounce types tracked.'),
            ('Admin UI: Email Log + per-customer Emails tab', 'Filter by recipient, customer, order, status, type, date range. Expand any row for the full event timeline.'),
            ('CSV export', '`/email-track/log/export.csv` returns up to 50k rows with the same filter shape as the list view.'),
            ('Works with any SMTP transport', 'Gmail, SES, SendGrid, Postmark, Mailgun, raw SMTP. Just plug `TrackingEmailSender()` into your email-plugin config.'),
        ],
        'endpoints': [
            ('GET',  '/email-track/open/:id.gif',     'Pixel — logs an open then serves a 1×1 GIF'),
            ('GET',  '/email-track/click/:id?u=<url>', 'Click redirector — logs then 302s to the original URL'),
            ('POST', '/email-track/bounce',           'Bounce / complaint webhook — DSN bridge'),
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
        'version': '0.2.0',
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
        'version': '0.3.0',
        'title': 'Visitor Analytics',
        'tagline': 'Self-hosted, privacy-respecting visitor journey + conversion goals — no third party.',
        'description': (
            'Self-hosted visitor analytics. Page views, time-on-page, exit pages, '
            'a configurable funnel, conversion goals, UTM attribution, bot '
            'detection. Per-visitor profile drawer with parsed UA + MaxMind '
            'GeoLite2 geo. Survives login — guest and signed-in events share '
            'the same visitor id. Privacy-first defaults: DNT respected, IPs '
            'anonymised, optional consent gate.'
        ),
        'features': [
            ('Lightweight ingest endpoint', '`POST /ees/track` accepts a batch of pageviews / unloads / custom events. Cookies (`ees_vid`, `ees_sid`) issued + refreshed automatically.'),
            ('Configurable conversion goals', 'CRUD a goal with a URL glob (`/checkout/thank-you/*`) and a value (£/$). Live matcher tags every pageview that hits the pattern. Dashboard shows completions per goal.'),
            ('Bot detection', 'UA-classified `isBot` flag on every event. Excluded from "real human" counts but visible on the dashboard so you can see crawler share.'),
            ('Privacy-first defaults', 'DNT respected, IPs anonymised to /24 (IPv4) / /48 (IPv6), optional `requireConsent` gate. All three opt-outable.'),
            ('UTM attribution', 'Source / medium / campaign / term / content captured server-side per pageview. Plus referrer domain so reports group by source without UTM.'),
            ('Funnel + exit-page reports', 'Configurable funnel with per-step drop-off, exit-page report, top events, top pages.'),
            ('Per-visitor journey drawer', 'Click any visitor for the full timeline: pages, custom events, time on page, country, browser, OS.'),
            ('Live-now SSE widget', 'Real-time tile on the admin dashboard showing visitors active right now (by country).'),
            ('Custom event helpers', '`recordEvent("add_to_cart", { productVariantId, quantity })` on the storefront — fires fire-and-forget, batched, with the same enrichment.'),
            ('CSV export', '`/ees/visitors/export.csv?days=N` returns the last N days (max 90) of raw events with full enrichment.'),
        ],
        'endpoints': [
            ('POST', '/ees/track',                 'Public: ingest a batch of events'),
            ('GET',  '/ees/visitors/summary',      'Admin: top-line counters + daily series'),
            ('GET',  '/ees/visitors/sources',      'Admin: top sources by visits / sessions'),
            ('GET',  '/ees/visitors/top-pages',    'Admin: most-visited URLs'),
            ('GET',  '/ees/visitors/funnel',       'Admin: configurable funnel with drop-offs'),
            ('GET',  '/ees/visitors/exit-pages',   'Admin: top exit pages'),
            ('GET',  '/ees/visitors/top-events',   'Admin: top custom event types'),
            ('GET',  '/ees/visitors/live',         'Admin: SSE live-now stream'),
            ('GET',  '/ees/visitors/journey/:visitorId', 'Admin: per-visitor timeline'),
            ('GET',  '/ees/visitors/recent',       'Admin: recent events'),
            ('GET',  '/ees/visitors/export.csv',   'Admin: CSV export'),
            ('GET',  '/ees/goals',                 'Admin: list conversion goals'),
            ('POST', '/ees/goals',                 'Admin: create a goal'),
            ('PUT',  '/ees/goals/:id',             'Admin: update a goal'),
            ('DELETE', '/ees/goals/:id',           'Admin: delete a goal'),
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
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=2">
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
.vp-price-num small {{ font-size: 15px; font-weight: 500; color: var(--color-ink-500, #64748b); margin-left: 4px; }}
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

FOOTER = CURRENCY_JS + '''
</main>
<footer class="border-t border-ink-100 bg-ink-50 mt-20">
<div class="container-page py-10 grid gap-6 sm:grid-cols-2">
<div>
<p class="text-sm text-ink-700">Hulo Global Limited — UK Companies House 17134928</p>
<p class="text-sm text-ink-600 mt-1">Unit A, 82 James Carter Road, Mildenhall, IP28 7DE, United Kingdom</p>
</div>
<div class="sm:text-right">
<p class="text-sm text-ink-700"><a href="mailto:hello@huloglobal.com" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">hello@huloglobal.com</a></p>
<p class="text-sm text-ink-600 mt-1"><a href="/vendure-plugins/" class="underline underline-offset-4 decoration-ink-300 hover:decoration-ink-800">Vendure plugins</a></p>
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
            'Open + click tracking with full history',
            'Suppression list (auto + manual)',
            'Per-template open / click rates',
            'CSV export',
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
    <span class="text-xs text-ink-500 font-mono ml-auto">v{p['version']}</span>
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

    faqs = [
        ('How are the plugins licensed?', 'Each plugin is licensed individually. Monthly (£9.95/mo, cancel any time) or one-off lifetime (£199, never expires, 12 months of updates included). Both options give you a JWT licence key you set as an env var.'),
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

<section class="vp-section" style="background:#fff">
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
         f'It targets Vendure 3.x (compatibility set to <code class="font-mono text-sm bg-ink-100 px-1 py-0.5 rounded">^3.0.0</code>). Major version bumps will be tested against new Vendure releases.'),
    ]
    faq_html = '\n'.join(f'<details><summary>{html.escape(q)}</summary><p>{a}</p></details>' for q, a in faqs)

    body = f'''
<section class="vp-hero">
<div class="container-page relative pt-16 pb-10 md:pt-24 md:pb-14">
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
<span class="text-xs text-ink-500 font-mono ml-auto">{html.escape(p['pkg'])}@{p['version']}</span>
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
<p class="text-xs uppercase tracking-wider text-ink-500 font-semibold">Monthly</p>
<p class="vp-price-num mt-2"><span data-monthly-price>£9.95</span><small>/mo</small></p>
<p class="mt-2 text-sm text-ink-600">Cancel any time. Updates included.</p>
<form method="post" action="{CHECKOUT_URL}" class="mt-5">
<input type="hidden" name="pluginId" value="{pkg_short}">
<input type="hidden" name="plan" value="monthly">
<input type="hidden" name="currency" value="GBP" data-currency-input>
<button type="submit" class="btn btn-secondary w-full">Subscribe →</button>
</form>
</div>
<div class="vp-price-card featured">
<p class="text-xs uppercase tracking-wider text-accent-600 font-semibold">Lifetime · Best value</p>
<p class="vp-price-num mt-2" data-lifetime-price>£199</p>
<p class="mt-2 text-sm text-ink-600">One-off. Never expires. 12 months of updates.</p>
<form method="post" action="{CHECKOUT_URL}" class="mt-5">
<input type="hidden" name="pluginId" value="{pkg_short}">
<input type="hidden" name="plan" value="lifetime">
<input type="hidden" name="currency" value="GBP" data-currency-input>
<button type="submit" class="btn btn-primary w-full">Buy lifetime →</button>
</form>
</div>
<p class="mt-4 text-xs text-ink-500 leading-relaxed">Payments processed by Stripe. VAT applied where applicable. 30-day refund if it doesn't fit your stack.</p>
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
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'index.html').write_text(index_page(), encoding='utf-8')
    for p in PLUGINS:
        d = OUT / p['slug']
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(plugin_page(p), encoding='utf-8')
        sh = d / 'install.sh'
        sh.write_text(install_sh(p), encoding='utf-8')
        sh.chmod(0o755)
    print(f'Wrote {len(PLUGINS) + 1} pages + {len(PLUGINS)} install scripts to {OUT}')


if __name__ == '__main__':
    main()
