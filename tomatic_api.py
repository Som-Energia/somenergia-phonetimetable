#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from tomatic.api import app, pbx
from tomatic.tomatic_websockets import WebSocketTomaticServer
import click
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
@click.option('--ring',
	is_flag=True,
	help="Listen incommings calls",
	)
def main(fake, debug, host, port, printrules, ring):
    "Runs the Tomatic web and API"
    print(fake, debug, host, port, printrules)
    if fake:
        warn("Using fake pbx")
    else:
        warn("Using real pbx")
        from tomatic.pbxasterisk import PbxAsterisk
        import dbconfig
        pbx(PbxAsterisk(
            dbconfig.tomatic.storagepath,
            *dbconfig.tomatic.dbasterisk.args,
            **dbconfig.tomatic.dbasterisk.kwds))

    if printrules:
        for rule in app.url_map.iter_rules():
            print(rule)

    if ring:
        step("Starting WS thread")
        app.websocket_kalinfo_server = WebSocketTomaticServer()
        app.websocket_kalinfo_server.startCallInfoWS(host=host)
    step("Starting API")
    for rule in app.url_map.iter_rules():
        step("- {}", rule)
    app.run(debug=debug, host=host, port=port, processes=1)
    step("API stopped")
    if ring:
        app.websocket_kalinfo_server.stopCallInfoWS()
        step("WS thread stopped")

if __name__=='__main__':
    main()

