# ECE CET website

WordPress theme and plugin for the Department of Electronics and Communication Engineering, College of Engineering Trivandrum.

## Try it in your browser

**[Open the demo in WordPress Playground](https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/jim79/cet-ece-wp/main/playground/blueprint.json)**

The demo builds a complete site in your browser in a few minutes: Secure Custom Fields, the plugin, the theme, all pages, and the department's current content converted from ece.cet.ac.in: faculty profiles with photos, labs, technical staff, staff advisor batches, publications, news, OBE and programme pages. You are logged in as an administrator, so you can open the dashboard and edit anything. Changes stay in your browser tab and disappear when you close it; nothing is saved to any server. A banner on every page says it is a preview. The content has not been reviewed yet: see `migration/warnings.csv` after running the converter.

**[Open an empty import test site](https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/jim79/cet-ece-wp/main/playground/import-blueprint.json)**: the same theme and plugin with no sample content. It opens on Tools › ECE import, so you can upload the reviewed spreadsheets (see [tools/migrate/](tools/migrate/README.md)) and see the result. It also lives only in your browser tab.

## Static copy for everyone

**[ECE CET website preview](https://jim79.github.io/cet-ece-wp/)**: the same site as plain web pages on GitHub Pages. It opens instantly on any phone or computer, so it is the link to share for review. Nobody can log in or edit there.

It is rebuilt automatically on every push to `main` (`.github/workflows/pages.yml`, about 15 minutes), so it always matches the code and `playground/data/`. One-time setup: repository Settings › Pages › Source: **GitHub Actions**. Progress and errors show on the repository's Actions tab.

To build it yourself: `sh tools/build_static.sh _site` (needs Node 24 or later, wget and Python 3). The faculty, lab and publication filters work in the static copy; the header search box needs WordPress, so the copy leaves it out.

## Repository layout

| Folder | Contents |
|---|---|
| `cet-ece/` | The theme (source). |
| `cet-ece-core/` | The plugin (source). |
| `dist/` | Installable zips of both. Upload these in WordPress. |
| `playground/` | Playground blueprints, the demo banner, and `data/`: the converted content the demo loads, without phone numbers or personal email addresses (made by `tools/make_demo_data.py`). |
| `tools/` | Template and pattern generator, block markup validator, build script, blueprint generator, static copy builder (`build_static.sh`). |
| `tools/migrate/` | Converter from the old site to review spreadsheets, and the guide to importing them (Tools › ECE import, or `wp ece import`). |

To rebuild after changing the generator: `cd tools && npm install && cd .. && sh tools/build.sh`. Commit the updated `dist/` zips so the demo picks them up.

## About the theme and plugin

| Part | What it does |
|---|---|
| `cet-ece` (theme) | Design: colours, Inter font, light and dark mode, header, footer, page templates and page layouts. |
| `cet-ece-core` (plugin) | Content: Faculty, Labs, Staff advisor batches, Publications and Technical staff, their forms, and the blocks that list them. Also automatic updates, comment removal, image settings and redirects from old addresses. |

The content lives in the plugin, so a future theme change keeps every faculty profile, lab and publication.

## Requirements

- WordPress 6.8 or later (tested on 7.1.5), PHP 8.0 or later.
- **Secure Custom Fields** (free, from Plugins › Add New). It provides the repeater fields used for qualifications, courses, equipment and projects. ACF Pro also works. The free ACF plugin does not, because it has no repeater field.

## Install

1. Back up the current site (files and database).
2. Plugins › Add New: install and activate **Secure Custom Fields**.
3. Plugins › Add New › Upload: upload `cet-ece-core.zip`, then activate it.
4. Appearance › Themes › Add New › Upload: upload `cet-ece.zip`, then activate it.

On first activation the theme creates the site's pages (Home, About, Academics and the eight programme pages, OBE, Research, Publications, Placements, Students, Library, Staff advisors, Technical staff, Alumni, Downloads, Contact, Privacy, Accessibility, News and Events). It sets Home as the homepage and News and Events as the posts page, adds the news categories (Announcements, Department news, Student achievements, Placements, Workshops and FDPs, Talks, Outreach) and switches permalinks to `/page-name/`. Pages that already exist with the same address are left alone.

5. Settings › General: check the site title and tagline. Appearance › Editor › Site logo: upload the department logo.
6. In `wp-config.php`, add `define( 'DISALLOW_FILE_EDIT', true );` if it is not there. (The plugin sets it too.)

## Filling in content

Work through the [brackets] on each page: they mark facts to confirm or add (NBA status, PIN code, office hours, scheme years, PEOs and PSOs, placement figures, names).

| To add | Go to | Appears on |
|---|---|---|
| A faculty member | Faculty › Add | Faculty directory, their profile, lab pages, staff advisor tables |
| A lab | Labs › Add, choose Teaching or Research | Laboratories page, programme pages, Research page |
| A staff advisor batch | Staff advisors › Add batch | Staff advisors page; moves to Past batches after graduation |
| A publication | Publications › Add | Publications page, Research page, faculty profiles, BibTeX download |
| Technical staff | Technical staff › Add | Technical staff page, lab pages |
| News or an announcement | Posts › Add, pick a category | Homepage, News and Events, Students (announcements) |
| An achievement or placement poster | Posts › Add, category *Student achievements* or *Placements*, poster as the featured image | Homepage poster strip, Students (achievements), Placements (recent placements), News and Events |

Posters: always write the essentials as text in the post (name, batch, award or company, date). Text inside an image cannot be searched, read by screen readers, or read easily on a phone. Posters are shown whole, never cropped, and old ones move to the archive on their own.

Rules built into the forms:

- Faculty email must end in `@cet.ac.in`. There is no personal phone field.
- A faculty photo cannot be saved without alternative text.
- DOIs are checked and stored without the `https://doi.org/` prefix.
- Batch titles are generated, e.g. "B.Tech ECE 2026 A".
- Ad hoc appointments are entered as Assistant Professor.

Lab pages: the Programme box in the sidebar decides which programme pages list the lab. Research areas (sidebar) link faculty, labs and publications to the research area pages.

## Built-in behaviour

- WordPress, plugins and themes update automatically. Keep daily off-site backups at the host.
- Comments and XML-RPC are off. The WordPress version is hidden. User names are not exposed.
- JPEG and PNG uploads are saved as WebP where the server supports it; images larger than 2000 px are scaled down.
- Old addresses redirect: `/faculty-2/` → `/faculty/`, `/placements-latest/` → `/placements/`, `/research-overview/` → `/research/`, `/publications/` → `/research/publications/`, `/activities/` → `/news/`, `/laboratories/` → `/labs/`, `/golden-jubilee-celebrations/` → `/about/`, `/obe/` → `/academics/obe/`, `/programs/` → `/academics/`.
- Dark mode follows the visitor's device setting.
- Every page has a meta description and a sharing preview (title, description, image) for WhatsApp, Facebook and LinkedIn. The homepage carries organisation data for search engines. If an SEO plugin is installed later, these step aside.
- WordPress's built-in sitemap lists every page, faculty profile and lab at `/wp-sitemap.xml`. Submit it in Google Search Console.

## Recommended extra

- **Two Factor** (free, by WordPress contributors): turn on two-step login for every administrator account.

## Yearly check (one person, about an hour)

1. Dashboard › Updates: confirm updates are running.
2. Restore a backup to a test copy once, to prove backups work.
3. Check every section has a named owner.
4. Review placeholders: search the site for "[".

## Changing the design

Colours: `cet-ece/assets/css/theme.css` (light and dark sets at the top). Sizes and spacing: `cet-ece/theme.json`. Page layouts: `cet-ece/patterns/`. The block markup is generated by a script and validated against WordPress's own parser before release.
