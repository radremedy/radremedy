#!/usr/bin/env python
from remedy.radremedy import create_app

import os

application, manager = (None, None)

if os.environ.get('RAD_PRODUCTION'):
    print('Running production configuration')
    application, manager = create_app('remedy.config.ProductionConfig')
else:
    print('Running development configuration')
    application, manager = create_app('remedy.config.DevelopmentConfig')

if __name__ == '__main__':
    manager.run()
