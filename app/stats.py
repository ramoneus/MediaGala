"""The stats page: what you finished, how much of it, and how you rated it.

"All time" counts everything in the collection, including the episodes, pages and hours of
titles you're still on. A single year counts the titles you finished that year (by their
"finished" date), since only those can be placed in a year.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import date

from app.catalog import Kind, Status
from app.models import Title

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
TOP = 5  # rows in each "top" list


@dataclass(frozen=True)
class Bar:
    label: str
    value: int

    def percent_of(self, peak: int) -> int:
        """Length of the bar, as a percentage of the longest one."""
        return round(100 * self.value / peak) if peak else 0


@dataclass(frozen=True)
class Chart:
    bars: list[Bar]

    @property
    def peak(self) -> int:
        return max((bar.value for bar in self.bars), default=0)

    @property
    def is_empty(self) -> bool:
        return self.peak == 0


@dataclass(frozen=True)
class Goal:
    """How far along you are with this year's goal for one kind."""

    label: str
    done: int
    target: int

    @property
    def percent(self) -> int:
        return min(100, round(100 * self.done / self.target))

    @property
    def reached(self) -> bool:
        return self.done >= self.target


@dataclass(frozen=True)
class Report:
    name: str
    year: int | None  # None for all time
    years: list[int]  # every year something was finished, newest first
    finished: int
    episodes: int
    hours: int
    pages: int
    average_rating: float | None
    goal_year: int  # the year the goals are for: the current one
    goals: list[Goal]
    over_time: Chart  # finished per month (a year) or per year (all time)
    by_kind: Chart
    genres: Chart
    ratings: Chart  # how many titles got each score, 1 to 10
    platforms: Chart
    top_rated: list[Title]
    fastest: list[Title]
    longest_games: list[Title]


def _episodes(item: Title) -> int:
    # A series marked as watched counts in full, even if its episodes were never ticked off.
    return item.total_episodes if item.status == Status.FINISHED else item.watched_episodes


def _pages(item: Title) -> int:
    if item.status == Status.FINISHED:
        return item.pages or 0
    return item.current_page or 0


def _ranked(counts: Counter[str]) -> Chart:
    return Chart([Bar(label, value) for label, value in counts.most_common(TOP)])


def _goals(finished: list[Title], targets: dict[str, int], year: int) -> list[Goal]:
    this_year = Counter(t.kind for t in finished if t.finished_on and t.finished_on.year == year)
    return [Goal(kind.config.plural, this_year[kind], targets[kind.value]) for kind in Kind if kind.value in targets]


def build_report(
    titles: list[Title],
    year: int | None,
    name: str = "",
    targets: dict[str, int] | None = None,
    today: date | None = None,
) -> Report:
    """`targets` are the profile's goals for the current year, by kind ("book" -> 20)."""
    current_year = (today or date.today()).year
    finished = [t for t in titles if t.status == Status.FINISHED]
    years = sorted({t.finished_on.year for t in finished if t.finished_on}, reverse=True)

    if year is None:
        scope = titles  # progress on unfinished titles counts too
        done = finished
        per_year = Counter(t.finished_on.year for t in done if t.finished_on)
        span = range(min(per_year), max(per_year) + 1) if per_year else range(0)
        over_time = Chart([Bar(str(y), per_year[y]) for y in span])
    else:
        done = [t for t in finished if t.finished_on and t.finished_on.year == year]
        scope = done
        per_month = Counter(t.finished_on.month for t in done)
        over_time = Chart([Bar(name, per_month[month]) for month, name in enumerate(MONTHS, start=1)])

    rated = [t for t in done if t.rating is not None]
    kinds = Counter(t.kind for t in done)
    timed = [t for t in done if t.days_spent is not None]
    games = [t for t in scope if t.kind == Kind.GAME and t.hours_played]

    return Report(
        name=name,
        year=year,
        years=years,
        finished=len(done),
        episodes=sum(_episodes(t) for t in scope if t.kind.has_episodes),
        hours=sum(t.hours_played or 0 for t in scope if t.kind == Kind.GAME),
        pages=sum(_pages(t) for t in scope if t.kind.has_pages),
        average_rating=round(sum(t.rating for t in rated) / len(rated), 1) if rated else None,
        goal_year=current_year,
        # Goals are for this year, so they show on the all-time view and on this year's own tab.
        goals=_goals(finished, targets or {}, current_year) if year in (None, current_year) else [],
        over_time=over_time,
        by_kind=Chart(sorted((Bar(k.config.plural, kinds[k]) for k in Kind if kinds[k]), key=lambda b: -b.value)),
        genres=_ranked(Counter(t.genre for t in done)),
        ratings=Chart([Bar(str(score), sum(1 for t in rated if t.rating == score)) for score in range(1, 11)]),
        platforms=_ranked(Counter(t.platform for t in done if t.platform)),
        top_rated=sorted(rated, key=lambda t: (-t.rating, t.title.lower()))[:TOP],
        fastest=sorted(timed, key=lambda t: (t.days_spent, t.title.lower()))[:3],
        longest_games=sorted(games, key=lambda t: -t.hours_played)[:3],
    )
