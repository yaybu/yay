
from yay.nodes import Node

class Define(Node):
    
    def __init__(self, var, node):
        super(Define, self).__init__()
        self.var = var
        self.node = node
        
class Call(Node):
    
    def __init__(self, var, node):
        super(Call, self).__init__()
        self.var = var
        self.node = node
        
        
        