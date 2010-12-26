
class Resolver(object):

    """ Run .format() on all strings in a dictionary, raises a ValueError on cycles """

    def __init__(self, raw):
        self._raw = raw

    def resolve_value(self, value, label=""):
        if isinstance(value, basestring):
            return self.resolve_string(value, label)
        elif isinstance(value, dict):
            return self.resolve_dict(value, label)
        elif isinstance(value, list):
            return self.resolve_list(value, label)

    def resolve_string(self, value, label=""):
        encountered = set()
        previous = None
        while value != previous:
            if value in encountered:
                raise ValueError("Cycle encountered (%s)" % label)
            encountered.add(value)

            previous = value
            value = value.format(**self._raw)

        return value

    def resolve_list(self, lst, label=""):
        new_lst = []
        for i, item in enumerate(lst):
            new_lst.append(self.resolve_value(item, "%s[%s]" % (label,i)))
        return new_lst

    def resolve_dict(self, dct, label=""):
        new_dct = {}
        for key, value in dct.iteritems():
            key_label = label + "." + key if label else key
            new_dct[key] = self.resolve_value(value, key_label)
        return new_dct

    def resolve(self):
        return self.resolve_dict(self._raw)

