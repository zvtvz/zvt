# -*- coding: utf-8 -*-
class TraderError(Exception):
    """Base class for exceptions in this module."""

    pass


class QmtError(TraderError):
    def __init__(self, message="qmt error"):
        self.message = message


class PositionOverflowError(TraderError):
    def __init__(self, message="超出仓位限制"):
        self.message = message


# the __all__ is generated
__all__ = ["TraderError", "QmtError", "PositionOverflowError"]
