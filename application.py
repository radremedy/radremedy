from remedy.radremedy import create_app


if __name__ == '__main__':
    application, manager = create_app('remedy.config.ProductionConfig')

    application.run(host='0.0.0.0', debug=True)

