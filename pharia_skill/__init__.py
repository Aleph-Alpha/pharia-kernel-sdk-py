import json
from typing import Callable
from .skill import exports

def pharia_skill(func: Callable) -> Callable:
    class SkillHandler(exports.SkillHandler):
        def run(self, input: bytes) -> bytes:
            try:
                return func(input)
            except Exception as e:
                return json.dumps(str(e)).encode() 
    
    func.__globals__["SkillHandler"] = SkillHandler
    return func

    
    

