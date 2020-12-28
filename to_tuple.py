def to_tuple(lst):
    return tuple(to_tuple(i) if isinstance(i, list) else i for i in lst)
