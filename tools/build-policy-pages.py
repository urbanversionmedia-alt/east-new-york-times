#!/usr/bin/env python3
"""Generate /ethics/ and /corrections/ policy pages for eastnewyorktimes.com."""
import os, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://eastnewyorktimes.com"
EFFECTIVE = "September 1, 2026"        # date the policy takes effect (shown to readers)
EFFECTIVE_ISO = "2026-09-01"
PUBLISHED_ISO = "2026-08-19"           # date the page went live (schema datePublished)

CSS = """
    :root {
      --bg: #0d1117; --surface: #161b22; --surface-2: #1c2128; --surface-3: #21262d;
      --border: #2d333b; --divider: #21262d;
      --text: #e6edf3; --text-muted: #8b949e; --text-faint: #484f58;
      --accent: #e8952a; --accent-hover: #d4820a; --accent-dim: rgba(232,149,42,0.12);
      --font-display: 'Clash Display', 'Georgia', serif;
      --font-body: 'Satoshi', 'Inter', sans-serif;
      --font-serif: 'Georgia', 'Times New Roman', serif;
      --radius: 6px; --radius-lg: 12px;
      --transition: 200ms cubic-bezier(0.16,1,0.3,1);
      --max-w: 1200px;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; scroll-padding-top: 100px; -webkit-font-smoothing: antialiased; }
    body { font-family: var(--font-body); font-size: 1rem; line-height: 1.65; color: var(--text); background: var(--bg); overflow-x: hidden; }
    img { display: block; max-width: 100%; height: auto; }
    a { color: inherit; text-decoration: none; }
    ul, ol { list-style: none; }
    h1,h2,h3 { font-family: var(--font-display); line-height: 1.18; letter-spacing: -0.01em; text-wrap: balance; }
    :focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 3px; }
    .container { width: 100%; max-width: var(--max-w); margin-inline: auto; padding-inline: clamp(1.25rem, 5vw, 4rem); }

    .topbar { background: var(--accent); color: #0d1117; font-size: 0.75rem; font-weight: 700;
      letter-spacing: 0.08em; text-transform: uppercase; padding: 0.4rem 0; text-align: center; }
    .header { position: sticky; top: 0; z-index: 50; background: rgba(13,17,23,0.92);
      backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); }
    .header-inner { display: flex; align-items: center; justify-content: space-between;
      gap: 1.5rem; padding-block: 0.85rem; flex-wrap: wrap; }
    .masthead-name { display: block; font-family: var(--font-display); font-weight: 700;
      font-size: 1.35rem; letter-spacing: -0.02em; }
    .masthead-name span { color: var(--accent); }
    .masthead-sub { display: block; font-size: 0.62rem; letter-spacing: 0.16em;
      text-transform: uppercase; color: var(--text-muted); margin-top: 0.15rem; }
    .nav ul { display: flex; gap: 1.4rem; flex-wrap: wrap; }
    .nav a { font-size: 0.85rem; font-weight: 500; color: var(--text-muted); transition: color var(--transition); }
    .nav a:hover { color: var(--text); }
    .nav a.active { color: var(--accent); }

    .policy-hero { padding: clamp(2.5rem, 6vw, 4.5rem) 0 2rem; border-bottom: 1px solid var(--border); }
    .eyebrow { display: inline-block; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.14em;
      text-transform: uppercase; color: var(--accent); background: var(--accent-dim);
      padding: 0.3rem 0.7rem; border-radius: 3px; margin-bottom: 1.1rem; }
    .policy-hero h1 { font-size: clamp(1.9rem, 4.6vw, 2.9rem); margin-bottom: 1rem; }
    .policy-hero .standfirst { color: var(--text-muted); font-size: 1.05rem; max-width: 64ch; }
    .policy-meta { margin-top: 1.35rem; font-size: 0.78rem; letter-spacing: 0.06em;
      text-transform: uppercase; color: var(--text-faint); }

    .policy-layout { display: grid; grid-template-columns: 260px minmax(0,1fr);
      gap: clamp(2rem, 4vw, 3.5rem); padding-block: clamp(2rem, 5vw, 3.5rem); align-items: start; }
    .sidebar { position: sticky; top: 105px; display: grid; gap: 1.5rem; }
    .panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.35rem; }
    .panel h2 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
      color: var(--accent); margin-bottom: 1rem; font-family: var(--font-body); }
    .toc li + li { margin-top: 0.6rem; }
    .toc a { font-size: 0.88rem; color: var(--text-muted); transition: color var(--transition); }
    .toc a:hover { color: var(--accent); }
    .panel p { font-size: 0.88rem; color: var(--text-muted); }
    .panel p + p { margin-top: 0.6rem; }
    .panel a.inline { color: var(--accent); }

    .prose { max-width: 72ch; }
    .prose section + section { margin-top: clamp(2.2rem, 4vw, 3rem); }
    .prose h2 { font-size: clamp(1.3rem, 2.7vw, 1.65rem); padding-bottom: 0.6rem;
      margin-bottom: 1.1rem; border-bottom: 2px solid var(--accent); }
    .prose h3 { font-size: 1.05rem; margin-top: 1.6rem; margin-bottom: 0.6rem; color: var(--text); }
    .prose p { color: #c9d1d9; margin-bottom: 1rem; }
    .prose p:last-child { margin-bottom: 0; }
    .prose strong { color: var(--text); font-weight: 700; }
    .prose ul.bullets { margin: 0 0 1rem 0; }
    .prose ul.bullets li { position: relative; padding-left: 1.15rem; color: #c9d1d9; margin-bottom: 0.6rem; }
    .prose ul.bullets li::before { content: ""; position: absolute; left: 0; top: 0.62em;
      width: 5px; height: 5px; border-radius: 50%; background: var(--accent); }
    .prose ol.steps { counter-reset: step; margin: 0 0 1rem 0; }
    .prose ol.steps li { counter-increment: step; position: relative; padding-left: 2.1rem;
      color: #c9d1d9; margin-bottom: 0.75rem; }
    .prose ol.steps li::before { content: counter(step); position: absolute; left: 0; top: 0.05em;
      width: 1.5rem; height: 1.5rem; border-radius: 50%; background: var(--accent-dim);
      color: var(--accent); font-size: 0.75rem; font-weight: 700; display: grid; place-items: center; }
    .prose a.inline { color: var(--accent); border-bottom: 1px solid rgba(232,149,42,0.35); }
    .prose a.inline:hover { border-bottom-color: var(--accent); }
    .callout { background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--accent);
      border-radius: var(--radius); padding: 1.1rem 1.25rem; margin: 1.35rem 0; }
    .callout p { margin-bottom: 0.55rem; }
    .callout p:last-child { margin-bottom: 0; }
    .callout .callout-label { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--accent); display: block; margin-bottom: 0.5rem; }
    .empty-log { background: var(--surface-2); border: 1px dashed var(--border);
      border-radius: var(--radius); padding: 1.5rem; text-align: center; }
    .empty-log p { color: var(--text-muted); margin: 0; font-size: 0.92rem; }

    .footer { background: var(--surface); border-top: 1px solid var(--border);
      padding: clamp(2.5rem, 5vw, 3.5rem) 0 1.5rem; margin-top: clamp(2.5rem, 5vw, 4rem); }
    .footer-grid { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 2.5rem; }
    .footer-brand h3 { font-size: 1.3rem; margin-bottom: 0.7rem; }
    .footer-brand h3 span { color: var(--accent); }
    .footer-brand p { font-size: 0.88rem; color: var(--text-muted); max-width: 42ch; }
    .footer-col h4 { font-family: var(--font-body); font-size: 0.72rem; font-weight: 700;
      letter-spacing: 0.14em; text-transform: uppercase; color: var(--accent); margin-bottom: 0.9rem; }
    .footer-col li + li { margin-top: 0.5rem; }
    .footer-col a { font-size: 0.88rem; color: var(--text-muted); transition: color var(--transition); }
    .footer-col a:hover { color: var(--text); }
    .footer-bottom { margin-top: 2.5rem; padding-top: 1.25rem; border-top: 1px solid var(--border);
      display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
      font-size: 0.78rem; color: var(--text-faint); }

    @media (max-width: 980px) {
      .policy-layout { grid-template-columns: 1fr; }
      .sidebar { position: static; order: -1; }
      .footer-grid { grid-template-columns: 1fr; gap: 2rem; }
    }
    @media (max-width: 620px) { .nav ul { gap: 1rem; } }
"""


PUBLISHED_LABEL = "August 19, 2026"


def shell(*, slug, title, description, h1, eyebrow, standfirst, toc, body, schema):
    toc_html = "\n            ".join(
        f'<li><a href="#{anchor}">{label}</a></li>' for anchor, label in toc
    )
    schema_html = "\n".join(
        f'  <script type="application/ld+json">\n{json.dumps(s, indent=2)}\n  </script>'
        for s in schema
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-ESCSB47KZY"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-ESCSB47KZY');
  </script>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <link rel="canonical" href="{SITE}/{slug}/" />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <link href="https://api.fontshare.com/v2/css?f[]=clash-display@400,500,600,700&f[]=satoshi@300,400,500,700&display=swap" rel="stylesheet" />
  <link rel="icon" type="image/x-icon" href="/favicon.ico" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="apple-touch-icon" href="/favicon.png" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="East New York Times" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url" content="{SITE}/{slug}/" />
  <meta property="og:image" content="{SITE}/broadway-junction-hire-east-ny.jpg" />
  <meta property="og:locale" content="en_US" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{description}" />
  <meta name="twitter:image" content="{SITE}/broadway-junction-hire-east-ny.jpg" />
{schema_html}
  <style>{CSS}  </style>
</head>
<body>

  <div class="topbar">East New York, Brooklyn · Independent Community Journalism</div>

  <header class="header">
    <div class="container header-inner">
      <a href="/" class="masthead">
        <span class="masthead-name">East New York <span>Times</span></span>
        <span class="masthead-sub">East New York · Brooklyn · Est. 2026</span>
      </a>
      <nav class="nav" aria-label="Primary">
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/stories/">Archive</a></li>
          <li><a href="/ethics/"{' class="active" aria-current="page"' if slug == 'ethics' else ''}>Ethics</a></li>
          <li><a href="/corrections/"{' class="active" aria-current="page"' if slug == 'corrections' else ''}>Corrections</a></li>
          <li><a href="https://eastnewyorktimes.substack.com" target="_blank" rel="noopener">Subscribe</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main>
    <div class="policy-hero">
      <div class="container">
        <span class="eyebrow">{eyebrow}</span>
        <h1>{h1}</h1>
        <p class="standfirst">{standfirst}</p>
        <p class="policy-meta">Effective {EFFECTIVE} · Published {PUBLISHED_LABEL} · Urban Version Media LLC</p>
      </div>
    </div>

    <div class="container policy-layout">
      <aside class="sidebar">
        <nav class="panel" aria-label="On this page">
          <h2>On this page</h2>
          <ul class="toc">
            {toc_html}
          </ul>
        </nav>
        <div class="panel">
          <h2>Reach the newsroom</h2>
          <p>Corrections, questions about this policy, or a concern about our coverage:</p>
          <p><a class="inline" href="mailto:info@eastnewyorktimes.com">info@eastnewyorktimes.com</a></p>
          <p>Put <strong>Correction</strong> in the subject line if you are reporting an error, and we will treat it as urgent.</p>
        </div>
      </aside>

      <div class="prose">
{body}
      </div>
    </div>
  </main>

  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <h3>East New York <span>Times</span></h3>
          <p>Independent community journalism covering East New York, Brooklyn. Civic news,
          local stories, and community events. Also known as ENYT.</p>
        </div>
        <div class="footer-col">
          <h4>Navigate</h4>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/stories/">Story Archive</a></li>
            <li><a href="/honorary-street-names/">Honorary Names</a></li>
            <li><a href="/the-sit-down/">The Sit Down</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Standards</h4>
          <ul>
            <li><a href="/ethics/">Editorial Standards &amp; Ethics</a></li>
            <li><a href="/corrections/">Corrections Policy</a></li>
            <li><a href="mailto:info@eastnewyorktimes.com">Report an Error</a></li>
            <li><a href="mailto:info@eastnewyorktimes.com">Submit a Story Tip</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; 2026 East New York Times. A publication of Urban Version Media. All rights reserved.</p>
        <p>East New York · Brooklyn · New York City</p>
      </div>
    </div>
  </footer>

</body>
</html>
"""


# ────────────────────────────── ETHICS ──────────────────────────────

ETHICS_TOC = [
    ("who-we-are", "Who we are"),
    ("independence", "Editorial independence"),
    ("the-wall", "The wall between UVM and ENYT"),
    ("disclosure", "Disclosure and recusal"),
    ("political", "Political clients and campaigns"),
    ("advertising", "Advertising and sponsored content"),
    ("sourcing", "Sourcing and verification"),
    ("ai", "How we use AI tools"),
    ("opinion", "Opinion, letters and analysis"),
    ("gifts", "Gifts, access and civic roles"),
    ("corrections", "Corrections"),
    ("contact", "Questions and complaints"),
]

ETHICS_BODY = """        <section id="who-we-are">
          <h2>Who we are</h2>
          <p><strong>The East New York Times</strong> (ENYT) is an independent community news
          publication covering East New York, Cypress Hills, City Line, Starrett City and
          Brownsville, Brooklyn. We report on Brooklyn Community Board 5, housing and NYCHA,
          transit and development, schools, public safety, benefits access and neighborhood life.</p>
          <p>ENYT is published by <strong>Urban Version Media LLC</strong>, a Brooklyn multimedia
          production company co-founded by Deric Johnson and Ro Johnson. Deric Johnson is ENYT's
          editor and reporter and is responsible for everything the publication publishes.</p>
          <p>We are privately owned. No newspaper chain, publicly traded company, hedge fund,
          private equity firm, political organization or religious institution owns any part of
          this publication or has any say in what we cover.</p>
          <p>We can be reached at
          <a class="inline" href="mailto:info@eastnewyorktimes.com">info@eastnewyorktimes.com</a>.</p>
        </section>

        <section id="independence">
          <h2>Editorial independence</h2>
          <p>Coverage in the East New York Times cannot be bought, traded or promised. Not by an
          advertiser, not by a sponsor, not by a client of our parent company, not by an elected
          official, not by a community organization, and not by anyone who does us a favor.</p>
          <p>We decide what to cover based on what matters to people who live in East New York.
          The tests we apply are simple: is it true, is it verifiable, does it affect this
          neighborhood, and can we report it responsibly.</p>
          <p>No one outside the newsroom reviews a story before we publish it. We do not give
          sources or subjects advance copies of articles for approval. We will read a specific
          quote or a technical figure back to a source to confirm accuracy — that is fact-checking,
          not approval, and it does not extend to the framing, the headline or the rest of the story.</p>
        </section>

        <section id="the-wall">
          <h2>The wall between Urban Version Media and the East New York Times</h2>
          <p>Urban Version Media is a production studio. It is hired to make video, photography,
          event coverage, social content and websites for clients including businesses,
          nonprofits, community organizations, developers and political campaigns.</p>
          <p>The East New York Times is a newsroom. These are two different businesses that
          happen to share founders, and we keep them separate on purpose.</p>
          <div class="callout">
            <span class="callout-label">The rule</span>
            <p>Client work through Urban Version Media never includes editorial coverage in the
            East New York Times. We do not offer it, promise it, imply it, discount for it or
            trade it. Anyone who hires Urban Version Media gets a production company — not
            access to a newsroom.</p>
          </div>
          <p>We say this to every prospective client in writing before an engagement begins,
          because we would rather lose a client early than have a reader wonder later whether a
          story was purchased.</p>
        </section>

        <section id="disclosure">
          <h2>Disclosure and recusal</h2>
          <p>Because Urban Version Media works in the same neighborhoods the East New York Times
          covers, overlap is inevitable. When it happens, we handle it in the open.</p>
          <ul class="bullets">
            <li><strong>We disclose in the story.</strong> When ENYT covers a person, business or
            project that is a current or recent Urban Version Media client, the article carries a
            clearly marked editor's note stating the relationship. Readers should never have to
            discover a connection on their own.</li>
            <li><strong>The assigned reporter recuses.</strong> When a client is a primary subject
            of a story, the reporter with the relationship does not report or write it. If ENYT
            has no one else available to report that story independently, we do not publish it —
            and if asked, we say why.</li>
            <li><strong>We disclose in both directions.</strong> We tell the client, in writing,
            that ENYT covers their sector and may report on them, and that our coverage is not
            theirs to influence.</li>
            <li><strong>Personal conflicts count too.</strong> Family, close friendships,
            financial interests, and prior employment get disclosed and, where the connection is
            material, trigger the same recusal.</li>
          </ul>
          <p>Our editor is a retired member of the New York City Police Department after 22 years
          of service. We report on the NYPD, the 75th Precinct and PSA 2 regularly and hold them
          to the same standard as any other agency. We disclose that history here so readers can
          weigh our public-safety reporting with full information.</p>
        </section>

        <section id="political">
          <h2>Political clients and campaigns</h2>
          <p>Urban Version Media does political communications work. This is the sharpest conflict
          risk we carry, so it carries the strictest rules.</p>
          <ul class="bullets">
            <li>A campaign or elected official's office that hires Urban Version Media cannot buy,
            influence, soften or kill East New York Times coverage of that candidate, that office
            or that race.</li>
            <li>Any ENYT story involving a current or recent political client of Urban Version
            Media carries an editor's note naming the relationship.</li>
            <li>The reporter who does the campaign work does not report or write ENYT stories in
            which that campaign or officeholder is a primary subject.</li>
            <li>We do not endorse candidates.</li>
          </ul>
          <p>If we cannot cover a race independently, we will say that plainly rather than publish
          compromised coverage.</p>
        </section>

        <section id="advertising">
          <h2>Advertising and sponsored content</h2>
          <p>The East New York Times is free to read and intends to be supported partly by local
          advertising and sponsorship. Revenue never buys coverage.</p>
          <ul class="bullets">
            <li>Every paid placement is labeled <strong>Advertisement</strong>,
            <strong>Sponsored</strong> or <strong>Paid content</strong> so it cannot be mistaken
            for reporting.</li>
            <li>Sponsors have no advance look at editorial content, no input into what we cover,
            and no ability to remove or change a story.</li>
            <li>Sponsoring a coverage area — a committee, a beat, a newsletter — buys visible
            credit and nothing else. It does not buy favorable treatment, and it does not protect
            a sponsor from being reported on.</li>
            <li>We will report critically on an advertiser or sponsor when the facts require it,
            and we will not tell them first.</li>
            <li>We reserve the right to decline advertising.</li>
          </ul>
        </section>

        <section id="sourcing">
          <h2>Sourcing and verification</h2>
          <p>We publish what we can support. When we cannot support it, we do not publish it, or
          we tell you what we do not yet know.</p>
          <ul class="bullets">
            <li>We name sources whenever possible. We grant anonymity only when a source faces a
            real risk — retaliation, loss of housing, loss of a job, immigration exposure — and
            when the information cannot be obtained another way. When we do, we tell readers why
            the source is unnamed.</li>
            <li>Claims made at a public meeting are reported as claims, attributed to the person
            who made them, and checked before we present them as fact. When a statistic asserted
            in a meeting is not supported by the record, we say so.</li>
            <li>Public-safety reporting is confirmed through official channels — NYPD or DCPI, the
            precinct, the District Attorney, or city records. A single weak or unconfirmed report
            is a lead, not a story.</li>
            <li>When an official describes a "bill," we verify the introduction number, sponsorship
            status, and whether it is legislation, a budget allocation or a proposal before
            describing it as law.</li>
            <li>We link to primary documents — agendas, transcripts, filings, data — so readers
            can check our work.</li>
            <li>We seek comment from anyone we report critically on, and we say in the story when
            someone declined to comment or did not respond.</li>
          </ul>
          <p>Our photography and video are our own or properly licensed and credited. We do not
          alter the content of a news image beyond standard cropping and exposure. Illustrations
          and reenactments, if ever used, are labeled.</p>
        </section>

        <section id="ai">
          <h2>How we use AI tools</h2>
          <p>We are transparent about this because a lot of publications are not.</p>
          <p>We use AI tools for research assistance, transcription, background summarization and
          drafting support — the same way a newsroom uses a clipping service, a transcription
          service or a research assistant.</p>
          <p>An AI tool does not have a byline here, and its output is not journalism until a human
          does the reporting. Anything published under a reporter's byline has been verified by
          that reporter: sources contacted, records checked, facts confirmed, original photography
          or video where applicable, and editorial judgment applied. Every fact in a story is our
          responsibility, regardless of what tool touched the draft.</p>
        </section>

        <section id="opinion">
          <h2>Opinion, letters and analysis</h2>
          <p>News reporting and opinion are different things and we label them that way. Letters
          to the editor, guest commentary and analysis are clearly marked and represent the views
          of the writer, not the East New York Times.</p>
          <p>We welcome letters, including letters that disagree with our reporting, and we have
          published them. We verify the identity of a letter writer before publishing, we may edit
          for length and clarity, and we do not publish anonymous letters, personal attacks or
          claims we cannot support.</p>
          <p>Send letters to
          <a class="inline" href="mailto:info@eastnewyorktimes.com">info@eastnewyorktimes.com</a>.</p>
        </section>

        <section id="gifts">
          <h2>Gifts, access and civic roles</h2>
          <ul class="bullets">
            <li>We do not accept gifts, payments, favors or free services from people or
            organizations we cover. We pay our own way. Ordinary press access — a press pass, a
            seat at a public meeting, refreshments available to everyone at a community event —
            is not a gift.</li>
            <li>We do not accept paid travel or paid speaking fees from organizations we cover.</li>
            <li>Our staff hold no political office and take no political appointments.</li>
            <li>Urban Version Media produces media for Brooklyn Community Board 5, a body ENYT
            covers closely. We disclose that relationship here, we cover CB5 independently
            including when the coverage is unflattering, and ENYT's CB5 reporting is not reviewed
            by the board before publication.</li>
          </ul>
        </section>

        <section id="corrections">
          <h2>Corrections</h2>
          <p>We will make mistakes. When we do, we fix them publicly and quickly rather than
          quietly. Our full process for reporting and handling errors is on our
          <a class="inline" href="/corrections/">corrections policy page</a>.</p>
        </section>

        <section id="contact">
          <h2>Questions and complaints</h2>
          <p>If you believe we got something wrong, treated you unfairly, failed to disclose a
          relationship, or violated anything on this page, write to
          <a class="inline" href="mailto:info@eastnewyorktimes.com">info@eastnewyorktimes.com</a>.
          A person reads every message and you will get a response.</p>
          <p>This policy was published on """ + PUBLISHED_LABEL + """ and takes effect """ + EFFECTIVE + """.
          We will update it as the publication grows, and material changes will be dated here.</p>
        </section>"""


# ──────────────────────────── CORRECTIONS ────────────────────────────

CORRECTIONS_TOC = [
    ("commitment", "Our commitment"),
    ("report", "How to report an error"),
    ("what-we-do", "What we do when you tell us"),
    ("levels", "Corrections, clarifications, updates"),
    ("no-unpublishing", "We do not unpublish"),
    ("log", "Published corrections"),
]

CORRECTIONS_BODY = """        <section id="commitment">
          <h2>Our commitment</h2>
          <p>The East New York Times is reported by people, and people get things wrong. What
          separates a trustworthy publication from an untrustworthy one is not the absence of
          errors — it is what happens after one.</p>
          <p>When we get something wrong, we correct it promptly, we say plainly what was wrong,
          and we leave a permanent record on the story itself. We do not delete a story to make a
          mistake disappear, and we do not quietly edit an error out and pretend it was never
          there.</p>
        </section>

        <section id="report">
          <h2>How to report an error</h2>
          <p>Email <a class="inline" href="mailto:info@eastnewyorktimes.com">info@eastnewyorktimes.com</a>
          with <strong>Correction</strong> in the subject line. That subject line moves your
          message to the front of the queue.</p>
          <p>It helps if you can include:</p>
          <ul class="bullets">
            <li>A link to the story, or its headline and date</li>
            <li>The specific sentence, number, name, date or quote you believe is wrong</li>
            <li>What the correct information is</li>
            <li>Anything that supports it — a document, a record, a link, or simply your firsthand
            knowledge</li>
          </ul>
          <p>You do not need to be the subject of a story to report an error, you do not need
          documents to raise a concern, and you do not need to be certain. Tell us and we will
          check it.</p>
          <p>If you are the subject of a story and believe it is unfair rather than factually
          wrong, write to us as well. That is a different conversation than a correction, and we
          want to have it. A response from you may become a
          <a class="inline" href="/ethics/#opinion">letter to the editor</a>.</p>
        </section>

        <section id="what-we-do">
          <h2>What we do when you tell us</h2>
          <ol class="steps">
            <li><strong>We acknowledge you.</strong> You get a reply from a person, normally within
            two business days.</li>
            <li><strong>We check it.</strong> We return to the original sourcing — the transcript,
            the record, the document, the person we interviewed — rather than relying on memory.</li>
            <li><strong>We fix it fast when we are wrong.</strong> A clear factual error is
            corrected as soon as we have confirmed it, typically the same day.</li>
            <li><strong>We label the fix on the story.</strong> The correction appears on the
            article itself, dated, describing what was wrong and what it now says. It is not
            hidden at the bottom in small type and it is not removed later.</li>
            <li><strong>We tell you what we found.</strong> If we conclude the original reporting
            was accurate, we explain our reasoning rather than going silent.</li>
            <li><strong>We fix it everywhere.</strong> If the error also went out in our newsletter,
            on social media or in a video, we correct it on those platforms too.</li>
          </ol>
        </section>

        <section id="levels">
          <h2>Corrections, clarifications and updates</h2>
          <p>We use three labels, and we use them consistently so readers know exactly what
          changed.</p>
          <h3>Correction</h3>
          <p>We published something factually wrong — a wrong name, title, number, date, location,
          or a misattributed quote. The label states the error and the fix. Example:
          <em>Correction, August 19, 2026: An earlier version of this story misstated the number of
          residents hired. It is 13, not 30.</em></p>
          <h3>Clarification</h3>
          <p>What we published was accurate but could reasonably be misread, or was missing context
          that changes how a reader understands it. We add the context and label it.</p>
          <h3>Update</h3>
          <p>Nothing was wrong. The story developed — a vote happened, an agency responded, a
          number changed. We add the new information with a dated update note, and we do not
          re-timestamp an old story to make it look new.</p>
          <p>Fixing a typo or a broken link does not get a public note. Anything that changes a
          fact, a number, a name or the meaning of a sentence does.</p>
        </section>

        <section id="no-unpublishing">
          <h2>We do not unpublish</h2>
          <p>Published journalism is a public record. We do not remove a story because a subject
          later regrets what they said, dislikes the coverage, or asks us to take it down.</p>
          <p>We make narrow exceptions in rare circumstances — for example, when leaving material
          online would put someone at genuine risk of harm, or when a court requires removal. In
          those cases we will normally note that a change was made. Requests are decided by the
          editor and we will explain our decision to the person who asked.</p>
        </section>

        <section id="log">
          <h2>Published corrections</h2>
          <p>Corrections are always posted on the story they belong to. Substantive corrections
          are also listed here so readers can see our full record in one place.</p>
          <div class="empty-log">
            <p>No corrections have been published to date. When we issue one, it will appear here
            with the date, the story, and what changed.</p>
          </div>
        </section>"""


def main():
    org_ref = {
        "@type": "NewsMediaOrganization",
        "name": "East New York Times",
        "alternateName": "ENYT",
        "url": f"{SITE}/",
        "email": "info@eastnewyorktimes.com",
        "sameAs": [
            "https://www.instagram.com/eastnewyorktimes/",
            "https://www.youtube.com/@eastnewyorktimes",
            "https://eastnewyorktimes.substack.com",
        ],
        "ethicsPolicy": f"{SITE}/ethics/",
        "correctionsPolicy": f"{SITE}/corrections/",
        "parentOrganization": {
            "@type": "Organization",
            "name": "Urban Version Media",
            "url": "https://urbanversionmedia.com",
        },
    }

    pages = {
        "ethics": dict(
            title="Editorial Standards, Ethics & Conflicts of Interest — East New York Times",
            description=(
                "How the East New York Times reports: editorial independence, the wall between "
                "Urban Version Media client work and ENYT coverage, disclosure and recusal, "
                "political clients, sponsored-content labeling, sourcing standards and AI use."
            ),
            eyebrow="Editorial Standards",
            h1="Editorial standards, ethics and conflicts of interest",
            standfirst=(
                "Everything a reader, source or subject needs to know about how the East New York "
                "Times decides what to publish — and what cannot be bought."
            ),
            toc=ETHICS_TOC,
            body=ETHICS_BODY,
        ),
        "corrections": dict(
            title="Corrections Policy — East New York Times",
            description=(
                "How to report an error in East New York Times reporting and how we handle it: "
                "our correction, clarification and update labels, our response timeline, and our "
                "policy against unpublishing."
            ),
            eyebrow="Corrections Policy",
            h1="Corrections and clarifications",
            standfirst=(
                "We get things wrong sometimes. Here is exactly how to tell us, and exactly what "
                "we do about it."
            ),
            toc=CORRECTIONS_TOC,
            body=CORRECTIONS_BODY,
        ),
    }

    for slug, cfg in pages.items():
        schema = [
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": cfg["h1"],
                "url": f"{SITE}/{slug}/",
                "description": cfg["description"],
                "datePublished": PUBLISHED_ISO,
                "dateModified": PUBLISHED_ISO,
                "inLanguage": "en-US",
                "isPartOf": {"@type": "WebSite", "name": "East New York Times",
                             "alternateName": "ENYT", "url": f"{SITE}/"},
                "publisher": org_ref,
                "about": {"@type": "Thing", "name": (
                    "Journalism ethics and conflicts of interest" if slug == "ethics"
                    else "Editorial corrections policy")},
            },
            {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                    {"@type": "ListItem", "position": 2, "name": cfg["eyebrow"],
                     "item": f"{SITE}/{slug}/"},
                ],
            },
        ]
        out_dir = os.path.join(ROOT, slug)
        os.makedirs(out_dir, exist_ok=True)
        html = shell(slug=slug, schema=schema, **cfg)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"wrote /{slug}/index.html  ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
