"""Write playground/blueprint.json for a given GitHub repo and branch.
Usage: python3 tools/make_blueprint.py owner/repo [branch]
"""
import json, sys, pathlib
repo = sys.argv[1] if len(sys.argv) > 1 else 'jim79/cet-ece-wp'
branch = sys.argv[2] if len(sys.argv) > 2 else 'main'
raw = f'https://raw.githubusercontent.com/{repo}/{branch}'
bp = {
    '$schema': 'https://playground.wordpress.net/blueprint-schema.json',
    'meta': {
        'title': 'ECE CET website demo',
        'description': 'Department of Electronics and Communication Engineering, College of Engineering Trivandrum: theme, plugin and sample content.',
        'author': repo.split('/')[0],
    },
    'landingPage': '/',
    'preferredVersions': {'php': '8.3', 'wp': 'latest'},
    'features': {'networking': True},
    'login': True,
    'siteOptions': {
        'blogname': 'Department of Electronics and Communication Engineering',
        'blogdescription': 'College of Engineering Trivandrum',
        'timezone_string': 'Asia/Kolkata',
    },
    'steps': [
        {'step': 'installPlugin', 'pluginData': {'resource': 'wordpress.org/plugins', 'slug': 'secure-custom-fields'}},
        {'step': 'installPlugin', 'pluginData': {'resource': 'url', 'url': f'{raw}/dist/cet-ece-core.zip'}},
        {'step': 'installTheme', 'themeData': {'resource': 'url', 'url': f'{raw}/dist/cet-ece.zip'}, 'options': {'activate': True}},
        {'step': 'mkdir', 'path': '/wordpress/wp-content/mu-plugins'},
        {'step': 'writeFile', 'path': '/wordpress/wp-content/mu-plugins/demo-banner.php', 'data': {'resource': 'url', 'url': f'{raw}/playground/demo-banner.php'}},
        {'step': 'mkdir', 'path': '/wordpress/wp-content/uploads/demo-posters'},
    ] + [
        {'step': 'writeFile', 'path': f'/wordpress/wp-content/uploads/demo-posters/{n}.jpg', 'data': {'resource': 'url', 'url': f'{raw}/playground/posters/{n}.jpg'}}
        for n in ('placement-1', 'placement-2', 'placement-3', 'achievement-1', 'achievement-2', 'achievement-3')
    ] + [
        {'step': 'writeFile', 'path': '/wordpress/demo-seed.php', 'data': {'resource': 'url', 'url': f'{raw}/playground/seed.php'}},
        {'step': 'runPHP', 'code': "<?php require_once '/wordpress/wp-load.php'; require '/wordpress/demo-seed.php';"},
    ],
}
out = pathlib.Path(__file__).resolve().parent.parent / 'playground' / 'blueprint.json'
out.write_text(json.dumps(bp, indent=2) + '\n')
print('https://playground.wordpress.net/?blueprint-url=' + f'{raw}/playground/blueprint.json')
