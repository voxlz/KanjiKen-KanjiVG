import os
import sys

PYTHON_VERSION_MAJOR = sys.version_info[0]

if PYTHON_VERSION_MAJOR < 3:
    # In python 2, io.open does not support encoding parameter
    pass
else:

    # In python 3, strings are used so unicode() is a pass-through
    def unicode(s):
        return s


def canonicalId(char_id):
    if isinstance(char_id, str):
        idLen = len(char_id)
        if idLen == 1:
            char_id = ord(char_id)
        elif idLen >= 2 and idLen <= 5:
            char_id = int(char_id, 16)
        else:
            raise ValueError(
                "Character id must be a 1-character string with the character itself, or 2-5 hex digit unicode codepoint."
            )
    if not isinstance(char_id, int):
        raise ValueError("canonicalId: id must be int or str")
    if char_id > 0xF and char_id <= 0xFFFFF:
        return "%05x" % (char_id)
    raise ValueError("Character id out of range")


class SvgFileInfo:
    def __init__(self, file, directory):
        self.path = os.path.join(directory, file)
        if file[-4:].lower() != ".svg":
            raise Exception(f"File should have .svg extension. ({str(self.path)})")
        parts = (file[:-4]).split("-")
        if len(parts) == 2:
            self.variant = parts[1]
        elif len(parts) != 1:
            raise Exception(
                f"File should have at most 2 parts separated by a dash. ({str(file)})"
            )
        self.id = parts[0]
        if self.id != canonicalId(self.id):
            raise Exception(f"File name not in canonical format ({str(self.path)})")

    def __repr__(self):
        return repr(vars(self))

    def read(self, SVGHandler=None):
        if SVGHandler is None:
            from src.kvg.kanjivg import SVGHandler
        handler = SVGHandler()
        parseXmlFile(self.path, handler)
        parsed = list(handler.kanjis.values())
        if len(parsed) != 1:
            raise Exception(f"File does not contain 1 kanji entry. ({self.path})")
        return parsed[0]


def parseXmlFile(path, handler):
    from xml.sax import parse

    parse(path, handler)


def listSvgFiles(directory):
    return [SvgFileInfo(f, directory) for f in os.listdir(directory)]


def readXmlFile(path, KanjisHandler=None):
    if KanjisHandler is None:
        from src.kvg.kanjivg import KanjisHandler
    handler = KanjisHandler()
    parseXmlFile(path, handler)
    if list(handler.kanjis.values()):
        return handler.kanjis
    else:
        raise Exception(f"File does not contain any kanji entries. ({path})")
