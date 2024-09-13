import os

def get_skill_wit_path():
    curdir = os.path.dirname(__file__)
    return os.path.join(curdir, "skill.wit")

print(get_skill_wit_path())
