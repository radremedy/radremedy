
from remedy.radremedy import create_app

application, manager = create_app('remedy.config.ProductionConfig')
application.debug = True

if __name__ == '__main__':

    manager.run()

