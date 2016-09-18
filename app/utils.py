import boto3


def l_search(l, k, v):
    result = [element for element in l if element[k] == v]
    if len(result) == 0:
        return None
    else:
        return result[0]


def l_contains(l, k, v):
    if l_search(l, k, v) is None:
        return False
    else:
        return True


def has_key_chain(d, *args):
    c = d
    for count, k in enumerate(args):
        if c.has_key(k):
            c = c[k]
        else:
            return False
    return True
