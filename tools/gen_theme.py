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


def pattern(slug, title, desc, content, cats='cet-ece-pages', post_types='page', inserter=True):
    head = f"""<?php
/**
 * Title: {title}
 * Slug: cet-ece/{slug}
 * Categories: {cats}
 * Description: {desc}
 * Post Types: {post_types}
 * Inserter: {'true' if inserter else 'false'}
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


# ---------- department content from the old site (ece.cet.ac.in, November 2026) ----------

VISION = 'To transform young students into responsible and competent professionals with focus on dissemination of knowledge in the sphere of Electronics, Communication and Instrumentation Engineering.'
MISSION = [
    'To impart quality engineering education to satisfy the needs of academics, industry and society.',
    'To achieve excellence in teaching-learning, research and innovation in the area of Electronics, Communication and Instrumentation Engineering.',
    'To facilitate networking with alumni, industries and institutions in bringing about excellence and nourishing the entrepreneurial skills of the students.',
    'To practise the highest level of professional integrity, transparency and accountability.',
]
WK = [
    ('WK1', 'A systematic, theory-based understanding of the natural sciences applicable to the discipline and awareness of relevant social sciences.'),
    ('WK2', 'Conceptually-based mathematics, numerical analysis, data analysis, statistics and formal aspects of computer and information science to support detailed analysis and modelling applicable to the discipline.'),
    ('WK3', 'A systematic, theory-based formulation of engineering fundamentals required in the engineering discipline.'),
    ('WK4', 'Engineering specialist knowledge that provides theoretical frameworks and bodies of knowledge for the accepted practice areas in the engineering discipline; much is at the forefront of the discipline.'),
    ('WK5', 'Knowledge, including efficient resource use, environmental impacts, whole-life cost, re-use of resources, net zero carbon, and similar concepts, that supports engineering design and operations in a practice area.'),
    ('WK6', 'Knowledge of engineering practice (technology) in the practice areas in the engineering discipline.'),
    ('WK7', 'Knowledge of the role of engineering in society and identified issues in engineering practice in the discipline, such as the professional responsibility of an engineer to public safety and sustainable development.'),
    ('WK8', 'Engagement with selected knowledge in the current research literature of the discipline, awareness of the power of critical thinking and creative approaches to evaluate emerging issues.'),
    ('WK9', 'Ethics, inclusive behaviour and conduct. Knowledge of professional ethics, responsibilities, and norms of engineering practice. Awareness of the need for diversity by reason of ethnicity, gender, age, physical ability etc. with mutual understanding and respect, and of inclusive attitudes.'),
]
POS = [
    ('PO1', 'Engineering knowledge', 'Apply knowledge of mathematics, natural science, computing, engineering fundamentals and an engineering specialization as specified in WK1 to WK4 respectively to develop to the solution of complex engineering problems.'),
    ('PO2', 'Problem analysis', 'Identify, formulate, review research literature and analyze complex engineering problems reaching substantiated conclusions with consideration for sustainable development. (WK1 to WK4)'),
    ('PO3', 'Design/development of solutions', 'Design creative solutions for complex engineering problems and design/develop systems/components/processes to meet identified needs with consideration for the public health and safety, whole-life cost, net zero carbon, culture, society and environment as required. (WK5)'),
    ('PO4', 'Conduct investigations of complex problems', 'Conduct investigations of complex engineering problems using research-based knowledge including design of experiments, modelling, analysis and interpretation of data to provide valid conclusions. (WK8)'),
    ('PO5', 'Engineering tool usage', 'Create, select and apply appropriate techniques, resources and modern engineering and IT tools, including prediction and modelling recognizing their limitations to solve complex engineering problems. (WK2 and WK6)'),
    ('PO6', 'The engineer and the world', 'Analyze and evaluate societal and environmental aspects while solving complex engineering problems for its impact on sustainability with reference to economy, health, safety, legal framework, culture and environment. (WK1, WK5 and WK7)'),
    ('PO7', 'Ethics', 'Apply ethical principles and commit to professional ethics, human values, diversity and inclusion; adhere to national and international laws. (WK9)'),
    ('PO8', 'Individual and collaborative team work', 'Function effectively as an individual, and as a member or leader in diverse/multi-disciplinary teams.'),
    ('PO9', 'Communication', 'Communicate effectively and inclusively within the engineering community and society at large, such as being able to comprehend and write effective reports and design documentation, make effective presentations considering cultural, language, and learning differences.'),
    ('PO10', 'Project management and finance', 'Apply knowledge and understanding of engineering management principles and economic decision-making and apply these in multidisciplinary environments.'),
    ('PO11', 'Life-long learning', 'Recognize the need for, and have the preparation and ability for i) independent and life-long learning ii) adaptability to new and emerging technologies and iii) critical thinking in the broadest context of technological change. (WK8)'),
]
# The first five M.Tech programme outcomes are common to all specialisations.
MTECH_PO = [
    'An ability to independently carry out research/investigation and development work to solve practical problems.',
    'An ability to write and present a substantial technical report/document.',
    'Students should be able to demonstrate a degree of mastery over the area as per the specialization of the program. The mastery should be at a level higher than the requirements in the appropriate bachelor program.',
    'Students will be able to demonstrate ethics related to intellectual properties and professional practice.',
    'Ability to learn independently based on the individual and system level needs especially in the context of rapidly changing technology.',
]
BTECH_PSO = {
    'btech-ece': [
        ('Domain knowledge', 'The ability to apply the knowledge of basic science and engineering to understand various real world problems of Electronics and Communication engineering systems using sustainable technologies demonstrating the practice of professional ethics and the concerns for societal and environmental well-being.'),
        ('Application skill', 'The ability to apply domain knowledge to design and solve the state of the art requirements of Electronics industry with good interpersonal skills as a leader in a team in appreciation of professional ethics and societal responsibilities.'),
        ('Research', 'Excellent adaptability to changing work environment by selecting and applying cutting edge engineering hardware and software tools to analyze and improve systems/processes for a variety of applications as well as to interpret/synthesize the simulated and experimental data leading to valid conclusions aimed at the furtherance of research activities for the well-being of humanity.'),
    ],
    'btech-aei': [
        ('Domain knowledge', 'The ability to apply the knowledge of basic science and engineering to understand various real world problems of Electronics, Instrumentation and Control using sustainable technologies demonstrating the practice of professional ethics and the concerns for societal and environmental well-being.'),
        ('Application skill', 'The ability to apply domain knowledge to design and solve the state of the art requirements of Electronics and Instrumentation industry with good interpersonal skills as a leader in a team in appreciation of professional ethics and societal responsibilities.'),
        ('Research', 'Excellent adaptability to changing work environment by selecting and applying cutting edge engineering hardware and software tools to analyze and improve systems/processes for a variety of applications as well as to interpret/synthesize the simulated and experimental data leading to valid conclusions aimed at the furtherance of research activities for the well-being of humanity.'),
    ],
}
PEOS = {
    'btech-ece': ['Build successful professional career in industry and academic institutions as engineers, managers and academicians.', 'Develop solutions to engineering problems through innovation and research.', 'Strive for the betterment of society by proposing solutions to engineering problems or as entrepreneurs.', 'Uphold good ethical practices, right professional conduct and provide responsible team leadership.'],
    'btech-aei': ['Excel in academia or industries as engineers, managers and academicians.', 'Demonstrate ability to adapt to technological challenges by acquiring new skills and competencies.', 'Pursue a socially responsible approach while proposing solutions to engineering problems or as entrepreneurs.', 'Uphold professional ethical values, exhibit leadership skills and professional competence.'],
    'mtech-applied-electronics': ['Technocrats capable of developing eco-friendly automation systems.', 'Competent researchers solving state-of-the-art problems.', 'Successful entrepreneurs taking lead role for developing engineering solutions with global, societal, and environmental perspectives.', 'Responsible professionals exhibiting integrity and ethical values.'],
    'mtech-micro-nano-electronics': ['Engage in development of innovative and sustainable solutions in microelectronics.', 'Address emerging challenges through reskilling and upskilling.', 'Exhibit self-reliance and entrepreneurial skills to meet the needs of the society.', 'Maintain high professional and ethical standards.'],
    'mtech-communication-systems': ['To be successful engineers, capable of analysing, designing and optimizing communication systems and developing innovative solutions for real-world engineering challenges in society.', 'To be professionals fostering a culture of continuous learning and innovation while pursuing research in communication systems or related fields.', 'To be proficient in communication and collaboration, capable of excelling as entrepreneurs and working effectively in multidisciplinary teams.', 'To be ethically responsible engineers who consider the societal impact of their work, promoting safety, sustainability and inclusivity in the design and development of communication systems.'],
    'mtech-robotics-automation': ['Be a promising technology expert capable of solving industrial and social issues through nature friendly initiatives.', 'Address emerging challenges, reinvent existing solutions and practices in Robotics and Automation.', 'Establish business startups and be a successful entrepreneur.', 'Be an outstanding professional with high degree of managerial skills and ethical values.'],
    'mtech-signal-processing': ['Demonstrate the ability to cater to the diverse and evolving needs of the industry, through sustainable and eco-friendly solutions.', 'Formulate novel solutions to existing and emerging problems in the domain of signal processing through research.', 'Exhibit leadership skills, professional competence and entrepreneurial skills.', 'Uphold professional and ethical values.'],
}
MTECH_PO6 = {
    'mtech-applied-electronics': 'Attain the capability to design and develop solutions in the field of electronics, control and instrumentation engineering using modern engineering tools.',
    'mtech-micro-nano-electronics': 'Ability to design, model and develop micro and nano systems using modern tools.',
    'mtech-communication-systems': 'Design and develop systems using modern engineering tools for solving problems in the area of communication systems.',
    'mtech-robotics-automation': 'Design, analyse and develop solutions for robotic and automation systems.',
    'mtech-signal-processing': 'Design and develop algorithms for computer aided signal processing and implement state-of-the-art signal processing systems.',
}
# slug: intake, duration, labs programme term, accreditation, started, overview
PROGRAMMES = {
    'btech-ece': ('120 + 12 lateral entry', '4 years, 8 semesters', 'btech-ece', 'NBA accredited; extended to 30 June 2025 [confirm the renewal]', 'Started in 1965 with 33 students; a second batch was approved in 2024. Part-time B.Tech from 1982.'),
    'btech-aei': ('60 + 6 lateral entry', '4 years, 8 semesters', 'btech-aei', 'NBA accredited; extended to 30 June 2025 [confirm the renewal]', 'Started in 1981.'),
    'mtech-applied-electronics': ('18', '2 years, 4 semesters', 'mtech', '[NBA status]', 'Started in 1986.'),
    'mtech-communication-systems': ('18', '2 years, 4 semesters', 'mtech', '[NBA status]', 'Started in 1972 as Microwave and Television Engineering; renamed Communication Systems in 2023.'),
    'mtech-signal-processing': ('18', '2 years, 4 semesters', 'mtech', 'NBA accredited for 2024–25 to 2026–27, to 30 June 2027', 'Started in 2005.'),
    'mtech-micro-nano-electronics': ('18', '2 years, 4 semesters', 'mtech', '[NBA status]', 'Started in 2015, during the department’s Golden Jubilee.'),
    'mtech-robotics-automation': ('18', '2 years, 4 semesters', 'mtech', '[NBA status]', 'An interdisciplinary programme, started in 2016.'),
}
SCHEMES = {
    'btech': [['2024 scheme', 'Admitted 2024 onwards', '<a href="#">Scheme and syllabus (PDF)</a>', 'Current'], ['2019 scheme', 'Admitted 2019–2023', '<a href="https://ktu.edu.in/">Scheme and syllabus (KTU)</a>', 'Current for older batches'], ['2015 scheme', 'Admitted 2015–2018', '<a href="https://ktu.edu.in/">Scheme and syllabus (KTU)</a>', 'Archived']],
    'mtech': [['2022 scheme', 'Admitted 2022 onwards', '<a href="#">Scheme and syllabus (PDF)</a>', 'Current'], ['2015 scheme', 'Admitted 2015–2021', '<a href="#">Scheme and syllabus (PDF)</a>', 'Archived']],
}
ACCREDITATION_HISTORY = [
    ('1999', 'B.Tech ECE accredited with A5 grade'),
    ('2000', 'B.Tech AEI accredited with B5 grade'),
    ('2001', 'ISO 9002:1994 certification'),
    ('2007', 'B.Tech ECE, B.Tech AEI and M.Tech Microwave and Television Engineering accredited with A5 grade; M.Tech AEI with A3 grade'),
    ('2013', 'M.Tech AEI and M.Tech Signal Processing accredited for 3 years'),
    ('2014', 'B.Tech ECE, B.Tech AEI and M.Tech Microwave and Television Engineering accredited for 5 years'),
    ('2019', 'B.Tech ECE and B.Tech AEI accredited for 3 years'),
    ('2022', 'Accreditation of B.Tech ECE and B.Tech AEI extended by 3 years, to 30 June 2025'),
    ('2024', 'M.Tech Signal Processing accredited for 3 years, 2024–25 to 2026–27'),
]
MILESTONES = [
    ('1965', 'B.Tech in Electronics and Communication Engineering'), ('1972', 'M.Tech in Microwave and Television Engineering'),
    ('1981', 'B.Tech in Applied Electronics and Instrumentation'), ('1982', 'Part-time B.Tech in Electronics and Communication Engineering'),
    ('1986', 'M.Tech in Applied Electronics and Instrumentation'), ('1988', 'Part-time M.Tech in Microwave and Television Engineering, and in Applied Electronics and Instrumentation'),
    ('1991', 'Project IMPACT'), ('1995', 'Project NETWORK; department library'), ('1996', 'Leased line connectivity'), ('1998', 'Project RESPOND'),
    ('2003', 'Project FIST'), ('2005', 'M.Tech in Signal Processing'), ('2006', 'New PG labs: VLSI, Embedded Systems, Advanced Communication and Fiber Optics'),
    ('2008', 'Power Electronics Research Laboratory (PERL)'), ('2010', 'Project NPMaSS'),
    ('2011', 'ECE new block; approved as a QIP centre; full-time Ph.D. under CERD and SPEED-IT'), ('2012', 'Higher intake in the M.Tech Microwave and AEI programmes'),
    ('2013', 'Computer Vision Lab'), ('2015', 'M.Tech in Micro and Nano Electronics; RUSA; Ph.D. centre; Golden Jubilee year opens, 9 September 2015'),
    ('2016', 'M.Tech in Robotics and Automation'), ('2017', 'Construction of the PG and Research Block begins'), ('2018', 'Ph.D. under the National Doctoral Fellowship scheme'),
    ('2020', 'Patent: an automated duct fan based wall climbing device'), ('2021', 'CET Oxymonitor, a tabletop pulse oximeter, developed for the Government of Kerala during COVID-19'),
    ('2022', 'RISC-V processor developed by CET with TrEST Research Park and Westguard'),
    ('2023', 'C V Raman Centre for Nanoelectronics and Srinivasa Ramanujan Centre for Machine Intelligence approved by the Government of Kerala; Golden Jubilee PG and Research Block inaugurated; M.Tech Microwave and Television Engineering renamed Communication Systems; C2S project funded by MeitY, Government of India (₹4.7 crore)'),
    ('2024', 'Second batch of B.Tech Electronics and Communication Engineering approved'),
    ('2025', 'Patent granted, 15 December 2025: method of automatic grading of ribbed smoked sheets and system thereof'),
]
PATENTS = [
    ('Method of automatic grading of ribbed smoked sheets and system thereof', 'Granted and recorded in the Register of Patents on 15 December 2025'),
    ('An automatic safety system that enhances safety of a user while riding a vehicle', 'Patent No. 470200, granted 16 November 2023'),
    ('An automated duct fan based wall climbing device', 'September 2020'),
]

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
    p('The Department of Electronics and Communication Engineering was established at the CET campus, Sreekariyam, in 1964–65. The B.Tech programme in Electronics and Communication Engineering started with an intake of 33 students.'),
    p('Today the department offers B.Tech programmes in Electronics and Communication Engineering and in Applied Electronics and Instrumentation; M.Tech programmes in Applied Electronics and Instrumentation, Communication Systems, Signal Processing, Micro and Nano Electronics, and Robotics and Automation; and a doctoral programme. All programmes are approved by AICTE, and the department is an approved QIP centre.'),
    h(2, 'Vision'),
    p(VISION, fontSize='large', style={'typography': {'fontWeight': '500'}}),
    h(2, 'Mission'),
    ul(MISSION, ordered=True),
    h(2, 'Accreditation'),
    table(['Programme', 'Body', 'Status', 'Valid until'], [['B.Tech ECE', 'NBA', 'Accredited; extension granted in 2022', '30 June 2025 [confirm the renewal]'], ['B.Tech AEI', 'NBA', 'Accredited; extension granted in 2022', '30 June 2025 [confirm the renewal]'], ['M.Tech Signal Processing', 'NBA', 'Accredited, 2024–25 to 2026–27', '30 June 2027']]),
    p('Current status only. Link each programme name to its certificate (PDF).', textColor='muted', fontSize='small'),
    h(3, 'Accreditation history'),
    table(['Year', 'Accreditation or certification'], [list(x) for x in ACCREDITATION_HISTORY]),
    h(2, 'Milestones'),
    table(['Year', 'Milestone'], [list(x) for x in MILESTONES]),
    h(2, 'Patents'),
    table(['Title', 'Status'], [list(x) for x in PATENTS]),
    h(2, 'Golden Jubilee'),
    p('The department marked its Golden Jubilee in 2015 with a year of programmes for students and faculty rather than celebrations: an alumni lecture series, workshops, exhibitions and a project exposition. The Chief Minister of Kerala inaugurated the year on 9 September 2015 and laid the foundation stone of the Golden Jubilee PG and Research Block, which opened in 2023. The M.Tech programme in Micro and Nano Electronics was launched the same day.'),
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

def programme_page(slug=None):
    """One programme page. Without a slug: the generic pattern with placeholders."""
    if slug:
        intake, duration, term, accr, started = PROGRAMMES[slug]
        level = 'btech' if slug.startswith('btech') else 'mtech'
    else:
        intake, duration, term, accr, started, level = '[Intake]', '[Duration]', '', '[NBA status, valid to date]', '', 'btech'
    if slug and level == 'btech':
        outcomes = [
            h(3, 'Programme educational objectives (PEOs)'),
            ul([f'<strong>PEO{i}:</strong> {t}' for i, t in enumerate(PEOS[slug], 1)]),
            h(3, 'Programme specific outcomes (PSOs)'),
            ul([f'<strong>PSO{i} ({k}):</strong> {t}' for i, (k, t) in enumerate(BTECH_PSO[slug], 1)]),
            p('Programme outcomes (POs) are common to all B.Tech programmes and listed on the <a href="/academics/obe/">outcome-based education</a> page, with attainment reports.'),
        ]
    elif slug:
        outcomes = [
            h(3, 'Programme educational objectives (PEOs)'),
            ul([f'<strong>PEO{i}:</strong> {t}' for i, t in enumerate(PEOS[slug], 1)]),
            h(3, 'Programme outcomes (POs)'),
            ul([f'<strong>PO{i}:</strong> {t}' for i, t in enumerate(MTECH_PO + [MTECH_PO6[slug]], 1)]),
            p('Attainment reports are on the <a href="/academics/obe/">outcome-based education</a> page.'),
        ]
    else:
        outcomes = [
            h(3, 'Programme educational objectives (PEOs)'),
            ul(['<strong>PEO1:</strong> [Statement]', '<strong>PEO2:</strong> [Statement]', '<strong>PEO3:</strong> [Statement]']),
            h(3, 'Programme specific outcomes (PSOs)'),
            ul(['<strong>PSO1:</strong> [Statement]', '<strong>PSO2:</strong> [Statement]']),
            p('Programme outcomes (POs) are common to all programmes and listed on the <a href="/academics/obe/">outcome-based education</a> page, with attainment reports.'),
        ]
    overview = (started + ' ' if started else '') + '[One paragraph: what the programme covers, electives, project work and internships, and what graduates go on to do.]'
    schemes = SCHEMES[level] if slug else [['[2024] scheme', 'Admitted [2024] onwards', '<a href="#">Scheme and syllabus (PDF)</a>', 'Current'], ['[2019] scheme', 'Admitted [2019–2023]', '<a href="#">Scheme and syllabus (PDF)</a>', 'Current for older batches'], ['[2015] scheme', 'Admitted [2015–2018]', '<a href="#">Archive (PDF)</a>', 'Archived']]
    admissions = '[KEAM / GATE / university process]' if not slug else ('KEAM, through the Commissioner for Entrance Examinations, Kerala' if level == 'btech' else 'GATE score and the state PG admission process [confirm]')
    return '\n\n'.join([
        grid([fact('Intake', intake), fact('Duration', duration), fact('Accreditation', accr), fact('Programme coordinator', '[Faculty name]')], '170px', cols=4, align='wide'),
        p('On this page: <a href="#overview">Overview</a> · <a href="#curriculum">Curriculum</a> · <a href="#outcomes">Outcomes</a> · <a href="#labs">Labs</a> · <a href="#contacts">Contacts</a>', fontSize='small'),
        h(2, 'Overview', anchor='overview'),
        p(overview),
        h(2, 'Curriculum', anchor='curriculum'),
        table(['Scheme', 'Applies to', 'Documents', 'Status'], schemes),
        p('Regulations and the academic calendar come from APJ Abdul Kalam Technological University: <a href="https://ktu.edu.in/">ktu.edu.in</a>.', textColor='muted', fontSize='small'),
        h(2, 'Outcomes', anchor='outcomes'),
        *outcomes,
        h(2, 'Labs used in this programme', anchor='labs'),
        dyn('cet-ece/lab-list', type='teaching', programme=term),
        h(2, 'Contacts', anchor='contacts'),
        ul(['Programme coordinator: [Faculty name], [name]@cet.ac.in', 'Staff advisors: <a href="/staff-advisors/">current batches</a>', f'Admissions: {admissions}, see <a href="/contact/">contact</a>']),
    ])


PROGRAMME_NAMES = {'btech-ece': 'B.Tech ECE', 'btech-aei': 'B.Tech AEI', 'mtech-applied-electronics': 'M.Tech Applied Electronics and Instrumentation', 'mtech-communication-systems': 'M.Tech Communication Systems', 'mtech-signal-processing': 'M.Tech Signal Processing', 'mtech-micro-nano-electronics': 'M.Tech Micro and Nano Electronics', 'mtech-robotics-automation': 'M.Tech Robotics and Automation'}
PROG = programme_page()
for _slug in PROGRAMMES:
    pattern('page-programme-' + _slug, 'Programme page: ' + PROGRAMME_NAMES[_slug], 'Starter content for this programme page, used when the theme creates the site\u2019s pages.', programme_page(_slug), inserter=False)
pattern('page-programme', 'Programme page', 'Facts, curriculum by scheme, PEOs and PSOs, labs and contacts for one programme.', PROG)

PHD = '\n\n'.join([
    p('Full-time and part-time Ph.D. under APJ Abdul Kalam Technological University. The department is a QIP centre with approved research guides across its research areas.'),
    h(2, 'Fellowship schemes'),
    table(['Scheme', 'What it is'], [['QIP', 'Quality Improvement Programme, for faculty from other institutions'], ['NET-JRF', 'UGC Junior Research Fellowship holders'], ['KSCSTE', 'Kerala State Council for Science, Technology and Environment fellowship'], ['NDF / ADF', 'AICTE National Doctoral Fellowship and AICTE Doctoral Fellowship'], ['CERD', 'Centre for Engineering Research and Development, Government of Kerala, fellowship']]),
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
    p(VISION, fontSize='large', style={'typography': {'fontWeight': '500'}}),
    h(2, 'Department mission'),
    ul(MISSION, ordered=True),
    h(2, 'Programme outcomes (POs)'),
    p('Common to all B.Tech programmes. The M.Tech programme outcomes are on each M.Tech programme page.', textColor='muted', fontSize='small'),
    table(['PO', 'Outcome', 'Statement'], [[a, b, c] for a, b, c in POS]),
    h(3, 'Knowledge and attitude profile (WK)'),
    p('The programme outcomes refer to this knowledge and attitude profile.', textColor='muted', fontSize='small'),
    table(['WK', 'Statement'], [[a, b] for a, b in WK]),
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
    dyn('cet-ece/research-figures', align='wide'),
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
    p('The department library supports the B.Tech, M.Tech and Ph.D. programmes. It began as a small reference collection given by the teaching faculty. In 1993 it became a full library with separate lending and reference sections, using funds from the IMPACT project; later purchases came from the NETWORK and TEQIP projects.'),
    p('In 2013 the library was renovated and air-conditioned with a contribution from the alumni batch of 1983–88. It is dedicated to the memory of their classmate Dr. Suresh Kumar R., who taught in the department before leaving for research in the USA.'),
    h(2, 'Holdings'),
    table(['Collection', 'Count', 'As of'], [['All books', 'Over 9,355', '[Date]'], ['Lending section', '6,673', '[Date]'], ['Reference section', 'Over 1,788', '[Date]']]),
    p('There is a separate reference area with seating, and a reading area with newspapers and periodicals.'),
    h(2, 'Opening hours'),
    p('[Days and times]'),
    h(2, 'E-resources'),
    p('IEEE journals and Elsevier ScienceDirect through the INDEST consortium, with computers in the library for online journals and internet reference. [Confirm the current subscriptions and access period]'),
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
    p('Head of Department<br>Department of Electronics and Communication Engineering<br>College of Engineering Trivandrum<br>Sreekariyam, Thiruvananthapuram, Kerala 695016'),
    p('<a href="tel:04712515563">0471-2515563</a> · <a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a> · Office hours: [Mon–Fri, 9:00–17:00]'),
    p('<a href="https://maps.google.com/?q=College+of+Engineering+Trivandrum">Open in Google Maps</a>'),
    h(2, 'Who to contact'),
    table(['For', 'Contact', 'Email'], [['Admissions and general queries', 'Department office', '<a href="mailto:hodece@cet.ac.in">hodece@cet.ac.in</a>'], ['Placements and internships', '[Placement coordinator]', '[name]@cet.ac.in'], ['Ph.D. admissions', '[Research coordinator]', '[name]@cet.ac.in'], ['Website corrections', '[Web coordinator]', '[name]@cet.ac.in']]),
    h(2, 'How to reach'),
    table(['By', 'Directions'], [
        ['Air', 'Thiruvananthapuram International Airport has domestic and international flights daily. Take a cab from the pre-paid taxi counter (about ₹500) or an online taxi. Places near CET: Sreekariyam, Chavadimukku, Kulathoor and Mannanthala.'],
        ['Train', 'Get off at Thiruvananthapuram Central (Thampanoor). A pre-paid autorickshaw from outside the station costs about ₹120, or take a bus from the Thampanoor bus stand, 100 m away. Online taxis are also available.'],
        ['Bus', 'The main bus terminus is at Thampanoor, opposite the railway station, with buses to the CET campus. Otherwise take a bus to Sreekariyam or Chavadimukku: CET is 2 km from Sreekariyam and 1 km (a 10-minute walk) from Chavadimukku. An autorickshaw from either costs ₹20–30.'],
    ]),
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
