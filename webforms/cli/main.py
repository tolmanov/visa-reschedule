import click


@click.group()
def cli():
    pass


@cli.command()
def scheduler():
    from webforms import settings
    from webforms.visa import main as schedule
    from logging.config import dictConfig
    click.echo('Initialized the scheduler')
    dictConfig(settings.logging)
    schedule()


if __name__ == '__main__':
    cli()
