
import copy

class IAction(object):

    def run(self, mgr, current_value, action_data, *action_args):
        """ Given the current value of a parameter and some data, apply a transformation """
        pass


class Actions(object):

    def __init__(self, config):
        self.config = config
        self.actions = {}
        for cls in IAction.__subclasses__():
            self.actions[cls.name] = cls()

    def lookup(self, key):
        return self.config._raw.get(key, None)

    def run(self, action, current_value, action_data):
        if not action in self.actions:
            raise KeyError("'%s' is not a supported action" % action)
        return self.actions[action].run(self, current_value, action_data)


class Assign(IAction):
    """ Replace the current value with an entirely new one """

    name = "assign"

    def run(self, mgr, current_value, action_data, *action_args):
        """ Just return action_data to replace current value entirely """
        return action_data


class Append(IAction):
    """ Append some values to an existing list """

    name = "append"

    def run(self, mgr, current_value, action_data, *action_args):
        # FIXME: Ensure that current value is a list
        # FIXME: Ensure that action data is a list
        return current_value + action_data


class Remove(IAction):
    """ Remove a set of values from an existing list """

    name = "remove"

    def run(self, mgr, current_value, action_data, *action_args):
        # FIXME: Ensure action_data is a list or supports __contains__
        if current_value is None:
            return []
        return [x for x in current_value if x not in action_data]

class Copy(IAction):
    """ Inherit a section, copy a literal etc """

    name = "copy"

    def run(self, mgr, current_value, action_data, *action_args):
        # This is derived from string.py Formatter so lookup language
        # is consistent
        # field name parser is written in C and available as
        #   str._formatter_field_name_split()
        first, rest = action_data._formatter_field_name_split()
        obj = mgr.lookup(first)

        for is_attr, i in rest:
            if is_attr:
                obj = getattr(obj, i)
            else:
                obj = obj[i]

        return copy.deepcopy(obj)

