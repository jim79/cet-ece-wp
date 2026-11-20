"""Convert the old ece.cet.ac.in content into review spreadsheets (CSV).

Input, either:
  --export old-site.xml      WordPress export from the old site (Tools > Export > All content)
  --pages  folder/           saved HTML pages: faculty-2.html, technical-staff.html,
                             staff-advisors.html, laboratories.html, publications.html

Output (in --out, default ./migration):
  faculty.csv, staff.csv, batches.csv, labs.csv, publications.csv, news.csv
  warnings.csv   every row that needs a human look, with the reason

Review and correct the CSVs in a spreadsheet, then load them with
  wp ece import <type> <file.csv>

Nothing here guesses silently: anything uncertain is written to warnings.csv.
"""
import argparse
import csv
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

WARN = []


def warn(kind, item, reason):
    WARN.append({'type': kind, 'item': item, 'reason': reason})


def clean(text):
    text = html.unescape(text or '')
    text = text.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def norm_name(name):
    n = re.sub(r'^(dr|prof|mr|ms|mrs|smt|shri)[\.,]?\s+', '', clean(name), flags=re.I)
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


def read_pages(folder):
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
            photo = img.get('data-src') or img.get('src') or ''
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
        if re.search(r'\bug\b.*lab|under\s*graduate', low) and len(text) < 40:
            section = 'ug'
            continue
        if re.search(r'pg|post\s*graduate|research', low) and 'lab' in low and len(text) < 40:
            section = 'pg'
            continue
        if tag != 'li' or not section:
            continue
        name = clean(text)
        a = el.find('a')
        if not re.search(r'lab|centre|center|c2s', name, re.I):
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

QUOTE = re.compile(r'[“"]\s*(.+?)\s*[,.]?\s*[”"]')
DOI = re.compile(r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)?\b(10\.\d{4,9}/[^\s,;]+|1\d{3}/[A-Za-z0-9.\-()/]+)', re.I)


def parse_pub_entry(text, year_ctx):
    raw = clean(text)
    r = {'title': '', 'authors': '', 'venue': '', 'type': '', 'year': '', 'volume': '', 'pages': '', 'doi': '', 'status': 'published', 'faculty': '', 'raw': raw, 'confidence': 'low'}
    m = DOI.search(raw)
    if m:
        d = m.group(1).rstrip('.')
        if not d.startswith('10.'):
            d = '10.' + d
            warn('publications', raw[:80], 'DOI was missing "10.": corrected to %s, check it' % d)
        r['doi'] = d
    q = QUOTE.search(raw)
    if q:
        r['title'] = q.group(1).strip(' ,.')
        r['authors'] = raw[:q.start()].strip(' ,.:')
        rest = raw[q.end():]
    else:
        parts = [p.strip() for p in re.split(r'(?<=[a-z\]\)])\.\s+|,\s+(?=[A-Z])', raw) if p.strip()]
        rest = ''
        if len(parts) >= 2:
            r['authors'], r['title'] = parts[0], parts[1]
            rest = ' '.join(parts[2:])
        else:
            r['title'] = raw
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
    venue = re.split(r'\bvol\b|\bpp?\.|\b(19|20)\d{2}\b|doi', rest, flags=re.I)[0]
    r['venue'] = venue.strip(' ,.;:-')
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
    if r['title'] and r['authors'] and r['venue']:
        r['confidence'] = 'high' if q else 'medium'
    return r


def parse_publications(soup):
    rows, year, fac = [], '', ''
    for tag, text, el in blocks(soup):
        t = text.strip()
        if re.fullmatch(r'(19|20)\d{2}', t.strip(' :')):
            year = t.strip(' :')
            continue
        if len(t) < 60 and t.endswith(':') and re.search(r'[A-Za-z]', t):
            fac = clean(t.rstrip(':'))
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


# ---------- output ----------

def write(path, rows, cols):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--export')
    ap.add_argument('--pages')
    ap.add_argument('--out', default='migration')
    a = ap.parse_args()
    if not a.export and not a.pages:
        ap.error('give --export or --pages')
    pages, posts, atts = ({}, [], {})
    if a.export:
        pages, posts, atts = read_export(a.export)
    if a.pages:
        pages.update(read_pages(a.pages))
    os.makedirs(a.out, exist_ok=True)

    sets = {
        'faculty': (parse_faculty, ('faculty-2', 'faculty'), ['name', 'designation', 'designation_text', 'additional_role', 'joined_year', 'email', 'specialisation', 'research_areas', 'photo_url', 'old_profile_url']),
        'staff': (parse_staff, ('technical-staff',), ['name', 'category', 'lab']),
        'batches': (parse_batches, ('staff-advisors',), ['programme', 'admission_year', 'batch_label', 'advisors', 'source_line']),
        'labs': (parse_labs, ('laboratories',), ['name', 'type', 'programmes', 'summary', 'lead_faculty', 'old_url']),
        'publications': (parse_publications, ('publications',), ['title', 'authors', 'venue', 'type', 'year', 'volume', 'pages', 'doi', 'status', 'faculty', 'confidence', 'raw']),
    }
    summary = []
    for name, (fn, slugs, cols) in sets.items():
        soup = page(pages, *slugs)
        if soup is None:
            warn(name, '-', 'Page not found in the input (%s)' % ', '.join(slugs))
            continue
        rows = fn(soup)
        write(os.path.join(a.out, name + '.csv'), rows, cols)
        summary.append('%-13s %4d rows' % (name, len(rows)))
    if posts:
        rows = parse_news(posts, atts)
        write(os.path.join(a.out, 'news.csv'), rows, ['old_id', 'title', 'date', 'slug', 'category', 'old_categories', 'featured_image_url', 'excerpt', 'content_html', 'old_url'])
        summary.append('%-13s %4d rows' % ('news', len(rows)))
    write(os.path.join(a.out, 'warnings.csv'), WARN, ['type', 'item', 'reason'])
    print('\n'.join(summary))
    print('%-13s %4d to review' % ('warnings', len(WARN)))


if __name__ == '__main__':
    sys.exit(main())
