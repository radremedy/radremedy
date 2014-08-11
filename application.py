
from remedy.radremedy import create_app

application, manager = create_app('remedy.config.ProductionConfig')
application.debug = True
if __name__ == '__main__':

    application.run(host='0.0.0.0', debug=True)

