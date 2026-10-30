# How this repository was made (Isle of Man)

This file is written by the build on 2026-10-30, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| legislation.gov.im: Acts of Tynwald PDFs (front matter: citation and Received Royal Assent date), read from Internet Archive copies | <https://legislation.gov.im/> | 2026-10-30 | Facts only (citation, Royal Assent date); no Act text is reproduced. |
| Wikipedia: List of acts of Tynwald | <https://en.wikipedia.org/wiki/List_of_acts_of_Tynwald> | 2026-10-30 | Facts only (short title, citation, Royal Assent date); the list text is CC BY-SA 4.0 and is not reproduced |
| Wikidata | <https://www.wikidata.org/wiki/Q9676> | 2026-10-30 | CC0 1.0 |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| `catalogue` | Catalogue of Acts of Tynwald (titles, citations and Royal Assent dates only) | 524 | 1645-06-25 to 2026-04-21 |
| `legal-system` | Isle of Man: legal system facts (Wikidata) | 2 | 1765-05-10 to 2026-10-30 |
| `criminal-code-1872` | Criminal Code 1872 | 1 | 2024-08-14 to 2024-08-14 |
| `criminal-justice-1963` | Criminal Justice Act 1963 | 1 | 2021-05-06 to 2021-05-06 |
| `evidence-1871` | Evidence Act 1871 | 1 | 2025-01-21 to 2025-01-21 |
| `companies-1931` | Companies Act 1931 | 1 | 2026-01-02 to 2026-01-02 |
| `constitution-1961` | Isle of Man Constitution Act 1961 | 1 | 2022-01-21 to 2022-01-21 |

The build made 531 commits:

| Commits | Kind |
| ---: | --- |
| 7 | first version of an act |
| 524 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `future`: laws not yet in force on 2026-10-30.
- 189 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 530 laws in the record.
- 1055 tags.

## Dates

Each commit is dated at noon (Europe/London) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: Catalogue entries are dated by the Act's Royal Assent date; they describe laws and are not law text. https://legislation.gov.im/

## How the history is built

`tools/build.py` turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/SCHEMA.md`.

- Corpus: sha256 `87a3813b0a7f95cb74f85fc7985a2625e33dcd9663c79489e3e5207009067076` (768171 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `a4faa25af85facb64b956b372f6b528aafdd7ec1`, `check.py` `3d00541d258745461ab52b1b0cb4e1716a27a95d`, `on.py` `644a6c0857fbcc72562032b58d57aa113fee0641`.
- Python 3.12.10; git version 2.46.0.windows.1.

## Checks

531 versions of 7 acts read back from git on the day each took effect and on the day before: 0 mismatches. Trailers: 0 commits whose trailers git cannot parse. Health: 0 merge commits on main, 0 commit dates that go backwards, 0 commits dated after the build.

No second build of this corpus has been compared yet.

## Decisions made by hand

- Law text is published only where Crown copyright has ended: Copyright Act 1991 s 157(2) limits copyright in an Act of Tynwald to 50 years from the end of the year of Royal Assent, so Acts assented in 1975 or earlier are free, except for words inserted by later instruments. Every other Act appears only in the catalogue.
- The catalogue holds facts only (short title, citation "AT n of YYYY", Royal Assent date). Long titles are descriptive text and are not copied.
- Royal Assent dates are taken from the "Received Royal Assent" line in the front of each Act’s own PDF matter on legislation.gov.im, read from Internet Archive copies; they replace the Wikipedia list’s date wherever both exist. Acts whose PDF is not archived keep the Wikipedia date.
- One version per Royal Assent date, credited to a catalogue-<date> entry; acts without a full Royal Assent date in the source list are left out.
- Wikidata facts (CC0) form the "legal-system" act: one version at the inception date Wikidata records, one at the retrieval date 2026-10-30.
- Not built: treaty actions (the Isle of Man is not itself a party; UK treaties are extended to it by declaration, and no open list was read in the time box).
- Criminal Code 1872: one version, the official revised edition as published on 2024-08-14 (the PDF states no 'as at' date, so it is dated by the day that copy was published); only provisions out of Crown copyright (Copyright Act 1991 s 157(2)) and with no endnote naming an instrument after 1975 are kept (41 kept, 81 left out).
- Criminal Justice Act 1963: one version, the official revised edition as published on 2021-05-06 (the PDF states no 'as at' date, so it is dated by the day that copy was published); only provisions out of Crown copyright (Copyright Act 1991 s 157(2)) and with no endnote naming an instrument after 1975 are kept (5 kept, 15 left out).
- Evidence Act 1871: one version, the official revised edition as published on 2025-01-21 (the PDF states no 'as at' date, so it is dated by the day that copy was published); only provisions out of Crown copyright (Copyright Act 1991 s 157(2)) and with no endnote naming an instrument after 1975 are kept (24 kept, 9 left out).
- Companies Act 1931: one version, the official revised edition as published on 2026-01-02 (the PDF states no 'as at' date, so it is dated by the day that copy was published); only provisions out of Crown copyright (Copyright Act 1991 s 157(2)) and with no endnote naming an instrument after 1975 are kept (153 kept, 166 left out).
- Isle of Man Constitution Act 1961: one version, the official revised edition as published on 2022-01-21 (the PDF states no 'as at' date, so it is dated by the day that copy was published); only provisions out of Crown copyright (Copyright Act 1991 s 157(2)) and with no endnote naming an instrument after 1975 are kept (3 kept, 4 left out).

## What AI did and did not do

The scripts that read the sources and build this repository were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- Claude Code with Claude Sonnet 5.5 wrote Lexifina's code and chose the sources; it did not write or alter any legal text. The code is deterministic and runs no model.
