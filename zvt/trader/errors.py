# -*- coding: utf-8 -*-
class TraderError(Exception):
    """Base class for exceptions in this module."""
    pass


class InvalidOrderParamError(TraderError):
    def __init__(self, message="invalid order param"):
        self.message = message


class NotEnoughMoneyError(TraderError):
    def __init__(self, message="not enough money"):
        self.message = message


class NotEnoughPositionError(TraderError):
    def __init__(self, message="not enough position"):
        self.message = message


class InvalidOrderError(TraderError):
    def __init__(self, message="invalid order"):
        self.message = message


class WrongKdataError(TraderError):
    def __init__(self, message="wrong kdata"):
        self.message = message
