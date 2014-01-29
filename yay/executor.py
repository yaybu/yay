from gevent import getcurrent, Greenlet, GreenletExit
from gevent.event import AsyncResult
from gevent.pool import Group

from yay import errors


class Yaylet(Greenlet):
    def _report_error(self, exc_info):
        """ Same as gevent.Greenlet, but doesnt insist on logging expected tracebacks to stderr """
        exception = exc_info[1]
        if isinstance(exception, GreenletExit):
            self._report_result(exception)
            return
        self._exception = exception

        if self._links and not self._notifier:
            self._notifier = self.parent.loop.run_callback(self._notify_links)


class YGroup(Group):
    greenlet_class = Yaylet


class PeekySection(object):

    def __init__(self, operation):
        self.operation = operation

    def __enter__(self):
        self.operation.peeky = True

    def __exit__(self, type, value, traceback):
        self.operation.peeky = False


class BaseOperation(object):

    def __init__(self):
        self.depends = []
        self.rdepends = []
        self.peeks = []
        self.peeky = False
        self.primary_parent = None

    def peek(self):
        return PeekySection(self)

    def purge_one(self):
        if self.id in self.monitor.operations:
            del self.monitor.operations[self.id]
        for dep in self.depends:
            if self in dep.rdepends:
                dep.rdepends.remove(self)
        for dep in self.rdepends:
            if self in dep.depends:
                dep.depends.remove(self)
            if dep.primary_parent == self:
                dep.primary_parent = None

    def purge_rdepends(self):
        rdepends = list(self.rdepends)
        self.purge_one()
        [d.purge_rdepends() for d in rdepends]

    def add_dependency(self, dep):
        # FIXME: Can has weakrefs or something?
        self.depends.append(dep)
        dep.rdepends.append(self)
        if self.peeky:
            self.peeks.append(dep)

    def walk_children(self):
        class Control:
            descend = True
            primary_only = True

        visited = []
        if True:  # primary_only:
            operations = list(c for c in self.depends if c.primary_parent == self)
        else:
            operations = list(self.depends)
        while operations:
            op = operations.pop(0)
            if op in visited:
                continue
            visited.append(op)
            control = Control()
            yield control, op
            if control.descend:
                if control.primary_only:
                    operations.extend((c for c in op.depends if c.primary_parent == op))
                else:
                    operations.extend(op.depends)

    def map(self, func, iterable):
        def _(obj):
            getcurrent().operation = self
            return func(obj)
        return YGroup().imap(_, iterable)

    def map_unordered(self, func, iterable):
        def _(obj):
            getcurrent().operation = self
            return func(obj)
        #return map(_, iterable)
        return YGroup().imap_unordered(_, iterable)


class RootOperation(BaseOperation):

    id = "<ROOT>"
    method = "get"

    def __repr__(self):
        return "Root.get()"

    def __hash__(self):
        return self.__repr__()


class Operation(BaseOperation):

    def __init__(self, monitor, callable, *args):
        super(Operation, self).__init__()

        self.monitor = monitor

        self.id = (callable, args)

        self.callable = callable
        self.args = args
        self.node = getattr(callable, "__self__", None)
        self.method = getattr(callable, "__name__", None)

        self.result = AsyncResult()

        self.primary_parent = self.monitor.get_current()
        self.primary_parent.add_dependency(self)

        self.greenlet = Yaylet(callable, *args)
        self.greenlet.operation = self
        self.greenlet.link(self._operation_finish)

    def start(self):
        self.greenlet.start()

    def ready(self):
        return self.result.ready()

    def get(self):
        return self.result.get()

    def _operation_finish(self, source):
        # WARNING: This method will be caused in it's own greenlet.
        # Using self.monitor.execute from here will cause work to be owned by Root

        # Cycle breaking
        source.operation = None

        # Setup the AsyncResult so *new* calls will return immediately
        # But let's not notify the existing blocked greenlets until we
        # have run the paradox detector
        if source.successful():
            self.result.value = source.value
            self.result._exception = None
        else:
            self.result.value = None
            self.result._exception = source.exception

        # Purge any operations that were cached during a peek operation
        checks = []

        for p in self.peeks:
            for c, op in p.walk_children():
                if op.method.startswith("as_"):
                    checks.append(op)
                op.purge_one()

            if p.method.startswith("as_"):
                checks.append(p)
            p.purge_one()

        getcurrent().operation = self

        for op in checks:
            current_val = op.get()
            new_val = self.monitor.wait(getattr(op.node, op.method))
            if new_val != current_val:
                self.result.set_exception(errors.ParadoxError(
                    "Inconsistent configuration detected - changed from %r to %r" % (current_val, new_val), anchor=op.node.anchor))
                getcurrent().operation = None
                return

        getcurrent().operation = None

        # Now notify all the other greenlets waiting for us that it is safe to continue
        if source.successful():
            self.result.set(source.value)
        else:
            self.result.set_exception(source.exception)

    def __repr__(self):
        return "%s<%s>.%s(%r)" % (self.node.__class__.__name__, id(self), self.method, self.args)


class Executor(object):

    """
    I run graph resolve operations in a greenlet and track dependencies between them.

    I record enough details that I can handle the following details:

      * Cycle detection
      * Purge and re-resolve
      * Peek-behind
      * Paradox detection

    I do not record sufficient information that I can replay chains, however.
    For example::

        self.get_key('foo').resolve()

    I would know that the current operation depends on ``get_key('foo')`` and a
    ``resolve`` but i would know that to replay the ``resolve`` i need to
    replay the ``get_key`` operation first.
    """

    def __init__(self):
        self.operations = {}
        self.root = RootOperation()

    def get_current(self):
        try:
            return getcurrent().operation
        except AttributeError:
            return self.root

    def get_operation(self, callable, *args):
        return self.operations[(callable, args)]

    def execute(self, callable, *args):
        id = (callable, args)

        try:
            op = self.get_operation(callable, *args)
        except KeyError:
            op = Operation(self, callable, *args)
            self.operations[id] = op
            op.start()
            return op

        c = p = self.get_current()

        if op.ready():
            p.add_dependency(op)
            return op

        while c.primary_parent is not None:
            if c != op:
                c = c.primary_parent
                continue

            if hasattr(op.node, "peek"):
                pr = op.node.peek()
                child = self.execute(getattr(pr, op.method), *args)
                return child

            op.result.set_exception(errors.CycleError(
                "A cyclic dependency was detected in your configration and processing cannot continue",
                anchor=op.node.anchor,
            ))
            return op

        p.add_dependency(op)
        return op

    def wait(self, callable, *args):
        child = self.execute(callable, *args)
        return child.get()

    def get_dia_graph(self):
        lines = ['graph network {']
        for op in self.operations.values():
            lines.append('%s [label="%s"];' % (id(op), repr(op)))
            for dep in op.depends:
                lines.append('%s -> %s;' % (id(op), id(dep)))
        lines.append('}')
        return '\n'.join(lines)
