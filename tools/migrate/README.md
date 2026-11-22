# Moving content from the old site

Three steps: convert, review, import. The scripts do the bulk work; people check the data in a spreadsheet before anything reaches the new site.

## 1. Convert

No login to the old site is needed. The script reads the public website:

```
pip install beautifulsoup4 lxml
python3 tools/migrate/convert_old_site.py --site https://ece.cet.ac.in --out migration
```

It downloads the Faculty, Technical staff, Staff advisors, Laboratories and Publications pages, every page from the site's public pages feed (faculty profiles, lab pages, OBE, Programs, Research overview, Placements), and every news post from the public posts feed. Copies of what it read are kept in `migration/source/` (the pages feed in `migration/source/api/pages.json`). To convert again later without downloading, use `--pages migration/source/`.

Other inputs, if they are easier:

- `--export old-site.xml`: the WordPress export from the old site's dashboard (Tools › Export › All content), if someone with a login can provide it.
- `--pages folder/`: the five pages saved from a browser (File › Save page as, "HTML only") as `faculty-2.html`, `technical-staff.html`, `staff-advisors.html`, `laboratories.html` and `publications.html`. This gives no news, and no profile or lab details unless the folder also has `api/pages.json`.

This writes to `migration/`:

| File | From the old page | Notes |
|---|---|---|
| `faculty.csv` | Faculty, and each person's profile page | Designation mapped to Professor, Associate or Assistant (ad hoc counts as Assistant). Joining year, email, room, specialisation, suggested research areas, qualifications, courses, Google Scholar, ORCID and Scopus links, approved Ph.D. guide, an "about" text (experience, achievements, responsibilities, memberships, teaching innovations) and the full-size photo. Phone numbers are left out on purpose. |
| `staff.csv` | Technical staff | Name and designation. The `lab` column is filled from the lab pages. |
| `batches.csv` | Staff advisors | Programme, admission year, batch letter, advisor names. Graduated batches are kept; the site files them under past batches. |
| `labs.csv` | Laboratories, and each lab's page | Name, teaching or research, programmes, a summary taken from the course aims, lab in charge, technical staff, courses (code, name, programme, semester), research scholars, photos, the lab manual, and the page text (course aims, experiment lists, research areas, links to every manual). Labs listed in both UG and PG are merged. |
| `publications.csv` | Recent publications | Split into authors, title, venue, year, volume, pages and DOI. Duplicates merged. Shared conference DOIs removed. `confidence` shows how cleanly each entry split. |
| `news.csv` | All posts | Title, date, new category, image link, text. |
| `sections.csv` | OBE, Programs, Research overview, Placements | Changes to the new site's department pages: OBE committees, head of department, programme coordinators, scheme and syllabus links for each programme, academic calendars and newsletters (Downloads), research guides and their areas (Ph.D.), placement details and the 2025 recruiters. |
| `warnings.csv` | | Every row that needs a person to look at it, with the reason. |

## 2. Review

Open the CSVs in Excel or Google Sheets. Work through `warnings.csv` first. Typical fixes:

- replace personal Gmail addresses with `@cet.ac.in` ones;
- fill in missing emails and joining years;
- check the suggested research areas (separate several with `;`);
- for labs: set teaching or research, programmes (`btech-ece; btech-aei; mtech; phd`), the lab in charge (a faculty name exactly as in `faculty.csv`) and a one-line summary;
- for publications with `confidence` low: split them by hand; replace removed DOIs with each paper's own DOI;
- publications marked "No authors on the old page": the old page listed only the title under a faculty heading, so add the author list;
- publication headings "Not on the current faculty page": usually former faculty. Their papers still import, without a link to a profile. Decide whether to keep them, or add those people as faculty first. Headings with a different spelling of a current name (for example "Monterio") are matched to that name and listed for checking.

Multi-line cells (qualifications, courses, scholars, about, content) hold one item per line:

- `qualifications`: `degree | specialisation | institution | year`, for example `M.Tech | Signal Processing | CUSAT | 2010`
- `courses` (faculty): `code | name`, or just the name; (labs): `code | name | programme | semester`
- `scholars`: `name | phd or mtech | guide (a faculty name) | topic | ongoing or completed`

Formatted text (`about`, `content`, and `content` in `sections.csv`): a line starting with `## ` is a heading, `- ` a bullet, `1. ` a numbered item, `| a | b |` a table row (the first row is the header); leave a blank line between paragraphs; write links as `[label](https://...)`.

In `sections.csv`, `action` is `replace_section` (replace what is under the heading named in `target`), `add_section` (add a new heading and content at the end of the page) or `replace_text` (replace the exact text in `target`, such as `[Faculty name]`). `page` is the page address on the new site, for example `academics/obe`.

Keep the column headings. Save each sheet as CSV (UTF-8).

## 3. Import

On the new site, with the CET ECE Core plugin and Secure Custom Fields active, go to **Tools › ECE import**. Import in this order: Faculty, Technical staff, Labs, Staff advisor batches, Publications, News, Department pages. Run each with **Dry run** ticked first, read the result, then run it for real.

Photos, lab manuals, the syllabus, calendar, newsletter and placement PDFs, and the pictures inside news posts are copied from the old site into the media library, and links to them are rewritten, so the new site does not depend on the old one. Each file is copied once: importing again reuses it. Copying hundreds of files takes a while. If the import screen stops before showing a result, run the same import again: it continues where it stopped. On the command line there is no time limit.

Or, with command-line access to the server:

```
wp ece import faculty      migration/faculty.csv      --dry-run
wp ece import faculty      migration/faculty.csv      --report=reports/faculty.csv
wp ece import staff        migration/staff.csv
wp ece import labs         migration/labs.csv
wp ece import batches      migration/batches.csv
wp ece import publications migration/publications.csv
wp ece import news         migration/news.csv
wp ece import sections     migration/sections.csv
```

Rows are matched by name (Dr., Prof. and punctuation are ignored), so importing a corrected file again updates entries instead of duplicating them. A faculty "about" text or a lab page text that someone has edited on the new site since the last import is kept, not overwritten; the report says so. Photos get alt text ("Photo of …").

## After the import

Faculty members check their own profiles: qualifications (the old pages wrote them in many styles), research areas, courses and the "About" text. Add Scopus links and selected publications; few old profiles had them. Profiles of people who are no longer on the faculty list are not imported: `warnings.csv` lists them.

The theme's own pages already carry the department's vision, mission, programme outcomes, PEOs and PSOs for every programme, accreditation history, milestones, library and directions, taken from the old site. Check the remaining [brackets].

## Privacy

The `migration/` folder holds staff names and emails. It is listed in `.gitignore`: keep it out of the public repository.
