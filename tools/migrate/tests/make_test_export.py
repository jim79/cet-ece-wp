"""Build a small WordPress export shaped like the old ece.cet.ac.in pages, with
invented names and the same kinds of mess the audit found (typos, Gmail
addresses, duplicates, a broken DOI, "Prof," with a comma). Used to test
convert_old_site.py and the importer.

Usage: python3 make_test_export.py out.xml [image_base_url]
"""
import sys
from xml.sax.saxutils import escape

out = sys.argv[1]
img = sys.argv[2] if len(sys.argv) > 2 else 'https://ece.cet.ac.in/wp-content/uploads/2024/03'

faculty = [
    ('Dr. Anil Kumar R', 'Professor (Principal in charge)', '11-03-2019', 'Signal Processing, Image Processing', 'anilkumar@cet.ac.in', 'IMG_1631.jpg'),
    ('Dr.  Beena Thomas', 'Professor', '02-07-2001', 'Communication Engineering', 'beena@cet.ac.in', 'beena.jpg'),
    ('Dr. Cyriac Joseph', 'Assosciate Professor', '15-06-2010', 'VLSI Design', 'cyriac@cet.ac.in', 'cyriac.jpg'),
    ('Prof. Deepa S', 'Assistant Professor', '27-08-2025', 'Embedded Systems', 'deepa.s@gmail.com', 'WhatsApp-Image-2025.jpg'),
    ('Prof. Sivakumar P', 'Assistant Professor (Ad hoc)', '01-07-2026', 'Power Electronics', '', ''),
    ('Dr. Elizabeth Mathew', 'Assistant Professor', '05-01-2017', 'Machine Learning', 'elizabeth@cet.ac.in', 'eliz.jpg'),
]
fac_html = []
for n, d, j, s, e, p in faculty:
    fig = f'<figure class="wp-block-image"><img src="{img}/{p}" alt=""/></figure>' if p else ''
    fac_html.append(f'''{fig}
<h3><a href="https://ece.cet.ac.in/{n.lower().replace(' ', '-').replace('.', '')}/">{n}</a></h3>
<p><strong>{d}</strong><br><strong>Date of Joining:</strong> {j}<br><strong>Specialization / Area of  Interest:</strong> {s}<br>{e}<br>94473 20562</p>''')

staff_html = '''<p><strong>Instructor Grade I</strong></p><ul><li>Rajan K</li><li>Prasobha K. Prasad</li></ul>
<p><strong> Instructor Grade II </strong></p><ul><li>Beena V S</li></ul>
<p><strong>Trade Instructors</strong></p><ul><li>Sunilkumar B</li><li>Manoj T</li></ul>
<p><strong>Tradesmen</strong></p><ul><li>Shaji M</li></ul>'''

adv_html = '''<h2>B.Tech. (ECE)</h2>
<h4>ECE 2026  admission</h4>
<p><strong>Batch A: Prof. Deepa S 9447454377</strong></p>
<p><strong>Batch B: Dr. Elizabeth Mathew</strong></p>
<h4>ECE 2023 admission</h4>
<p><strong>Dr. Cyriac Joseph 9562710322</strong></p>
<h4>ECE 2019 admission</h4>
<p><strong>Prof, Sivakumar P</strong></p>
<h2>B.Tech. (AEI)</h2>
<h4>AEI 2025 admission</h4>
<p><strong>Dr. Beena Thomas</strong></p>
<h2>M.Tech Signal Processing</h2>
<h4>Signal Processing (2025 – 27)</h4>
<p><strong>Dr. Anil Kumar R</strong></p>'''

labs_html = '''<h2>UG Labs</h2><ul><li><a href="https://ece.cet.ac.in/ec-lab/">Electronic Circuits  Lab</a></li><li>Microwave Lab</li><li><a href="https://ece.cet.ac.in/fo/">Fiber Optics Lab</a></li></ul>
<p><a href="https://ece.cet.ac.in/ug-dsp/">UG DSP Lab</a></p><p>Electronics Workshop</p>
<h2>PG &amp; Research Labs</h2><p>RF Research Lab</p><ul><li><a href="https://ece.cet.ac.in/fo/">Fiber Optics Lab</a></li><li>Power Electronics Research Lab [P E R L]</li><li>C2S</li><li>Advanced Communication Lab</li></ul>'''

pubs_html = '''<p><strong>2025</strong></p>
<p>Dr. Anil Kumar R:</p>
<ol><li>A. K. R and E. Mathew, “Learning-based denoising of retinal images,” <em>IEEE Access</em>, vol. 13, pp. 1201-1210, 2025, doi: 10.1109/ACCESS.2025.1234567.</li>
<li>A. K. R, “Sparse coding for speech enhancement,” Proc. IEEE ICASSP, 2025.</li></ol>
<p>Elizabeth Mathew :</p>
<ol><li>A. K. R and E. Mathew, “Learning-based denoising of retinal images,” <em>IEEE Access</em>, vol. 13, pp. 1201-1210, 2025, doi: 10.1109/ACCESS.2025.1234567.</li>
<li>E. Mathew, “Graphine-based sensors,” Applied Physics A, 2022, doi: 1007/s00339-021-04550-5</li></ol>
<p><strong>2023</strong></p>
<p>Dr. Beena Thomas:</p>
<ol><li>B. Thomas, “Antenna arrays for 5G,” Proc. ICCC 2023, doi: 10.1109/ICCC57789.2023.10165227</li>
<li>C. Joseph and B. Thomas, “Low power LNA design,” Proc. ICCC 2023, doi: 10.1109/ICCC57789.2023.10165227</li>
<li>B. Thomas, “Channel estimation survey,” Accepted for presentation at NCC on July 2-5, 2023</li></ol>'''

posts = [
    ('ROS 2 &amp; TurtleBot 3 Workshop', '2026-08-06 10:00:00', 'Activities', '<p>27 participants from several institutions.</p><img src="%s/ros.jpg"/>' % img),
    ('FDP on VLSI System Design', '2024-01-22 09:00:00', 'Activities', '<p>Faculty development programme on EDA tools.</p>'),
    ('Examination Calendar Nov 2026', '2026-10-10 09:00:00', 'Announcements', '<p>Calendar attached.</p>'),
    ('Congratulations to university rank holders', '2025-09-01 09:00:00', 'Uncategorized', '<p>First rank in AEI.</p>'),
]


def item(pid, title, slug, ptype, body, date='2024-01-01 00:00:00', cat=None, extra=''):
    c = f'<category domain="category" nicename="{cat.lower()}"><![CDATA[{cat}]]></category>' if cat else ''
    return f'''<item><title>{title}</title><link>https://ece.cet.ac.in/{slug}/</link>
<content:encoded><![CDATA[{body}]]></content:encoded><excerpt:encoded><![CDATA[]]></excerpt:encoded>
<wp:post_id>{pid}</wp:post_id><wp:post_date>{date}</wp:post_date><wp:post_name>{slug}</wp:post_name>
<wp:status>publish</wp:status><wp:post_type>{ptype}</wp:post_type>{c}{extra}</item>'''


items = [
    item(10, 'Faculty', 'faculty-2', 'page', '\n'.join(fac_html)),
    item(11, 'Technical staff', 'technical-staff', 'page', staff_html),
    item(12, 'Staff Advisors', 'staff-advisors', 'page', adv_html),
    item(13, 'Laboratories', 'laboratories', 'page', labs_html),
    item(14, 'Recent Publications', 'publications', 'page', pubs_html),
    item(90, 'ros', 'ros', 'attachment', '', extra=f'<wp:attachment_url>{img}/ros.jpg</wp:attachment_url>'),
]
for i, (t, d, c, b) in enumerate(posts):
    extra = '<wp:postmeta><wp:meta_key>_thumbnail_id</wp:meta_key><wp:meta_value>90</wp:meta_value></wp:postmeta>' if i == 0 else ''
    items.append(item(100 + i, t, 'post-%d' % i, 'post', b, d, c, extra))

xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wp="http://wordpress.org/export/1.2/">
<channel><title>ECE CET (test export)</title>
{''.join(items)}
</channel></rss>'''
open(out, 'w').write(xml)
print('wrote', out)
