# Isle of Man: law history in git

The law of Isle of Man as a git history: one file per provision, one commit per law on the day it took effect, and the law that made each change as the commit's author. `git blame` names the law behind every paragraph; `git log` lists every change; picking a date gives the text in force that day.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

## What this repository holds

**Some law text, and a catalogue of every other Act.** Copyright in an Act of Tynwald ends 50 years after the end of the year it received Royal Assent (Copyright Act 1991 s 157(2)). So this repository holds the text of a few core Acts assented in 1975 or earlier, but only their provisions that no later instrument has amended: words put in by a later Act may still be in copyright. Provisions showing fine amounts are left out too, because the Acts' general notes say the amounts were raised by later Acts. Every other Act is listed only by its short title, citation and Royal Assent date. To read an Act in full, go to [legislation.gov.im](https://legislation.gov.im/).

| Folder | Act | Versions | History |
| --- | --- | ---: | --- |
| `criminal-code-1872/` | Criminal Code 1872 (AT 1 of 1872) | 1 | 41 provisions, the official revised edition as published on 2024-08-14 |
| `criminal-justice-1963/` | Criminal Justice Act 1963 (AT 3 of 1963) | 1 | 5 provisions, the official revised edition as published on 2021-05-06 |
| `evidence-1871/` | Evidence Act 1871 (AT 1 of 1871) | 1 | 24 provisions, the official revised edition as published on 2025-01-21 |
| `companies-1931/` | Companies Act 1931 (AT 2 of 1931) | 1 | 153 provisions, the official revised edition as published on 2026-01-02 |
| `constitution-1961/` | Isle of Man Constitution Act 1961 (AT 6 of 1961) | 1 | 3 provisions, the official revised edition as published on 2022-01-21 |
| `catalogue/` | Catalogue of Acts of Tynwald: short title, citation and Royal Assent date only | 524 | One version per Royal Assent day: 859 Acts from 1645 onward are listed, each added on the day it received Royal Assent |
| `legal-system/` | Legal system facts from Wikidata (CC0) | 2 | The island's inception date Wikidata records (10 May 1765), then the facts held on 30 October 2026. |

Each Act's commit message lists the provisions left out and why.

## Sources

The Act texts come from the official revised editions (PDF) of the Isle of Man Government, Attorney General's Chambers, published on [legislation.gov.im](https://legislation.gov.im/). Each version names the edition's address, its revision number and the sha256 of the file it was read from. Every provision was checked word for word against a second, independent reading of the same file.

The Royal Assent date and citation (for example `AT 8 of 1991`) of 548 catalogue entries come from the Acts' own front matter, the "Received Royal Assent" line of each Act's official PDF; only the date and citation were taken. The other Acts' short titles, citations and Royal Assent dates are facts from Wikipedia's [List of acts of Tynwald](https://en.wikipedia.org/wiki/List_of_acts_of_Tynwald); the official date replaces Wikipedia's wherever both exist (535 agreed, 4 differed). The list is incomplete, and only entries with a full Royal Assent date are used. No text of the list is reproduced. The Wikidata facts are from [Wikidata](https://www.wikidata.org/wiki/Q9676) (CC0).

## Dates

The revised editions state no "as at" date, so each Act has one version, "oldest version available", dated by the day that edition was published and credited to the publisher. The provisions kept have no amendment notes, so their words are as enacted; the Act's own law entry gives its Royal Assent and commencement dates. A catalogue entry is dated by the Act's Royal Assent date, not its commencement date, and is credited to a `catalogue-<date>` entry. The Wikidata facts are dated by the inception date Wikidata records, then by the retrieval date (30 October 2026). Dates before 1752 are given as the list gives them, without conversion between calendars.

## How it is checked

Every version is read back from git on the day it took effect and on the day before (`tools/check_repo.py`) and must match `corpus.json`; results are in `REPRODUCE.md`.

## What "author" means

The author of a commit is the law (or, for facts, the retrieval or the publisher) that made the change, with an e-mail address that cannot exist. The committer is always Lexifina.

## Limits

- **No history yet.** Each Act has a single version; amendments are not recorded, and amended, inserted and repealed provisions are not shown.
- **Part and group headings, general notes and endnotes** are not law text and are not in the files.
- **The catalogue** only grows as Acts are enacted; repeals are not recorded and long titles are not copied.
- Nothing here is an official record of the Acts.
