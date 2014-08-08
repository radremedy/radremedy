from remedy.radremedy import create_app


if __name__ == '__main__':
    application, manager = create_app('remedy.config.ProductionConfig')

    application.run()
