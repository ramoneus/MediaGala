<h1 align="center">🥛 MediaGala</h1>

<p align="center">
  One personal tracker for the movies, series, anime, games and books in your life.
</p>

<p align="center">
  <a href="#features">Features</a>
  ·
  <a href="#getting-started">Getting started</a>
  ·
  <a href="#architecture">Architecture</a>
  ·
  <a href="#security-and-validation">Security</a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.162-009688?logo=fastapi&logoColor=white">
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white">
  <img alt="Tested with pytest" src="https://img.shields.io/badge/tested_with-pytest-0A9EDC?logo=pytest&logoColor=white">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green">
</p>

<p align="center">
  <img src="docs/screenshots/home.png" alt="MediaGala home page: the fridge overview beside a shelf of covers">
</p>

## Overview

Most people keep a separate app for each kind of media: one for films, one for shows, one for games, one for books. MediaGala puts them in one collection. It remembers which episode you stopped at, which page you're on and how many hours you've played, and turns all of it into yearly stats.

It is a server-rendered web app built with **FastAPI**, **SQLAlchemy 2.0**, **SQLite** and **Jinja2**, and uses no JavaScript framework. Search fills in titles from free public APIs, so you don't need any API keys. The look is inspired by a milk carton, with light and dark themes.

## Features

**One collection for everything**
- Movies, series, anime, games and books live side by side, with a tab for each kind.
- Statuses fit each kind: *Watchlist / Watching / Watched* for series, *Backlog / Playing / Completed* for games, *To read / Reading / Read* for books, plus *Dropped*.
- The collection is a shelf of portrait covers. Titles without an image get a typeset cover in their kind's colour.
- The home page has **"The fridge"**: the overview is drawn as a fridge, with one magnet per status that filters the list. Open its door to see what you're in the middle of.

**Progress tracking**
- **Series and anime:** you set the episodes for each season, and seasons can be different lengths. Tick off episodes, or use the one-tap *✓ next episode* button. The app shows an *Up next* episode and a progress bar.
- **Books:** you record the author and the number of pages, and update the page you're on.
- **Games:** you record how far you got (*Story*, *Story + DLC*, *100%*) and how many hours you played.
- Finishing something asks for your rating. Starting a planned title records its start date.

**Adding titles in seconds**
- **Quick add:** search, then add a result to your watchlist in one click, with its cover and details. Results you already own are marked *In your fridge*.
- **Find it online:** the add form fills itself in from:

  | Kind   | Source                                                            |
  | ------ | ----------------------------------------------------------------- |
  | Series | TVmaze, including every season's episodes                         |
  | Anime  | AniList, including episodes                                       |
  | Movies | Wikipedia, or TMDB with an optional free key                      |
  | Games  | Wikipedia, so console games are found too                         |
  | Books  | Open Library, including the author and page count                 |

- Everything still works by hand when you're offline. You can also upload your own cover.

**A page for every title**
- A header with the cover, your status and rating, and a trailer link.
- **Your log:** where you watched, played or read it (Netflix, PS5, Kindle and so on), when you started and finished, and your notes.
- **Online details:** cast and crew, network, studio, developer and community rating. They are stored with the title, so the page loads instantly and works offline.

**Stats and goals**
- Shows stats for all time or for any single year: titles finished, episodes watched, hours played, pages read and your average rating.
- Charts by month, kind, genre and platform. Each chart can also be read as a table.
- Lists your top-rated titles, quickest finishes and longest games.
- Yearly goals for each kind, with a progress bar for each.

**Everyday use**
- Search by title or author, filter by kind, genre and status, and sort by title, year, rating or date added.
- Light and dark themes that follow your system setting, with no flash of the wrong theme.
- A responsive layout for desktop, tablet and mobile.

## Tech stack

| Layer       | Technology                                                    |
| ----------- | ------------------------------------------------------------- |
| Language    | Python 3.13                                                   |
| Web         | FastAPI, served by Uvicorn                                    |
| Database    | SQLite with the SQLAlchemy 2.0 ORM                            |
| Validation  | Pydantic v2                                                   |
| Frontend    | Jinja2 templates, HTML and CSS, and a small amount of plain JavaScript |
| HTTP client | httpx, for the online sources                                 |
| Images      | Pillow, for resizing and re-encoding                          |
| Testing     | pytest, 250 tests                                             |

## Architecture

- **One table for every kind.** All titles share a single `titles` table, so search, filters, sorting and images work the same way everywhere. A series also has a one-to-many list of `seasons`, with cascade delete.
- **The rules for each kind live in one place.** [`catalog.py`](app/catalog.py) defines each kind's statuses, labels, genres and features, such as `has_episodes` and `has_pages`. Validation, templates and the form's JavaScript all read from it. Adding anime took one configuration entry that reuses the series behaviour.
- **Episode progress is stored as a bookmark.** Episodes are watched in order, so the app keeps only the last watched season and episode. *Up next* and the progress percentage are simple calculations from that.
- **Online sources share one interface.** Each provider in [`app/lookup/`](app/lookup/) implements the same `search` and `details` functions, and each kind has a preferred order of sources. Details are stored as a small JSON list of facts, because every kind has different ones.
- **Older databases are upgraded on start-up.** New columns are added in place, so existing collections keep their data.

## Security and validation

- **Validation:** all input is checked with Pydantic before it reaches the database. Invalid forms come back with the user's input kept and an error on each field (HTTP 422).
- **Business rules:** each kind accepts only its own statuses and genres. A finished title needs a rating. A completed game must say how far it was played. Dates can't be in the future or in the wrong order. A database `CHECK` constraint enforces the rating range a second time.
- **SQL injection:** every query uses parameter binding, sort options come from a whitelist, and `LIKE` wildcards are escaped.
- **XSS:** Jinja2 autoescaping is on, and flash messages are chosen by key, never taken from user text.
- **Safe uploads:** the file type is detected from the file's bytes, and only JPG, PNG and WebP are accepted, with no SVG. The limit is 10 MB. Every image is resized to 800 px and re-encoded as WebP, which also strips metadata such as GPS location. Files are stored under random names.
- **SSRF:** online covers are downloaded only over HTTPS and only from the sources' own image hosts, and every redirect is checked.
- **Resubmission:** every create, update and delete ends in a `303` redirect (Post/Redirect/Get), so refreshing a page never submits a form twice.
- **Open redirects:** the *next episode* button only redirects back to paths inside the app.
- **Errors:** custom 400, 404 and 500 pages. Unexpected errors are logged and never shown to the user.

## Getting started

### Quick start (Windows)

Clone or download the project and **double-click `run.bat`**. The first run creates a virtual environment and installs the dependencies. The app then opens in your browser.

### Manual setup

You need Python 3.11 or newer.

```bash
git clone https://github.com/ramoneus/mediagala.git
cd mediagala

python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows (PowerShell)
source .venv/bin/activate         # macOS / Linux

pip install -r requirements.txt
python run.py                     # or: uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000**. The database is created automatically in `data/` the first time the app starts.

To fill an empty collection with examples, run `python -m app.seed`.

### Optional: TMDB for movies

Movies are looked up on Wikipedia by default. A free [TMDB](https://www.themoviedb.org/) key gives sharper posters and more accurate genres:

1. Create an account and request a personal API key under **Settings → API**.
2. Copy `.env.example` to `.env` and paste the key after `TMDB_API_KEY=`.
3. Restart the app.

`.env` is git-ignored, so the key never reaches GitHub.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The 250 pytest tests cover:
- the validation and business rules for each kind
- episode and reading progress
- every online source, with each service's answers faked so the tests run offline
- creating, editing and deleting through the real web forms
- search, filters and sorting
- uploads
- stats
- database migrations
- the security checks above

Each test gets a fresh database in a temporary folder (`MEDIAGALA_DATA_DIR`), so running the tests never touches your own collection.

## Roadmap

- Import from Letterboxd, IMDb and Goodreads (CSV)
- Pagination for large collections
- An optional IGDB source for game covers and platforms
- User accounts, CSRF protection and Alembic migrations, before any public deployment

## Data sources

The online search uses free public services. Their data stays theirs, under their own terms.

| Kind             | Source                                                       | Terms                                                                                                                                  |
| ---------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| Series           | [TVmaze API](https://www.tvmaze.com/api)                     | [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/)                                                                            |
| Anime            | [AniList API](https://docs.anilist.co/)                      | [Terms of use](https://docs.anilist.co/guide/terms-of-use)                                                                             |
| Movies (with a key) | [TMDB API](https://developer.themoviedb.org/)             | [API terms](https://www.themoviedb.org/api-terms-of-use). This product uses the TMDB API but is not endorsed or certified by TMDB.       |
| Movies and games | [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/)  | Text under [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/); posters and covers are non-free images kept at low resolution |
| Books            | [Open Library API](https://openlibrary.org/developers/api)   | Open data                                                                                                                              |

MediaGala is a personal, non-commercial project.

## License

Released under the [MIT License](LICENSE).
