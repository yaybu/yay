
import urllib

class IOpener(object):

    def open(self, uri):
        """ Given a uri, return a YAML compatible stream """
        pass


class FileOpener(IOpener):

    scheme = "file://"

    def open(self, uri):
        if uri.startswith("file://"):
            uri = uri[8:]
        return open(uri, "r")


class UrlOpener(IOpener):

    scheme = "http://"

    def open(self, uri):
        return urllib.urlopen(uri)


class MemOpener(IOpener):

    """ 
    This is purely a testing stub.

    It has a class-shared dictionary called 'data', where keys are uris and
    values are data to return as a StringIO when open() is called. This means
    test cases can exercise the yay extends machinery without the need to create
    temporary files
    """

    scheme = "mem://"
    data = {}

    def open(self, uri):
        return StringIO.StringIO(data[uri])

    @classmethod
    def add(cls, uri, data):
        cls.data[uri] = data

    @classmethod
    def reset(cls):
        cls.data = {}


class Openers(object):

    def __init__(self):
        self.openers = {}
        for cls in IOpener.__subclasses__():
            self.openers[cls.scheme] = cls()

    def open(self, uri):
        for scheme, opener in self.openers.iteritems():
            if uri.startswith(scheme):
                return opener.open(uri)

        # Support direct file paths that dont specify a scheme
        if os.path.exists(uri):
            return self.openers["file://"].open(uri)

        raise ValueError("URI '%s' cannot be opened (unsupported scheme or missing local file)" % uri)

