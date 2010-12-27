
import copy
from yay.resolver import IResolvable

class IAction(object):

    def run(self, current_value, action_data, *action_args):
        """ Given the current value of a parameter and some data, apply a transformation """
        pass


class ResolvableAction(IAction):
    """ I am an action that simply returns a Resolvable subclass (something that is delayed to the resolver runs) """

    resolvable = None

    def run(self, current_value, action_data, **action_args):
        return self.resolvable(current_value, action_data, **action_args) 


class Actions(object):

    def __init__(self, config):
        self.config = config
        self.actions = {}
        def find_subclasses(cls):
            for node in cls.__subclasses__():
                if not hasattr(node, "name"):
                    find_subclasses(node)
                    continue
                self.actions[node.name] = node()
        find_subclasses(IAction)

    def lookup(self, key):
        return self.config._raw.get(key, None)

    def run(self, action, current_value, action_data):
        if not action in self.actions:
            raise KeyError("'%s' is not a supported action" % action)
        return self.actions[action].run(current_value, action_data)


class Assign(IAction):
    """ Replace the current value with an entirely new one """

    name = "assign"

    def run(self, current_value, action_data, *action_args):
        """ Just return action_data to replace current value entirely """
        return action_data


class AppendResolver(IResolvable):
    """ Append some values to an existing list """

    def resolve(self, data):
        # FIXME: Ensure that current value is a list
        # FIXME: Ensure that action data is a list
        return self.current_value + self.action_data

class Append(ResolvableAction):

    name = "append"
    resolvable = AppendResolver


class RemoveResolver(IResolvable):
    """ Remove a set of values from an existing list """

    def resolve(self, data):
        # FIXME: Ensure action_data is a list or supports __contains__
        if self.current_value is None:
            return []
        return [x for x in self.current_value if x not in self.action_data]

class Remove(ResolvableAction):

    name = "remove"
    resolvable = RemoveResolver


class CopyResolver(IResolvable):

    def resolve(self, data):
        # Make sure full chain is resolved
        super(CopyResolver, self).resolve(data)

        # This is derived from string.py Formatter so lookup language
        # is consistent
        # field name parser is written in C and available as
        #   str._formatter_field_name_split()
        first, rest = self.action_data._formatter_field_name_split()
        obj = data[first]

        for is_attr, i in rest:
            if is_attr:
                obj = getattr(obj, i)
            else:
                obj = obj[i]

        return copy.deepcopy(obj)

class Copy(ResolvableAction):
    """ Inherit a section, copy a literal etc """

    name = "copy"
    resolvable = CopyResolver

