"""Convert the old ece.cet.ac.in content into review spreadsheets (CSV).

Input, one of:
  --site   https://ece.cet.ac.in   read the public website directly (no login needed):
                             the five pages below, every page from the public
                             pages feed (faculty profiles, lab pages, OBE,
                             Programs...), and all news posts from the posts feed
  --export old-site.xml      WordPress export from the old site (Tools > Export > All content)
  --pages  folder/           saved HTML pages: faculty-2.html, technical-staff.html,
                             staff-advisors.html, laboratories.html, publications.html

Output (in --out, default ./migration):
  faculty.csv, staff.csv, batches.csv, labs.csv, publications.csv, news.csv
  sections.csv   changes to department pages (committees, syllabus, calendars...)
  warnings.csv   every row that needs a human look, with the reason

Review and correct the CSVs in a spreadsheet, then load them with
  wp ece import <type> <file.csv>

Nothing here guesses silently: anything uncertain is written to warnings.csv.
"""
import argparse
import csv
import difflib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

import old_pages

WARN = []
API_PAGES = []  # every published page of the old site, from /wp-json/wp/v2/pages


def warn(kind, item, reason):
    WARN.append({'type': kind, 'item': item, 'reason': reason})


def clean(text):
    text = html.unescape(text or '')
    text = text.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def norm_name(name):
    # \b keeps names such as "Drishya" intact; [\W_]* takes "Dr.David", "Prof`. X".
    n = re.sub(r'^(dr|prof|mr|ms|mrs|smt|shri)\b[\W_]*', '', clean(name), flags=re.I)
    return re.sub(r'[^a-z]', '', n.lower())


# ---------- reading the export ----------

NS = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
}


def read_export(path):
    """Return (pages_by_slug, posts, attachments_by_id)."""
    tree = ET.parse(path)
    pages, posts, atts = {}, [], {}
    for item in tree.getroot().iter('item'):
        ptype = item.findtext('wp:post_type', default='', namespaces=NS)
        status = item.findtext('wp:status', default='', namespaces=NS)
        slug = item.findtext('wp:post_name', default='', namespaces=NS)
        pid = item.findtext('wp:post_id', default='', namespaces=NS)
        body = item.findtext('content:encoded', default='', namespaces=NS)
        if ptype == 'attachment':
            atts[pid] = item.findtext('wp:attachment_url', default='', namespaces=NS)
        elif ptype == 'page' and status == 'publish':
            pages[slug] = body
            API_PAGES.append({'slug': slug, 'link': item.findtext('link', default=''),
                              'title': {'rendered': item.findtext('title', default='')}, 'content': {'rendered': body}})
        elif ptype == 'post' and status == 'publish':
            meta = {m.findtext('wp:meta_key', namespaces=NS): m.findtext('wp:meta_value', namespaces=NS) for m in item.findall('wp:postmeta', NS)}
            cats = [c.text for c in item.findall('category') if c.get('domain') == 'category']
            posts.append({
                'old_id': pid,
                'title': clean(item.findtext('title')),
                'date': item.findtext('wp:post_date', default='', namespaces=NS),
                'slug': slug,
                'content': body,
                'excerpt': item.findtext('excerpt:encoded', default='', namespaces=NS),
                'old_categories': '; '.join(c for c in cats if c),
                'thumbnail_id': meta.get('_thumbnail_id', ''),
                'link': item.findtext('link', default=''),
            })
    return pages, posts, atts


PAGE_SLUGS = ('faculty-2', 'technical-staff', 'staff-advisors', 'laboratories', 'publications')


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (site migration script)'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', errors='replace'), r.headers


def read_site(base, save_to):
    """Read the public website: the five list pages and every published post.

    Returns (pages_by_slug, posts, attachments_by_id) like read_export. Copies of
    what was read are saved in save_to, so a later run can use --pages instead.
    """
    base = base.rstrip('/')
    os.makedirs(save_to, exist_ok=True)
    pages, posts, atts = {}, [], {}
    for slug in PAGE_SLUGS:
        try:
            pages[slug], _ = fetch('%s/%s/' % (base, slug))
        except urllib.error.URLError as e:
            warn('site', slug, 'Could not download %s/%s/ (%s)' % (base, slug, e))
            continue
        with open(os.path.join(save_to, slug + '.html'), 'w', encoding='utf-8') as fh:
            fh.write(pages[slug])
        time.sleep(1)  # be gentle with the old server
    API_PAGES[:] = read_api_pages(base, save_to)
    n = 1
    raw_posts = []
    while True:
        url = '%s/wp-json/wp/v2/posts?per_page=100&page=%d&_embed=wp:featuredmedia,wp:term' % (base, n)
        try:
            body, headers = fetch(url)
        except urllib.error.HTTPError as e:
            if e.code == 400 and n > 1:  # past the last page
                break
            warn('news', '-', 'The public posts feed is not available (%s): news not converted' % e)
            break
        except urllib.error.URLError as e:
            warn('news', '-', 'Could not read the public posts feed (%s): news not converted' % e)
            break
        batch = json.loads(body)
        raw_posts += batch
        if not batch or n >= int(headers.get('X-WP-TotalPages') or 1):
            break
        n += 1
        time.sleep(1)
    with open(os.path.join(save_to, 'posts.json'), 'w', encoding='utf-8') as fh:
        json.dump(raw_posts, fh, ensure_ascii=False, indent=1)
    for p in raw_posts:
        emb = p.get('_embedded', {})
        media = (emb.get('wp:featuredmedia') or [{}])[0] or {}
        if p.get('featured_media') and media.get('source_url'):
            atts[str(p['featured_media'])] = media['source_url']
        cats = [t.get('name', '') for group in emb.get('wp:term', []) for t in group if t.get('taxonomy') == 'category']
        posts.append({
            'old_id': str(p['id']),
            'title': clean(p['title']['rendered']),
            'date': p['date'].replace('T', ' '),
            'slug': p['slug'],
            'content': p['content']['rendered'],
            'excerpt': p['excerpt']['rendered'],
            'old_categories': '; '.join(clean(c) for c in cats if c),
            'thumbnail_id': str(p.get('featured_media') or ''),
            'link': p.get('link', ''),
        })
    return pages, posts, atts


def read_api_pages(base, save_to):
    """Every published page (faculty profiles, lab pages, OBE, Programs...)."""
    out, n = [], 1
    while True:
        try:
            body, headers = fetch('%s/wp-json/wp/v2/pages?per_page=100&page=%d' % (base, n))
        except urllib.error.HTTPError as e:
            if e.code == 400 and n > 1:
                break
            warn('pages', '-', 'The public pages feed is not available (%s): profiles, lab pages and department pages not converted' % e)
            break
        except urllib.error.URLError as e:
            warn('pages', '-', 'Could not read the public pages feed (%s)' % e)
            break
        batch = json.loads(body)
        out += batch
        if not batch or n >= int(headers.get('X-WP-TotalPages') or 1):
            break
        n += 1
        time.sleep(1)
    if out:
        os.makedirs(os.path.join(save_to, 'api'), exist_ok=True)
        with open(os.path.join(save_to, 'api', 'pages.json'), 'w', encoding='utf-8') as fh:
            json.dump(out, fh, ensure_ascii=False)
    return out


def read_pages(folder):
    api = os.path.join(folder, 'api', 'pages.json')
    if os.path.exists(api):
        with open(api, encoding='utf-8') as fh:
            API_PAGES[:] = json.load(fh)
    pages = {}
    for f in os.listdir(folder):
        if f.endswith('.html'):
            with open(os.path.join(folder, f), encoding='utf-8', errors='replace') as fh:
                pages[f[:-5]] = fh.read()
    return pages


def page(pages, *slugs):
    for s in slugs:
        if s in pages:
            return BeautifulSoup(pages[s], 'lxml')
    return None


def main_area(soup):
    """For saved full pages, keep only the main content."""
    for sel in ('main', 'article', '.entry-content', '#content'):
        el = soup.select_one(sel)
        if el:
            return el
    return soup


def blocks(soup):
    """Text blocks in document order: (tag, text, element)."""
    out = []
    for el in main_area(soup).find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'strong', 'b', 'figcaption']):
        if el.name in ('strong', 'b') and el.find_parent(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'td']):
            continue
        t = clean(el.get_text(' '))
        if t:
            out.append((el.name, t, el))
    return out


# ---------- faculty ----------

DESIG = [
    (r'principal', 'professor'),
    (r'associate|assosciate|asso\.', 'associate_professor'),
    (r'assistant|asst', 'assistant_professor'),
    (r'professor', 'professor'),
]
EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
DATE = re.compile(r'(\d{1,2})[-./](\d{1,2})[-./](\d{4})')


def designation_key(text):
    for pat, key in DESIG:
        if re.search(pat, text, re.I):
            return key
    return ''


AREA_HINTS = [
    (r'signal|image|speech|audio|video|vision', 'Signal and image processing'),
    (r'communication|antenna|wireless|microwave|\brf\b|network', 'Communication systems'),
    (r'optic|photon|fib(er|re)|laser', 'Optics and photonics'),
    (r'bio-?medical|medical|health', 'Biomedical engineering'),
    (r'power|control|drive|converter', 'Control and power electronics'),
    (r'machine learning|deep learning|\bai\b|neural|\bml\b|data science', 'Machine learning'),
    (r'vlsi|nano|semiconductor|device|microelectronic', 'VLSI and micro-nano electronics'),
]


def suggest_areas(text):
    return '; '.join(dict.fromkeys(area for pat, area in AREA_HINTS if re.search(pat, text or '', re.I)))


def parse_faculty(soup):
    from bs4 import NavigableString
    rows = []
    root = main_area(soup)
    order = {id(el): i for i, el in enumerate(root.descendants)}
    heads = root.find_all(['h2', 'h3', 'h4'])
    for i, h in enumerate(heads):
        name = clean(h.get_text(' '))
        if not re.search(r'^(dr|prof)\b', name, re.I) and not h.find('a'):
            continue
        if len(name) > 60 or name.lower() in ('faculty', 'faculty members'):
            continue
        nxt = heads[i + 1] if i + 1 < len(heads) else None
        texts = []
        for node in h.next_elements:
            if node is nxt:
                break
            if isinstance(node, NavigableString) and node.parent is not h and h not in node.parents:
                t = clean(node)
                if t:
                    texts.append(t)
        # Photo: the nearest image before this heading and after the previous one.
        prev = heads[i - 1] if i > 0 else None
        img = h.find_previous('img')
        photo = ''
        if img is not None and (prev is None or order.get(id(img), -1) > order.get(id(prev), -1)):
            photo = old_pages.original_image(img.get('data-src') or img.get('src') or '')
        joined = ' | '.join(texts)
        des_text = next((t for t in texts if re.search(r'professor|principal', t, re.I)), '')
        role = ''
        m = re.search(r'\(([^)]*(principal|head|dean|hod)[^)]*)\)', des_text, re.I)
        if m:
            role = clean(m.group(1))
        d = DATE.search(joined)
        year = d.group(3) if d else ''
        spec = ''
        for k, t in enumerate(texts):
            if re.search(r'speciali[sz]ation|area\s*of\s*interest', t, re.I):
                after = re.split(r':', t, maxsplit=1)
                spec = after[1].strip() if len(after) > 1 else ''
                if not spec and k + 1 < len(texts) and not EMAIL.search(texts[k + 1]) and not re.search(r'\d{5}', texts[k + 1]):
                    spec = texts[k + 1]
                break
        spec = clean(spec)
        email = ''
        em = EMAIL.findall(joined)
        if em:
            email = em[0]
        link = h.find('a')
        row = {
            'name': re.sub(r'\s+', ' ', name).replace('Dr. ', 'Dr. ').strip(),
            'designation': designation_key(des_text),
            'designation_text': des_text,
            'additional_role': role,
            'joined_year': year,
            'email': email,
            'specialisation': spec,
            'research_areas': suggest_areas(spec),
            'photo_url': photo,
            'old_profile_url': link.get('href', '') if link else '',
        }
        if not row['designation']:
            warn('faculty', name, 'Designation not recognised: "%s"' % des_text)
        if not email:
            warn('faculty', name, 'No email found')
        elif not email.lower().endswith('@cet.ac.in'):
            warn('faculty', name, 'Personal email (%s): replace with the @cet.ac.in address' % email)
        if not year:
            warn('faculty', name, 'No joining date found')
        if not photo:
            warn('faculty', name, 'No photo found')
        rows.append(row)
    # Merge duplicate names.
    seen, out = {}, []
    for r in rows:
        k = norm_name(r['name'])
        if k in seen:
            warn('faculty', r['name'], 'Listed twice on the old page; kept the first entry')
            continue
        seen[k] = r
        out.append(r)
    return out


# ---------- technical staff ----------

STAFF_CATS = [
    (r'instructor\s*grade\s*(i|1)\b(?!i)', 'instructor_grade_1'),
    (r'instructor\s*grade\s*(ii|2)', 'instructor_grade_2'),
    (r'trade\s*instructor', 'trade_instructor'),
    (r'instrument\s*mechanic', 'instrument_mechanic'),
    (r'tradesm[ae]n', 'tradesman'),
]


def parse_staff(soup):
    rows, cat = [], ''
    for tag, text, el in blocks(soup):
        found = ''
        for pat, key in STAFF_CATS:
            if re.search(pat, text, re.I) and len(text) < 40:
                found = key
        if found:
            cat = found
            continue
        if not cat or len(text) > 60 or text.lower() in ('technical staff',):
            continue
        for name in re.split(r'\s*[,;]\s*|\s{2,}', text):
            name = clean(name)
            if name and re.search(r'[A-Za-z]{2}', name) and not re.search(r'@|\d{6,}', name):
                rows.append({'name': name, 'category': cat, 'lab': ''})
    if not rows:
        warn('staff', '-', 'No technical staff found: check the page layout')
    return rows


# ---------- staff advisor batches ----------

PROGS = [
    (r'm\.?\s*tech.*(applied electronics|aei)', 'mtech-aei'),
    (r'm\.?\s*tech.*(communication|cms|cs\b|microwave)', 'mtech-cs'),
    (r'm\.?\s*tech.*(signal|sp\b)', 'mtech-sp'),
    (r'm\.?\s*tech.*(micro|nano|mne)', 'mtech-mne'),
    (r'm\.?\s*tech.*(robot|raa|automation)', 'mtech-ra'),
    (r'b\.?\s*-?tech.*(applied electronics|aei)|\baei\b', 'btech-aei'),
    (r'b\.?\s*-?tech.*(electronics and communication|ece)|\bece\b', 'btech-ece'),
]


def prog_key(text):
    for pat, key in PROGS:
        if re.search(pat, text, re.I):
            return key
    return ''


def parse_batches(soup):
    rows, prog, mtech_spec, year, label = [], '', '', '', ''
    for tag, text, el in blocks(soup):
        low = text.lower()
        p = prog_key(text)
        heading_like = tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b') or len(text) < 50
        if p and heading_like:
            prog = p
        ym = re.search(r'(20\d{2})\s*(?:[-–]\s*(\d{2,4}))?', text)
        if ym and heading_like and not re.search(r'^(dr|prof)', low):
            year = ym.group(1)
            bm = re.search(r'batch\s*([a-z])\b', low)
            label = bm.group(1).upper() if bm else ''
        names = re.findall(r'((?:Dr|Prof)[\.,]?\s+[A-Z][A-Za-z\.\s]+?)(?=\s*(?:\d|\(|,|$|Dr|Prof|[A-Za-z0-9._%+-]+@))', text)
        if names and prog and year:
            lm = re.search(r'batch\s*([a-z])\b', low)
            line_label = lm.group(1).upper() if lm else label
            for n in names:
                n = clean(re.sub(r'Prof,', 'Prof.', n))
                rows.append({'programme': prog, 'admission_year': year, 'batch_label': line_label, 'advisors': n, 'source_line': text[:120]})
    # Group advisors of the same batch.
    grouped = {}
    for r in rows:
        k = (r['programme'], r['admission_year'], r['batch_label'])
        g = grouped.setdefault(k, dict(r, advisors=[]))
        if r['advisors'] not in g['advisors']:
            g['advisors'].append(r['advisors'])
    out = []
    for g in grouped.values():
        g['advisors'] = '; '.join(g['advisors'])
        out.append(g)
    if not out:
        warn('batches', '-', 'No batches found: check the page layout')
    for g in out:
        if not g['programme']:
            warn('batches', g['source_line'], 'Programme not recognised')
    return out


# ---------- labs ----------

def parse_labs(soup):
    rows, section = [], ''
    for tag, text, el in blocks(soup):
        low = text.lower()
        # Only real headings switch section: lab names such as "UG DSP Lab" or
        # "RF Research Lab" would otherwise match these patterns.
        is_heading = tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') or (tag in ('strong', 'b'))
        if is_heading and re.search(r'\bug\b.*lab|under\s*graduate', low) and len(text) < 40:
            section = 'ug'
            continue
        if is_heading and re.search(r'pg|post\s*graduate|research', low) and 'lab' in low and len(text) < 40:
            section = 'pg'
            continue
        # The live page lists labs as one paragraph each; older copies used bullets.
        if tag not in ('li', 'p') or not section:
            continue
        name = clean(text)
        a = el.find('a')
        # Any short line under a lab heading is a lab ("Electronics Workshop",
        # "Department Computing Facility (DCF)"); longer paragraphs are prose.
        if len(name) > 90 or name.endswith('.'):
            continue
        is_research = section == 'pg' and re.search(r'research|perl|\[', name, re.I)
        rows.append({
            'name': re.sub(r'\s*\[\s*P\s*E\s*R\s*L\s*\]', ' (PERL)', name),
            'type': 'research' if is_research else 'teaching',
            'programmes': 'btech-ece; btech-aei' if section == 'ug' else 'mtech',
            'summary': '',
            'lead_faculty': '',
            'old_url': a.get('href', '') if a else '',
        })
    merged = {}
    for r in rows:
        k = re.sub(r'[^a-z]', '', r['name'].lower())
        if k in merged:
            m = merged[k]
            progs = [x for x in (m['programmes'] + '; ' + r['programmes']).split('; ') if x]
            m['programmes'] = '; '.join(dict.fromkeys(progs))
            warn('labs', r['name'], 'Appears in both the UG and PG lists; merged, with both sets of programmes')
            continue
        merged[k] = r
    out = list(merged.values())
    for r in out:
        if len(re.sub(r'[^A-Za-z]', '', r['name'])) <= 4:
            warn('labs', r['name'], 'Abbreviation only: write the full lab name')
    if out:
        warn('labs', 'all labs', 'Check each lab\'s type (teaching or research), programmes, lab in charge and one-line summary')
    return out


# ---------- publications ----------

# The old page sometimes opens with ” after a comma: 'Narayanan,”MS-HViT ...”'.
QUOTE = re.compile(r'(?:[“"]|(?<=[,\s])”)\s*(.+?)\s*[,.]?\s*[”"]')
# Single curly quotes, used as quotation marks only after a comma or space
# and before a capital, so apostrophes ("Parkinson’s") are left alone.
SQUOTE = re.compile(r'(?:(?<=[,\s])|^)[‘’](?=[A-Z0-9])(.+?)[’‘](?=\s*[,.;]|$)')
# APA: "Pradeep, R., Veerasimman, A. & Rajendran, S." optionally followed by "(2024)."
APA_AUTHORS = re.compile(r"^((?:(?:&\s*)?[A-Z][\w'’-]+(?: [A-Z][\w'’-]+)?,\s(?:[A-Z]\.\s?-?){1,3},?\s*)+)(?:\((?:19|20)\d{2}\)\.?\s*)?(?=[A-Z][a-z]|[A-Z]{2}|[0-9“\"])")
DOI = re.compile(r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)?\b(10\.\d{4,9}/[^\s,;]+|1\d{3}/[A-Za-z0-9.\-()/]+)', re.I)


NOT_NAME = re.compile(r'\b(of|for|using|the|based|with|in|on|via|from|to|by|an?|its|under|over|towards?)\b')


def looks_like_authors(s):
    """True for "A. Dubey and J. Zacharias", "LP Gokul, P Adarsh", "Noumida A."."""
    s = s.strip(' ,.;:')
    if not s or len(s) > 300:
        return False
    for n in [n.strip(' .') for n in re.split(r',|\band\b|&', s)]:
        if not n or n.lower() in ('et al', 'et al.'):
            continue
        words = n.split()
        if len(words) > 5 or NOT_NAME.search(n):
            return False
        if any(w[0].isalpha() and not w[0].isupper() and w.lower() not in ('et', 'al') for w in words):
            return False
    return True


def split_unquoted(s):
    """(authors, title, rest) for citations without quotation marks."""
    # APA: Surname, I., Surname, I. & Surname, I. (2023). Title. Venue
    m = APA_AUTHORS.match(s)
    if m and m.group(1).count(',') >= 2:
        authors = re.sub(r'\s*\((?:19|20)\d{2}\)\.?\s*$', '', m.group(1)).strip(' ,')
        t, _, rest = s[m.end():].partition('. ')
        if not looks_like_authors(t):  # "..., Sivakumar, R., R. Pradeep, Title" is not APA
            return authors, t.rstrip('.'), rest
    # Authors. Title. Venue
    dot = [p.strip() for p in re.split(r'(?<=[a-z\]\)0-9])\.\s+(?=[A-Z0-9])', s) if p.strip()]
    if len(dot) >= 3 and looks_like_authors(dot[0]):
        return dot[0], dot[1].rstrip('.'), ' '.join(dot[2:])
    # Title; Venue; Year  or  Authors; Title; Venue
    segs = [p.strip(' .') for p in s.split(';') if p.strip(' .')]
    if len(segs) >= 2:
        if len(segs) >= 3 and looks_like_authors(segs[0]):
            return segs[0], segs[1], '; '.join(segs[2:])
        return '', segs[0], '; '.join(segs[1:])
    # Author, Author, Title, Venue, ...  or  Title, Venue, ...
    pieces = [p.strip() for p in re.split(r',\s+', s) if p.strip()]
    i = 0
    while i < len(pieces) - 1 and looks_like_authors(pieces[i]):
        i += 1
    if len(pieces) >= 2:
        authors, title, rest = ', '.join(pieces[:i]), pieces[i], ', '.join(pieces[i + 1:])
        # "Titto Anujan, Vismaya Vijayan- Exploring Terahertz ...- 2nd Conference"
        dm = re.match(r'([A-Z][\w. ]{2,40}?)\s*-\s*([A-Z].+)$', title)
        if dm and authors and len(dm.group(1).split()) >= 2 and looks_like_authors(dm.group(1)):
            authors += ', ' + dm.group(1).strip()
            title, _, more = dm.group(2).partition('- ')
            rest = more + (', ' + rest if more and rest else rest)
        # "R. Pradeep, Visual analysis of dance. Visual Computer (2025)"
        tm = re.match(r'(.+?[a-z\)])\.\s+([A-Z].*)$', title)
        if tm and len(tm.group(1).split()) >= 3:
            title, rest = tm.group(1), (tm.group(2) + (', ' + rest if rest else ''))
        return authors, title.rstrip('.'), rest
    return '', s, ''


def parse_pub_entry(text, year_ctx):
    raw = clean(text)
    r = {'title': '', 'authors': '', 'venue': '', 'type': '', 'year': '', 'volume': '', 'pages': '', 'doi': '', 'status': 'published', 'faculty': '', 'raw': raw, 'confidence': 'low'}
    body = re.sub(r',(?=[A-Za-z])', ', ', raw)  # "Remanan,Vismaya"
    body = re.sub(r'^accepted the paper titled\s*', '', body, flags=re.I)  # status is still read from raw
    # "Title; Authors, “Title”, Venue": drop the repeated title in front.
    if ';' in body:
        head, tail = body.split(';', 1)
        h = re.sub(r'[^a-z0-9]', '', head.lower())
        if len(h) > 15 and h in re.sub(r'[^a-z0-9]', '', tail.lower()):
            body = tail.strip()
    m = DOI.search(body)
    if m:
        d = m.group(1).rstrip('.')
        if not d.startswith('10.'):
            d = '10.' + d
            warn('publications', raw[:80], 'DOI was missing "10.": corrected to %s, check it' % d)
        r['doi'] = d
    q = QUOTE.search(body) or SQUOTE.search(body)
    if q:
        r['title'] = q.group(1).strip(' ,.')
        r['authors'] = body[:q.start()].strip(' ,.:;')
        rest = body[q.end():]
    else:
        r['authors'], r['title'], rest = split_unquoted(body)
    rest = DOI.sub('', rest)
    vm = re.search(r'\bvol(?:ume)?\.?\s*([\w-]+)', rest, re.I)
    if vm:
        r['volume'] = vm.group(1)
    pm = re.search(r'\bpp?\.?\s*([\d]+\s*[-–]\s*[\d]+|\d+)', rest)
    if pm:
        r['pages'] = pm.group(1).replace(' ', '')
    ys = re.findall(r'\b(19[89]\d|20[0-3]\d)\b', raw)
    r['year'] = ys[-1] if ys else year_ctx
    if ys and year_ctx and ys[-1] != year_ctx:
        warn('publications', r['title'][:80], 'Listed under %s but the citation says %s' % (year_ctx, ys[-1]))
    # Stop at volume, pages, a trailing ", 2021", DOI or ISSN. A year at the
    # start belongs to the name ("2024 International Conference on ...").
    venue = re.split(r'\bvol\b|\bvol\.|\bpp?\.\s*\d|[,;]\s*(?:19|20)\d{2}\b|\bdoi\b|\(ISSN', rest.strip(' ,.;:'), flags=re.I)[0]
    r['venue'] = re.sub(r'^in\s+', '', venue.strip(' ,.;:-'), flags=re.I)
    r['title'] = r['title'].strip(' ,.;:“”"‘’')
    blob = raw.lower()
    if re.search(r'accepted|to be presented|in press|status', blob):
        r['status'] = 'accepted'
        warn('publications', r['title'][:80], 'Marked accepted or "to be presented": update with the final details')
    if re.search(r'patent', blob):
        r['type'] = 'patent'
    elif re.search(r'proc\.|proceedings|conference|symposium|workshop|\bicc|\bconf\b|congress', blob):
        r['type'] = 'conference'
    elif re.search(r'journal|transactions|letters|access|elsevier|springer|wiley|ieee|jour', blob):
        r['type'] = 'journal'
    elif re.search(r'chapter|book', blob):
        r['type'] = 'chapter'
    elif r['venue'] and r['status'] == 'published':
        r['type'] = 'journal'
    else:
        r['type'] = 'other'
    # A split that left an initial or a name on the wrong side is not trusted.
    suspect = (re.match(r'[A-Z]\.\s', r['title']) or re.search(r'[,&]$', r['authors'])
               or (r['authors'] and not looks_like_authors(r['authors']) and not APA_AUTHORS.match(r['authors'] + ' X')))
    if suspect:
        pass
    elif r['title'] and r['authors'] and r['venue']:
        r['confidence'] = 'high' if q else 'medium'
    elif r['title'] and r['venue'] and not r['authors']:
        # Common on the old page: "Title, Journal, 2023" under a faculty heading.
        r['confidence'] = 'medium'
        warn('publications', r['title'][:80], 'No authors on the old page: add the author list')
    return r


FACULTY_NAMES = []  # filled from faculty.csv rows before publications are parsed
SEEN_HEADINGS = {}


def resolve_faculty(heading):
    """Map a heading on the publications page to the name in faculty.csv."""
    name = clean(heading)
    if name in SEEN_HEADINGS:
        return SEEN_HEADINGS[name]
    idx = {norm_name(n): n for n in FACULTY_NAMES}
    k = norm_name(name)
    out = name
    if not idx:
        pass
    elif k in idx:
        out = idx[k]
    else:
        close = difflib.get_close_matches(k, idx, n=1, cutoff=0.85)
        if close:
            out = idx[close[0]]
            warn('publications', name, 'Heading matched to faculty "%s" (spelling differs): check' % out)
        else:
            near = difflib.get_close_matches(k, idx, n=1, cutoff=0.6)
            hint = ' Closest current name: "%s".' % idx[near[0]] if near else ''
            warn('publications', name, 'Not on the current faculty page (former faculty?): their papers import without a faculty link.' + hint)
    SEEN_HEADINGS[name] = out
    return out


def parse_publications(soup):
    rows, year, fac = [], '', ''
    for tag, text, el in blocks(soup):
        t = text.strip()
        if re.fullmatch(r'(19|20)\d{2}', t.strip(' :')):
            year = t.strip(' :')
            continue
        if len(t) < 60 and t.endswith(':') and re.search(r'[A-Za-z]', t):
            fac = resolve_faculty(t.rstrip(':'))
            continue
        if len(t) < 40 or tag in ('h1', 'h2'):
            continue
        r = parse_pub_entry(t, year)
        r['faculty'] = fac
        rows.append(r)
    # Merge duplicates (same title), combining faculty.
    merged = {}
    for r in rows:
        k = re.sub(r'[^a-z0-9]', '', r['title'].lower())[:80]
        if k in merged:
            m = merged[k]
            fs = [f for f in (m['faculty'].split('; ') + [r['faculty']]) if f]
            m['faculty'] = '; '.join(dict.fromkeys(fs))
            warn('publications', r['title'][:80], 'Listed more than once on the old page; merged')
            continue
        merged[k] = r
    out = list(merged.values())
    # A DOI shared by several papers is a conference-level DOI, not a paper DOI.
    by_doi = {}
    for r in out:
        if r['doi']:
            by_doi.setdefault(r['doi'], []).append(r)
    for d, lst in by_doi.items():
        if len(lst) > 1:
            for r in lst:
                warn('publications', r['title'][:80], 'DOI %s is shared by %d papers: find this paper\'s own DOI' % (d, len(lst)))
                r['doi'] = ''
    for r in out:
        if r['confidence'] == 'low':
            warn('publications', r['raw'][:80], 'Could not split into authors, title and venue: fill in by hand')
    return out


# ---------- news ----------

def news_category(title, content, old):
    blob = (title + ' ' + old + ' ' + content[:400]).lower()
    if re.search(r'exam|calendar|notice|circular|timetable|announcement', blob):
        return 'announcements'
    if re.search(r'placed|placement|recruit|offer letter', blob):
        return 'placements'
    if re.search(r'rank|prize|award|won|winner|achiev|congratulat', blob):
        return 'student-achievements'
    if re.search(r'fdp|faculty development|workshop|training|hands-on', blob):
        return 'workshops-and-fdps'
    if re.search(r'talk|lecture|webinar|seminar', blob):
        return 'talks'
    if re.search(r'outreach|school|thrive|community', blob):
        return 'outreach'
    return 'department-news'


def parse_news(posts, atts):
    rows = []
    for p in posts:
        thumb = atts.get(p['thumbnail_id'], '')
        if not thumb:
            img = BeautifulSoup(p['content'], 'lxml').find('img')
            thumb = img.get('src', '') if img else ''
            # WordPress resized copy ("photo-1024x768.jpg"): use the original.
            thumb = re.sub(r'-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif)$)', '', thumb, flags=re.I)
        excerpt = clean(BeautifulSoup(p['excerpt'] or '', 'lxml').get_text(' '))
        if not excerpt:
            excerpt = ' '.join(clean(BeautifulSoup(p['content'], 'lxml').get_text(' ')).split()[:35])
        rows.append({
            'old_id': p['old_id'], 'title': p['title'], 'date': p['date'], 'slug': p['slug'],
            'category': news_category(p['title'], clean(BeautifulSoup(p['content'], 'lxml').get_text(' ')), p['old_categories']),
            'old_categories': p['old_categories'], 'featured_image_url': thumb, 'excerpt': excerpt,
            'content_html': p['content'], 'old_url': p['link'],
        })
        if not thumb:
            warn('news', p['title'], 'No image')
    return rows



# ---------- individual pages: profiles and labs ----------

def enrich_faculty(rows):
    by_slug = {p['slug']: p for p in API_PAGES}
    guides = []
    if 'programs' in by_slug:
        guides = [norm_name(g) for g in old_pages.approved_guides(by_slug['programs'])]
    for r, page in old_pages.match_profiles(rows, API_PAGES, warn):
        d = old_pages.parse_profile(page)
        r['old_profile_url'] = page['link']
        for k in ('room', 'qualifications', 'courses', 'scholar_url', 'orcid_url', 'scopus_url', 'about'):
            r[k] = d[k]
        if d['photo_url'] and (not r.get('photo_url') or re.search(r'-\d+x\d+\.', r.get('photo_url', ''))):
            r['photo_url'] = d['photo_url']
        if d['email'] and not r.get('email'):
            r['email'] = d['email']
        des = designation_key(d['designation_text'])
        if des and r['designation'] and des != r['designation']:
            warn('faculty', r['name'], 'Faculty page says "%s", profile page says "%s": check the designation' % (r['designation_text'], d['designation_text']))
        if not r.get('additional_role'):
            m = re.search(r'dean\s*\(([^)]+)\)', d['designation_text'], re.I)
            if m:
                r['additional_role'] = 'Dean (%s)' % clean(m.group(1))
            elif re.search(r'&\s*head|\bhod\b', d['designation_text'], re.I):
                r['additional_role'] = 'Head of Department'
        if d['interests']:
            r['research_areas'] = suggest_areas(d['interests'] + ' ' + r.get('specialisation', '')) or r['research_areas']
            if not r.get('specialisation'):
                r['specialisation'] = d['interests'][:200]
        r['is_guide'] = '1' if norm_name(r['name']) in guides else ''
        if not d['qualification_rows']:
            warn('faculty', r['name'], 'No qualifications could be read from the profile page: add them by hand')
        elif any(not q['institution'] for q in d['qualification_rows']):
            warn('faculty', r['name'], 'A qualification has no institution: check the qualifications column')
        if not d['courses']:
            warn('faculty', r['name'], 'No courses on the profile page')
        if d['publication_lines'] > 3:
            warn('faculty', r['name'], 'The profile page lists %d papers: check they are in publications.csv' % d['publication_lines'])
    return rows


def resolve_people(names, pool, kind, item):
    """Map names on a lab page to names in faculty.csv or staff.csv."""
    idx = {norm_name(n): n for n in pool}
    out = []
    for n in names:
        k = norm_name(n)
        if k in idx:
            out.append(idx[k])
            continue
        close = difflib.get_close_matches(k, list(idx), n=1, cutoff=0.88)
        if close:
            out.append(idx[close[0]])
            if idx[close[0]] != n:
                warn('labs', item, '%s "%s" matched to "%s" (spelling differs): check' % (kind, n, idx[close[0]]))
        else:
            warn('labs', item, '%s "%s" is not in %s.csv: add them there or fix the name' % (kind, n, 'faculty' if kind == 'Lab in charge' else 'staff'))
    return list(dict.fromkeys(out))


PROG_OF = [
    (r'^S\d', 'ECE', 'btech-ece', 'B.Tech ECE'), (r'^S\d', 'AEI', 'btech-aei', 'B.Tech AEI'),
    (r'^M\d', 'AEI', 'mtech', 'M.Tech AEI'), (r'^M\d', 'MTV', 'mtech', 'M.Tech CS'), (r'^M\d', 'CMS', 'mtech', 'M.Tech CS'),
    (r'^M\d', 'SP', 'mtech', 'M.Tech SP'), (r'^M\d', 'MNE', 'mtech', 'M.Tech MNE'), (r'^M\d', 'RAA', 'mtech', 'M.Tech RA'),
]


def enrich_labs(rows, faculty_names, staff_rows):
    staff_names = [s['name'] for s in staff_rows]
    staff_labs = {}
    def slug_of(url):
        return re.sub(r'^(https?://[^/]+)?/|/$', '', url or '').split('/')[-1]
    lab_pages = [p for p in API_PAGES if re.search(r'Lab in charge|Labs conducted', p['content']['rendered'], re.I)
                 and 'pp-dual-heading' not in p['content']['rendered']]  # profiles mention labs too
    titles = {p['slug']: clean(BeautifulSoup(p['title']['rendered'], 'lxml').get_text()) for p in lab_pages}
    match, used = {}, set()
    # Each lab row takes one page: by its old link, then by exact name, then by a close name.
    for how in ('slug', 'name', 'close'):
        for page in lab_pages:
            if page['slug'] in match:
                continue
            for i, r in enumerate(rows):
                if i in used:
                    continue
                a, b = norm_name(titles[page['slug']]), norm_name(r['name'])
                if (how == 'slug' and slug_of(r.get('old_url')) == page['slug']) or (how == 'name' and a == b) \
                        or (how == 'close' and difflib.SequenceMatcher(None, a, b).ratio() >= 0.9):
                    match[page['slug']] = i
                    used.add(i)
                    break
    for page in lab_pages:
        title = titles[page['slug']]
        r = rows[match[page['slug']]] if page['slug'] in match else None
        if r is None:
            r = {'name': title, 'type': 'teaching', 'programmes': '', 'summary': '', 'lead_faculty': '', 'old_url': page['link']}
            rows.append(r)
            warn('labs', title, 'Has a page on the old site but is not on the Laboratories page: added, check it is still a lab')
        d = old_pages.parse_lab_page(page)
        r['old_url'] = page['link']
        lead = resolve_people(d['lead_faculty'], faculty_names, 'Lab in charge', r['name'])
        r['lead_faculty'] = '; '.join(lead)
        staff = resolve_people(d['staff'], staff_names, 'Technical staff', r['name'])
        r['tech_staff'] = '; '.join(staff)
        for sname in staff:
            staff_labs.setdefault(sname, []).append(r['name'])
        progs = [p for p in r.get('programmes', '').split('; ') if p]
        courses = []
        for c in d['courses']:
            labels = []
            for pat, code, tax, label in PROG_OF:
                if re.match(pat, c['semester'] or '') and code in c['programme'].split('; '):
                    labels.append(label)
                    progs.append(tax)
            courses.append('%s | %s | %s | %s' % (c['code'], c['name'], ', '.join(labels) or c['programme'], c['semester']))
        r['courses'] = '\n'.join(courses)
        r['programmes'] = '; '.join(dict.fromkeys(progs))
        scholars = [old_pages.parse_scholar(x, faculty_names) for x in d['scholars'] if 3 < len(x) < 160]
        r['scholars'] = '\n'.join('%s | %s | %s | %s | %s' % (x['name'], x['level'], x['guide'], x['topic'], x['status']) for x in scholars if x['name'])
        if (scholars or d['research_areas']) and not d['courses']:
            r['type'] = 'research'
        if d['research_areas'] and r['type'] == 'research':
            r['research_areas'] = suggest_areas(' '.join(d['research_areas'] + d['description'])) or r.get('research_areas', '')
        r['photo_url'] = d['images'][0] if d['images'] else ''
        r['gallery'] = '\n'.join(d['images'][1:6])
        manual = next((h for l, h in d['manuals'] if 'manual' in l.lower()), '')
        r['manual_url'] = manual if len([1 for l, h in d['manuals'] if 'manual' in l.lower()]) == 1 else ''
        r['content'] = old_pages.lab_content(d, d['manuals'])
        if not r.get('summary'):
            aims = [a for b in d['blocks'] for a in b['aims']] + d['description'] + d['aims']
            first = next((a for a in aims if len(a) > 30), '')
            if first:
                first = re.sub(r'^to\s+', '', first.strip(' .'), flags=re.I)
                r['summary'] = (first[:1].upper() + first[1:])[:200].rstrip(' ,;') + '.'
            elif d['courses']:
                r['summary'] = 'Lab for ' + ', '.join(c['name'] for c in d['courses'][:3]) + '.'
            if r['summary']:
                warn('labs', r['name'], 'Summary written from the old page ("%s"): check it reads well' % r['summary'][:60])
    for st in staff_rows:
        if not st.get('lab') and st['name'] in staff_labs:
            st['lab'] = staff_labs[st['name']][0]  # the labs import links every lab they work in
    return rows


# ---------- output ----------

def write(path, rows, cols):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--site', help='public address of the old site, e.g. https://ece.cet.ac.in')
    ap.add_argument('--export')
    ap.add_argument('--pages')
    ap.add_argument('--out', default='migration')
    a = ap.parse_args()
    if not (a.site or a.export or a.pages):
        ap.error('give --site, --export or --pages')
    pages, posts, atts = ({}, [], {})
    if a.site:
        pages, posts, atts = read_site(a.site, os.path.join(a.out, 'source'))
    if a.export:
        pages, posts, atts = read_export(a.export)
    if a.pages:
        pages.update(read_pages(a.pages))
    os.makedirs(a.out, exist_ok=True)

    cols = {
        'faculty': ['name', 'designation', 'designation_text', 'additional_role', 'joined_year', 'email', 'room', 'specialisation', 'research_areas', 'qualifications', 'courses', 'scholar_url', 'orcid_url', 'scopus_url', 'is_guide', 'about', 'photo_url', 'old_profile_url'],
        'staff': ['name', 'category', 'lab'],
        'batches': ['programme', 'admission_year', 'batch_label', 'advisors', 'source_line'],
        'labs': ['name', 'type', 'programmes', 'summary', 'lead_faculty', 'tech_staff', 'research_areas', 'courses', 'scholars', 'photo_url', 'gallery', 'manual_url', 'content', 'old_url'],
        'publications': ['title', 'authors', 'venue', 'type', 'year', 'volume', 'pages', 'doi', 'status', 'faculty', 'confidence', 'raw'],
    }
    parsers = {
        'faculty': (parse_faculty, ('faculty-2', 'faculty')),
        'staff': (parse_staff, ('technical-staff',)),
        'batches': (parse_batches, ('staff-advisors',)),
        'labs': (parse_labs, ('laboratories',)),
        'publications': (parse_publications, ('publications',)),
    }
    out = {}
    for name, (fn, slugs) in parsers.items():
        soup = page(pages, *slugs)
        if soup is None:
            warn(name, '-', 'Page not found in the input (%s)' % ', '.join(slugs))
            out[name] = []
            continue
        out[name] = fn(soup)
        if name == 'faculty':
            FACULTY_NAMES[:] = [r['name'] for r in out[name]]
    if API_PAGES:
        enrich_faculty(out['faculty'])
        enrich_labs(out['labs'], FACULTY_NAMES, out['staff'])
    else:
        warn('pages', '-', 'No individual pages in the input: profiles and lab details not converted (use --site, or --pages with api/pages.json)')
    summary = []
    for name in parsers:
        if out[name] or name in ('faculty', 'labs'):
            write(os.path.join(a.out, name + '.csv'), out[name], cols[name])
            summary.append('%-13s %4d rows' % (name, len(out[name])))
    if API_PAGES:
        by_slug = {p['slug']: p for p in API_PAGES}
        sections = old_pages.department_sections(by_slug, out['faculty'], warn)
        write(os.path.join(a.out, 'sections.csv'), sections, ['page', 'action', 'target', 'content'])
        summary.append('%-13s %4d rows' % ('sections', len(sections)))
    if posts:
        rows = parse_news(posts, atts)
        write(os.path.join(a.out, 'news.csv'), rows, ['old_id', 'title', 'date', 'slug', 'category', 'old_categories', 'featured_image_url', 'excerpt', 'content_html', 'old_url'])
        summary.append('%-13s %4d rows' % ('news', len(rows)))
    write(os.path.join(a.out, 'warnings.csv'), WARN, ['type', 'item', 'reason'])
    print('\n'.join(summary))
    print('%-13s %4d to review' % ('warnings', len(WARN)))


if __name__ == '__main__':
    sys.exit(main())
