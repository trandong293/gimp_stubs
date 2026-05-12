import json
import sys

import util

XML_NS = {"a": "http://www.gtk.org/introspection/core/1.0"}
CONTEXT = ""


def get_str_short_type(typ: str | type) -> str:
    if type(typ) is not str:
        typ = "%s.%s" % (typ.__module__, typ.__name__)
    return (
        # replace
        typ.replace("gi._gi", "GObject")
        .replace("gobject", "GObject")
        # remove
        .replace("builtins.", "")
        .replace("typing.", "")
        .replace("gi.repository.", "")
        .replace("gi.overrides.", "")
        .replace("%s." % CONTEXT, "")
    )


def main():
    module_name = sys.argv[1]
    child = sys.argv[2]
    global CONTEXT
    CONTEXT = module_name

    with open("metadata.json") as f:
        METADATA = json.load(f)

    if module_name not in METADATA:
        sys.exit("[ERROR] cannot find metadata for module %s" % module_name)

    gir_path = "%s-%s.gir" % (module_name, METADATA[module_name]["version"])
    main_ns = util.get_main_namespace_from_gir(gir_path)

    callback = main_ns.find("a:callback[@name='%s']" % child, XML_NS)
    if callback is None:
        sys.exit("[ERROR] cannot find callback %s in module %s" % (child, module_name))

    ret = callback.find("a:return-value", XML_NS)
    ret_type = ret.find("a:type", XML_NS)
    ret_type_name = ret_type.get("name")
    if ret_type_name == "none":
        ret_type_name = "None"
    if ret_type_name in util.GTYPE_MAPPING:
        typ = util.GTYPE_MAPPING[ret_type_name]
        ret_type_name = get_str_short_type("%s.%s" % (typ.__module__, typ.__name__))

    params = callback.findall("a:parameters/a:parameter", XML_NS)
    s_params = []
    for param in params:
        param_name = param.get("name")
        param_type_name = param.find("a:type", XML_NS).get("name")
        if param_type_name in util.GTYPE_MAPPING:
            typ = util.GTYPE_MAPPING[param_type_name]
            param_type_name = get_str_short_type(
                "%s.%s" % (typ.__module__, typ.__name__)
            )
        s_params.append("%s: %s" % (param_name, param_type_name))

    print("def %s(%s) -> %s: ..." % (child, ", ".join(s_params), ret_type_name))


if __name__ == "__main__":
    main()
