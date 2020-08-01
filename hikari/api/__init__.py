# -*- coding: utf-8 -*-
# cython: language_level=3str, boundscheck=False
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Interfaces for components that make up Hikari applications.

These are provided to uncouple specific implementation details from each
implementation, thus allowing custom solutions to be engineered such as bots
relying on a distributed event bus or cache.
"""

__all__ = []  # type: ignore[var-annotated]
