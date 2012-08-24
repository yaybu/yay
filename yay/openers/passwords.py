import socket
import os

class PasswordStore(object):
    pass

class GpgAgentError(RuntimeError):
    pass

class GpgAgent(PasswordStore):

    def __init__(self, path=None):
        if not path:
            if not "GPG_AGENT_INFO" in os.environ:
                raise GpgAgentError("GPG Agent not available")
            path, a, b = os.environ["GPG_AGENT_INFO"].split(":")

        self.path = path

        self.agent = socket.socket(socket.AF_UNIX)
        self.agent.connect(self.path)
        self.fp = self.agent.makefile('rb')

        #FIXME: Should validate this line?
        self.fp.readline()

    def request(self, *params):
        self.agent.send('%s\n' % ' '.join(params))

        line = self.fp.readline()
        if not line:
            raise GpgAgentError("Agent stopped responding mid request")
        if line.startswith("ERROR"):
            raise GpgAgentError(line[6:])

        print line
        return line

    def reset(self):
        self.request("RESET")

    def get_passphrase(self, prompt, description=None, error_message=None, cache_id=None):
        if not cache_id:
            cache_id = "yay:2"
        if not description:
            description = 'X'
        if not error_message:
            error_message = 'X'

        prompt = prompt.replace(' ', '+')
        description = description.replace(' ', '+')
        error_message = error_message.replace(' ', '+')

        response = self.request("GET_PASSPHRASE", cache_id, error_message, prompt, description)

    def clear_passphrase(self, cache_id):
        self.request("CLEAR_PASSPHRASE", cache_id)

g = GpgAgent()
g.reset()
g.get_passphrase("Enter password for http://eggs.isotoma.com")

