
class IAction(object):

    def run(self, current_value, action_data, *action_args):
        """ Given the current value of a parameter and some data, apply a transformation """
        pass


class Actions(object):

    def __init__(self):
        self.actions = {}
        for cls in IAction.__subclasses__():
            self.actions[cls.name] = cls()

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


class Append(IAction):
    """ Append some values to an existing list """

    name = "append"

    def run(self, current_value, action_data, *action_args):
        # FIXME: Ensure that current value is a list
        # FIXME: Ensure that action data is a list
        return current_value + action_data


class Remove(IAction):
    """ Remove a set of values from an existing list """

    name = "remove"

    def run(self, current_value, action_data, *action_args):
        # FIXME: Ensure action_data is a list or supports __contains__
        if current_value is None:
            return []
        return [x for x in current_value if x not in action_data]

