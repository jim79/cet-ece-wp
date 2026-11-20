# ECE CET website

WordPress theme and plugin for the Department of Electronics and Communication Engineering, College of Engineering Trivandrum.

## Try it in your browser

**[Open the demo in WordPress Playground](https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/jim79/cet-ece-wp/main/playground/blueprint.json)**

The demo builds a complete site in your browser in about a minute: Secure Custom Fields, the plugin, the theme, all pages, and sample faculty, labs, batches, publications and news. You are logged in as an administrator, so you can open the dashboard and edit anything. Changes stay in your browser tab and disappear when you close it; nothing is saved to any server. Faculty names, publications and figures in the demo are invented, and a banner on every page says so.

## Repository layout

| Folder | Contents |
|---|---|
| `cet-ece/` | The theme (source). |
| `cet-ece-core/` | The plugin (source). |
| `dist/` | Installable zips of both. Upload these in WordPress. |
| `playground/` | Playground blueprint, demo sample content and the demo banner. |
| `tools/` | Template and pattern generator, block markup validator, build script, blueprint generator. |

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

On first activation the theme creates the site's pages (Home, About, Academics and the eight programme pages, OBE, Research, Publications, Placements, Students, Library, Staff advisors, Technical staff, Contact, News and Events). It sets Home as the homepage and News and Events as the posts page, adds the news categories (Announcements, Department news, Workshops and FDPs, Talks, Outreach) and switches permalinks to `/page-name/`. Pages that already exist with the same address are left alone.

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

## Yearly check (one person, about an hour)

1. Dashboard › Updates: confirm updates are running.
2. Restore a backup to a test copy once, to prove backups work.
3. Check every section has a named owner.
4. Review placeholders: search the site for "[".

## Changing the design

Colours: `cet-ece/assets/css/theme.css` (light and dark sets at the top). Sizes and spacing: `cet-ece/theme.json`. Page layouts: `cet-ece/patterns/`. The block markup is generated by a script and validated against WordPress's own parser before release.
