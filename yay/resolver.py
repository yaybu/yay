
class IResolvable(object):
    """ Something that we dont want to do until the Resolver().resolve() stage """
    #FIXME: There is a bit of conflation between resolver and actions that needs ironing out
    #FIXME: This is no longer an interface
    def __init__(self, current_value, action_data, **action_args):
        self.current_value = current_value
        self.action_data = action_data
        self.action_args = action_args

    def resolve(self, data):
        #FIXME: needs cycle detection
        while isinstance(self.current_value, IResolvable):
            self.current_value = self.current_value.resolve(data)

class Resolver(object):

    """ Run .format() on all strings in a dictionary, raises a ValueError on cycles """

    def __init__(self, raw):
        self._raw = raw

    def resolve_resolvable(self, resolvable):
        return resolvable.resolve(self._raw)

    def resolve_value(self, value, label=""):
        if isinstance(value, basestring):
            return self.resolve_string(value, label)
        elif isinstance(value, dict):
            return self.resolve_dict(value, label)
        elif isinstance(value, list):
            return self.resolve_list(value, label)
        elif isinstance(value, IResolvable):
            return self.resolve_resolvable(value)
        return value

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

