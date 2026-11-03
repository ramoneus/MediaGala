"""The profile: your name and this year's goals, shown on the stats page."""

from datetime import date

from app import crud
from app.models import Profile
from app.stats import build_report


def test_profile_starts_empty(client):
    page = client.get("/profile").text
    assert "Your profile" in page
    assert 'name="goal_book"' in page


def test_save_profile(client, db):
    response = client.post("/profile", data={"name": " Maria ", "goal_book": "20", "goal_movie": "", "goal_game": "5"})
    assert response.status_code == 303
    assert response.headers["location"] == "/profile?msg=saved"

    profile = db.get(Profile, 1)
    assert (profile.name, profile.goals) == ("Maria", {"game": 5, "book": 20})

    page = client.get("/profile?msg=saved").text
    assert "Profile saved." in page
    assert 'value="Maria"' in page
    assert 'name="goal_book" value="20"' in page


def test_saving_again_replaces_the_profile(client, db):
    client.post("/profile", data={"name": "Maria", "goal_book": "20"})
    client.post("/profile", data={"name": "", "goal_movie": "10"})
    assert db.query(Profile).count() == 1
    profile = crud.get_profile(db)
    assert (profile.name, profile.goals) == ("", {"movie": 10})


def test_invalid_goals_keep_the_input_and_show_errors(client, db):
    response = client.post("/profile", data={"name": "Maria", "goal_book": "lots", "goal_movie": "0", "goal_game": "5000"})
    assert response.status_code == 422
    assert response.text.count("field-error") == 3
    assert 'value="Maria"' in response.text
    assert 'value="lots"' in response.text
    assert db.query(Profile).count() == 0


def test_name_too_long(client):
    assert client.post("/profile", data={"name": "x" * 41}).status_code == 422


def finish(make_title, title, kind, on, **fields):
    return make_title(kind=kind, title=title, status="watched", rating=8, started_on=on, finished_on=on, **fields)


def test_goals_count_what_was_finished_this_year(db, make_title):
    finish(make_title, "Heat", "movie", date(2026, 2, 1))
    finish(make_title, "Arrival", "movie", date(2026, 5, 1))
    finish(make_title, "Old one", "movie", date(2025, 12, 31))
    finish(make_title, "Dune", "book", date(2026, 3, 1), pages=500)
    make_title(title="Planned")

    report = build_report(crud.list_all_titles(db), None, "Maria", {"movie": 4, "book": 1}, today=date(2026, 8, 1))
    goals = {goal.label: (goal.done, goal.target, goal.percent, goal.reached) for goal in report.goals}
    assert goals == {"Movies": (2, 4, 50, False), "Books": (1, 1, 100, True)}
    assert report.goal_year == 2026


def test_goals_only_show_for_all_time_and_the_current_year(db, make_title):
    finish(make_title, "Heat", "movie", date(2025, 2, 1))
    finish(make_title, "Arrival", "movie", date(2026, 2, 1))
    titles = crud.list_all_titles(db)
    today = date(2026, 8, 1)
    assert build_report(titles, None, "", {"movie": 4}, today).goals
    assert build_report(titles, 2026, "", {"movie": 4}, today).goals
    assert not build_report(titles, 2025, "", {"movie": 4}, today).goals


def test_stats_page_shows_the_name_and_goals(client, make_title):
    year = date.today().year
    finish(make_title, "Heat", "movie", date(year, 1, 2))
    client.post("/profile", data={"name": "Chris", "goal_movie": "3"})

    page = client.get("/stats").text
    assert "Chris&#39; all time" in page
    assert f"Goals for {year}" in page
    assert "1 / 3" in page
    assert f"Chris&#39; {year}" in client.get(f"/stats?year={year}").text


def test_stats_page_without_a_profile(client, make_title):
    finish(make_title, "Heat", "movie", date(2025, 1, 2))
    page = client.get("/stats").text
    assert "<h1>All time</h1>" in page
    assert "Goals for" not in page
