import sys
import xml.etree.ElementTree as ET
from typing import Any
from xml.etree.ElementTree import Element

from gi.repository import GLib, GObject

# gtype
GTYPE_MAPPING = {
    # https://stackoverflow.com/a/78306153/16187830
    # {GObject.type_from_name(GObject.type_name(pytype)).name: pytype.__name__ for pytype in [int, float, str, bool, object]}
    "gint": int,
    "gdouble": float,
    "gchararray": str,
    "gboolean": bool,
    "PyObject": object,
    #
    # {mb.name: mb.pytype for name, mb in inspect.getmembers(GObject) if type(mb) is GObject.GType}
    "GValue": GObject.Value,
    "GVariant": GLib.Variant,
    "GObject": GObject.Object,
    "GParam": GObject.ParamSpec,
    "GStrv": GObject.Strv,
    "GString": GObject.String,
    # *: pass ".is_a()" test, so it should be right
    "GEnum": GObject.GEnum,
    "GInterface": GObject.GInterface,
    "GFlags": GObject.GFlags,
    "void": None,
    # **: from https://docs.gtk.org/glib/types.html
    "gchar": int,
    "guchar": int,
    "guint": int,
    "gint64": int,
    "guint64": int,
    "glong": int,
    "gulong": int,
    "gfloat": float,
    "gpointer": Any,  # void *
    # ***: just guest
    "GType": GObject.GType,
    "invalid": None,
    "GBoxed": GObject.GBoxed,
    # others
    "utf8": str,
    "guint8": int,
    "guint32": int,
    "gsize": int,
}


def get_str_pytype(gtype: GObject.GType) -> str:
    typ = gtype.pytype
    if typ is not None:
        return "%s.%s" % (typ.__module__, typ.__name__)

    if gtype.name in GTYPE_MAPPING:
        typ = GTYPE_MAPPING[gtype.name]
        return "%s.%s" % (typ.__module__, typ.__name__)

    return gtype.name


# xml
XML_NS = {"a": "http://www.gtk.org/introspection/core/1.0"}


def get_main_namespace_from_gir(filepath: str) -> Element:
    tree = ET.parse(filepath)
    root = tree.getroot()
    main_ns = root.find("a:namespace", XML_NS)
    if main_ns is None:
        sys.exit("[ERROR] cannot analyze %s" % filepath)
    return main_ns


def get_str_field_type_from_gir(gir: Element, klass: str, field_name: str) -> str:
    e_field = gir.find(
        "a:class[@name='%s']/a:field[@name='%s']" % (klass, field_name), XML_NS
    )
    if e_field is None:
        e_field = gir.find(
            "a:record[@name='%s']/a:field[@name='%s']" % (klass, field_name), XML_NS
        )

    # field in [type, array-type, callback]
    e_type = e_field.find("a:type", XML_NS)
    if e_type is None:
        e_type = e_field.find("a:array/a:type", XML_NS)
    if e_type is None:
        if e_field.find("a:callback", XML_NS) is not None:
            return object.__name__  # all callbacks are object
        else:
            sys.exit("[ERROR] cannot get field type of %s.%s" % (klass, field_name))
    e_type_name = e_type.get("name")
    s_type = GTYPE_MAPPING.get(e_type_name, e_type_name)
    if isinstance(s_type, str):
        return s_type
    return "%s.%s" % (s_type.__module__, s_type.__name__)

    # todo: wait GTYPE_TO_PYTHON
    # return GTYPE_TO_PYTHON.get(GObject.type_from_name(s_type), object)


# others
