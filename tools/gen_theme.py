"""Generate block templates and page patterns for the CET ECE theme.

Block markup follows WordPress core's saved output so the editor accepts it
without "unexpected content" warnings. Run validate.mjs afterwards.
"""
import json
import os

import pathlib
THEME = str(pathlib.Path(__file__).resolve().parent.parent / 'cet-ece')


def a(attrs):
    return (' ' + json.dumps(attrs, separators=(',', ':'), ensure_ascii=False)) if attrs else ''


def css(style):
    out = []
    sp = style.get('spacing', {})
    for side in ('top', 'right', 'bottom', 'left'):
        if side in sp.get('margin', {}):
            out.append(f'margin-{side}:{sp["margin"][side]}')
    for side in ('top', 'right', 'bottom', 'left'):
        if side in sp.get('padding', {}):
            out.append(f'padding-{side}:{sp["padding"][side]}')
    ty = style.get('typography', {})
    if 'fontSize' in ty:
        out.append(f'font-size:{ty["fontSize"]}')
    if 'fontWeight' in ty:
        out.append(f'font-weight:{ty["fontWeight"]}')
    if 'letterSpacing' in ty:
        out.append(f'letter-spacing:{ty["letterSpacing"]}')
    if 'lineHeight' in ty:
        out.append(f'line-height:{ty["lineHeight"]}')
    if 'textTransform' in ty:
        out.append(f'text-transform:{ty["textTransform"]}')
    return ';'.join(out)


def classes(base, attrs, color_order=True):
    c = [base] if base else []
    if attrs.get('align'):
        c.append('align' + attrs['align'])
    if attrs.get('className'):
        c.append(attrs['className'])
    if attrs.get('textColor'):
        c.append(f'has-{attrs["textColor"]}-color')
    if attrs.get('backgroundColor'):
        c.append(f'has-{attrs["backgroundColor"]}-background-color')
    if attrs.get('textColor'):
        c.append('has-text-color')
    if attrs.get('backgroundColor'):
        c.append('has-background')
    if attrs.get('fontSize'):
        c.append(f'has-{attrs["fontSize"]}-font-size')
    return ' '.join(c)


def attr_html(cls, attrs):
    out = ''
    if cls:
        out += f' class="{cls}"'
    st = css(attrs.get('style', {}))
    if st:
        out += f' style="{st}"'
    return out


def p(text, **attrs):
    return f'<!-- wp:paragraph{a(attrs)} -->\n<p{attr_html(classes("", attrs), attrs)}>{text}</p>\n<!-- /wp:paragraph -->'


def h(level, text, **attrs):
    if level != 2:
        attrs = {'level': level, **attrs}
    anchor = attrs.get('anchor')
    idattr = f' id="{anchor}"' if anchor else ''
    cls = classes('wp-block-heading', attrs)
    st = css(attrs.get('style', {}))
    sta = f' style="{st}"' if st else ''
    return f'<!-- wp:heading{a(attrs)} -->\n<h{level}{idattr} class="{cls}"{sta}>{text}</h{level}>\n<!-- /wp:heading -->'


def group(inner, tag='div', **attrs):
    if tag != 'div':
        attrs = {'tagName': tag, **attrs}
    attrs.setdefault('layout', {'type': 'constrained'})
    body = '\n\n'.join(inner) if isinstance(inner, list) else inner
    return f'<!-- wp:group{a(attrs)} -->\n<{tag}{attr_html(classes("wp-block-group", attrs), attrs)}>{body}</{tag}>\n<!-- /wp:group -->'


def buttons(items, **attrs):
    bs = []
    for text, href, outline in items:
        battrs = {'className': 'is-style-outline'} if outline else {}
        cls = 'wp-block-button' + (' is-style-outline' if outline else '')
        bs.append(f'<!-- wp:button{a(battrs)} -->\n<div class="{cls}"><a class="wp-block-button__link wp-element-button" href="{href}">{text}</a></div>\n<!-- /wp:button -->')
    return f'<!-- wp:buttons{a(attrs)} -->\n<div{attr_html(classes("wp-block-buttons", attrs), attrs)}>' + '\n\n'.join(bs) + '</div>\n<!-- /wp:buttons -->'


def ul(items, ordered=False, **attrs):
    if ordered:
        attrs = {'ordered': True, **attrs}
    tag = 'ol' if ordered else 'ul'
    lis = '\n\n'.join(f'<!-- wp:list-item -->\n<li>{i}</li>\n<!-- /wp:list-item -->' for i in items)
    return f'<!-- wp:list{a(attrs)} -->\n<{tag}{attr_html(classes("wp-block-list", attrs), attrs)}>{lis}</{tag}>\n<!-- /wp:list -->'


def table(head, rows, **attrs):
    attrs = {'hasFixedLayout': False, **attrs}
    th = ''.join(f'<th>{x}</th>' for x in head)
    body = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'<!-- wp:table{a(attrs)} -->\n<figure{attr_html(classes("wp-block-table", attrs), attrs)}><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></figure>\n<!-- /wp:table -->'


def columns(cols, **attrs):
    inner = []
    for width, content in cols:
        cattrs = {'width': width} if width else {}
        st = f' style="flex-basis:{width}"' if width else ''
        body = '\n\n'.join(content) if isinstance(content, list) else content
        inner.append(f'<!-- wp:column{a(cattrs)} -->\n<div class="wp-block-column"{st}>{body}</div>\n<!-- /wp:column -->')
    return f'<!-- wp:columns{a(attrs)} -->\n<div{attr_html(classes("wp-block-columns", attrs), attrs)}>' + '\n\n'.join(inner) + '</div>\n<!-- /wp:columns -->'


def dyn(name, **attrs):
    return f'<!-- wp:{name}{a(attrs)} /-->'


def sep():
    return '<!-- wp:separator -->\n<hr class="wp-block-separator has-alpha-channel-opacity"/>\n<!-- /wp:separator -->'


# ---------- reusable pieces ----------

def card(title, text, href, eyebrow=''):
    inner = []
    if eyebrow:
        inner.append(p(eyebrow, className='ece-eyebrow'))
    inner.append(h(3, f'<a href="{href}">{title}</a>', style={'typography': {'fontSize': '17px'}}))
    inner.append(p(text, textColor='muted', fontSize='small'))
    return group(inner, className='ece-card-surface', style={'spacing': {'padding': {'top': '20px', 'right': '20px', 'bottom': '20px', 'left': '20px'}, 'blockGap': '6px'}}, layout={'type': 'flex', 'orientation': 'vertical'})


def grid(items, min_w='240px', cols=None, **attrs):
    lay = {'type': 'grid', 'minimumColumnWidth': min_w}
    if cols:
        lay['columnCount'] = cols
    return group(items, layout=lay, style={'spacing': {'blockGap': '16px'}}, **attrs)


def stat(num, label):
    return group([p(num, className='ece-stat-number'), p(label, className='ece-stat-label')], style={'spacing': {'blockGap': '4px'}}, layout={'type': 'flex', 'orientation': 'vertical'})


def section(title, inner, anchor=None, align='wide'):
    hattrs = {'anchor': anchor} if anchor else {}
    return group([h(2, title, **hattrs)] + (inner if isinstance(inner, list) else [inner]), align=align, style={'spacing': {'blockGap': '16px', 'margin': {'top': '48px'}}}, layout={'type': 'default'})


def band(inner, size='1200px'):
    return group(inner, align='full', className='ece-band', backgroundColor='tint', style={'spacing': {'margin': {'top': '0', 'bottom': '0'}, 'padding': {'top': '36px', 'bottom': '40px'}}}, layout={'type': 'constrained', 'contentSize': size})


def fact(k, v):
    return group([p(k, textColor='muted', fontSize='small', style={'typography': {'fontWeight': '600'}}), p(v, style={'typography': {'fontSize': '17px', 'fontWeight': '600'}})], className='ece-card', style={'spacing': {'padding': {'top': '14px', 'right': '18px', 'bottom': '14px', 'left': '18px'}, 'blockGap': '2px'}}, layout={'type': 'flex', 'orientation': 'vertical'})


def pattern(slug, title, desc, content, cats='cet-ece-pages', post_types='page'):
    head = f"""<?php
/**
 * Title: {title}
 * Slug: cet-ece/{slug}
 * Categories: {cats}
 * Description: {desc}
 * Post Types: {post_types}
 * Inserter: true
 */
?>
"""
    with open(os.path.join(THEME, 'patterns', slug + '.php'), 'w') as f:
        f.write(head + content + '\n')


def template(name, content, folder='templates'):
    with open(os.path.join(THEME, folder, name + '.html'), 'w') as f:
        f.write(content + '\n')


HEADER = dyn('template-part', slug='header', tagName='div')
FOOTER = dyn('template-part', slug='footer', tagName='div')
MAIN_STYLE = {'spacing': {'margin': {'top': '0'}, 'padding': {'top': '40px', 'bottom': '72px'}}}


def main(inner, size='1200px', style=None):
    return group(inner, tag='main', style=style or MAIN_STYLE, layout={'type': 'constrained', 'contentSize': size})


# ---------- templates ----------

PAGE_BAND = band([
    dyn('post-title', level=1),
    dyn('post-excerpt', className='ece-lead', fontSize='large'),
], size='760px')

template('page', '\n\n'.join([
    HEADER,
    PAGE_BAND,
    main([dyn('post-content', layout={'type': 'constrained'}), dyn('cet-ece/last-updated')], size='760px'),
    FOOTER,
]))

template('page-no-title', '\n\n'.join([
    HEADER,
    group([dyn('post-content', align='full', layout={'type': 'constrained'})], tag='main', style={'spacing': {'margin': {'top': '0'}, 'padding': {'top': '0', 'bottom': '0'}}}, layout={'type': 'default'}),
    FOOTER,
]))

template('front-page', '\n\n'.join([
    HEADER,
    group([dyn('post-content', align='full', layout={'type': 'constrained'})], tag='main', style={'spacing': {'margin': {'top': '0'}, 'padding': {'top': '0', 'bottom': '0'}}}, layout={'type': 'default'}),
    FOOTER,
]))

NEWS_ROW = group([
    dyn('post-featured-image', isLink=True, aspectRatio='3/2', width='220px', style={'border': {'radius': '10px'}}),
    group([
        group([dyn('post-terms', term='category', separator=' · ', className='ece-eyebrow'), dyn('post-date', format='j M Y')], style={'spacing': {'blockGap': '12px'}}, layout={'type': 'flex', 'flexWrap': 'wrap'}),
        dyn('post-title', isLink=True, level=2, style={'typography': {'fontSize': '20px'}}),
        dyn('post-excerpt', excerptLength=30, textColor='body'),
    ], style={'spacing': {'blockGap': '8px'}}, layout={'type': 'flex', 'orientation': 'vertical'}),
], className='ece-news', style={'spacing': {'padding': {'top': '20px', 'bottom': '20px'}, 'blockGap': '20px'}}, layout={'type': 'flex', 'flexWrap': 'wrap', 'verticalAlignment': 'top'})


def query_list(no_results='No posts yet.'):
    return f'''<!-- wp:query {{"queryId":0,"query":{{"perPage":10,"pages":0,"offset":0,"postType":"post","order":"desc","orderBy":"date","author":"","search":"","exclude":[],"sticky":"","inherit":true}},"align":"wide"}} -->
<div class="wp-block-query alignwide"><!-- wp:post-template -->
{NEWS_ROW}

{sep()}
<!-- /wp:post-template -->

<!-- wp:query-pagination {{"layout":{{"type":"flex","justifyContent":"center"}}}} -->
<!-- wp:query-pagination-previous /-->

<!-- wp:query-pagination-numbers /-->

<!-- wp:query-pagination-next /-->
<!-- /wp:query-pagination -->

<!-- wp:query-no-results -->
{p(no_results)}
<!-- /wp:query-no-results --></div>
<!-- /wp:query -->'''


template('home', '\n\n'.join([
    HEADER,
    band([h(1, 'News and Events'), p('Workshops, talks, outreach and department news, newest first.', className='ece-lead', fontSize='large'),
          dyn('categories', displayAsDropdown=True, showHierarchy=False, showPostCounts=False, label='Category', showLabel=True)]),
    main([query_list()]),
    FOOTER,
]))

template('archive', '\n\n'.join([
    HEADER,
    band([dyn('query-title', type='archive', showPrefix=False), dyn('term-description', className='ece-lead')]),
    main([query_list()]),
    FOOTER,
]))

template('index', '\n\n'.join([
    HEADER,
    band([dyn('query-title', type='archive', showPrefix=False)]),
    main([query_list()]),
    FOOTER,
]))

template('search', '\n\n'.join([
    HEADER,
    band([dyn('query-title', type='search'), dyn('search', label='Search', showLabel=False, buttonText='Search', placeholder='Search the site')]),
    main([query_list('Nothing matched your search. Try fewer or different words.')]),
    FOOTER,
]))

template('404', '\n\n'.join([
    HEADER,
    band([h(1, 'Page not found'), p('The page may have moved when the site was redesigned. Try a search, or start from the menu.', className='ece-lead', fontSize='large'),
          dyn('search', label='Search', showLabel=False, buttonText='Search', placeholder='Search the site')]),
    main([group([h(2, 'Popular pages'), ul(['<a href="/academics/">Academics</a>', '<a href="/faculty/">Faculty</a>', '<a href="/labs/">Laboratories</a>', '<a href="/students/">Students</a>', '<a href="/contact/">Contact</a>'])], layout={'type': 'default'})], size='760px'),
    FOOTER,
]))

template('single', '\n\n'.join([
    HEADER,
    main([
        group([dyn('post-terms', term='category', separator=' · ', className='ece-eyebrow'), dyn('post-date', format='j M Y')], style={'spacing': {'blockGap': '12px'}}, layout={'type': 'flex', 'flexWrap': 'wrap'}),
        dyn('post-title', level=1),
        dyn('post-excerpt', className='ece-lead', fontSize='large'),
        dyn('post-featured-image', aspectRatio='16/9', style={'border': {'radius': '14px'}}),
        dyn('post-content', layout={'type': 'constrained'}),
        sep(),
        group([p('<a href="/news/">All news and events</a>'), dyn('cet-ece/last-updated')], layout={'type': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-between'}),
    ], size='760px'),
    FOOTER,
]))

template('single-faculty', '\n\n'.join([
    HEADER,
    main([dyn('cet-ece/faculty-details', align='wide')], style={'spacing': {'margin': {'top': '0'}, 'padding': {'top': '28px', 'bottom': '72px'}}}),
    FOOTER,
]))

template('archive-faculty', '\n\n'.join([
    HEADER,
    band([h(1, 'Faculty'), p('Faculty members across communication, signal processing, electronics, instrumentation and allied areas. Select a name for qualifications, research areas and publications.', className='ece-lead', fontSize='large')]),
    main([dyn('cet-ece/faculty-directory', align='wide')]),
    FOOTER,
]))

template('single-lab', '\n\n'.join([
    HEADER,
    group([dyn('cet-ece/lab-details', align='full')], tag='main', style={'spacing': {'margin': {'top': '0'}}}, layout={'type': 'default'}),
    FOOTER,
]))

template('archive-lab', '\n\n'.join([
    HEADER,
    band([h(1, 'Laboratories'), p('Teaching labs for the B.Tech and M.Tech programmes, and research labs for Ph.D. and M.Tech work.', className='ece-lead', fontSize='large')]),
    main([dyn('cet-ece/lab-list', showFilters=True, align='wide')]),
    FOOTER,
]))

template('taxonomy-research_area', '\n\n'.join([
    HEADER,
    band([p('Research area', className='ece-eyebrow'), dyn('query-title', type='archive', showPrefix=False, level=1), dyn('term-description', className='ece-lead')]),
    main([
        section('Faculty', [dyn('cet-ece/faculty-directory', showFilters=False)]),
        section('Labs', [dyn('cet-ece/lab-list')]),
        section('Publications', [dyn('cet-ece/publications', showFilters=False)]),
    ]),
    FOOTER,
]))

# ---------- page patterns ----------

hero = f'''<!-- wp:cover {{"dimRatio":100,"overlayColor":"hero","isUserOverlayColor":true,"minHeight":460,"minHeightUnit":"px","align":"full","className":"ece-hero","style":{{"spacing":{{"padding":{{"top":"96px","bottom":"88px"}},"margin":{{"top":"0","bottom":"0"}}}}}},"layout":{{"type":"constrained","contentSize":"1200px"}}}} -->
<div class="wp-block-cover alignfull ece-hero" style="margin-top:0;margin-bottom:0;padding-top:96px;padding-bottom:88px;min-height:460px"><span aria-hidden="true" class="wp-block-cover__background has-hero-background-color has-background-dim-100 has-background-dim"></span><div class="wp-block-cover__inner-container">{p("Since 1964 · Sreekariyam, Thiruvananthapuram", className="ece-eyebrow")}

{h(1, "Electronics and Communication Engineering at CET", fontSize="xx-large", style={"typography": {"lineHeight": "1.06"}})}

{p("Two B.Tech programmes, five M.Tech specialisations and a doctoral programme. AICTE approved, with QIP centre status.", fontSize="large")}

{buttons([("Explore programmes", "/academics/", False), ("Research at ECE", "/research/", True)])}</div></div>
<!-- /wp:cover -->'''

HOME = '\n\n'.join([
    hero,
    group([grid([stat('1964', 'Established, with a first intake of 33 students'), stat('180', 'B.Tech seats a year, plus lateral entry'), stat('5', 'M.Tech specialisations, 18 seats each'), stat('41', 'Faculty members')], '170px', cols=4, align='wide')],
          align='full', style={'spacing': {'padding': {'top': '40px', 'bottom': '40px'}, 'margin': {'top': '0', 'bottom': '0'}}}, layout={'type': 'constrained', 'contentSize': '1200px'}),
    group([
        section('Find what you need', [grid([
            card('Prospective students', 'Programmes, intake, admissions', '/academics/'),
            card('Current students', 'Calendar, syllabus, notices, advisors', '/students/'),
            card('Researchers', 'Labs, projects, publications, Ph.D.', '/research/'),
            card('Recruiters', 'Placement statistics and contacts', '/placements/'),
            card('Alumni', 'Stay in touch, give a talk, mentor', '/alumni/'),
        ], '200px')]),
        group([columns([
            ('66.66%', [h(2, 'Latest news'), dyn('cet-ece/news', limit=3, exclude='announcements,student-achievements,placements'), p('<a href="/news/">All news and events</a>', style={'typography': {'fontWeight': '600'}})]),
            ('33.33%', [h(2, 'Announcements'), dyn('cet-ece/news', limit=4, category='announcements', style='list'), p('<a href="/category/announcements/">All announcements</a>', style={'typography': {'fontWeight': '600'}})]),
        ], style={'spacing': {'blockGap': {'left': '48px'}}})], align='wide', style={'spacing': {'margin': {'top': '56px'}}}, layout={'type': 'default'}),
        section('Achievements and placements', [dyn('cet-ece/news', limit=4, category='student-achievements,placements', style='posters'), p('<a href="/category/student-achievements/">All achievements</a> · <a href="/category/placements/">All placement news</a>', style={'typography': {'fontWeight': '600'}})]),
    ], align='full', style={'spacing': {'padding': {'top': '24px', 'bottom': '72px'}, 'margin': {'top': '0', 'bottom': '0'}}}, layout={'type': 'constrained', 'contentSize': '1200px'}),
    group([group([h(2, 'Research areas'), dyn('cet-ece/research-areas'), p('<a href="/research/">Labs, projects and publications</a>', style={'typography': {'fontWeight': '600'}})], align='wide', style={'spacing': {'blockGap': '20px'}}, layout={'type': 'default'})],
          align='full', backgroundColor='tint', style={'spacing': {'padding': {'top': '64px', 'bottom': '64px'}, 'margin': {'top': '0', 'bottom': '0'}}}, layout={'type': 'constrained', 'contentSize': '1200px'}),
])
pattern('page-home', 'Homepage', 'Hero, key figures, visitor paths, news, announcements and research areas.', HOME)

ABOUT = '\n\n'.join([
    h(2, 'Vision'),
    p('To transform young students into responsible and competent professionals.', fontSize='large', style={'typography': {'fontWeight': '500'}}),
    h(2, 'Mission'),
    ul(['[Mission point 1]', '[Mission point 2]', '[Mission point 3]', '[Mission point 4]'], ordered=True),
    h(2, 'Accreditation'),
    table(['Programme', 'Body', 'Status', 'Valid until'], [['B.Tech ECE', 'NBA', '[Confirm current status]', '[Date]'], ['B.Tech AEI', 'NBA', '[Confirm current status]', '[Date]'], ['M.Tech Signal Processing', 'NBA', 'Accredited', '30 June 2027'], ['[Other M.Tech]', 'NBA', '[Status]', '[Date]']]),
    p('Current status only. Link each programme name to its certificate (PDF).', textColor='muted', fontSize='small'),
    h(2, 'Milestones'),
    table(['Year', 'Milestone'], [['1964–65', 'Department established with an intake of 33 students'], ['2015', 'Golden Jubilee year opens, 9 September 2015'], ['[Year]', 'Golden Jubilee PG and Research Block inaugurated'], ['2025', 'Patent granted, December 2025: [title]']]),
    h(2, 'Head of Department'),
    p('[Name]<br><a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a> · 0471-2515563'),
])
pattern('page-about', 'About and accreditation', 'Vision, mission, accreditation status, milestones and head of department.', ABOUT)

ACAD = '\n\n'.join([
    section('B.Tech programmes', [grid([card('Electronics and Communication Engineering', 'Intake 120 + 12 · 4 years', '/academics/btech-ece/', 'B.Tech'), card('Applied Electronics and Instrumentation', 'Intake 60 + 6 · 4 years', '/academics/btech-aei/', 'B.Tech')], '300px')]),
    section('M.Tech specialisations', [grid([
        card('Applied Electronics and Instrumentation', 'Intake 18 · 2 years', '/academics/mtech-applied-electronics/', 'M.Tech'),
        card('Communication Systems', 'Intake 18 · 2 years · formerly Microwave and Television Engineering', '/academics/mtech-communication-systems/', 'M.Tech'),
        card('Signal Processing', 'Intake 18 · 2 years', '/academics/mtech-signal-processing/', 'M.Tech'),
        card('Micro and Nano Electronics', 'Intake 18 · 2 years', '/academics/mtech-micro-nano-electronics/', 'M.Tech'),
        card('Robotics and Automation', 'Intake 18 · 2 years · interdisciplinary', '/academics/mtech-robotics-automation/', 'M.Tech'),
    ], '260px')]),
    section('Doctoral programme', [grid([card('Ph.D. in Electronics and Communication Engineering', 'Full-time and part-time · QIP centre', '/academics/phd/', 'Ph.D.')], '300px')]),
    section('For all programmes', [grid([card('Outcome-based education', 'Vision, mission, POs and attainment reports', '/academics/obe/'), card('Staff advisors', 'Current batches and contacts', '/staff-advisors/'), card('Laboratories', 'Teaching and research labs', '/labs/'), card('Students', 'Calendar, syllabus, notices', '/students/')], '220px')]),
])
pattern('page-academics', 'Academics overview', 'All programmes with intake and links.', ACAD)

PROG = '\n\n'.join([
    grid([fact('Intake', '[Intake]'), fact('Duration', '[Duration]'), fact('Accreditation', '[NBA status, valid to date]'), fact('Programme coordinator', '[Faculty name]')], '170px', cols=4, align='wide'),
    p('On this page: <a href="#overview">Overview</a> · <a href="#curriculum">Curriculum</a> · <a href="#outcomes">Outcomes</a> · <a href="#labs">Labs</a> · <a href="#contacts">Contacts</a>', fontSize='small'),
    h(2, 'Overview', anchor='overview'),
    p('[One paragraph: what the programme covers, electives, project work and internships, and what graduates go on to do.]'),
    h(2, 'Curriculum', anchor='curriculum'),
    table(['Scheme', 'Applies to', 'Documents', 'Status'], [['[2024] scheme', 'Admitted [2024] onwards', '<a href="#">Scheme and syllabus (PDF)</a>', 'Current'], ['[2019] scheme', 'Admitted [2019–2023]', '<a href="#">Scheme and syllabus (PDF)</a>', 'Current for older batches'], ['[2015] scheme', 'Admitted [2015–2018]', '<a href="#">Archive (PDF)</a>', 'Archived']]),
    p('Regulations and the academic calendar come from APJ Abdul Kalam Technological University: <a href="https://ktu.edu.in/">ktu.edu.in</a>.', textColor='muted', fontSize='small'),
    h(2, 'Outcomes', anchor='outcomes'),
    h(3, 'Programme educational objectives (PEOs)'),
    ul(['<strong>PEO1:</strong> [Statement]', '<strong>PEO2:</strong> [Statement]', '<strong>PEO3:</strong> [Statement]']),
    h(3, 'Programme specific outcomes (PSOs)'),
    ul(['<strong>PSO1:</strong> [Statement]', '<strong>PSO2:</strong> [Statement]']),
    p('Programme outcomes (POs) are common to all programmes and listed on the <a href="/academics/obe/">outcome-based education</a> page, with attainment reports.'),
    h(2, 'Labs used in this programme', anchor='labs'),
    dyn('cet-ece/lab-list', type='teaching', programme=''),
    h(2, 'Contacts', anchor='contacts'),
    ul(['Programme coordinator: [Faculty name], [name]@cet.ac.in', 'Staff advisors: <a href="/staff-advisors/">current batches</a>', 'Admissions: [KEAM / GATE / university process], see <a href="/contact/">contact</a>']),
])
pattern('page-programme', 'Programme page', 'Facts, curriculum by scheme, PEOs and PSOs, labs and contacts for one programme.', PROG)

PHD = '\n\n'.join([
    p('Full-time and part-time Ph.D. under APJ Abdul Kalam Technological University. The department is a QIP centre with approved research guides across its research areas.'),
    h(2, 'Fellowship schemes'),
    table(['Scheme', 'What it is'], [['QIP', 'Quality Improvement Programme, for faculty from other institutions'], ['NET-JRF', 'UGC Junior Research Fellowship holders'], ['KSCSTE', 'Kerala State Council for Science, Technology and Environment fellowship'], ['NDF / ADF', '[Expand the scheme name]'], ['CERD', '[Expand: Centre for Engineering Research and Development fellowship]']]),
    h(2, 'Eligibility and admission'),
    ul(['[Eligibility]', '[Admission calendar and how to apply]', '[Course work requirements]']),
    h(2, 'Guides and research areas'),
    p('See <a href="/research/">Research</a> for research areas and labs, and the <a href="/faculty/">faculty directory</a> for guides.'),
    h(2, 'Contact'),
    p('Research coordinator: [Faculty name], [name]@cet.ac.in'),
])
pattern('page-phd', 'Ph.D. programme', 'Schemes, eligibility, admission and contacts for the doctoral programme.', PHD)

OBE = '\n\n'.join([
    h(2, 'Department vision'),
    p('To transform young students into responsible and competent professionals.', fontSize='large', style={'typography': {'fontWeight': '500'}}),
    h(2, 'Department mission'),
    ul(['[Mission point 1]', '[Mission point 2]', '[Mission point 3]', '[Mission point 4]'], ordered=True),
    h(2, 'Programme outcomes (POs)'),
    p('The NBA graduate attributes, common to all B.Tech programmes.', textColor='muted', fontSize='small'),
    table(['PO', 'Statement'], [['PO1', '[NBA statement]'], ['PO2', '[NBA statement]'], ['PO3', '[NBA statement]'], ['…', '[Add every PO in the current NBA list]']]),
    h(2, 'PEOs and PSOs by programme'),
    ul(['<a href="/academics/btech-ece/#outcomes">B.Tech Electronics and Communication Engineering</a>', '<a href="/academics/btech-aei/#outcomes">B.Tech Applied Electronics and Instrumentation</a>', '<a href="/academics/mtech-applied-electronics/#outcomes">M.Tech Applied Electronics and Instrumentation</a>', '<a href="/academics/mtech-communication-systems/#outcomes">M.Tech Communication Systems</a>', '<a href="/academics/mtech-signal-processing/#outcomes">M.Tech Signal Processing</a>', '<a href="/academics/mtech-micro-nano-electronics/#outcomes">M.Tech Micro and Nano Electronics</a>', '<a href="/academics/mtech-robotics-automation/#outcomes">M.Tech Robotics and Automation</a>']),
    h(2, 'Programme assessment committees'),
    table(['Programme', 'Coordinator', 'Members'], [['B.Tech ECE', '[Faculty name]', '[Faculty names]'], ['B.Tech AEI', '[Faculty name]', '[Faculty names]']]),
    h(2, 'Attainment reports'),
    table(['Academic year', 'Report', 'Published'], [['2025–26', '<a href="#">CO–PO attainment (PDF)</a>', '[Date]'], ['2024–25', '<a href="#">CO–PO attainment (PDF)</a>', '[Date]']]),
    p('Last reviewed: [month year], by the Department Advisory Board.', textColor='muted', fontSize='small'),
])
pattern('page-obe', 'Outcome-based education', 'Vision, mission, POs, links to PEOs and PSOs, committees and attainment reports.', OBE)

pattern('page-staff-advisors', 'Staff advisors', 'Current batches and their advisors, with past batches below.', '\n\n'.join([
    p('Every batch has a named faculty advisor for academic and personal guidance. Batches move to the past list automatically after they graduate.'),
    dyn('cet-ece/staff-advisors', type='current', align='wide'),
    h(2, 'Past batches'),
    dyn('cet-ece/staff-advisors', type='past', align='wide'),
]))

pattern('page-technical-staff', 'Technical staff', 'Technical staff by designation, with assigned labs.', '\n\n'.join([
    p('The technical staff run the department’s laboratories. Each is listed with the lab they support.'),
    dyn('cet-ece/tech-staff', align='wide'),
]))

RES = '\n\n'.join([
    grid([stat('[n]', 'Approved research guides'), stat('[n]', 'Ph.D. scholars'), stat('[n]', 'Funded projects, ongoing'), stat('[n]', 'Publications last year')], '170px', cols=4, align='wide'),
    section('Research areas', [dyn('cet-ece/research-areas'), p('Each area lists its faculty, labs and publications.', textColor='muted', fontSize='small')]),
    section('Research labs', [dyn('cet-ece/lab-list', type='research')]),
    section('Funded projects', [dyn('cet-ece/projects')]),
    section('Industry collaborations and MoUs', [table(['Partner', 'Type', 'Since', 'Activities'], [['[Organisation]', 'MoU', '[Year]', '[Internships, projects, training]'], ['[Organisation]', 'Consultancy', '[Year]', '[Work done]']]), p('List current agreements only. Link each partner to the signed MoU (PDF) if it can be public.', textColor='muted', fontSize='small')]),
    section('Ph.D. programme', [p('Full-time and part-time Ph.D. under APJ Abdul Kalam Technological University. The department is a QIP centre. <a href="/academics/phd/">Schemes, eligibility and admission</a>.')]),
    section('Latest publications', [dyn('cet-ece/publications', showFilters=False, limit=5), p('<a href="/research/publications/">All publications</a>', style={'typography': {'fontWeight': '600'}})]),
])
pattern('page-research', 'Research hub', 'Figures, research areas, labs, funded projects, Ph.D. and latest publications.', RES)

pattern('page-publications', 'Publications', 'Filterable list of publications in IEEE style.', dyn('cet-ece/publications', align='wide'))

LIB = '\n\n'.join([
    p('The department library supports the B.Tech, M.Tech and Ph.D. programmes.'),
    h(2, 'Holdings'),
    table(['Collection', 'Count', 'As of'], [['Lending', '[n]', '[Date]'], ['Reference', '[n]', '[Date]'], ['Journals', '[n]', '[Date]']]),
    h(2, 'Opening hours'),
    p('[Days and times]'),
    h(2, 'E-resources'),
    p('[Current subscriptions, how to access them, and the access period]'),
    h(2, 'Lending rules'),
    ul(['[Loan period]', '[Number of books]', '[Fines]']),
    h(2, 'Contact'),
    p('[Librarian or faculty in charge], [email]'),
])
pattern('page-library', 'Library', 'Holdings, hours, e-resources, rules and contact.', LIB)

PLC = '\n\n'.join([
    h(2, '[Year] batch at a glance'),
    grid([stat('[n]', 'Students placed'), stat('[n]%', 'Of eligible students'), stat('[x] LPA', 'Median package'), stat('[n]', 'Recruiting companies')], '170px', cols=4, align='wide'),
    h(2, 'Recent placements'),
    dyn('cet-ece/news', limit=8, category='placements', style='posters', align='wide'),
    p('<a href="/category/placements/">All placement news</a>', style={'typography': {'fontWeight': '600'}}),
    h(2, 'Year by year'),
    table(['Batch', 'Programme', 'Eligible', 'Placed', 'Median CTC (LPA)', 'Highest CTC (LPA)'], [['[2025]', 'B.Tech ECE', '[n]', '[n]', '[x]', '[x]'], ['[2025]', 'B.Tech AEI', '[n]', '[n]', '[x]', '[x]'], ['[2024]', 'B.Tech ECE', '[n]', '[n]', '[x]', '[x]'], ['[2024]', 'B.Tech AEI', '[n]', '[n]', '[x]', '[x]']]),
    p('All packages in lakhs per annum (LPA). Link each batch to its detailed list (PDF).', textColor='muted', fontSize='small'),
    h(2, 'Recruiters this year'),
    p('[Company names, current year only. Add logos with the Gallery block if wanted.]'),
    h(2, 'Student stories'),
    p('[Two or three short quotes from placed students, with name, batch and company.]'),
    h(2, 'Recruit from ECE'),
    p('Placement coordinator: [Faculty name], [name]@cet.ac.in'),
])
pattern('page-placements', 'Placements', 'Headline figures, year-by-year table, recruiters and contact.', PLC)

STU = '\n\n'.join([
    h(2, 'Notices'),
    dyn('cet-ece/news', limit=6, category='announcements', style='list'),
    p('<a href="/category/announcements/">All notices</a>', style={'typography': {'fontWeight': '600'}}),
    h(2, 'Recent achievements'),
    dyn('cet-ece/news', limit=4, category='student-achievements', style='posters', align='wide'),
    p('<a href="/category/student-achievements/">All achievements</a>', style={'typography': {'fontWeight': '600'}}),
    section('Quick links', [grid([card('Academic calendar', 'Current semester, from KTU', 'https://ktu.edu.in/'), card('Scheme and syllabus', 'By programme and admission year', '/academics/'), card('Staff advisors', 'Your batch advisor', '/staff-advisors/'), card('Labs and manuals', 'Lab pages carry the manuals', '/labs/'), card('Downloads', 'Forms, calendars, syllabus', '/downloads/'), card('Exam results', 'KTU results portal', 'https://ktu.edu.in/')], '200px')], align=None),
    h(2, 'University rank holders'),
    table(['Year', 'B.Tech ECE', 'B.Tech AEI'], [['[2025]', '[Name, rank]', '[Name, rank]'], ['[2024]', '[Name, rank]', '[Name, rank]']]),
    h(2, 'Student associations'),
    p('[Department association, IEEE student branch and other chapters]'),
    h(2, 'Need help?'),
    p('Talk to your staff advisor first. For anything else, write to <a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a>.'),
])
pattern('page-students', 'Students', 'Notices, quick links, rank holders and help.', STU)

CON = '\n\n'.join([
    h(2, 'Address'),
    p('Head of Department<br>Department of Electronics and Communication Engineering<br>College of Engineering Trivandrum<br>Sreekariyam, Thiruvananthapuram, Kerala [PIN]'),
    p('<a href="tel:04712515563">0471-2515563</a> · <a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a> · Office hours: [Mon–Fri, 9:00–17:00]'),
    p('<a href="https://maps.google.com/?q=College+of+Engineering+Trivandrum">Open in Google Maps</a>'),
    h(2, 'Who to contact'),
    table(['For', 'Contact', 'Email'], [['Admissions and general queries', 'Department office', '<a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a>'], ['Placements and internships', '[Placement coordinator]', '[name]@cet.ac.in'], ['Ph.D. admissions', '[Research coordinator]', '[name]@cet.ac.in'], ['Website corrections', '[Web coordinator]', '[name]@cet.ac.in']]),
    h(2, 'How to reach'),
    table(['By', 'Directions'], [['Air', '[Trivandrum International Airport: distance and route]'], ['Train', '[Nearest station: distance and route]'], ['Bus', '[Buses to Sreekariyam, nearest stop]']]),
])
pattern('page-contact', 'Contact and directions', 'Address, contacts by purpose and directions.', CON)

ALUMNI = '\n\n'.join([
    p('Graduates of the department work across industry, research and academia in India and abroad. This page is how alumni stay connected with current students and faculty.'),
    h(2, 'Stay in touch'),
    p('Send your name, batch, programme and current role to [alumni coordinator email], or fill in the <a href="#">alumni form</a> [link to a Google Form].'),
    h(2, 'Ways to give back'),
    ul(['Give a talk in the Technical Talk Series (alumni talks appear under <a href="/category/talks/">Talks</a>)', 'Mentor final-year students on projects and careers', 'Offer internships or refer recruiters to the <a href="/placements/">placement cell</a>', 'Support a lab, award or scholarship']),
    h(2, 'Recent alumni talks'),
    dyn('cet-ece/news', limit=3, category='talks', style='list'),
    h(2, 'Notable alumni'),
    table(['Name', 'Batch', 'Role'], [['[Name]', '[Programme, year]', '[Role, organisation]'], ['[Name]', '[Programme, year]', '[Role, organisation]']]),
    p('Listed with their consent.', textColor='muted', fontSize='small'),
    h(2, 'Batch coordinators'),
    table(['Batch', 'Coordinator', 'Contact'], [['[Year]', '[Name]', '[Email]']]),
])
pattern('page-alumni', 'Alumni', 'Stay in touch, ways to give back, alumni talks and notable alumni.', ALUMNI)

DOWN = '\n\n'.join([
    p('Forms, calendars and documents in one place. Each link opens a PDF. Replace a file when a new version comes out; do not add a second copy.'),
    h(2, 'Academic'),
    table(['Document', 'Applies to', 'Updated'], [['<a href="#">Academic calendar [semester]</a>', 'All programmes', '[Date]'], ['<a href="#">B.Tech scheme and syllabus, [2024]</a>', 'B.Tech admitted [2024] onwards', '[Date]'], ['<a href="#">M.Tech scheme and syllabus, [2022]</a>', 'M.Tech admitted [2022] onwards', '[Date]']]),
    h(2, 'Student forms'),
    table(['Form', 'Submit to', 'Updated'], [['<a href="#">Leave application</a>', 'Staff advisor', '[Date]'], ['<a href="#">Bonafide certificate request</a>', 'Department office', '[Date]'], ['<a href="#">Internship approval</a>', 'Placement coordinator', '[Date]']]),
    h(2, 'Department'),
    table(['Document', 'Updated'], [['<a href="#">Department brochure</a>', '[Date]'], ['<a href="#">Placement brochure</a>', '[Date]'], ['<a href="#">NBA accreditation certificates</a>', '[Date]']]),
    p('Lab manuals are on each <a href="/labs/">lab page</a>. Attainment reports are on the <a href="/academics/obe/">outcome-based education</a> page.', textColor='muted', fontSize='small'),
])
pattern('page-downloads', 'Downloads', 'Forms, calendars, syllabus and department documents.', DOWN)

PRIV = '\n\n'.join([
    p('This page explains what information this website collects and how it is used.'),
    h(2, 'What we collect'),
    p('The site does not use tracking or advertising cookies and has no analytics. The web server keeps standard access logs (IP address, page requested, time) for security, deleted after [period]. Editors who log in use a session cookie.'),
    h(2, 'Information about staff and students'),
    p('Faculty and staff profiles show institutional email addresses and work details only. Student names appear in news, rank lists and placement posts with their consent. To correct or remove information about you, write to <a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a>.'),
    h(2, 'Embedded and linked content'),
    p('Some pages link to other sites, such as the university portal or Google Maps. Those sites have their own privacy policies.'),
    h(2, 'Contact'),
    p('Head of Department, Department of Electronics and Communication Engineering, College of Engineering Trivandrum. <a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a>'),
])
pattern('page-privacy', 'Privacy', 'What the website collects and how to correct information.', PRIV)

ACC = '\n\n'.join([
    p('We want everyone to be able to use this website, including people who use screen readers, keyboard navigation or magnification.'),
    h(2, 'What we do'),
    ul(['Pages follow the Web Content Accessibility Guidelines (WCAG) 2.2 at level AA as the target.', 'Text and background colours meet contrast requirements in light and dark mode.', 'Every page works with a keyboard and has a skip-to-content link.', 'Photos carry text descriptions, and posters have their text written out in the post.']),
    h(2, 'Known gaps'),
    p('Some older PDF documents are scanned images and cannot be read by screen readers. Ask us for an accessible copy.'),
    h(2, 'Report a problem'),
    p('Write to <a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a> with the page address and the problem. We aim to reply within [number] working days.'),
])
pattern('page-accessibility', 'Accessibility', 'Accessibility statement and how to report problems.', ACC)

# ---------- section patterns for editors ----------
pattern('section-link-cards', 'Link cards', 'A responsive grid of linked cards.', grid([card('[Title]', '[One line]', '#'), card('[Title]', '[One line]', '#'), card('[Title]', '[One line]', '#')], '220px', align='wide'), cats='cet-ece-sections', post_types='page,post')
pattern('section-figures', 'Key figures', 'Four large numbers with labels.', grid([stat('[n]', '[Label]'), stat('[n]', '[Label]'), stat('[n]', '[Label]'), stat('[n]', '[Label]')], '170px', cols=4, align='wide'), cats='cet-ece-sections', post_types='page,post')
pattern('section-facts', 'Fact boxes', 'Small boxes with a label and a value.', grid([fact('[Label]', '[Value]'), fact('[Label]', '[Value]'), fact('[Label]', '[Value]')], '170px', align='wide'), cats='cet-ece-sections', post_types='page,post')

print('ok')
