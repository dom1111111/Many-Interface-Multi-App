def flatten_generator(container:list|tuple|set):
    """Pass in a list, tuple, or set which can have any number of other lists/tuples/sets 
    or non container items within, as well as any arbitrary depth for further 
    nested containers, and get back a flattened iterable generator."""
    for item in container:
        if isinstance(item, (list, tuple, set)):
            yield from flatten_generator(item)
        else:
            yield item

def is_numbers(x):
    """Return true if item is an int or a float, or an iterable with only ints or floats"""
    try:
        for item in x:
            if not isinstance(item, (int, float)) or isinstance(item, bool):    # need to check for bool because it's a subclass of int
                return False
    except:
        if not isinstance(x, (int, float)) or isinstance(x, bool):
            return False
    return True
