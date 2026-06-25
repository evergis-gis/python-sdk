# -*- coding: utf-8 -*-
"""Registry mapping ``StringSubType`` values to attribute builders.

A typed-attribute class registers itself with :func:`register_sub_type`;
``create_layer_from_schema`` looks builders up here when it sees a
Pydantic field with ``Field(json_schema_extra={"sub_type": "..."})``.

This keeps ``layers/create.py`` agnostic of individual sub-types - adding
a new one is a single new file under ``attribute_types/``.
"""

from __future__ import annotations

from typing import Any, Callable, Dict


# A builder takes ``(field_name, field_info)`` from a Pydantic model and
# returns a ready-to-publish ``AttributeConfigurationDc`` subclass. The
# return type is intentionally Any to avoid a hard import cycle on the
# evergis_api side.
SubTypeBuilder = Callable[[str, Any], Any]

SUB_TYPE_BUILDERS: Dict[str, SubTypeBuilder] = {}


def register_sub_type(name: str) -> Callable[[type], type]:
    """Class decorator: register ``cls.from_field`` under ``StringSubType`` ``name``.

    Example:
        >>> @register_sub_type("Attachments")
        ... class AttachmentsAttribute(StringAttributeConfigurationDc):
        ...     @classmethod
        ...     def from_field(cls, field_name, field_info):
        ...         return cls(attributeName=field_name, ...)
    """

    def decorator(cls: type) -> type:
        builder = getattr(cls, "from_field", None)
        if builder is None or not callable(builder):
            raise TypeError(
                f"{cls.__name__} must define a classmethod ``from_field"
                "(field_name, field_info)`` to be registered as a sub_type"
            )
        SUB_TYPE_BUILDERS[name] = builder
        return cls

    return decorator


__all__ = ["SUB_TYPE_BUILDERS", "SubTypeBuilder", "register_sub_type"]
