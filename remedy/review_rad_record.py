from rad.models import Resource
from radrecord import RadRecord
from functools import partial

instance_variables = partial(filter, lambda a: not a.startswith('_') or a == 'id')
columns = lambda m: set(instance_variables(m.__dict__))


def analyse(source):

    def diff(c1, c2):
        d = columns(c1) - columns(c2)

        if len(d) > 0:
            print('{} could learn from {}. It doesn\'t contain {}'.format(
                c2, c1, d))

    diff(RadRecord, source)
    diff(source, RadRecord)

analyse(Resource)


