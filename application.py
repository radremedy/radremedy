#!/usr/bin/env python
from remedy.radremedy import create_app
from remedy.sitemap import create_sitemap

import os

application, manager = (None, None)

if os.environ.get('RAD_PRODUCTION'):
    print('Running production configuration')
    application, manager = create_app('remedy.config.ProductionConfig')
else:
    print('Running development configuration')
    application, manager = create_app('remedy.config.DevelopmentConfig')


@manager.command
def sitemap():
    """
    Generates a sitemap based on the current configuration.
    """
    create_sitemap(application)

if __name__ == '__main__':
    manager.run()
