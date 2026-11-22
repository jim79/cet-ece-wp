"""Copy the converted spreadsheets into playground/data/ for the public demo.

Usage: python3 tools/make_demo_data.py [migration]

The demo shows the department's real content, as published on ece.cet.ac.in.
This copy leaves out what should not be in a public repository:
  - personal email addresses (only @cet.ac.in addresses are kept);
  - the staff advisor page's source lines, which carry phone numbers;
  - review-only columns (raw citations, old links, parser confidence).
It stops if any other cell still looks like a personal phone number.
"""
import csv
import os
import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else 'migration'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'playground', 'data')

DROP = {
    'faculty': ['designation_text', 'old_profile_url'],
    'batches': ['source_line'],
    'labs': ['old_url'],
    'publications': ['raw', 'confidence'],
    'news': ['old_id', 'old_categories', 'old_url'],
}
# Mobile numbers and landlines, except the department office.
PHONE = re.compile(r'(?<![\d-])(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)|\b0\d{2,4}[\s-]\d{6,8}\b')
OFFICE = {'0471-2515563'}


def main():
    os.makedirs(OUT, exist_ok=True)
    problems = []
    for name in ('faculty', 'staff', 'labs', 'batches', 'publications', 'news', 'sections'):
        path = os.path.join(SRC, name + '.csv')
        with open(path, encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
        cols = [c for c in (rows[0].keys() if rows else []) if c not in DROP.get(name, [])]
        for r in rows:
            if name == 'faculty' and not r.get('email', '').lower().endswith('@cet.ac.in'):
                r['email'] = ''
            for c in cols:
                for m in PHONE.findall(r.get(c) or ''):
                    if m not in OFFICE:
                        problems.append('%s.csv, %s: %s' % (name, c, m))
        with open(os.path.join(OUT, name + '.csv'), 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            w.writerows(rows)
        print('%-13s %4d rows' % (name, len(rows)))
    if problems:
        print('Phone numbers found, remove them before publishing:\n  ' + '\n  '.join(problems))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
