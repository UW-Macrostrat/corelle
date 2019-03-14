from click import group, argument, option, echo, style

@group()
def cli():
    pass

@cli.command(name='init')
@option('--drop', is_flag=True, default=False)
def init(drop=False):
    pass

