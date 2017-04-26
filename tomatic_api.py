#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tomatic.api import app, pbx
from tomatic.pbxasterisk import PbxAsterisk
import click
import dbconfig
from consolemsg import warn

@click.command()
@click.help_option()

@click.option('--fake',
    is_flag=True,
    help="Use the true pbx instead the fake one",
    )
@click.option('--debug',
    is_flag=True,
    help="Runs in debug mode",
    )
@click.option('--host', '-h',
    default='0.0.0.0',
    help="The address to listen to",
    )
@click.option('--port', '-p',
    type=int,
    default=4555,
    help="The port to listen to",
    )
@click.option('--printrules',
    is_flag=True,
    help="Prints the url patterns being serverd",
    )
def main(fake, debug, host, port, printrules):
    "Runs the Tomatic web and API"
    print fake, debug, host, port, printrules
    if fake:
        warn("Using fake pbx")
    else:
        warn("Using real pbx")
        pbx(PbxAsterisk(
            dbconfig.tomatic.storagepath,
            *dbconfig.tomatic.dbasterisk.args,
            **dbconfig.tomatic.dbasterisk.kwds))

    if printrules:
        for rule in app.url_map.iter_rules():
            print rule

    app.run(debug=debug, host=host, port=port, processes=1)

if __name__=='__main__':
    main()

