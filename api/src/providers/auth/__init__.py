#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Auth provider module."""

from .base import AuthProvider, NoopAuthProvider
from .cognito import CognitoAuthProvider

__all__ = [
    "AuthProvider",
    "NoopAuthProvider",
    "CognitoAuthProvider",
]
