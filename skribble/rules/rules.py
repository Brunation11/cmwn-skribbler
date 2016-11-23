"""
Skribble Rules
"""


class SkribbleRules:
    def __init__(self, skribble):
        if isinstance(skribble, 'Skribble') is False:
            raise Exception('Improper skribble passed')

        self.skribble = skribble


__all__ = ['SkribbleRules']
