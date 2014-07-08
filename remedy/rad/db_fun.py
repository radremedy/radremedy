from models import Resource, Category


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return False, instance
    else:
        instance = model(**kwargs)
        return True, instance


def add_get_or_create(database, model, **kwargs):
    new_record, record = get_or_create(database.session, model, **kwargs)
    database.session.add(record)

    return new_record, record


def get_or_create_resource(database, name, street=None, city=None, state=None, country=None,
                           zipcode=None, email=None, phone=None, fax=None, url=None,
                           description=None, source=None, category=None, visable=True, lazy=True):

    # TODO: there has got to be a better way to do this
    new_record, record = get_or_create(database.session, Resource, name=name)

    if new_record or not lazy:
        record.street = street
        record.city = city
        record.state = state
        record.country = country
        record.zipcode = zipcode
        record.email = email
        record.phone = phone
        record.fax = fax
        record.url = url
        record.description = description
        record.source = source
        record.visable = visable

        new_category, category_record = add_get_or_create(database, Category, name=category)

        record.category = category_record

        database.session.add(record)

    return new_record, record

