# -*- coding: utf-8 -*-
def to_string(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )

    cls.__str__ = __str__
    return cls
# the __all__ is generated
__all__ = ['to_string']