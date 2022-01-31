import re

def cap_to_kebab(name):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', name).lower()


def pluralize(name:str):
    if name.endswith('y'):
        return name[0:-1] + 'ies'
    else:
        return name + 's'