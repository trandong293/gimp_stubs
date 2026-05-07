import enum
import importlib
import inspect
from typing import Any

import gi
from gi.repository import GObject

SPACE = 4 * " "
CONTEXT = ""
# https://stackoverflow.com/a/78306153/16187830
GTYPE_TO_PYTHON = {
    GObject.type_from_name(GObject.type_name(ptype)): ptype
    for ptype in (int, float, str, bool, object)
}
METADATA = {
    "Gimp": {
        "imports": [
            "import collections",
            "import enum",
            "import typing",
            "from typing import Any, type_check_only",
            "import cairo",
            "import gi",
            "from gi.repository import GdkPixbuf, GExiv2, Gio, GLib, GObject, Pango",
            "import Babl",
            "import Gegl",
        ],
        "version": "3.0",
    },
    "GimpUi": {
        "imports": [
            "import collections",
            "import enum",
            "import typing",
            "from typing import Any, type_check_only",
            "import cairo",
            "import gi",
            "from gi.repository import Gdk, GdkPixbuf, Gio, GLib, GObject, Gtk",
            "import Babl",
            "import Gegl",
            "import Gimp",
        ],
        "version": "3.0",
    },
    "Babl": {
        "imports": [
            "import enum",
            "from typing import Any",
            "import gi",
        ],
        "version": "0.1",
    },
    "Gegl": {
        "imports": [
            "import collections",
            "import enum",
            "import typing",
            "from typing import Any, type_check_only",
            "import gi",
            "from gi.repository import GLib, GObject",
            "import Babl",
        ],
        "version": "0.4",
    },
}


def get_str_short_type(typ: str | type) -> str:
    if type(typ) is not str:
        typ = "%s.%s" % (typ.__module__, typ.__name__)
    return (
        # replace
        typ.replace("gi._gi", "GObject")
        .replace("gobject", "GObject")
        # remove
        .replace("builtins.", "")
        .replace("gi.repository.", "")
        .replace("gi.overrides.", "")
        .replace("%s." % CONTEXT, "")
    )


def get_str_bases(bases: tuple[type]) -> str:
    s_bases = []
    for base in bases:
        s_bases.append("%s.%s" % (base.__module__, base.__name__))
    return get_str_short_type(", ".join(s_bases))


def get_str_signature(obj: any) -> str:
    sig = inspect.signature(obj)
    return get_str_short_type(sig.format())


def get_str_introspection(parent: Any, num_space: int = 0) -> str:
    s_intros = []
    for name, child in vars(parent).items():
        if name.startswith("__") or name == "_lock":
            continue

        typ = type(child)
        if typ in [str, int, float]:
            f_const = "%s: %s = %s" if typ is not str else '%s: %s = "%s"'
            s_intros.append(f_const % (name, typ.__name__, child))
            continue

        # fields:
        # @property
        # def name(self) -> ret_type: ...
        if typ is property:
            # todo: get signature from gir fields
            s_intros.append("@property")
            s_intros.append("def %s(self) -> Any: ... " % name)
            continue

        if typ in [enum.EnumType, gi._enum.GEnumMeta, gi._enum.GFlagsMeta]:
            bases = get_str_bases(child.__bases__)
            s_intros.append("class %s(%s):" % (name, bases))
            for e in child:
                s_intros.append(SPACE + "%s = %s" % (e.name, e.value))
            continue

        if typ in [gi._gi.FunctionInfo, gi._gi.VFuncInfo]:
            s_sig = get_str_signature(child)
            s_intros.append("def %s%s: ..." % (name, s_sig))
            continue

        if typ is classmethod:
            s_sig = get_str_signature(child.__func__)
            s_intros.append("@classmethod")
            s_intros.append("def %s%s: ..." % (name, s_sig))
            continue

        if typ is staticmethod:
            s_sig = get_str_signature(child)
            s_intros.append("@staticmethod")
            s_intros.append("def %s%s: ..." % (name, s_sig))
            continue

        # todo: done?
        if typ in [gi.types.StructMeta, gi.types.GObjectMeta]:
            bases = get_str_bases(child.__bases__)
            s_intros.append("class %s(%s):" % (name, bases))
            # properties:
            # @type_check_only
            # class Props(base.Props):
            #   name: type
            #   ...
            # @property
            # def props(self) -> Props: ...
            s_props_exist = []
            if hasattr(child, "props"):
                props = getattr(child, "props")
                s_props = []
                for name, prop in inspect.getmembers(props):
                    # ignore all props not from its direct parent
                    if prop.owner_type.pytype is child:
                        prop_gtype = prop.value_type
                        prop_type = prop_gtype.pytype or GTYPE_TO_PYTHON.get(
                            prop_gtype, bytes
                        )
                        s_type = get_str_short_type(prop_type)
                        s_props.append(SPACE + "%s: %s" % (name, s_type))
                if len(s_props):
                    s_props_exist.append("@type_check_only")
                    s_props_exist.append(
                        "class Props(%s.Props):" % get_str_short_type(child.__base__)
                    )
                    s_props_exist.extend(s_props)
                    s_props_exist.append("@property")
                    s_props_exist.append("def props(self) -> Props: ...")
            s_props_exist = [SPACE + s_has_prop for s_has_prop in s_props_exist]
            s_intros.extend(s_props_exist)

            # others
            s_class_content = get_str_introspection(child, num_space + 1)
            if s_class_content != "":
                s_intros.append(s_class_content)
            elif s_props_exist == []:
                s_intros.append(SPACE + "pass")
            continue

        print("[MISSING]", name, child, typ)
    s_intros = [num_space * SPACE + s_intro for s_intro in s_intros]
    return "\n".join(s_intros)


def gen_stubs(module_name: str) -> str:
    global CONTEXT
    CONTEXT = module_name

    if "version" in METADATA[module_name]:
        gi.require_version(module_name, METADATA[module_name]["version"])
    mod = importlib.import_module(".%s" % module_name, package="gi.repository")

    s_intros = []
    s_intros.extend(METADATA[module_name]["imports"])
    inspect.getmembers(mod)  # force load
    s_intros.append(get_str_introspection(mod))
    return "\n".join(s_intros)


def main():
    for module_name in METADATA:
        with open("%s.pyi" % module_name, "w") as f:
            print(gen_stubs(module_name), file=f)


if __name__ == "__main__":
    main()
