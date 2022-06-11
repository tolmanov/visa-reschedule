import click
from webforms.visa import main as schedule


@click.group()
def cli():
    pass


@cli.command()
def scheduler():
    click.echo('Initialized the scheduler')
    schedule()


if __name__ == '__main__':
    cli()
