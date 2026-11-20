# Moving content from the old site

Three steps: convert, review, import. The scripts do the bulk work; people check the data in a spreadsheet before anything reaches the new site.

## 1. Convert

No login to the old site is needed. The script reads the public website:

```
pip install beautifulsoup4 lxml
python3 tools/migrate/convert_old_site.py --site https://ece.cet.ac.in --out migration
```

It downloads the Faculty, Technical staff, Staff advisors, Laboratories and Publications pages, and every news post from the site's public posts feed. Copies of what it read are kept in `migration/source/`. To convert again later without downloading, use `--pages migration/source/`.

Other inputs, if they are easier:

- `--export old-site.xml`: the WordPress export from the old site's dashboard (Tools › Export › All content), if someone with a login can provide it.
- `--pages folder/`: the five pages saved from a browser (File › Save page as, "HTML only") as `faculty-2.html`, `technical-staff.html`, `staff-advisors.html`, `laboratories.html` and `publications.html`. This gives no news.

This writes to `migration/`:

| File | From the old page | Notes |
|---|---|---|
| `faculty.csv` | Faculty | Designation mapped to Professor, Associate or Assistant (ad hoc counts as Assistant). Joining year, email, specialisation, photo link, suggested research areas. Phone numbers are left out on purpose. |
| `staff.csv` | Technical staff | Name and designation. Add each person's lab in the `lab` column. |
| `batches.csv` | Staff advisors | Programme, admission year, batch letter, advisor names. Graduated batches are kept; the site files them under past batches. |
| `labs.csv` | Laboratories | Name, teaching or research, programmes. Labs listed in both UG and PG are merged. |
| `publications.csv` | Recent publications | Split into authors, title, venue, year, volume, pages and DOI. Duplicates merged. Shared conference DOIs removed. `confidence` shows how cleanly each entry split. |
| `news.csv` | All posts | Title, date, new category, image link, text. |
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

Keep the column headings. Save each sheet as CSV (UTF-8).

## 3. Import

On the new site, with the CET ECE Core plugin and Secure Custom Fields active, go to **Tools › ECE import**. Import in this order: Faculty, Technical staff, Labs, Staff advisor batches, Publications, News. Run each with **Dry run** ticked first, read the result, then run it for real.

Or, with command-line access to the server:

```
wp ece import faculty      migration/faculty.csv      --dry-run
wp ece import faculty      migration/faculty.csv      --report=reports/faculty.csv
wp ece import staff        migration/staff.csv
wp ece import labs         migration/labs.csv
wp ece import batches      migration/batches.csv
wp ece import publications migration/publications.csv
wp ece import news         migration/news.csv
```

Rows are matched by name (Dr., Prof. and punctuation are ignored), so importing a corrected file again updates entries instead of duplicating them. Photos and news images are downloaded from the old site, so run the import while the old site is still online. Each photo gets alt text ("Photo of …").

## After the import

Faculty members complete their own profiles: qualifications, Google Scholar, ORCID and Scopus links, research areas, courses and a short "About" paragraph. The old site did not hold these.

## Privacy

The `migration/` folder holds staff names and emails. It is listed in `.gitignore`: keep it out of the public repository.
