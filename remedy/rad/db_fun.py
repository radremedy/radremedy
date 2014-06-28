
def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return (False, instance)
    else:
        instance = model(**kwargs)
        return (True, instance)