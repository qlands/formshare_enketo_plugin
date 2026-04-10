from jinja2.ext import babel_extract

jinja_extensions = """
                    jinja2.ext.do,jinja2.ext.i18n,                    
                    formshare.config.jinja_extensions:JSResourceExtension,
                    formshare.config.jinja_extensions:CSSResourceExtension,
                    formshare.config.jinja_extensions:ExtendThis,
                   """


def extract_formshare(fileobj, *args, **kw):
    if "options" not in kw:
        kw["options"] = {}
    if "trimmed" not in kw["options"]:
        kw["options"]["trimmed"] = "True"
    if "silent" not in kw["options"]:
        kw["options"]["silent"] = "False"
    if "extensions" not in kw["options"]:
        kw["options"]["extensions"] = jinja_extensions

    return babel_extract(fileobj, *args, **kw)
