"""The local provider catalogue.

Add a provider by adding a ``SPEC`` here; the game's hooks discover it.
"""

from . import opencodego

SPECS = (opencodego.SPEC,)
