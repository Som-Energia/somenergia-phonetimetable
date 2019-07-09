#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tomatic.api import app, pbx, startCallInfoWS
import click
import dbconfig
from consolemsg import warn, step
from tomatic import __version__

@click.command()
@click.help_option()
@click.version_option(__version__)

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
        from tomatic.pbxasterisk import PbxAsterisk
        pbx(PbxAsterisk(
            dbconfig.tomatic.storagepath,
            *dbconfig.tomatic.dbasterisk.args,
            **dbconfig.tomatic.dbasterisk.kwds))

    if printrules:
        for rule in app.url_map.iter_rules():
            print rule

    step("Starting WS thread")
    wsthread = startCallInfoWS(app)
    step("Starting API")
    app.run(debug=debug, host=host, port=port, processes=1)
    step("API stopped")
    app.wserver.server_close()
    wsthread.join(0)
    step("WS thread stopped")

if __name__=='__main__':
    main()

