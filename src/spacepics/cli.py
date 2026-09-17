import logging
from datetime import date

import click
from dotenv import load_dotenv

from . import pipeline, publish
from .sources import SOURCES, get_sources

source_opt = click.option("--source", "-s", "source_names", multiple=True, type=click.Choice(sorted(SOURCES)), help="Default: all sources")
day_opt = click.option("--day", type=click.DateTime(["%Y-%m-%d"]), default=None, help="UTC date; default today")


def _day(d) -> date:
    return d.date() if d else pipeline.today()


@click.group()
@click.option("--debug", is_flag=True)
def cli(debug: bool):
    load_dotenv()  # NASA_API_KEY for the api.nasa.gov sources; harmless when absent
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@cli.command()
@source_opt
@day_opt
def fetch(source_names, day):
    """Download raw feeds to data/feeds/ (network)."""
    pipeline.fetch(get_sources(source_names), _day(day))


@cli.command()
@source_opt
@day_opt
def extract(source_names, day):
    """Parse saved feeds into data/candidates/ (offline). Defaults to the latest saved feed."""
    pipeline.extract(get_sources(source_names), day.date() if day else None)


@cli.command()
@source_opt
@click.option("--limit", type=int, default=None, help="Max images per source")
def download(source_names, limit):
    """Download preview images into data/images/ (network, gitignored cache)."""
    pipeline.download(get_sources(source_names), limit)


@cli.command()
@source_opt
@day_opt
def pick(source_names, day):
    """Choose the image for a day (placeholder: seeded random) and record it in data/picks.jsonl."""
    p = pipeline.pick_random(get_sources(source_names), _day(day))
    click.echo(f"{p.day}: {p.candidate.key}  {p.candidate.image_url}")


@cli.command("publish")
@day_opt
def publish_cmd(day):
    """Write Jekyll posts (and copy images) into site/ for recorded picks."""
    for p in publish.publish(day.date() if day else None):
        click.echo(p)


@cli.command()
@source_opt
def debug_pages(source_names):
    """Write per-source, per-instrument candidate galleries to site/debug/ (plain HTML)."""
    for p in publish.write_debug_galleries(get_sources(source_names)):
        click.echo(p)


@cli.command("pipeline")
@source_opt
@day_opt
@click.pass_context
def pipeline_cmd(ctx, source_names, day):
    """fetch -> extract -> pick -> publish -> debug-pages, for the daily job."""
    sources = get_sources(source_names)
    d = _day(day)
    pipeline.fetch(sources, d)
    pipeline.extract(sources, d)
    pipeline.pick_random(sources, d)
    publish.publish(d)
    publish.write_debug_galleries(sources)
