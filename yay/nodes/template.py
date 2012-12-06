from yay.nodes import Node

class Template(Node):
    
    def __init__(self, value):
        super(Template, self).__init__()
        self.value = value
