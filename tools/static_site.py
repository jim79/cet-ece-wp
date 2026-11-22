"""Helpers for tools/build_static.sh, which makes the static copy of the site.

  python3 tools/static_site.py blueprint <file> [--local]   write the Playground blueprint
  python3 tools/static_site.py urls <base>                  list every page from the sitemap
  python3 tools/static_site.py fix <dir> <base> <public>    tidy the crawled files

Standard library only, so it runs on a bare CI machine.
"""
import json
import os
import re
import shutil
import sys
import urllib.request


def blueprint(path, local):
    steps = []
    if local:
        # WordPress and Secure Custom Fields already unpacked (see build_static.sh, WP_DIR).
        steps.append({'step': 'activatePlugin', 'pluginPath': 'secure-custom-fields/secure-custom-fields.php'})
    else:
        steps.append({'step': 'installPlugin', 'pluginData': {'resource': 'wordpress.org/plugins', 'slug': 'secure-custom-fields'}})
    steps += [
        {'step': 'activatePlugin', 'pluginPath': 'cet-ece-core/cet-ece-core.php'},
        {'step': 'activateTheme', 'themeFolderName': 'cet-ece'},
        {'step': 'mkdir', 'path': '/wordpress/wp-content/mu-plugins'},
        {'step': 'runPHP', 'code': "<?php copy( '/demo/demo-banner.php', '/wordpress/wp-content/mu-plugins/demo-banner.php' );"},
        {'step': 'runPHP', 'code': "<?php require_once '/wordpress/wp-load.php'; require '/demo/seed.php';"},
    ]
    bp = {
        '$schema': 'https://playground.wordpress.net/blueprint-schema.json',
        'preferredVersions': {'php': '8.3', 'wp': 'latest'},
        'features': {'networking': True},
        'login': False,
        'siteOptions': {
            'blogname': 'Department of Electronics and Communication Engineering',
            'blogdescription': 'College of Engineering Trivandrum',
            'timezone_string': 'Asia/Kolkata',
        },
        'steps': steps,
    }
    with open(path, 'w') as fh:
        json.dump(bp, fh, indent=1)


def get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read().decode('utf-8', 'replace')


def urls(base):
    """Every page in WordPress's sitemap, except author pages."""
    out, todo, seen = [base + '/'], [base + '/wp-sitemap.xml'], set()
    while todo:
        u = todo.pop()
        if u in seen:
            continue
        seen.add(u)
        try:
            xml = get(u)
        except OSError as e:
            print('sitemap %s: %s' % (u, e), file=sys.stderr)
            continue
        for loc in re.findall(r'<loc>([^<]+)</loc>', xml):
            loc = loc.strip()
            if 'users' in loc.rsplit('/', 1)[-1]:
                continue
            (todo if loc.endswith('.xml') else out).append(loc)
    # The 404 page is fetched separately; feeds and the REST API are left out.
    print('\n'.join(dict.fromkeys(out)))


TEXT = ('.html', '.css', '.js', '.xml', '.json', '.txt', '.bib')
# Links to things a static copy cannot serve: the REST API, feeds, editing.
DEAD_LINKS = re.compile(r'<link[^>]+(?:wp-json|xmlrpc\.php|/feed/|oembed|EditURI|wlwmanifest)[^>]*>\s*', re.I)
# The header search box needs the server.
SEARCH = re.compile(r'<form[^>]*\bwp-block-search\b.*?</form>', re.I | re.S)


def fix(folder, base, public):
    public = public.rstrip('/')
    host = re.sub(r'^https?://', '', base)
    renames = {}
    for root, _, files in os.walk(folder):
        for f in files:
            # BibTeX download: give it a proper name.
            if 'ece_bibtex=1' in f:
                new = os.path.join(root, 'publications.bib')
                os.replace(os.path.join(root, f), new)
                renames[f] = 'publications.bib'
    for root, _, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            if not f.endswith(TEXT) and not f.endswith('.bib'):
                continue
            with open(path, encoding='utf-8', errors='surrogateescape') as fh:
                s = fh.read()
            orig = s
            for old, new in renames.items():
                s = s.replace(old, new).replace(old.replace('=', '%3D'), new)
            s = s.replace('http://' + host, public).replace('http:\\/\\/' + host.replace('/', '\\/'), public.replace('/', '\\/'))
            s = s.replace('//' + host, public.split(':', 1)[1])
            if f.endswith('.html'):
                s = DEAD_LINKS.sub('', s)
                s = SEARCH.sub('', s)
            if s != orig:
                with open(path, 'w', encoding='utf-8', errors='surrogateescape') as fh:
                    fh.write(s)
    # "theme.css@ver=1.0.css" is what wget saved for "theme.css?ver=1.0"; pages
    # that were not link-converted (the 404 page) ask for "theme.css".
    for root, _, files in os.walk(folder):
        for f in files:
            if '@' in f:
                plain = os.path.join(root, f.split('@', 1)[0])
                if not os.path.exists(plain):
                    shutil.copyfile(os.path.join(root, f), plain)
    open(os.path.join(folder, '.nojekyll'), 'w').close()


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'blueprint':
        blueprint(sys.argv[2], '--local' in sys.argv)
    elif cmd == 'urls':
        urls(sys.argv[2].rstrip('/'))
    elif cmd == 'fix':
        fix(sys.argv[2], sys.argv[3].rstrip('/'), sys.argv[4])
    else:
        sys.exit(__doc__)
