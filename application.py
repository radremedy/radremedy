#!/usr/bin/env python
from remedy.radremedy import create_app
import sys

# without this some imports from inside the app
# do not work
sys.path.append("remedy")

application, manager = create_app('remedy.config.ProductionConfig')
application.debug = True

if __name__ == '__main__':

    manager.run()

