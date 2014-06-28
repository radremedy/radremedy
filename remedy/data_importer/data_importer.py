from toolz import unique, partial
import csv

# force python lazy functions to act
force = list


def open_csv(file_path, skip_head=True):

    f = csv.reader(open(file_path, 'r'))

    if skip_head:
        next(f)

    return f


def open_dict_csv(file_path):

    return csv.DictReader(open(file_path, 'r'))


def minus_key(d, k):
    d.pop(k)
    return d


def unique_from_column(n, columns):

    return unique([row[n] for row in columns])

zeroth = partial(unique_from_column, 0)
firsts = partial(unique_from_column, 1)
seconds = partial(unique_from_column, 2)
thirds = partial(unique_from_column, 3)
fourths = partial(unique_from_column, 4)
fifths = partial(unique_from_column, 5)
sixths = partial(unique_from_column, 6)
sevenths = partial(unique_from_column, 7)
eighths = partial(unique_from_column, 8)
ninths = partial(unique_from_column, 9)


