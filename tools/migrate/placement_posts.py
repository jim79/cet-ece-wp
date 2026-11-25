"""Placement posters and highlights from the old site's Placements page, as news posts.

The old site placed these photos straight onto ece.cet.ac.in/placements-latest/
instead of posting them as news, so the main converter missed them. This adds
them to playground/data/news.csv (category "placements"), one post per poster or
per company announcement, with the photo as the featured image.

Roll numbers are left out. Figures the old page states two ways are marked
[confirm], and posters whose text could not be read are marked for a person
to fill in.

Usage: python3 tools/migrate/placement_posts.py [news.csv]
"""
import csv
import os
import re
import sys

UP = 'https://ece.cet.ac.in/wp-content/uploads/'


def full(url):
    """Original upload instead of a resized copy (photo-150x150.jpg -> photo.jpg)."""
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.\w+$)', '', url.replace('http://', 'https://'))


def ul(items):
    return '<ul>' + ''.join('<li>%s</li>' % i for i in items) + '</ul>'


POSTS = [
    # 2025 posters
    ('Placement announcement, 13 November 2025 (3 of 3)', '2025-11-13 16:46:00', UP + '2025/11/WhatsApp-Image-2025-11-13-at-4.46.18-PM-819x1024.jpeg',
     '[Write the student names, programme, company and role shown on the poster.]', ''),
    ('Placement announcement, 13 November 2025 (2 of 3)', '2025-11-13 16:17:00', UP + '2025/11/WhatsApp-Image-2025-11-13-at-4.17.34-PM-768x960.jpeg',
     '[Write the student names, programme, company and role shown on the poster.]', ''),
    ('Placement announcement, 13 November 2025 (1 of 3)', '2025-11-13 14:19:00', UP + '2025/11/WhatsApp-Image-2025-11-13-at-2.19.01-PM-819x1024.jpeg',
     '[Write the student names, programme, company and role shown on the poster.]', ''),
    ('Placements of the S7 AEI 2022–26 batch', '2025-10-20 10:00:00', UP + '2025/10/Placements-S7-AEI-2022-26-768x960.jpeg',
     'Placement offers for the 2022–26 B.Tech AEI batch. [Write the names, companies and roles shown on the poster.]', ''),
    ('Placement announcement, October 2025 (2 of 2)', '2025-10-15 10:01:00', UP + '2025/10/2-724x1024.png',
     '[Write the student names, programme, company and role shown on the poster.]', ''),
    ('Placement announcement, October 2025 (1 of 2)', '2025-10-15 10:00:00', UP + '2025/10/1-768x1086.png',
     '[Write the student names, programme, company and role shown on the poster.]', ''),
    ('Tinu K Cheriya placed at Texas Instruments', '2025-08-15 10:01:00', UP + '2025/08/Tinu.png',
     'Tinu K Cheriya of the 2022–26 B.Tech ECE batch has been selected by Texas Instruments for an embedded software role.', ''),
    ('Neeraj Ninan Kuriakose placed at Texas Instruments', '2025-08-15 10:00:00', UP + '2025/08/Neeraj.png',
     'Neeraj Ninan Kuriakose of the 2022–26 B.Tech ECE batch has secured a placement at Texas Instruments, a global leader in semiconductor design and manufacturing.', ''),
    # 2021–25 batch: offers listed as text on the old page
    ('Placement offers for the 2021–25 B.Tech ECE batch', '2025-06-30 10:00:00', '',
     'Offers made to final-year B.Tech ECE students in the 2024–25 placement season.',
     '<table><thead><tr><th>Company</th><th>Students</th><th>Role</th><th>Package (LPA)</th></tr></thead><tbody>'
     '<tr><td>Texas Instruments</td><td>M V Mahadevan, Suryagayathri, Dave Paul Joseph, Fasna Sharaf</td><td>Digital and software</td><td>38.5</td></tr>'
     '<tr><td>AMD</td><td>Bhadra Ashok, Deena Mariya David</td><td>Silicon Design Engineer, Physical Design</td><td>[confirm: 25 with benefits, or 13]</td></tr>'
     '<tr><td>Amadeus</td><td>Althaf Mansoor</td><td></td><td>12.62</td></tr>'
     '<tr><td>Schneider Electric</td><td>Govind V, Sradha S Kumar</td><td>Hardware Design Engineer</td><td>12</td></tr>'
     '<tr><td>Schneider Electric</td><td>Rameesa Jahan</td><td>Industrial Control and Drives R&amp;D Engineer</td><td>12</td></tr>'
     '<tr><td>Tismo</td><td>Adarsh Varghese, Bristo C J</td><td>Firmware Engineer; Hardware Engineer</td><td>12</td></tr>'
     '<tr><td>Clairvolex</td><td>Aswin S</td><td>Graduate Engineer Trainee</td><td>12</td></tr>'
     '<tr><td>IBM</td><td>Aswathy N</td><td></td><td>11</td></tr>'
     '<tr><td>EmbedUR</td><td>Paul Thomas</td><td>Junior Software Engineer</td><td>8</td></tr>'
     '<tr><td>Ashok Leyland</td><td>Theertha Devan</td><td>Graduate Engineer Trainee</td><td>7.5</td></tr>'
     '<tr><td>Anora Semiconductor Labs</td><td>Safvan C K, Gokul Gopalakrishnan</td><td>Graduate Engineer Trainee</td><td>6</td></tr>'
     '<tr><td>Ignitarium</td><td>Akshay K Subhash, Yadukrishnan T P</td><td>Associate Verification Engineer; Software Engineer</td><td>5</td></tr>'
     '<tr><td>Centelon Solutions</td><td>Arjun P V, Harikrishnan P</td><td>Junior Consultant, IoT and Robotics</td><td>5</td></tr>'
     '<tr><td>Capgemini</td><td>Krishnendhu K P, Dilna Dinesh C</td><td>VLSI Analyst; Software Analyst</td><td>5</td></tr>'
     '<tr><td>Cavli Wireless</td><td>V Janaki</td><td>Junior Systems Engineer</td><td>5</td></tr>'
     '</tbody></table>'),
    # Highlights of earlier years
    ('Texas Instruments selects four ECE students at ₹38.5 lakh a year', '2024-07-27 12:57:00', UP + '2024/07/WhatsApp-Image-2024-07-27-at-12.57.17-PM.jpeg',
     'Texas Instruments offered a CTC of ₹38.5 lakh a year to four final-year ECE students: M V Mahadevan and Suryagayathri on the digital side, and Dave Paul Joseph and Fasna Sharaf on the software side.', ''),
    ('Texas Instruments selects three ECE students at ₹34.64 lakh a year', '2024-07-10 10:06:00', UP + '2024/07/Akshay-K-B.jpg',
     'Texas Instruments offered a CTC of ₹34.64 lakh a year to three final-year students in the 2023–24 placements.', ul(['Akshay K B', 'Dona Kurian', 'Sangeeth P'])),
    ('Synopsys selects ECE and AEI students at ₹17 lakh a year', '2024-07-10 10:05:00', UP + '2024/07/Amal-K-Ayyan.jpeg',
     'Synopsys offered a CTC of ₹17 lakh a year to Amal K Ayyan (ECE) and R Mukund (AEI) in the 2023–24 placements.', ''),
    ('Schneider Electric selects three students at ₹12 lakh a year', '2024-07-10 10:04:00', UP + '2024/07/P-N-Parameshwaran.jpg',
     'Schneider Electric offered a CTC of ₹12 lakh a year to P N Parameswaran (ECE), and Abhijith S and Judy Teresa Zacharia (AEI), in the 2023–24 placements.', ''),
    ('CynLr selects Vishnu S at ₹12 lakh a year', '2024-07-10 10:03:00', UP + '2024/07/Vishnu-S.jpeg',
     'CynLr offered a CTC of ₹12 lakh a year to Vishnu S (ECE) in the 2023–24 placements.', ''),
    ('Microchip Technology selects two ECE students at ₹10 lakh a year', '2024-07-10 10:02:00', UP + '2024/07/Ashok-R.jpeg',
     'Microchip Technology India offered a CTC of ₹10 lakh a year to Ashok R and Aswin K K (ECE) in the 2023–24 placements.', ''),
    ('Tejas Networks selects three ECE students at ₹10 lakh a year', '2024-07-10 10:01:00', UP + '2024/07/Dhanush-Joy.jpg',
     'Tejas Networks offered a CTC of ₹10 lakh a year to three final-year ECE students in the 2023–24 placements.', ul(['Dhanush Joy', 'Elsa Eldhose', 'Godson Antony'])),
    ('o9 Solutions selects Sandra Kakkarayil Jayakumar at ₹11.75 lakh a year', '2023-05-01 10:00:00', UP + '2023/05/Sandra-.png',
     'o9 Solutions offered an annual salary of ₹11.75 lakh to Sandra Kakkarayil Jayakumar (ECE).', ''),
    ('Texas Instruments selects nine students at ₹26.8 lakh a year', '2022-07-09 07:13:00', UP + '2022/07/Texas-WhatsApp-Image-2022-07-09-at-7.13.46-AM.jpg',
     'Texas Instruments offered a CTC of ₹26.8 lakh a year plus $10,000 in equity to nine students of the ECE department. [confirm: the old page lists names from both ECE and AEI]',
     ul(['Amrita A Nair (AEI)', 'Sreedeep K S (AEI)', 'Abhijith V J', 'Abinav U A', 'Aswin M', 'Niya Mariam Benoy', 'Rijohn K Pius', 'Sarath Sojan', 'Sanjith S Kumar'])),
    ('IBM selects Navaneeth S. Nair at ₹11 lakh a year', '2022-07-01 10:00:00', '',
     'IBM offered an annual salary of ₹11 lakh to Navaneeth S. Nair (AEI).', ''),
    ('Adobe selects Arshaly Jose', '2017-07-01 10:00:00', UP + '2020/01/photoarsh.jpg',
     'Adobe Systems India offered a position to Arshaly Jose (ECE). [confirm the package: the old page gives ₹39 lakh in the heading and ₹20.3 lakh CTC in the text]', ''),
]


def slug(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower().replace('₹', '')).strip('-')[:80]


def main():
    add_to(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'playground', 'data', 'news.csv'))


def add_to(path):
    """Add the placement posts to a news.csv (posts already there by title are skipped)."""
    with open(path, encoding='utf-8') as fh:
        rows = list(csv.DictReader(fh))
        cols = list(rows[0].keys()) if rows else ['title', 'date', 'slug', 'category', 'featured_image_url', 'excerpt', 'content_html']
    have = {r['title'] for r in rows}
    added = 0
    for title, date, img, text, extra in POSTS:
        if title in have:
            continue
        img = full(img) if img and re.search(r'-\d{2,4}x\d{2,4}\.\w+$', img) and ('150x150' in img or '300x300' in img) else img
        rows.append({'title': title, 'date': date, 'slug': slug(title), 'category': 'placements', 'featured_image_url': img,
                     'excerpt': re.sub(r'\s*\[[^\]]*\]', '', text).strip() or title, 'content_html': '<p>%s</p>%s' % (text, extra)})
        added += 1
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print('added %d placement posts to %s (%d news rows in all)' % (added, path, len(rows)))


if __name__ == '__main__':
    main()
