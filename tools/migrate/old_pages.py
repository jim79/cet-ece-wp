"""Readers for the old site's individual pages: faculty profiles, lab pages and
the department pages (OBE, Programs, Research overview, Placements).

Used by convert_old_site.py. Everything returns plain dicts and the review
markup described in README.md ("Formatted text"): lines starting with "## "
are headings, "- " bullets, "1. " numbered items, "| a | b |" table rows,
[label](https://...) links, and blank lines separate paragraphs.
"""
import difflib
import re

from bs4 import BeautifulSoup, NavigableString


def clean(text):
    text = (text or '').replace('\xa0', ' ').replace('​', '').replace('‪', '').replace('‬', '')
    return re.sub(r'\s+', ' ', text).strip()


def norm_name(name):
    n = re.sub(r'^(dr|prof|mr|ms|mrs|smt|shri)\b[\W_]*', '', clean(name), flags=re.I)
    n = re.sub(r'^(dr|prof)\b[\W_]*', '', n, flags=re.I)  # "Prof. (Dr.) X"
    return re.sub(r'[^a-z]', '', n.lower())


def original_image(url):
    """WordPress resized copy ("photo-150x150.jpg") -> the uploaded original."""
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif)$)', '', url or '', flags=re.I)


BLOCK_TAGS = ['p', 'div', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr', 'td', 'th', 'table', 'section', 'figure', 'figcaption', 'blockquote', 'span']


def lines_of(html):
    """Text lines in document order, one per block element or <br>."""
    soup = BeautifulSoup(html or '', 'lxml')
    text_soup = BeautifulSoup(html or '', 'lxml')
    for br in text_soup.find_all('br'):
        br.replace_with('\n')
    for el in text_soup.find_all(BLOCK_TAGS):
        el.insert_before('\n')
        el.insert_after('\n')
    out = []
    for raw in text_soup.get_text('').split('\n'):
        t = clean(raw)
        if t:
            out.append(t)
    return out, soup


def links_of(soup):
    return [(clean(a.get_text(' ')), a['href'].strip()) for a in soup.find_all('a', href=True)]


def md_link(label, url):
    label = label.replace('[', '(').replace(']', ')')
    return '[%s](%s)' % (label, url)


NOISE = re.compile(r'^(previous|next|read more|click here|google ?scholar( link| profile)?|orcid( profile)?( link)?|scopus( profile)?( link)?|web of science.*|publications? link|research ?gate.*|linked ?in.*|id ?:?|‪google scholar)$', re.I)


# ---------- faculty profiles ----------

SECTIONS = [
    (r'subject|courses|teaching$', 'courses'),
    (r'brief profile|about', 'profile'),
    (r'qualification', 'qualifications'),
    (r'total experience|experience|positions held', 'experience'),
    (r'area|interest|speciali[sz]ation|research areas', 'interests'),
    (r'achievement|award', 'achievements'),
    (r'responsibilit', 'responsibilities'),
    (r'membership|mbership|ations$', 'memberships'),
    (r'approved research guide|ph\.? ?d guidance|guidance', 'guidance'),
    (r'expert lectures|chaired', 'talks'),
    (r'innovation', 'innovations'),
    (r'sustainable', 'sustainability'),
    (r'publication|papers in|journal|conference', 'publications'),
    (r'web of science|orcid id|^ug$|^pg$', 'skip'),
]
SECTION_TITLES = {
    'profile': 'Profile', 'experience': 'Experience', 'interests': 'Areas of interest',
    'achievements': 'Achievements and awards', 'responsibilities': 'Other responsibilities',
    'memberships': 'Professional memberships', 'guidance': 'Research guidance',
    'talks': 'Invited talks and sessions chaired', 'innovations': 'Innovations in teaching and learning',
    'sustainability': 'Sustainable engineering practices',
}
ABOUT_ORDER = ['profile', 'interests', 'experience', 'achievements', 'responsibilities', 'memberships', 'guidance', 'talks', 'innovations', 'sustainability']


def section_key(line, is_heading):
    """Return the section key if this line is a section heading."""
    m = re.match(r'^(.{2,70}?)\s*:\s*$', line)
    bare = re.match(r'^(membership|other responsibilit|achievements?|awards?|(professional |teaching )?experience|(educational )?qualifications?|areas? of interests?|research interests?|subjects|publications)\b[^\d]{0,40}$', line, re.I)
    label = m.group(1) if m else (line if is_heading or bare else '')
    if not label or len(label) > 70:
        return ''
    low = label.lower().strip()
    for pat, key in SECTIONS:
        if re.search(pat, low):
            return key
    return ''


def heading_texts(soup):
    out = set()
    for el in soup.select('.elementor-heading-title, h2, h3, h4, h5, strong, b'):
        t = clean(el.get_text(' '))
        if t and len(t) < 80:
            out.add(t)
    return out


DEGREE = re.compile(
    r"\b(Ph\.?\s?D\.?|Doctorate|M\.?\s?Tech\.?|B\.?\s?Tech\.?|(?-i:[MB]\.?\s?E)\.?(?=[\s(,]|$)|M\.?\s?Sc\.?|B\.?\s?Sc\.?|MBA|M\.?\s?S\.(?!\w)|M\.?\s?Phil\.?|AMIE|Post ?Doc(?:toral)?)",
    re.I)
DEGREE_NAMES = [
    (r'ph|doctor', 'Ph.D.'), (r'post', 'Postdoctoral'), (r'm\.?\s?tech', 'M.Tech'), (r'b\.?\s?tech', 'B.Tech'),
    (r'm\.?\s?sc', 'M.Sc.'), (r'b\.?\s?sc', 'B.Sc.'), (r'mba', 'MBA'), (r'm\.?\s?phil', 'M.Phil.'), (r'amie', 'AMIE'),
    (r'^m\.?\s?s', 'M.S.'), (r'^m', 'M.E.'), (r'^b', 'B.E.'),
]
INST_HINT = re.compile(r'universit|college|institute|iit|nit\b|iisc|cusat|cet\b|school|centre|center|rit\b|tkm|gec|kerala|madras|calicut|kannur|cochin|bombay|delhi|kanpur|kharagpur|anna', re.I)


def degree_name(token):
    t = token.lower().replace(' ', '')
    for pat, name in DEGREE_NAMES:
        if re.search(pat, t):
            return name
    return token


def parse_qualification(line):
    """One line -> list of {degree, specialisation, institution, year}.

    Handles "B-Tech in ECE (Calicut University).", "Ph. D Faculty of Engineering
    (BioSignal Processing) at CUSAT", and "She received her B.Tech ... from RIT
    Kottayam and M.Tech in Microwave and Radar from CUSAT."
    """
    if re.search(r'pursuing|currently doing|ongoing|registered for', line, re.I):
        return []  # stays in the profile text
    text = re.sub(r'\b([BM])\s*-\s*Tech', r'\1.Tech', line)
    # Abbreviations that are not sentence ends: "Govt. Engineering College".
    text = re.sub(r'\b(Govt|Engg|Dept|Inst|Univ|St|Coll|Tech)\.\s', r'\1 ', text)
    hits = list(DEGREE.finditer(text))
    if not hits:
        return []
    rows = []
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        chunk = text[m.end():end].lstrip(' :.-–')
        year = ''
        ys = re.findall(r'\b(19[5-9]\d|20[0-4]\d)\b', chunk)
        if ys:
            year = ys[-1]
        spec, inst = '', ''
        chunk = re.sub(r'\bin the year\b', '', chunk)
        sm = re.search(r'\b(?:in|on)\s+(.+?)(?=\s+(?:from|at|under)\b|\s*\(|,|;|\s+-\s+|\s+–\s+|\.\s|\.$|\s+and\s*$|$)', chunk)
        if sm:
            spec = sm.group(1)
        im = re.search(r'\b(?:from|at|under)\s+(?:the\s+)?(.+?)(?=\s+and\s+(?:[BM]\.?\s?Tech|Ph|M\.?\s?E|B\.?\s?E)|;|\.\s|\.$|$)', chunk)
        if im:
            inst = im.group(1)
        pm = re.search(r'\((?!\s*(?:19|20)\d{2}\s*\))([^)]+)\)', chunk)
        if pm:
            inner = pm.group(1)
            if INST_HINT.search(inner) and not inst:
                inst = inner
            elif not spec:
                spec = inner
        if not spec and not inst:
            # "M.Tech, Signal Processing, CUSAT, 2010" or "Ph.D - IIT Madras"
            parts = [p.strip(' .-–') for p in re.split(r',|\s[-–]\s', chunk) if p.strip(' .-–')]
            parts = [p for p in parts if not re.fullmatch(r'(19|20)\d{2}', p) and p.lower() not in ('degree', 'and')]
            for k, p in enumerate(parts):
                if INST_HINT.search(p):
                    inst = ', '.join(parts[k:])  # "NIT Surathkal, Karnataka"
                    break
                if not spec and len(p) > 2:
                    spec = p
        if not inst or not spec:
            parts = [p.strip(' .-–') for p in re.split(r',|\s[-–]\s', re.sub(r'\((?:19|20)\d{2}\)', '', chunk)) if p.strip(' .-–')]
            if not inst:
                inst = next((p for p in parts[1:] if INST_HINT.search(p) and not re.search(r'\b(in|from)\b', p)), '')
            if not spec and parts and not INST_HINT.search(parts[0]) and not re.match(r'(from|at|under|in)\b', parts[0]):
                spec = parts[0]
        spec = re.sub(r'^(degree|the)\s+', '', clean(spec), flags=re.I).strip(' .,-–()')
        spec = re.sub(r'\s*\b(19|20)\d{2}\b.*$', '', spec).strip(' .,-–()')
        if re.fullmatch(r'(and|degree|degrees|&)?', spec, re.I):
            spec = ''
        inst = re.sub(r'\s*[,(]?\s*\b(19|20)\d{2}\b.*$', '', clean(inst)).strip(' .,-–()')
        inst = re.sub(r'\s+(in|on|during|and)$', '', inst)
        if inst.count('(') > inst.count(')'):
            inst += ')'
        if re.fullmatch(r'(is )?(completed|ongoing|pursuing)', spec, re.I):
            spec = ''
        rows.append({'degree': degree_name(m.group(1)), 'specialisation': spec, 'institution': inst, 'year': year})
    # "B. Tech and M. Tech degree in X from Y": the first degree has no details of its own.
    for i in range(len(rows) - 2, -1, -1):
        r, nxt = rows[i], rows[i + 1]
        if not r['specialisation'] and not r['institution']:
            r['specialisation'], r['institution'] = nxt['specialisation'], nxt['institution']
    return rows


def parse_course(line):
    m = re.match(r'^([A-Z0-9]{2,}\d{2,}[A-Z0-9]*)\s*[-–:]?\s*(.+)$', line)
    if m and re.search(r'\d', m.group(1)):
        return {'code': m.group(1), 'name': m.group(2).strip(' .')}
    return {'code': '', 'name': line.strip(' .')}


def parse_profile(page):
    """One old profile page -> dict of the fields the new faculty profile holds."""
    html = page['content']['rendered']
    lines, soup = lines_of(html)
    heads = heading_texts(soup)
    dual = soup.select_one('.pp-dual-heading')
    name = clean(dual.select_one('.pp-first-text').get_text(' ')) if dual and dual.select_one('.pp-first-text') else clean(page['title']['rendered'])
    des = clean(dual.select_one('.pp-second-text').get_text(' ')) if dual and dual.select_one('.pp-second-text') else ''
    img = soup.find('img')
    photo = original_image(img.get('data-src') or img.get('src') or '') if img else ''

    # Contact list: the icon tells what each line is.
    email, room = '', ''
    for li in soup.select('.elementor-icon-list-item'):
        icon = ' '.join(li.find('i').get('class', [])) if li.find('i') else ''
        t = clean(li.get_text(' '))
        m = re.search(r'[\w.+-]+@[\w.-]+\.\w+', t)
        if m:
            email = email or m.group(0)
        elif 'chair' in icon or re.match(r'room', t, re.I):
            room = clean(re.sub(r'^room\s*(no)?\.?\s*:?', '', t, flags=re.I))

    sec = {}
    cur = 'intro'
    for line in lines:
        k = section_key(line, line in heads or line.rstrip(' :') in heads)
        if k:
            cur = k
            # "Area of Interest: Bio Signal Processing, Instrumentation" on one line
            m = re.match(r'^[^:]{2,60}:\s*(.+)$', line)
            if m and not line.endswith(':'):
                sec.setdefault(cur, []).append(m.group(1))
            continue
        m = re.match(r'^([^:]{3,45}):\s*(.+)$', line)
        if m and section_key(m.group(1) + ':', True) and cur != 'courses':
            cur = section_key(m.group(1) + ':', True)
            sec.setdefault(cur, []).append(m.group(2))
            continue
        if NOISE.match(line) or line in (name, des):
            continue
        if cur in ('courses', 'intro') and (len(line) > 80 or re.search(r'\b(joined|received|did|completed|served|worked|teaches|she|he|her|his|currently)\b', line, re.I)) and cur != 'intro' or (cur == 'intro' and len(line) > 80):
            cur = 'profile'
        sec.setdefault(cur, []).append(line)

    links = links_of(soup)
    urls = {'scholar_url': '', 'orcid_url': '', 'scopus_url': ''}
    other_links = []
    for label, href in links:
        h = href.lower()
        if 'scholar.google' in h:
            urls['scholar_url'] = urls['scholar_url'] or href
        elif 'orcid.org' in h:
            m = re.search(r'\d{4}-\d{4}-\d{4}-\d{3}[\dX]', href)
            if m:
                urls['orcid_url'] = urls['orcid_url'] or 'https://orcid.org/' + m.group(0)
        elif 'scopus.com' in h:
            urls['scopus_url'] = urls['scopus_url'] or href
        elif re.search(r'webofscience|publons|researcherid|researchgate|linkedin|vidwan|irins', h):
            if re.fullmatch(r'[A-Z]{3}-\d{4}-\d{4}', label or ''):
                label = 'Web of Science ResearcherID ' + label
            other_links.append((label or 'Profile', href))
    for line in sec.get('skip', []) + sec.get('intro', []):
        m = re.search(r'\b([A-Z]{3}-\d{4}-\d{4})\b', line)  # Web of Science ResearcherID
        if m and not any(m.group(1) in l + u for l, u in other_links):
            other_links.append(('Web of Science ResearcherID ' + m.group(1), 'https://www.webofscience.com/wos/author/record/' + m.group(1)))

    quals, qual_notes = [], []
    keep = []
    for line in sec.get('profile', []):
        if DEGREE.search(line) and re.search(r'\b(from|at|in|under)\b', line):
            sec.setdefault('qualifications', []).append(line)
        else:
            keep.append(line)
    sec['profile'] = keep
    for line in sec.get('qualifications', []):
        rows = parse_qualification(line)
        if rows:
            quals += rows
        else:
            qual_notes.append(line)
    # The same degree written twice (prose and list) is kept once.
    seen, q2 = set(), []
    for q in quals:
        k = (q['degree'], q['specialisation'].lower()[:20])
        if k not in seen:
            seen.add(k)
            q2.append(q)
    quals = q2

    courses = []
    for line in sec.get('courses', []):
        for part in ([line] if len(line) > 60 or ';' not in line else line.split(';')):
            c = parse_course(clean(part))
            if c['name'] and len(c['name']) < 120 and c['name'].lower() not in [x['name'].lower() for x in courses]:
                courses.append(c)

    about = []
    if qual_notes:
        sec.setdefault('profile', [])
        sec['profile'] = qual_notes + sec['profile']
    for k in ABOUT_ORDER:
        items = [x for x in sec.get(k, []) if not NOISE.match(x)]
        if not items:
            continue
        about.append('## ' + SECTION_TITLES[k])
        if k == 'profile' or (len(items) == 1 and len(items[0]) > 120):
            about += [x + '\n' for x in items]
        else:
            about += ['- ' + re.sub(r'^(?:[•*\-–]|\d{1,2}[.)])\s*', '', x).strip() for x in items]
        about.append('')
    if other_links:
        about.append('## Other research profiles')
        about += ['- ' + md_link(l, u) for l, u in dict.fromkeys(other_links)]
        about.append('')
    pubs = sec.get('publications', [])
    interests = '; '.join(sec.get('interests', []))
    return {
        'name': name, 'designation_text': des, 'email': email, 'room': room, 'photo_url': photo,
        'qualifications': '\n'.join('%s | %s | %s | %s' % (q['degree'], q['specialisation'], q['institution'], q['year']) for q in quals),
        'qualification_rows': quals,
        'courses': '\n'.join(('%s | %s' % (c['code'], c['name'])) if c['code'] else c['name'] for c in courses),
        'interests': interests,
        'about': '\n'.join(about).strip(),
        'publication_lines': len([p for p in pubs if len(p) > 40]),
        **urls,
    }


def match_profiles(faculty_rows, pages, warn):
    """Attach the matching old profile page to each faculty row."""
    profiles = {}
    for p in pages:
        html = p['content']['rendered']
        if 'pp-dual-heading' in html or re.search(r'Educational Qualifications|Subjects:', html):
            profiles[p['slug']] = p
    by_name = {}
    for p in profiles.values():
        by_name[norm_name(clean(BeautifulSoup(p['title']['rendered'], 'lxml').get_text()))] = p
        d = BeautifulSoup(p['content']['rendered'], 'lxml').select_one('.pp-first-text')
        if d:
            by_name[norm_name(d.get_text(' '))] = p
    used = set()
    for r in faculty_rows:
        slug = re.sub(r'^(https?://[^/]+)?/|/$', '', r.get('old_profile_url', '')).split('/')[-1]
        p = profiles.get(slug) or by_name.get(norm_name(r['name']))
        if not p:
            close = difflib.get_close_matches(norm_name(r['name']), list(by_name), n=1, cutoff=0.82)
            if close:
                p = by_name[close[0]]
                warn('faculty', r['name'], 'Profile page matched by a similar name (%s): check' % p['link'])
        if not p:
            warn('faculty', r['name'], 'No profile page found on the old site: qualifications, courses and links to add by hand')
            continue
        used.add(p['slug'])
        yield r, p
    former = sorted(clean(BeautifulSoup(p['title']['rendered'], 'lxml').get_text()) for s, p in profiles.items() if s not in used)
    if former:
        warn('faculty', '%d other profile pages' % len(former), 'Profile pages for people not on the current faculty list (former faculty?), not imported: ' + ', '.join(former))


# ---------- lab pages ----------

PERSON = re.compile(r'^(?:(?:Dr|Prof|Mr|Ms|Mrs|Smt|Shri)\.?\s*)+[A-Z]', re.I)


def split_people(line):
    out = []
    for n in re.split(r'\s*/\s*|\s*,\s*(?=(?:Dr|Prof|Mr|Ms|Mrs)\b)|\s+and\s+', line):
        n = clean(re.sub(r'^(?:Mr|Ms|Mrs|Smt|Shri)\.?\s*', '', n, flags=re.I)).strip(' .')
        if n and re.search(r'[A-Za-z]{2}', n):
            out.append(n)
    return out


COURSE_LINE = re.compile(r'^([A-Z]{0,6}\d{2,}[A-Z]{0,5}\d{0,4}|[A-Z]{2,6}\s?\d{3}[A-Z]?)(?:\s*[–-]\s*|\s+(?=[A-Z]{3}))(.*)$')
ACRONYMS = {'rf', 'dsp', 'it', 'vlsi', 'iot', 'mems', 'ece', 'aei', 'pg', 'ug', 'ic', 'ics', 'ai', 'ml', 'hdl', 'fpga', 'cad', 'mtv', 'sp', 'plc', 'scada', 'dcs', 'cmos', 'pcb', 'c'}
SMALL = {'and', 'of', 'in', 'for', 'with', 'the', 'a', 'an', 'to', 'on', 'using'}


def smart_title(name):
    """'RF DESIGN AND SIMULATION LAB' -> 'RF Design and Simulation Lab'."""
    if not name.isupper():
        return name
    words = []
    for i, w in enumerate(name.split()):
        core = re.sub(r'[^A-Za-z]', '', w).lower()
        if core in ACRONYMS:
            words.append(w.upper())
        elif core in SMALL and i:
            words.append(w.lower())
        else:
            words.append(w[:1].upper() + w[1:].lower() if not w.startswith('(') else '(' + w[1:2].upper() + w[2:].lower())
    return ' '.join(words)


def parse_lab_page(page):
    html = page['content']['rendered']
    tsoup = BeautifulSoup(html, 'lxml')
    table_scholars = []
    for table in tsoup.find_all('table'):
        rows = [[clean(td.get_text(' ')) for td in tr.find_all(['td', 'th'])] for tr in table.find_all('tr')]
        rows = [r for r in rows if any(r)]
        if rows and re.search(r'scholar|name', ' '.join(rows[0]), re.I):
            head = [h.lower() for h in rows[0]]
            for r in rows[1:]:
                d = dict(zip(head, r))
                name = next((v for k, v in d.items() if 'name' in k and 'supervisor' not in k), r[0])
                guide = next((v for k, v in d.items() if 'supervisor' in k or 'guide' in k), '')
                year = next((v for k, v in d.items() if 'year' in k), '')
                mode = next((v for k, v in d.items() if 'time' in k), '')
                table_scholars.append(' – '.join(x for x in (name, guide, year, mode) if x))
            table.decompose()
    html = str(tsoup)
    lines, soup = lines_of(html)
    # "EC431 –" then "NAME – S7 ECE" on the next line: join them.
    joined = []
    for line in lines:
        if joined and (re.fullmatch(r'[A-Z0-9 ]{3,12}\s*[–-]', joined[-1]) or re.match(r'^[–-]\s*(S\d|M\d)', line)):
            joined[-1] = joined[-1] + ' ' + line
        else:
            joined.append(line)
    lines = joined
    out = {'lead_faculty': [], 'staff': [], 'courses': [], 'aims': [], 'blocks': [], 'research_areas': [], 'scholars': [], 'description': [], 'images': [], 'manuals': [], 'pubs': []}
    mode = ''
    course_order = []
    current = None
    for line in lines:
        low = line.lower().rstrip(' :')
        if re.match(r'^lab in charges?$|^(ece|aei)$', low):
            continue
        m = re.match(r'^(faculty(?: in charge)?|technical staffs?)\s*:\s*(.*)$', line, re.I)
        if m:
            mode = 'staff' if m.group(1).lower().startswith('tech') else 'faculty'
            if m.group(2):
                out['lead_faculty' if mode == 'faculty' else 'staff'] += split_people(m.group(2))
            continue
        if low.startswith('details of labs conducted') or low == 'labs conducted':
            mode = 'courses'
            continue
        if low in ('description', 'about iot lab', 'about the lab', 'about'):
            mode = 'description'
            continue
        if low.startswith('research areas') or low.startswith('areas of research'):
            mode = 'areas'
            continue
        if re.match(r'(details of )?research scholars', low):
            mode = 'scholars'
            continue
        if re.match(r'^(publications|selected publications|research publications)$', low):
            mode = 'pubs'
            continue
        if mode == 'pubs':
            out['pubs'].append(re.sub(r'^\d{1,3}[.)]\s*', '', line))
            continue
        if low == 'this course aims to':
            mode = 'aims'
            continue
        if low.startswith('list of experiments'):
            mode = 'experiments'
            continue
        if NOISE.match(line):
            continue
        if re.search(r'lab manual$', line, re.I):
            continue
        cm = COURSE_LINE.match(line)
        if cm and mode in ('courses', 'aims', 'experiments', 'description', 'staff', 'faculty') and len(line) < 140:
            code, rest = cm.group(1).replace(' ', ''), cm.group(2)
            parts = [p.strip(' –-') for p in re.split(r'\s+[–-]\s+', rest) if p.strip(' –-')]
            name = parts[0] if parts else ''
            where = parts[1] if len(parts) > 1 else ''
            known = [c for c in out['courses'] if c['code'] == code]
            if mode == 'courses' and not known:
                prog, sem = '', ''
                m = re.findall(r'\b([SM]\d)\s*([A-Z]{2,4}(?:\s*[,/]\s*[A-Z]{2,4})*)?', where)
                if m:
                    sem = ', '.join(dict.fromkeys(s for s, _ in m))
                    progs = ' '.join(p for _, p in m)
                    prog = '; '.join(dict.fromkeys(x for x in re.findall(r'ECE|AEI|CSE|EEE|ME|CE|IE|MTV|SP|AEI|MNE|RAA|CMS', progs)))
                out['courses'].append({'code': code, 'name': smart_title(name), 'programme': prog, 'semester': sem})
                continue
            if known or mode != 'courses':
                current = {'code': code, 'name': smart_title(name) or (known[0]['name'] if known else ''), 'aims': [], 'experiments': []}
                out['blocks'].append(current)
                course_order.append(code)
                mode = 'block'
                continue
        if mode == 'faculty':
            out['lead_faculty'] += split_people(line)
        elif mode == 'staff':
            out['staff'] += split_people(line)
        elif mode == 'description':
            out['description'].append(line)
        elif mode == 'areas':
            out['research_areas'].append(line)
        elif mode == 'scholars':
            out['scholars'].append(line)
        elif mode == 'aims' and current is not None:
            # A sentence the old page broke across lines continues in lowercase.
            if current['aims'] and line[:1].islower() and not current['aims'][-1].endswith('.'):
                current['aims'][-1] += ' ' + line
            else:
                current['aims'].append(line)
        elif mode == 'experiments' and current is not None:
            current['experiments'].append(line)
        elif mode in ('aims', 'experiments') and current is None:
            out['aims'].append(line)
        elif mode == 'courses':
            out['description'].append(line)
    out['scholars'] += table_scholars
    for img in soup.find_all('img'):
        src = original_image(img.get('data-src') or img.get('src') or '')
        if src and '/wp-content/uploads/' in src and src not in out['images']:
            out['images'].append(src)
    for label, href in links_of(soup):
        if href.lower().endswith('.pdf'):
            out['manuals'].append((label or 'Lab manual', href))
    return out


def lab_content(lab, manuals):
    """Review markup for the lab page body: course aims, experiments, manuals."""
    # The old pages write notes in square brackets ("[Any six experiments mandatory]");
    # on the new site square brackets mark placeholders, so these become parentheses.
    for key in ('description', 'research_areas', 'pubs', 'aims'):
        lab[key] = [re.sub(r'\[\s*([^\]]+?)\s*\]', r'(\1)', x) for x in lab[key]]
    for b in lab['blocks']:
        b['aims'] = [re.sub(r'\[\s*([^\]]+?)\s*\]', r'(\1)', x) for x in b['aims']]
        b['experiments'] = [re.sub(r'\[\s*([^\]]+?)\s*\]', r'(\1)', x) for x in b['experiments']]
    md = []
    if lab['description']:
        md += [x + '\n' for x in lab['description']]
    if lab['research_areas']:
        md.append('## Research areas')
        md += ['- ' + x for x in lab['research_areas']]
        md.append('')
    if lab['pubs']:
        md.append('## Publications')
        md += ['1. ' + x for x in lab['pubs']]
        md.append('')
    for b in lab['blocks']:
        md.append('## %s %s' % (b['code'], b['name']))
        if b['aims']:
            md.append('This course aims to:')
            md += ['- ' + x.lstrip('•-–* ') for x in b['aims']]
            md.append('')
        exps = []
        for x in b['experiments']:
            if re.match(r'^(part\s+[a-z]|microwave experiments|optical experiments|cycle\s*\d|.*\(minimum.*\)|.*experiments are mandatory.*)', x, re.I):
                exps.append('#### ' + x.rstrip(':'))
                continue
            m = re.match(r'^(\d{1,2})\s*[.):]?\s*(.+)$', x)
            if m:
                exps.append('1. ' + m.group(2))
            elif exps and exps[-1].startswith('1. ') and (x[:1].islower() or len(x) < 30):
                exps[-1] += ' ' + x  # wrapped line
            else:
                exps.append('1. ' + x)
        if exps:
            md.append('### List of experiments')
            md += exps
            md.append('')
        for label, href in manuals:
            if b['code'].lower() in (label + href).lower().replace(' ', ''):
                md.append(md_link('%s lab manual (PDF)' % b['code'], href))
                md.append('')
    return '\n'.join(md).strip()


def parse_scholar(line, faculty_names):
    """'Ms. Aswathy Madhu (2017-2022)' -> dict for the lab's scholars field."""
    s = {'name': '', 'level': 'phd', 'guide': '', 'topic': '', 'status': 'ongoing'}
    parts = [p.strip() for p in re.split(r'\s+[–-]\s+', line) if p.strip()]
    s['name'] = clean(re.sub(r'\(.*?\)', '', re.sub(r'^(?:Mr|Ms|Mrs)\.?\s*', '', parts[0]))).strip(' ,.')
    if re.search(r'thesis submitted|completed|awarded|\(\d{4}\s*[-–]\s*\d{4}\)', line, re.I):
        s['status'] = 'completed'
    idx = {norm_name(n): n for n in faculty_names}
    for p in parts[1:]:
        k = norm_name(p)
        close = difflib.get_close_matches(k, list(idx), n=1, cutoff=0.85) if k else []
        if close:
            s['guide'] = idx[close[0]]
        elif not re.fullmatch(r'[\d\s()–-]+|full ?time|part ?time|qip', p, re.I) and len(p) > 12:
            s['topic'] = p
    return s


# ---------- department pages ----------

def obe_data(page):
    """Committees from the OBE page (tables after "Department Structure")."""
    soup = BeautifulSoup(page['content']['rendered'], 'lxml')
    tables = []
    for t in soup.find_all('table'):
        rows = [[clean(td.get_text(' ')) for td in tr.find_all(['td', 'th'])] for tr in t.find_all('tr')]
        rows = [r for r in rows if any(r)]
        if rows and re.search(r'name', ' '.join(rows[0]), re.I):
            tables.append(rows)
    titles = [clean(x) for x in re.findall(r'(Department DQAC Cell|PAC of B\.Tech\.[^:<]*)', soup.get_text(' '))]
    return tables, titles


def committee_md(tables, titles):
    md = []
    names = {0: 'Department Quality Assurance Cell (DQAC)'}
    pac = [t for t in titles if t.startswith('PAC')]
    # The old page lists the AEI and ECE PAC headings together, then the AEI table, then ECE.
    order = ['Programme assessment committee: B.Tech Applied Electronics and Instrumentation', 'Programme assessment committee: B.Tech Electronics and Communication Engineering']
    for i, rows in enumerate(tables):
        title = names.get(i) or (order[i - 1] if i - 1 < len(order) else 'Committee')
        md.append('### ' + title)
        md.append('| Name | Role |')
        for r in rows[1:]:
            r = [x for x in r if not re.fullmatch(r'\d{1,2}\.?', x)]
            if len(r) >= 2:
                md.append('| %s | %s |' % (r[0], r[1]))
        md.append('')
    return '\n'.join(md).strip(), bool(pac)


def hod_from(tables):
    for rows in tables:
        for r in rows:
            for x in r:
                m = re.match(r'^(.*?)\s*\(HoD\)', x)
                if m:
                    return clean(m.group(1))
    return ''


def guides_md(page):
    """Research guides and their areas from the Research overview page."""
    soup = BeautifulSoup(page['content']['rendered'], 'lxml')
    md = ['| Guide | Research areas |']
    n = 0
    for t in soup.find_all('table'):
        for tr in t.find_all('tr'):
            cells = [clean(td.get_text(' ')) for td in tr.find_all(['td', 'th'])]
            if len(cells) >= 2 and cells[0] and not re.search(r'name of', cells[0], re.I):
                md.append('| %s | %s |' % (cells[0], cells[1]))
                n += 1
    return ('\n'.join(md) if n else ''), n


def approved_guides(programs_page):
    lines, _ = lines_of(programs_page['content']['rendered'])
    out, on = [], False
    for line in lines:
        if re.match(r'list of approved guides', line, re.I):
            on = True
            continue
        if on:
            if not re.match(r'^Dr\.?\s', line):
                break
            out.append(line)
    return out


def research_areas_list(programs_page):
    lines, _ = lines_of(programs_page['content']['rendered'])
    out, on = [], False
    for line in lines:
        if re.match(r'major areas of research', line, re.I):
            on = True
            continue
        if on:
            if line.endswith(':'):
                break
            out.append(line)
    return out


def doc_links(page):
    """Every PDF or KTU link on a page, with the text before it for context."""
    soup = BeautifulSoup(page['content']['rendered'], 'lxml')
    return [(clean(a.get_text(' ')), a['href'].strip()) for a in soup.find_all('a', href=True)
            if re.search(r'\.pdf$|ktu\.edu\.in', a['href'].strip(), re.I)]


PROGRAMME_PAGES = {
    'btech-ece': ('Electronics and Communication Engineering', 'ECE', 'btech'),
    'btech-aei': ('Applied Electronics and Instrumentation', 'AEI', 'btech'),
    'mtech-applied-electronics': ('Applied Electronics and Instrumentation', 'AEI', 'mtech'),
    'mtech-communication-systems': ('Communication Systems', 'CMS', 'mtech'),
    'mtech-signal-processing': ('Signal Processing', 'SP', 'mtech'),
    'mtech-micro-nano-electronics': ('Micro and Nano Electronics', 'MNE', 'mtech'),
    'mtech-robotics-automation': ('Robotics and Automation', 'RAA', 'mtech'),
}


def programme_documents(programs_page):
    """Scheme, syllabus and faculty list links per programme from the Programs page.

    The Programs page lists B.Tech links first (ECE, AEI), then M.Tech (AEI, CMS,
    SP, MNE, RAA); each programme block ends with its "Faculty List" link.
    """
    links = doc_links(programs_page)
    order = ['btech-ece', 'btech-aei', 'mtech-applied-electronics', 'mtech-communication-systems', 'mtech-signal-processing', 'mtech-micro-nano-electronics', 'mtech-robotics-automation']
    per = {k: [] for k in order}
    regulations = []
    i = 0
    started = False
    for label, href in links:
        if re.fullmatch(r'20\d\d', label):
            regulations.append((label, href))
            continue
        if re.search(r'scheme|syllabus|faculty list', label, re.I):
            started = True
        if not started or i >= len(order):
            continue
        per[order[i]].append((label, href))
        if re.search(r'faculty list', label, re.I):
            i += 1
    return per, regulations


def calendars(programs_page):
    return [(l, h) for l, h in doc_links(programs_page) if re.search(r'S\d', l) and re.search(r'20\d\d', l)]


def newsletters(programs_page):
    return [(l, h) for l, h in doc_links(programs_page) if re.search(r'newsletter', l, re.I)]


def placement_links(page):
    soup = BeautifulSoup(page['content']['rendered'], 'lxml')
    return [(clean(a.get_text(' ')), a['href'].strip()) for a in soup.find_all('a', href=True)
            if re.search(r'placement details', a.get_text(' '), re.I)]


def recruiters_2025(page):
    """'Schneider electric -12 lakhs' lines from the 2025 batch list: company and CTC only."""
    lines, _ = lines_of(page['content']['rendered'])
    out, on = [], False
    for line in lines:
        if re.search(r'list of students with placements', line, re.I):
            on = True
            continue
        if on:
            m = re.match(r'^([A-Z][\w .&()]+?)\s*[–-]\s*([\d.]+)\s*lakhs?$', line, re.I)
            if m:
                out.append((m.group(1).strip(), m.group(2)))
            elif re.search(r'texas instruments.*offers', line, re.I):
                break
    return out


def find_faculty(name, faculty_rows):
    idx = {norm_name(r['name']): r for r in faculty_rows}
    k = norm_name(re.sub(r'\(.*?\)', '', name))
    if k in idx:
        return idx[k]
    close = difflib.get_close_matches(k, list(idx), n=1, cutoff=0.85)
    return idx[close[0]] if close else None


def department_sections(pages, faculty_rows, warn):
    """Rows for sections.csv: changes to the new site's department pages.

    action: replace_section (the blocks under an existing heading), add_section
    (a new heading and content at the end of the page) or replace_text.
    """
    rows = []

    def add(page, action, target, content):
        if content:
            rows.append({'page': page, 'action': action, 'target': target, 'content': content})

    obe = pages.get('obe')
    if obe:
        tables, titles = obe_data(obe)
        md, _ = committee_md(tables, titles)
        add('academics/obe', 'replace_section', 'Programme assessment committees', md)
        hod = hod_from(tables)
        if hod:
            add('about', 'replace_section', 'Head of Department', '%s\n\n%s · 0471-2515563' % (hod, md_link('hodece@cet.ac.in', 'mailto:hodece@cet.ac.in')))
        # Programme coordinators from the PAC tables.
        coord = {}
        for i, t in enumerate(tables[1:3]):
            for r in t:
                if len(r) >= 3 and re.search(r'program(me)? coordinator', r[2], re.I):
                    coord['btech-aei' if i == 0 else 'btech-ece'] = r[1]
        for r in tables[0] if tables else []:
            if len(r) >= 3 and re.search(r'pg coordinator', r[2], re.I):
                for k in PROGRAMME_PAGES:
                    if k.startswith('mtech'):
                        coord[k] = r[1]
        for slug, name in coord.items():
            f = find_faculty(name, faculty_rows)
            email = f['email'] if f and f.get('email', '').endswith('@cet.ac.in') else '[name]@cet.ac.in'
            label = f['name'] if f else name
            add('academics/' + slug, 'replace_text', '[Faculty name], [name]@cet.ac.in', '%s, %s' % (label, email))
            add('academics/' + slug, 'replace_text', '[Faculty name]', label)
    else:
        warn('pages', 'obe', 'OBE page not found: committees not converted')

    prog = pages.get('programs')
    if prog:
        per, regs = programme_documents(prog)
        for slug, links in per.items():
            if not links:
                warn('pages', slug, 'No scheme or syllabus links found on the Programs page')
                continue
            md = ['| Scheme | Documents |']
            faculty_list = ''
            for label, href in links:
                if re.search(r'faculty list', label, re.I):
                    faculty_list = md_link('Faculty list (PDF)' if href.lower().endswith('.pdf') else 'Faculty list', href)
                    continue
                ym = re.search(r'(20\d\d)', label)
                part = re.search(r'S\d\s*&\s*S\d', label)
                doc = 'Syllabus' + (' ' + part.group(0) if part else '') + (' (PDF)' if href.lower().endswith('.pdf') else ' (KTU website)')
                md.append('| %s scheme | %s |' % (ym.group(1) if ym else label, md_link(doc, href)))
            if PROGRAMME_PAGES[slug][2] == 'btech' and regs:
                md.append('')
                md.append('Regulations: ' + ' · '.join(md_link('%s regulations' % l, h) for l, h in regs))
            if faculty_list:
                md.append('')
                md.append(faculty_list)
            md.append('')
            md.append('Regulations and the academic calendar come from APJ Abdul Kalam Technological University: ' + md_link('ktu.edu.in', 'https://ktu.edu.in/') + '.')
            add('academics/' + slug, 'replace_section', 'Curriculum', '\n'.join(md))
        cals = calendars(prog)
        if cals:
            md = ['| Academic calendar | Programme |']
            for label, href in cals:
                p = 'M.Tech' if re.search(r'm\.?\s?tech', label, re.I) else 'B.Tech'
                md.append('| %s | %s |' % (md_link(label, href), p))
            md.append('')
            md.append('Calendars are published by APJ Abdul Kalam Technological University. Older calendars are kept for reference.')
            add('downloads', 'replace_section', 'Academic', '\n'.join(md))
        nls = newsletters(prog)
        if nls:
            add('downloads', 'add_section', 'Department newsletters', '\n'.join('- ' + md_link(l, h) for l, h in nls))
        guides = approved_guides(prog)
        res = pages.get('research-overview')
        gmd, n = guides_md(res) if res else ('', 0)
        if guides or gmd:
            md = []
            if gmd:
                md += [gmd, '']
            if guides:
                md.append('Approved research guides: ' + ', '.join(guides) + '.')
                md.append('')
            md.append('See ' + md_link('Research', '/research/') + ' for research areas and labs, and the ' + md_link('faculty directory', '/faculty/') + ' for profiles.')
            add('academics/phd', 'replace_section', 'Guides and research areas', '\n'.join(md))
    else:
        warn('pages', 'programs', 'Programs page not found: syllabus, calendars and newsletters not converted')

    home = pages.get('home')
    ranks = rank_winners(home) if home else {}
    if ranks:
        years = sorted({y for _, y in ranks}, reverse=True)
        def cell(prog, year):
            return '; '.join('%s (%s, CGPA %s)' % (n.title() if n.islower() or ' ' in n and n.split()[-1].islower() else n, r.lower(), c)
                             for n, r, c in ranks.get((prog, year), [])) or '–'
        md = ['| Year | B.Tech ECE | B.Tech AEI |'] + ['| %s | %s | %s |' % (y, cell('B.Tech ECE', y), cell('B.Tech AEI', y)) for y in years]
        md += ['', '[Add the rank holders from 2019 onwards: the old website showed them only on posters.]']
        add('students', 'replace_section', 'University rank holders', '\n'.join(md))

    plc = pages.get('placements-latest') or pages.get('placement')
    if plc:
        links = placement_links(plc)
        rec = recruiters_2025(plc)
        md = []
        if links:
            md.append('Placement details for earlier batches:')
            md += ['- ' + md_link(l.title().replace('Ece', 'ECE').replace('Aei', 'AEI'), h) for l, h in links]
            md.append('')
        md.append('Year-by-year figures (eligible, placed, median and highest CTC) are to be added from the placement cell\'s records.')
        add('placements', 'replace_section', 'Year by year', '\n'.join(md))
        if rec:
            md = ['| Company | CTC (lakhs per annum) |'] + ['| %s | %s |' % (c, v) for c, v in rec]
            md += ['', 'Offers of 5 LPA and above to the 2025 B.Tech ECE batch, from the old website.']
            add('placements', 'replace_section', 'Recruiters this year', '\n'.join(md))
    return rows


# ---------- homepage: announcements and highlights ----------

def upload_date(url):
    """'.../uploads/2025/08/photo.jpg' -> '2025-08-01 10:00:00' (the month it was posted)."""
    m = re.search(r'/uploads/(20\d\d)/(\d\d)/', url or '')
    return '%s-%s-01 10:00:00' % (m.group(1), m.group(2)) if m else ''


def home_items(page):
    """Announcements (links in the Announcements box) and captioned photo highlights."""
    soup = BeautifulSoup(page['content']['rendered'], 'lxml')
    out = []
    for el in soup.find_all(string=re.compile(r'^\s*Announcements\s*$')):
        box = el.find_parent(class_='elementor-widget-container') or el.find_parent('div')
        for a in (box.find_all('a', href=True) if box else []):
            text = clean(a.get_text(' '))
            if len(text) > 15:
                out.append({'kind': 'announcement', 'title': text.rstrip(' .'), 'link': a['href'].strip(),
                            'image': '', 'date': upload_date(a['href'])})
    seen = set()
    for sl in soup.select('.swiper-slide'):
        cap = clean(sl.get_text(' '))
        if len(cap) < 25 or cap in seen:
            continue
        seen.add(cap)
        img = sl.find('img')
        src = (img.get('src') or img.get('data-src') or '') if img else ''
        if not src:
            bg = re.search(r'url\(([^)]+)\)', str(sl))
            src = bg.group(1).strip('\'"') if bg else ''
        src = original_image(src.replace('-scaled.', '.')) if src else ''
        out.append({'kind': 'highlight', 'title': cap, 'link': '', 'image': src, 'date': upload_date(src)})
    return out


def short_title(caption, limit=90):
    """First sentence of a caption, cut at a word boundary."""
    # Split at a sentence end, but not after "Dr.", "Mr.", "Prof." or an initial ("T.U.").
    parts = re.split(r'(?<!\bDr\.)(?<!\bMr\.)(?<!\bMs\.)(?<!\bProf\.)(?<!\b[A-Z]\.)(?<=[.!?])\s+', caption.strip())
    t = parts[0].strip(' .!🏸🏐')
    t = re.sub(r'\s*[.!]{2,}.*$', '', t)
    if len(t) > limit:
        t = t[:limit].rsplit(' ', 1)[0].rstrip(',;:–-') + '…'
    return t


# ---------- homepage activities and the Technical Talks page ----------

MONTHS = 'January|February|March|April|May|June|July|August|September|October|November|December'


def first_date(text, fallback=''):
    """'On August 6, 2026' / '22 October 2025' / '23 – 08 – 2023' / '01.02.2024' -> 'YYYY-MM-DD 10:00:00'."""
    names = MONTHS.split('|')
    m = re.search(r'\b(%s)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d\d)' % MONTHS, text)
    if m:
        return '%s-%02d-%02d 10:00:00' % (m.group(3), names.index(m.group(1)) + 1, int(m.group(2)))
    m = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(%s),?\s+(20\d\d)' % MONTHS, text)
    if m:
        return '%s-%02d-%02d 10:00:00' % (m.group(3), names.index(m.group(2)) + 1, int(m.group(1)))
    m = re.search(r'\b(\d{1,2})\s*[.–-]\s*(\d{1,2})\s*[.–-]\s*(20\d\d)\b', text)
    if m and 1 <= int(m.group(2)) <= 12:
        return '%s-%02d-%02d 10:00:00' % (m.group(3), int(m.group(2)), int(m.group(1)))
    return fallback


def clean_html(nodes, skip_first_heading=True):
    """Plain paragraphs, subheadings and lists from Elementor markup (no classes or styles)."""
    out, skipped = [], not skip_first_heading
    for el in nodes:
        if el.find_parent(['li', 'p']) is not None and el.name != 'li':
            continue
        if el.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            t = clean(el.get_text(' '))
            if not t:
                continue
            if not skipped:
                skipped = True
                continue
            out.append('<h3>%s</h3>' % html_escape(t))
        elif el.name == 'p':
            t = clean(el.get_text(' '))
            if t and not NOISE.match(t):
                out.append('<p>%s</p>' % html_escape(t))
        elif el.name in ('ul', 'ol') and el.find_parent(['ul', 'ol']) is None:
            items = [clean(li.get_text(' ')) for li in el.find_all('li', recursive=False)]
            items = [i for i in items if i]
            if items:
                out.append('<%s>%s</%s>' % (el.name, ''.join('<li>%s</li>' % html_escape(i) for i in items), el.name))
    return '\n'.join(out)


def html_escape(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def images_in(el):
    out = []
    for img in el.find_all('img'):
        src = img.get('data-src') or img.get('src') or ''
        src = original_image(src.replace('-scaled.', '.'))
        if '/wp-content/uploads/' in src and src not in out:
            out.append(src)
    return out


def home_activities(page):
    """The 'Activities associated with ECE department' write-ups on the old homepage."""
    soup = BeautifulSoup(page['content']['rendered'], 'lxml')
    start = soup.find(string=re.compile(r'ACTIVITIES ASSOCIATED', re.I))
    if not start:
        return []
    sec = start.find_parent('section')
    out = []
    for el in sec.find_next_siblings('section'):
        head = el.find(['h2', 'h3', 'h4', 'h5'])
        text = clean(el.get_text(' '))
        if re.search(r'University Rank Winners', text):
            break
        if len(text) < 200 or el.find(string=re.compile(r'Read More')):
            continue  # empty spacer, or teasers for posts that exist already
        title = clean(head.get_text(' ')) if head else ''
        imgs = images_in(el)
        nodes = el.find_all(['h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol'])
        out.append({'title': title, 'date': first_date(text, upload_date(imgs[0]) if imgs else ''),
                    'html': clean_html(nodes, skip_first_heading=bool(head)), 'images': imgs, 'text': text})
    return out


def rank_winners(page):
    """University rank winners written as text on the old homepage: {(programme, year): [(name, rank, cgpa)]}."""
    soup = BeautifulSoup(page['content']['rendered'], 'lxml')
    start = soup.find(string=re.compile(r'University Rank Winners'))
    if not start:
        return {}
    lines, _ = lines_of(str(start.find_parent('section')))
    out, prog, year = {}, '', ''
    i = 0
    while i < len(lines):
        t = lines[i]
        if re.match(r'B\.\s*Tech\.\s*\((EC|ECE)\)', t):
            prog = 'B.Tech ECE'
        elif re.match(r'B\.\s*Tech\.\s*\(AEI\)', t):
            prog = 'B.Tech AEI'
        elif re.fullmatch(r'20\d\d', t):
            year = t
        elif re.match(r'^(Ms|Mr)\.?\s*\S', t) and i + 1 < len(lines) and re.search(r'Rank', lines[i + 1]):
            name = clean(re.sub(r'^(Ms|Mr)\.?\s*', '', t))
            cg = re.search(r'([\d.]+)', lines[i + 2]) if i + 2 < len(lines) else None
            out.setdefault((prog, year), []).append((name, lines[i + 1], cg.group(1) if cg else ''))
            i += 2
        i += 1
    return out


def talks_page(page):
    """Talks written as text on the old Technical Talks page."""
    lines, soup = lines_of(page['content']['rendered'])
    imgs = images_in(soup)
    out, cur = [], None
    for i, t in enumerate(lines):
        if re.match(r'^(Dr|Ms|Mr|Prof)\.?\s+[A-Z]', t) and len(t) < 50:
            cur = {'speaker': t, 'lines': []}
            continue
        if cur is not None:
            cur['lines'].append(t)
            if re.search(r'\bon\s+\d{1,2}\.\d{1,2}\.20\d\d', t):
                out.append({'kind': 'alumni', 'speaker': cur['speaker'], 'about': cur['lines'][:-1],
                            'note': t, 'date': first_date(t), 'images': []})
                cur = None
    # The one talk written up in full: from "The talk was conducted on ..." to the end.
    k = next((i for i, t in enumerate(lines) if t.startswith('The talk was conducted on')), None)
    if k is not None:
        body = lines[k:]
        sp = re.search(r'resource person was (Mr|Ms|Dr)\.\s*([^(]+?)\s*\(([^)]+)\)', ' '.join(body))
        photos = [u for u in imgs if re.search(r'2023-08-23', u)]
        out.append({'kind': 'talk', 'speaker': ('%s. %s' % (sp.group(1), sp.group(2))) if sp else '', 'org': sp.group(3) if sp else '',
                    'paras': body, 'date': first_date(body[0]), 'images': photos})
    return out
