"""Native Hermes directory-plugin entry point."""


def register(ctx):
    from .hermes_fxmacrodata import register as register_plugin

    return register_plugin(ctx)


__all__ = ["register"]
