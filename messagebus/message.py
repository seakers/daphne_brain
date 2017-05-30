import json

class Message():
    
    def __init__(self,target=[],content={},context=None):
        self.target=target
        self.content=content
        self.context=context
        
    def serialize(self):
        return json.dumps({
            'target':self.target,
            'content':self.content,
            'context':self.context
        })
    
    def deserialize(value):
        obj = json.loads(value)
        return Message(target=obj.get('target'), content=obj.get('content'), context=obj.get('context'))
    