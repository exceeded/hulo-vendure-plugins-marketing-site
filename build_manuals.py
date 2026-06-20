#!/usr/bin/env python3
"""
Build user manuals for each plugin at
  /vendure-plugins/<slug>/docs/index.html

Manuals are self-contained HTML pages with the same look as the
marketing pages plus SVG illustrations of the key admin screens.
"""
from pathlib import Path
import html
import re
import textwrap

HERE = Path(__file__).parent
OUT = HERE / 'dist' / 'vendure-plugins'
ASTRO_CSS = '/_astro/index@_@astro.CpJRZGi5.css'

DOC_HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=2">
<link rel="stylesheet" href="''' + ASTRO_CSS + '''">
<style>
.doc {{ display: grid; grid-template-columns: minmax(0, 1fr); gap: 24px; }}
@media (min-width: 1024px) {{ .doc {{ grid-template-columns: 240px minmax(0, 1fr); gap: 48px; align-items: start; }} }}
.doc-body {{ min-width: 0; }}
.doc-toc {{ position: sticky; top: 96px; }}
.doc-toc ul {{ list-style: none; padding: 0; margin: 0; }}
.doc-toc li {{ margin-bottom: 6px; }}
.doc-toc a {{ display: block; padding: 6px 10px; border-radius: 6px; font-size: 13px; color: var(--color-ink-700, #334155); text-decoration: none; }}
.doc-toc a:hover {{ background: var(--color-ink-50, #f8fafc); color: var(--color-ink-900); }}
.doc-toc a.lvl-2 {{ padding-left: 22px; font-size: 12px; color: var(--color-ink-500, #64748b); }}
.doc-body h2 {{ margin-top: 48px; font-size: 28px; font-weight: 700; color: var(--color-ink-900, #0f172a); scroll-margin-top: 96px; }}
.doc-body h2:first-child {{ margin-top: 0; }}
.doc-body h3 {{ margin-top: 28px; font-size: 20px; font-weight: 600; color: var(--color-ink-900); scroll-margin-top: 96px; }}
.doc-body p {{ font-size: 16px; line-height: 1.7; color: var(--color-ink-700, #334155); margin: 16px 0; }}
.doc-body ul, .doc-body ol {{ font-size: 16px; line-height: 1.75; color: var(--color-ink-700); padding-left: 22px; margin: 12px 0; }}
.doc-body li {{ margin: 6px 0; }}
.doc-body code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; background: var(--color-ink-50, #f8fafc); padding: 2px 6px; border-radius: 4px; border: 1px solid var(--color-ink-100, #e2e8f0); color: var(--color-ink-900); }}
.doc-code {{ background: #0f172a; color: #f1f5f9; padding: 18px 22px; border-radius: 10px; font-size: 13px; line-height: 1.6; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; overflow-x: auto; margin: 18px 0; }}
.doc-code .c {{ color: #64748b; }}
.doc-code .k {{ color: #fbbf24; }}
.doc-code .s {{ color: #86efac; }}
.callout {{ background: var(--color-accent-50, #fffbeb); border-left: 4px solid var(--color-accent-500, #f59e0b); border-radius: 8px; padding: 14px 18px; margin: 18px 0; font-size: 14px; color: var(--color-ink-800, #1e293b); }}
.callout.warn {{ background: #fef2f2; border-color: #ef4444; }}
.screenshot {{ margin: 22px 0; border: 1px solid var(--color-ink-200, #e2e8f0); border-radius: 12px; overflow: hidden; background: #fff; box-shadow: 0 1px 3px rgba(15,23,42,.08); }}
.screenshot-caption {{ padding: 10px 14px; background: var(--color-ink-50, #f8fafc); border-top: 1px solid var(--color-ink-100); font-size: 12px; color: var(--color-ink-600); text-align: center; }}
.doc-body .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 18px 0; border: 1px solid var(--color-ink-100); border-radius: 10px; max-width: 100%; }}
.doc-body .table-wrap::-webkit-scrollbar {{ height: 8px; }}
.doc-body .table-wrap::-webkit-scrollbar-thumb {{ background: var(--color-ink-300, #cbd5e1); border-radius: 4px; }}
.doc-body table {{ width: max-content; min-width: 100%; border-collapse: collapse; font-size: 14px; margin: 0; }}
.doc-body th, .doc-body td {{ text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--color-ink-100); white-space: nowrap; }}
.doc-body td {{ white-space: normal; max-width: 380px; }}
.doc-body tr:last-child th, .doc-body tr:last-child td {{ border-bottom: 0; }}
.doc-body th {{ background: var(--color-ink-50); font-weight: 600; color: var(--color-ink-900); }}
.doc-body td code {{ background: transparent; border: 0; padding: 0; font-size: 13px; white-space: nowrap; }}
/* Screenshot SVGs scale to viewport — no min-width so they shrink on mobile. */
.doc-body .screenshot {{ max-width: 100%; }}
.doc-body .screenshot svg {{ width: 100%; max-width: 100%; height: auto; display: block; }}
.doc-body .doc-code {{ overflow-x: auto; -webkit-overflow-scrolling: touch; max-width: 100%; }}
/* TOC: stay inside its column on mobile, hide horizontally if anything spills */
.doc-toc {{ min-width: 0; }}
.doc-toc ul, .doc-toc li, .doc-toc a {{ max-width: 100%; }}
.doc-toc a {{ min-height: 40px; }}
/* On mobile the TOC is a thin top-of-page block, not a full sidebar */
@media (max-width: 1023px) {{
    .doc-toc {{ background: var(--color-ink-50, #f8fafc); border-radius: 12px; padding: 14px 16px; position: relative !important; top: auto; }}
    .doc-toc ul {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .doc-toc li {{ margin: 0; }}
    .doc-toc a {{ padding: 8px 12px; min-height: 36px; background: #fff; border: 1px solid var(--color-ink-100); border-radius: 6px; font-size: 13px; }}
}}
</style>
</head>
<body>
<a href="#main" class="skip-link">Skip to content</a>
<header class="sticky top-0 z-40 border-b border-ink-100 bg-white/85 backdrop-blur supports-[backdrop-filter]:bg-white/70">
<div class="container-page flex items-center justify-between py-4">
<a href="/" class="flex items-center gap-2.5 group">
<span class="grid size-9 place-items-center rounded-lg bg-ink-900 text-white font-bold tracking-tight text-sm">HG</span>
<span class="font-bold text-ink-900 tracking-tight text-lg">Hulo Global</span>
</a>
<nav class="hidden md:block">
<ul class="flex items-center gap-6 text-sm font-medium text-ink-700">
<li><a href="/" class="hover:text-ink-900 py-3 px-2 inline-block">Home</a></li>
<li><a href="/vendure-plugins/" class="hover:text-ink-900 py-3 px-2 inline-block">Vendure plugins</a></li>
<li><a href="/vendure-plugins/{slug}/" class="hover:text-ink-900 py-3 px-2 inline-block">← Back to {title_short}</a></li>
</ul>
</nav>
</div>
</header>
<main id="main" class="container-page py-12 md:py-16">
<nav class="mb-6 text-sm text-ink-600">
<a href="/vendure-plugins/" class="hover:text-ink-900">Vendure plugins</a>
<span class="mx-2 text-ink-400">/</span>
<a href="/vendure-plugins/{slug}/" class="hover:text-ink-900">{title_short}</a>
<span class="mx-2 text-ink-400">/</span>
<span class="text-ink-900 font-medium">Manual</span>
</nav>
<h1 class="text-4xl md:text-5xl font-bold tracking-tight text-ink-900 mb-8">{title_short} — User Manual</h1>
<div class="doc">
'''

DOC_FOOT = '''
</div>
</main>
</body>
</html>
'''


def svg_panel(title, body_lines, width=720, height=360):
    """Render a labeled SVG mockup of an admin panel. Text is sized large
    enough to stay legible when the SVG is scaled down to mobile width.
    Carries role=img + title/desc for screen readers."""
    desc_lines = []
    lines = ''
    for i, line in enumerate(body_lines):
        if line.startswith('::'):
            items = line[2:].split('|')
            x = 30
            y = 110 + 38 * i
            row = ''
            for item in items:
                w = 18 + 9 * len(item)
                row += f'<rect x="{x}" y="{y - 16}" width="{w}" height="26" rx="13" fill="#dbeafe" stroke="#93c5fd"/><text x="{x + w/2}" y="{y + 3}" text-anchor="middle" font-size="13" font-family="system-ui" fill="#1e3a8a">{html.escape(item)}</text>'
                x += w + 10
            lines += row
            desc_lines.append(' / '.join(items))
        elif line.startswith('//'):
            lbl = line[2:]
            y = 110 + 38 * i
            lines += f'<rect x="30" y="{y - 16}" width="360" height="30" rx="5" fill="#fff" stroke="#cbd5e1"/><text x="40" y="{y + 4}" font-size="14" font-family="ui-monospace,monospace" fill="#64748b">{html.escape(lbl)}</text>'
            desc_lines.append(f'Input: {lbl}')
        elif line.startswith('=='):
            lines += f'<text x="30" y="{110 + 38 * i}" font-size="15" font-weight="600" font-family="system-ui" fill="#0f172a">{html.escape(line[2:])}</text>'
            desc_lines.append(line[2:])
        else:
            lines += f'<text x="30" y="{110 + 38 * i}" font-size="14" font-family="system-ui" fill="#475569">{html.escape(line)}</text>'
            desc_lines.append(line)

    desc = ' — '.join(desc_lines).replace('"', "'")
    title_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    return f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="{title_id}-t {title_id}-d" style="width: 100%; height: auto; display: block;">
<title id="{title_id}-t">{html.escape(title)}</title>
<desc id="{title_id}-d">Admin panel mockup. {html.escape(desc)}</desc>
<rect width="{width}" height="{height}" fill="#fafafa"/>
<rect x="0" y="0" width="{width}" height="52" fill="#0f1419"/>
<text x="20" y="33" font-size="16" font-weight="600" font-family="system-ui" fill="#fff">Vendure Admin</text>
<circle cx="{width-30}" cy="26" r="11" fill="#1e293b"/>
<text x="20" y="85" font-size="20" font-weight="700" font-family="system-ui" fill="#0f172a">{html.escape(title)}</text>
{lines}
</svg>'''


# ─────────────────────────────────────────────────────────────────────────
# Email Tracking
# ─────────────────────────────────────────────────────────────────────────

EMAIL_TRACKING_MANUAL = {
    'slug': 'email-tracking',
    'title_short': 'Email Tracking',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Email Tracking</strong> logs every transactional email your Vendure server sends. It wraps the <code>@vendure/email-plugin</code> sender so opens and clicks are tracked automatically, plus exposes a service for ad-hoc sends from your own plugin code.</p>
<p>Data captured per email:</p>
<ul>
<li>Send: recipient, subject, type, related order / customer / invoice, the SMTP response, the SMTP <code>messageId</code>.</li>
<li>Opens: per-open history (last 50) with timestamp, IP, user-agent and parsed client (Gmail web, Outlook desktop, Apple Mail iOS …).</li>
<li>Clicks: per-click history (last 50) with timestamp, target URL, IP, user-agent.</li>
<li>Bounces / complaints: status update + auto-add to the suppression list.</li>
</ul>
'''),
        ('install', 'Install', '''
<p>One package, one line of config, one migration. The fastest way is the bundled installer:</p>
<div class="doc-code">curl -sSL https://huloglobal.com/vendure-plugins/email-tracking/install.sh | bash</div>
<p>Or by hand:</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-email-tracking

<span class="c"># 2. Register in vendure-config.ts</span>
import {{ <span class="k">EmailTrackingPlugin</span>, <span class="k">TrackingEmailSender</span> }} from <span class="s">'@huloglobal/vendure-plugin-email-tracking'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="k">EmailTrackingPlugin</span>.init({{
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_EMAIL_TRACKING</span>,
    }}),
    <span class="c">// also pass TrackingEmailSender to the @vendure/email-plugin:</span>
    EmailPlugin.init({{
      emailSender: new <span class="k">TrackingEmailSender</span>(),
      <span class="c">// ... your existing email-plugin options ...</span>
    }}),
  ],
}};

<span class="c"># 3. Generate + run migration</span>
yarn migration:generate AddEmailTrackingTables
yarn migration:run</div>
<p>Restart Vendure. The <strong>Email Log</strong> tab appears in the admin nav immediately.</p>
'''),
        ('admin-ui', 'Admin UI tour', '''
<p>The Email Log page is mounted at <code>/admin/extensions/email-log</code> (or via the side nav).</p>
<div class="screenshot">''' + svg_panel('Email Log — list view', [
    '== Status totals',
    '::All 1247 | Sent 1198 | Failed 12 | Deferred 8 | Bounced 14 | Opens 540 | Clicks 87',
    '== Filters',
    '// Filter recipient…',
    '// Filter type…',
    '== Recent emails',
    '#1247  29 May  order-confirmation  alice@example.com  Sent  ●●●  12 opens, 3 clicks',
    '#1246  29 May  password-reset      bob@example.com    Sent  ●    1 open, 0 clicks',
    '#1245  28 May  invoice             carol@example.com  Sent  ●●●● 8 opens, 2 clicks',
], height=410) + '''
<div class="screenshot-caption">List view — colour-coded status pills, per-row open/click counts, click any row for the timeline.</div>
</div>
<p>Click <strong>Details</strong> on any row to expand the timeline. You'll see:</p>
<ul>
<li><strong>Header block</strong> — From / To / BCC / subject / context</li>
<li><strong>SMTP block</strong> — message-id, SMTP response, any error message</li>
<li><strong>Open block</strong> — first/last open times, first-open IP and UA</li>
<li><strong>Open history table</strong> — every open with time, IP, UA</li>
<li><strong>Click history table</strong> — every click with time, target URL, IP, UA</li>
</ul>
<div class="callout">Open and click history are capped at the most recent 50 entries per email. The lifetime totals (<code>openCount</code> / <code>clickCount</code>) keep counting beyond 50.</div>
'''),
        ('suppression', 'Suppression list', '''
<p>The plugin maintains an <code>email_suppression</code> table — recipients who should never be sent to. The table is populated automatically when the bounce webhook reports a hard bounce or a complaint, and you can add entries manually.</p>
<p>When <code>sendTracked()</code> is called for a suppressed recipient, the row is written to <code>email_log</code> with <code>status='suppressed'</code> and <code>errorMessage='Recipient is on the suppression list'</code> — but no SMTP call is made.</p>
<h3>Adding entries manually</h3>
<div class="doc-code">curl -X POST https://shop.example.com/email-track/suppression \\
  -H "Content-Type: application/json" \\
  -d '{{"recipient":"angry@example.com","reason":"manual","note":"Asked to be removed via support"}}'</div>
<h3>Lifting a suppression</h3>
<div class="doc-code">curl -X DELETE https://shop.example.com/email-track/suppression/angry@example.com</div>
<h3>Listing the table</h3>
<div class="doc-code">curl https://shop.example.com/email-track/suppression?take=200</div>
'''),
        ('webhook', 'Bounce webhook', '''
<p>Wire your postmaster integration (or scheduled DSN parser) to POST to <code>/email-track/bounce</code>:</p>
<div class="doc-code">{{
  "messageId": "&lt;abc@gmail.com&gt;",       <span class="c">// the smtpMessageId from the original send</span>
  "status": "bounced",                       <span class="c">// or 'complained'</span>
  "reason": "550 5.1.1 The email account ..."
}}</div>
<p>The matching <code>email_log</code> row is updated and the recipient is auto-added to the suppression list. The endpoint is unauthenticated — gate it behind a shared secret header if you expose it to the public internet.</p>
'''),
        ('analytics', 'Per-template analytics', '''
<p>For an aggregated view of how each email <em>type</em> performs, hit:</p>
<div class="doc-code">GET /email-track/log/stats/by-template?fromDays=30</div>
<p>Returns:</p>
<div class="doc-code">{{
  "days": 30,
  "types": [
    {{
      "type": "order-confirmation",
      "sent": 1247,
      "opened": 540,
      "clicked": 87,
      "bounced": 14,
      "failed": 12,
      "suppressed": 3,
      "openRate": 0.433,
      "clickRate": 0.070,
      "ctor": 0.161             <span class="c">// click-to-open</span>
    }},
    ...
  ]
}}</div>
'''),
        ('csv-export', 'CSV export', '''
<p>The list endpoint has a CSV mirror. Same filters, same shape:</p>
<div class="doc-code">GET /email-track/log/export.csv?status=sent&from=2026-05-01</div>
<p>Up to 50 000 rows per call.</p>
'''),
        ('endpoints', 'HTTP endpoints', '''
<table>
<thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
<tbody>
<tr><td>GET</td><td><code>/email-track/open/:id.gif</code></td><td>Public pixel — logs an open then serves a 1×1 GIF</td></tr>
<tr><td>GET</td><td><code>/email-track/click/:id?u=&lt;url&gt;</code></td><td>Public click redirector — logs then 302s to the original URL</td></tr>
<tr><td>POST</td><td><code>/email-track/bounce</code></td><td>Bounce / complaint webhook</td></tr>
<tr><td>GET</td><td><code>/email-track/log</code></td><td>Admin: paginated log with filters</td></tr>
<tr><td>GET</td><td><code>/email-track/log/summary</code></td><td>Admin: status totals tile</td></tr>
<tr><td>GET</td><td><code>/email-track/log/:id</code></td><td>Admin: full detail (incl. opens + clicks arrays)</td></tr>
<tr><td>GET</td><td><code>/email-track/log/stats/by-template</code></td><td>Admin: per-template aggregates</td></tr>
<tr><td>GET</td><td><code>/email-track/log/export.csv</code></td><td>Admin: CSV export</td></tr>
<tr><td>GET</td><td><code>/email-track/suppression</code></td><td>Admin: list suppressions</td></tr>
<tr><td>POST</td><td><code>/email-track/suppression</code></td><td>Admin: add a suppression</td></tr>
<tr><td>DELETE</td><td><code>/email-track/suppression/:recipient</code></td><td>Admin: lift a suppression</td></tr>
</tbody>
</table>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<h3>Opens aren't being recorded</h3>
<p>Many email clients prefetch images through a proxy (Gmail's <code>googleimageproxy</code>, Outlook's SafeLinks). The plugin recognises common proxies and flags those opens as <code>isBot: true</code> on the open entry — they still count in <code>openCount</code> but you can filter them out in the UI.</p>
<h3>Clicks redirect to a "blank target" 400</h3>
<p>The redirector refuses URLs that don't start with <code>http://</code> or <code>https://</code> — including <code>javascript:</code>, <code>data:</code>, <code>mailto:</code>. The link rewriter already excludes <code>mailto:</code> and unsubscribe-style links from rewriting, so you shouldn't see this in normal use.</p>
<h3>Suppression list isn't catching recent bounces</h3>
<p>Make sure your bounce / DSN webhook is hitting <code>/email-track/bounce</code> with a <code>messageId</code> that matches what your SMTP transport returned at send time. Gmail returns the messageId in the <code>250 2.0.0 OK 1234567890 abc@gmail.com</code> response — the plugin stores it as <code>smtpMessageId</code> on the EmailLog row.</p>
'''),
    ],
}


# ─────────────────────────────────────────────────────────────────────────
# Geo Block
# ─────────────────────────────────────────────────────────────────────────

GEO_BLOCK_MANUAL = {
    'slug': 'geo-block',
    'title_short': 'Geo Block',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Geo Block</strong> gives you per-channel control over who can reach your Vendure storefront. Pick from 37 region presets, add countries manually, soft-block markets you don't ship to (so they can still browse), allow specific IPs to bypass all rules, and audit every block decision.</p>
<p>Two storefront integration modes:</p>
<ul>
<li><strong>Site-config polling</strong> — Storefront calls <code>/geo-block/site-config</code> once on boot, caches the resolved rules, and decides client-side. Cheapest on the server.</li>
<li><strong>Per-request check</strong> — Storefront calls <code>/geo-block/check</code> on entry, gets a fresh decision per visitor (also logs to the audit table). Use when you want stats.</li>
</ul>
'''),
        ('install', 'Install', '''
<div class="doc-code">curl -sSL https://huloglobal.com/vendure-plugins/geo-block/install.sh | bash</div>
<p>Or by hand:</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-geo-block

<span class="c"># 2. Register in vendure-config.ts</span>
import {{ <span class="k">GeoBlockPlugin</span> }} from <span class="s">'@huloglobal/vendure-plugin-geo-block'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="k">GeoBlockPlugin</span>.init({{
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_GEO_BLOCK</span>,
      <span class="c">// Optional: a one-shot maintenance lockdown window</span>
      maintenanceWindow: {{
        startsAt: <span class="s">'2026-07-15T02:00:00Z'</span>,
        endsAt:   <span class="s">'2026-07-15T04:00:00Z'</span>,
        allowedIps: [<span class="s">'203.0.113.0/24'</span>],
      }},
    }}),
  ],
}};

<span class="c"># 3. Migration</span>
yarn migration:generate AddGeoBlockTables
yarn migration:run</div>
'''),
        ('admin-ui', 'Admin UI tour', '''
<p>The Site Access page is mounted at <code>/admin/extensions/geo-block</code>. Five tabs:</p>
<h3>Rules</h3>
<div class="screenshot">''' + svg_panel('Site access — Rules tab', [
    '== Channel: Elite [GEO-BLOCK ON]  [Full block]',
    '== Mode',
    '::Full block (selected) | Soft block (browse-only)',
    '== Strategy',
    '::Allow specific places (selected) | Worldwide except blocked',
    '== Allowed regions (3 picked)',
    '::UK only ✓ | British Isles ✓ | EU | EEA | EFTA | Schengen | Nordic | DACH',
    '::G7 | G20 | NATO | OECD | Commonwealth | English-speaking | …',
    '== UK subdivisions',
    '::England ✓ | Wales ✓ | Scotland | Northern Ireland',
], height=400) + '''
<div class="screenshot-caption">Rules tab — pick mode, strategy, regions, sub-regions. Live preview shows resolved country list at the bottom.</div>
</div>

<h3>Block page</h3>
<p>Customise the block page per channel: a free-text message, optional redirect URL (when set, blocked visitors are 302'd there instead), optional logo URL.</p>

<h3>IP allowlist</h3>
<p>Add specific IPs or IPv4 CIDR ranges (<code>203.0.113.0/24</code>) that bypass every rule. Use for your office, oncall engineers, payment processor probes, monitoring.</p>

<h3>Simulate</h3>
<div class="screenshot">''' + svg_panel('Site access — Simulate tab', [
    '== Test a hypothetical visitor',
    '// Country code: US',
    '// UK region (optional): —',
    '// IP address (optional): 8.8.8.8',
    '== [Run simulation]',
    '== Result',
    '🚫 Blocked  (country-not-allowed)',
], height=320) + '''
<div class="screenshot-caption">Simulate tab — try any country / IP combination without saving anything to production.</div>
</div>

<h3>Stats</h3>
<p>Last N days of block decisions: total blocks, soft blocks, unique blocked IPs, top blocked countries, daily series, breakdown by reason.</p>
'''),
        ('presets', 'Region presets', '''
<p>The plugin ships 37 hand-curated presets, grouped in the picker by kind:</p>
<table>
<thead><tr><th>Group</th><th>Presets</th></tr></thead>
<tbody>
<tr><td>Everywhere</td><td>WORLDWIDE</td></tr>
<tr><td>Geography</td><td>UK_ONLY, BRITISH_ISLES, UK_CROWN_DEPENDENCIES, EUROPE, NORDIC, BALTIC, BENELUX, IBERIA, BALKANS, NORTH_AMERICA, CENTRAL_AMERICA, CARIBBEAN, SOUTH_AMERICA, LATAM, OCEANIA, ANZ, MENA, APAC, EAST_ASIA, SOUTH_ASIA, AFRICA</td></tr>
<tr><td>Trade blocs</td><td>EU, EEA, EFTA, GCC, ASEAN</td></tr>
<tr><td>Political / economic</td><td>SCHENGEN, G7, G20, BRICS, OECD, NATO, FIVE_EYES</td></tr>
<tr><td>Language / cultural</td><td>DACH, ENGLISH_SPEAKING, COMMONWEALTH</td></tr>
</tbody>
</table>
<p>Fetch the live catalogue (with country counts + descriptions):</p>
<div class="doc-code">GET /geo-block/presets</div>
'''),
        ('storefront', 'Storefront integration', '''
<h3>Polling site-config (cheap)</h3>
<div class="doc-code">// On storefront boot, once per channel
const res = await fetch(<span class="s">'https://shop.example.com/geo-block/site-config'</span>, {{
  headers: {{ <span class="s">'vendure-token'</span>: <span class="k">CHANNEL_TOKEN</span> }},
}});
const cfg = await res.json();
<span class="c">// Cache cfg.geoBlock for ~60s, decide client-side based on the visitor's country.</span></div>

<h3>Per-request check (with logging)</h3>
<div class="doc-code">// In your storefront middleware
const res = await fetch(<span class="s">'https://shop.example.com/geo-block/check'</span>, {{
  headers: {{
    <span class="s">'vendure-token'</span>: <span class="k">CHANNEL_TOKEN</span>,
    <span class="s">'cf-ipcountry'</span>: req.headers[<span class="s">'cf-ipcountry'</span>],   <span class="c">// proxy already resolved</span>
  }},
}});
const verdict = await res.json();
if (!verdict.allowed) {{
  if (verdict.redirectUrl) return res.redirect(302, verdict.redirectUrl);
  return res.render(<span class="s">'blocked'</span>, {{ message: verdict.message, mode: verdict.mode }});
}}</div>

<div class="callout">In <strong>soft</strong> mode the storefront should render the full site but include a banner explaining you don't ship to the visitor's country, and hide the checkout button. The plugin returns <code>mode: 'soft'</code> on the verdict to make this decision easy.</div>
'''),
        ('endpoints', 'HTTP endpoints', '''
<table>
<thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
<tbody>
<tr><td>GET</td><td><code>/geo-block/site-config</code></td><td>Public: resolved channel rules (cached client-side)</td></tr>
<tr><td>GET</td><td><code>/geo-block/check</code></td><td>Public: per-request decision (logs to audit table)</td></tr>
<tr><td>GET</td><td><code>/geo-block/presets</code></td><td>Public: 37-preset catalogue</td></tr>
<tr><td>GET</td><td><code>/geo-block/admin/channels</code></td><td>Admin: list channels + rules</td></tr>
<tr><td>POST</td><td><code>/geo-block/admin/save</code></td><td>Admin: save a channel's rules</td></tr>
<tr><td>GET</td><td><code>/geo-block/admin/stats</code></td><td>Admin: block totals + top countries</td></tr>
<tr><td>POST</td><td><code>/geo-block/admin/simulate</code></td><td>Admin: dry-run a visitor</td></tr>
<tr><td>POST</td><td><code>/geo-block/admin/gc</code></td><td>Admin: prune old audit rows</td></tr>
</tbody>
</table>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<h3>Every visitor is blocked but my rules look right</h3>
<p>Check the <em>Rules</em> tab's "Resolved allow-list" preview at the bottom — it shows the exact list that would be applied on save. If the list says <strong>nothing is allowed</strong>, you've probably picked a preset and then blocked every country in it.</p>
<h3>Cloudflare IP appears as the visitor IP</h3>
<p>The plugin reads the upstream proxy headers in this order: <code>cf-connecting-ip</code> → <code>true-client-ip</code> → <code>x-real-ip</code> → <code>x-forwarded-for[0]</code> → <code>req.ip</code>. Make sure Cloudflare's <code>cf-connecting-ip</code> is reaching your Vendure server (it's a default Cloudflare header).</p>
<h3>Stats panel is empty</h3>
<p>Stats are populated by the per-request <code>/check</code> endpoint, not by <code>/site-config</code>. If your storefront only polls <code>site-config</code>, no audit rows are written. Either switch to <code>/check</code> or call <code>/check</code> as well in your storefront middleware.</p>
'''),
    ],
}


# ─────────────────────────────────────────────────────────────────────────
# Visitor Analytics
# ─────────────────────────────────────────────────────────────────────────

VISITOR_ANALYTICS_MANUAL = {
    'slug': 'visitor-analytics',
    'title_short': 'Visitor Analytics',
    'sections': [
        ('overview', 'Overview', '''
<p><strong>Visitor Analytics</strong> is a self-hosted, privacy-aware visitor journey tracker. Page views, time-on-page, exit pages, configurable funnel, conversion goals, UTM attribution, bot detection. All data lives in your own database; nothing is sent to a third party.</p>
<p>Survives login — a visitor's pre-signin events and post-signin events share the same <code>visitorId</code>, so funnel analysis works across the auth boundary.</p>
'''),
        ('install', 'Install', '''
<div class="doc-code">curl -sSL https://huloglobal.com/vendure-plugins/visitor-analytics/install.sh | bash</div>
<p>Or by hand:</p>
<div class="doc-code"><span class="c"># 1. Install</span>
yarn add @huloglobal/vendure-plugin-visitor-analytics

<span class="c"># 2. Register in vendure-config.ts</span>
import {{ <span class="k">VisitorAnalyticsPlugin</span> }} from <span class="s">'@huloglobal/vendure-plugin-visitor-analytics'</span>;

export const config: VendureConfig = {{
  plugins: [
    <span class="k">VisitorAnalyticsPlugin</span>.init({{
      publicBaseUrl: <span class="s">'https://shop.example.com'</span>,
      licenceKey: process.env.<span class="k">HULO_LICENCE_KEY_VISITOR_ANALYTICS</span>,
      <span class="c">// Privacy options — these are the defaults</span>
      honorDoNotTrack: <span class="k">true</span>,
      anonymizeIp: <span class="k">true</span>,
      requireConsent: <span class="k">false</span>,
      dropBotEvents: <span class="k">false</span>,
    }}),
  ],
}};

<span class="c"># 3. Migration</span>
yarn migration:generate AddVisitorAnalyticsTables
yarn migration:run</div>
'''),
        ('storefront', 'Storefront integration', '''
<p>The plugin ships an ingest endpoint at <code>POST /ees/track</code>. Your storefront calls it with batches of events.</p>
<p>Drop a small client into your storefront to record pageviews automatically:</p>
<div class="doc-code"><span class="c">// utils/visitor-tracking.ts</span>
<span class="k">const</span> ENDPOINT = <span class="s">'https://shop.example.com/ees/track'</span>;
<span class="k">const</span> CHANNEL_ID = 1;
<span class="k">let</span> queue: any[] = [];
<span class="k">let</span> flushTimer: any;

<span class="k">export function</span> recordPageview(url: string, title: string) {{
  queue.push({{ type: <span class="s">'pageview'</span>, url, title, clientTs: Date.now() }});
  scheduleFlush();
}}

<span class="k">export function</span> recordEvent(type: string, meta: any) {{
  queue.push({{ type, url: location.pathname + location.search, meta, clientTs: Date.now() }});
  scheduleFlush();
}}

<span class="k">function</span> scheduleFlush() {{
  clearTimeout(flushTimer);
  flushTimer = setTimeout(flush, 1000);
}}
<span class="k">function</span> flush() {{
  <span class="k">if</span> (!queue.length) <span class="k">return</span>;
  <span class="k">const</span> body = JSON.stringify({{ channelId: CHANNEL_ID, events: queue }});
  queue = [];
  <span class="c">// sendBeacon survives navigation</span>
  navigator.sendBeacon?.(ENDPOINT, body) ||
    fetch(ENDPOINT, {{ method: <span class="s">'POST'</span>, body, headers: {{ <span class="s">'content-type'</span>: <span class="s">'application/json'</span> }}, keepalive: <span class="k">true</span> }});
}}</div>
<p>Then call <code>recordPageview()</code> on every route change. For custom events (add-to-cart, search, signup, etc.) call <code>recordEvent(type, meta)</code> at the appropriate point.</p>
'''),
        ('goals', 'Conversion goals', '''
<p>A conversion goal is a URL glob that, when matched by a pageview, counts that visitor as having completed the goal. Patterns support:</p>
<ul>
<li><code>*</code> — match zero or more chars within a path segment</li>
<li><code>**</code> — match zero or more segments (including <code>/</code>)</li>
<li>everything else is a literal substring (case-insensitive)</li>
</ul>
<h3>Examples</h3>
<table>
<thead><tr><th>Pattern</th><th>Matches</th></tr></thead>
<tbody>
<tr><td><code>/checkout/thank-you/*</code></td><td>Order confirmation page</td></tr>
<tr><td><code>/signup</code></td><td>Exact: signup landing</td></tr>
<tr><td><code>**/wishlist</code></td><td>Any wishlist page on any subdomain</td></tr>
<tr><td><code>/contact?*</code></td><td>Contact form with any query</td></tr>
</tbody>
</table>
<h3>Creating a goal</h3>
<div class="doc-code">curl -X POST https://shop.example.com/ees/goals \\
  -H "Content-Type: application/json" \\
  -d '{{
    "channelId": 1,
    "name": "Checkout completed",
    "urlPattern": "/checkout/thank-you/*",
    "valueMinor": 5000,
    "enabled": true
  }}'</div>
<p>Once created, every matching pageview is tagged with the <code>goalId</code> on its <code>visitor_event</code> row. The admin stats endpoint at <code>/ees/goals/stats?days=30</code> aggregates completions per goal.</p>
'''),
        ('privacy', 'Privacy controls', '''
<p>The plugin defaults to privacy-respecting behaviour. Toggle as needed:</p>
<table>
<thead><tr><th>Option</th><th>Default</th><th>Effect</th></tr></thead>
<tbody>
<tr><td><code>honorDoNotTrack</code></td><td><code>true</code></td><td>If the visitor's request has <code>DNT: 1</code> or <code>Sec-GPC: 1</code>, the endpoint returns 200 with <code>skipped: 'dnt'</code> and writes nothing.</td></tr>
<tr><td><code>anonymizeIp</code></td><td><code>true</code></td><td>The stored <code>ip</code> column drops the last octet of IPv4 (or last 80 bits of IPv6). The <code>ipHash</code> column still uses the raw IP so "unique visitor" counts remain accurate.</td></tr>
<tr><td><code>requireConsent</code></td><td><code>false</code></td><td>If on, the endpoint returns <code>skipped: 'no-consent'</code> unless the body sets <code>consent: true</code> or the request has cookie <code>ees_consent=1</code>.</td></tr>
<tr><td><code>dropBotEvents</code></td><td><code>false</code></td><td>If on, known bot UAs are dropped entirely. Default off so bot share is visible on the dashboard.</td></tr>
</tbody>
</table>
'''),
        ('bot-detection', 'Bot detection', '''
<p>Every event is checked against an embedded list of ~45 bot UA patterns: Googlebot, Bingbot, Facebook scrapers, monitoring probes (UptimeRobot, Datadog, Pingdom), HTTP libraries (curl, wget, axios, requests, node-fetch), headless browsers (HeadlessChrome, Puppeteer, Playwright).</p>
<p>By default these events are stored with <code>isBot: true</code> so you can see bot share but they're excluded from "real human" counts in the admin dashboards. Flip <code>dropBotEvents: true</code> to skip ingest entirely.</p>
'''),
        ('admin-ui', 'Admin UI tour', '''
<div class="screenshot">''' + svg_panel('Visitor Journey — Summary', [
    '== Last 30 days',
    '::42,135 visitors | 89,210 sessions | 312,447 pageviews | avg 2:18 on page',
    '== Daily series',
    '▁▂▄▅▇▆▇█▇▆▅▄▃▄▅▆▇▆▅▄▃▂▃▄▅▆▇█▇▆',
    '== Top sources',
    '#1  google.com         18,402 visits',
    '#2  direct             12,089 visits',
    '#3  twitter.com         3,541 visits',
    '#4  facebook.com        2,170 visits',
], height=400) + '''
<div class="screenshot-caption">Summary — top-line counters, daily series, top sources, top countries.</div>
</div>
<p>Other admin views:</p>
<ul>
<li><strong>Funnel</strong> — drop-off per configured step</li>
<li><strong>Exit pages</strong> — where visitors leave</li>
<li><strong>Top events</strong> — custom event distribution</li>
<li><strong>Top pages</strong> — most-visited URLs</li>
<li><strong>Live</strong> — SSE-streamed real-time count</li>
<li><strong>Journey</strong> — full per-visitor timeline (drill from any of the views above)</li>
</ul>
'''),
        ('endpoints', 'HTTP endpoints', '''
<table>
<thead><tr><th>Method</th><th>Path</th><th>Description</th></tr></thead>
<tbody>
<tr><td>POST</td><td><code>/ees/track</code></td><td>Public: ingest batch of events</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/summary</code></td><td>Admin: top-line + daily series</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/sources</code></td><td>Admin: top sources</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/top-pages</code></td><td>Admin: most-visited URLs</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/funnel</code></td><td>Admin: configurable funnel</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/exit-pages</code></td><td>Admin: top exit pages</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/top-events</code></td><td>Admin: top custom events</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/live</code></td><td>Admin: SSE live-now stream</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/journey/:visitorId</code></td><td>Admin: per-visitor timeline</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/recent</code></td><td>Admin: recent events</td></tr>
<tr><td>GET</td><td><code>/ees/visitors/export.csv</code></td><td>Admin: CSV export (max 90 days)</td></tr>
<tr><td>GET</td><td><code>/ees/goals</code></td><td>Admin: list conversion goals</td></tr>
<tr><td>POST</td><td><code>/ees/goals</code></td><td>Admin: create a goal</td></tr>
<tr><td>PUT</td><td><code>/ees/goals/:id</code></td><td>Admin: update a goal</td></tr>
<tr><td>DELETE</td><td><code>/ees/goals/:id</code></td><td>Admin: delete a goal</td></tr>
<tr><td>GET</td><td><code>/ees/goals/stats</code></td><td>Admin: per-goal completion stats</td></tr>
</tbody>
</table>
'''),
        ('troubleshooting', 'Troubleshooting', '''
<h3>Visitors aren't being counted</h3>
<p>Check the response of <code>POST /ees/track</code> — if <code>skipped: 'dnt'</code> the visitor is sending a Do-Not-Track header (and your <code>honorDoNotTrack</code> option is on, which it is by default). Set the option to <code>false</code> to override.</p>
<h3>Goals don't seem to fire</h3>
<p>The matcher only runs for <code>type: 'pageview'</code> events — custom events (<code>type: 'event'</code>) don't trigger goals. Also, the goal cache refreshes every 60s; new goals start counting after that.</p>
<h3>MaxMind geo isn't populating</h3>
<p>The plugin uses the <code>geolite2-redist</code> package to download the GeoLite2 City DB on first use. If the download fails (network, sandboxed env), geo fields stay null. You can force a re-download with <code>npx geolite2-redist refresh</code> from your Vendure project root.</p>
'''),
    ],
}


def wrap_tables(html_str):
    """Wrap every <table> in a scroll container so it doesn't overflow on mobile."""
    return re.sub(
        r'(<table>.*?</table>)',
        r'<div class="table-wrap" role="region" aria-label="Data table" tabindex="0">\1</div>',
        html_str,
        flags=re.DOTALL,
    )

def render_manual(m):
    canonical = f'https://huloglobal.com/vendure-plugins/{m["slug"]}/docs/'
    head = DOC_HEAD.format(
        title=f"{m['title_short']} — User Manual | Hulo Global",
        description=f"Complete user manual for the @huloglobal/vendure-plugin-{m['slug']} Vendure plugin: install, admin UI, endpoints, troubleshooting.",
        canonical=canonical,
        slug=m['slug'],
        title_short=m['title_short'],
    )
    toc_items = '\n'.join(
        f'<li><a href="#{slug}">{html.escape(title)}</a></li>'
        for slug, title, _ in m['sections']
    )
    body_items = '\n'.join(
        f'<section id="{slug}"><h2>{html.escape(title)}</h2>{wrap_tables(content)}</section>'
        for slug, title, content in m['sections']
    )
    return head + f'''
<nav class="doc-toc">
<p class="text-xs uppercase tracking-wider text-ink-500 font-semibold mb-3">On this page</p>
<ul>{toc_items}</ul>
</nav>
<article class="doc-body">{body_items}</article>
''' + DOC_FOOT


def main():
    for m in (EMAIL_TRACKING_MANUAL, GEO_BLOCK_MANUAL, VISITOR_ANALYTICS_MANUAL):
        d = OUT / m['slug'] / 'docs'
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(render_manual(m), encoding='utf-8')
        print(f"wrote {d / 'index.html'}")


if __name__ == '__main__':
    main()
