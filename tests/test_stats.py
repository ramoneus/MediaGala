"""The stats page: all-time totals, a single year, and the empty state."""

from datetime import date

from app import crud
from app.stats import build_report


def finished_movie(make_title, title, finished_on, rating=8, **fields):
    return make_title(title=title, status="watched", rating=rating, started_on=finished_on,
                      finished_on=finished_on, **fields)


def test_empty_collection(client):
    response = client.get("/stats")
    assert response.status_code == 200
    assert "Nothing to count yet." in response.text


def test_all_time_counts_progress_on_unfinished_titles(db, make_title):
    make_title(kind="series", title="Severance", year=2022, genre="Sci-Fi", status="watching",
               seasons=[9, 10], progress_season=2, progress_episode=3)
    make_title(kind="series", title="Dark", year=2017, genre="Mystery", status="watched", rating=9, seasons=[10, 8])
    make_title(kind="game", title="Hades", year=2020, genre="Action", status="watching", hours_played=30)
    make_title(kind="book", title="Dune", year=1965, genre="Sci-Fi", status="watching", pages=688, current_page=120)
    make_title(kind="book", title="Hail Mary", year=2021, genre="Sci-Fi", status="watched", rating=8, pages=476)

    report = build_report(crud.list_all_titles(db), None)
    assert report.finished == 2
    assert report.episodes == 12 + 18  # 9 + 3 watched, plus the whole finished series
    assert report.hours == 30
    assert report.pages == 120 + 476
    assert report.average_rating == 8.5


def test_a_year_counts_what_was_finished_that_year(client, make_title):
    finished_movie(make_title, "Inception", date(2026, 3, 1), rating=9, platform="Netflix")
    finished_movie(make_title, "Heat", date(2026, 3, 20), rating=7)
    finished_movie(make_title, "Parasite", date(2025, 11, 8), rating=10)
    make_title(title="Arrival")  # planned: never counted

    page = client.get("/stats?year=2026").text
    assert "Your 2026" in page
    assert '<a href="/stats?year=2025"' in page  # every year with a finish is a tab
    assert "<strong>2</strong>" in page  # finished
    assert "8.0<small>/10</small>" in page
    assert 'data-tip="Mar: 2 finished"' in page
    assert "Parasite" not in page


def test_all_time_charts_finishes_per_year(make_title, db):
    finished_movie(make_title, "A", date(2023, 5, 1))
    finished_movie(make_title, "B", date(2025, 5, 1))

    report = build_report(crud.list_all_titles(db), None)
    assert [(bar.label, bar.value) for bar in report.over_time.bars] == [("2023", 1), ("2024", 0), ("2025", 1)]


def test_bad_year_is_rejected(client):
    assert client.get("/stats?year=abc").status_code == 400


def test_fridge_links_to_stats(client):
    assert 'href="/stats"' in client.get("/").text
