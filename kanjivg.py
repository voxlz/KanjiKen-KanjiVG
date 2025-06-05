# type: ignore
#
# # -*- coding: utf-8 -*-
#
#  Copyright (C) 2009-2013 Alexandre Courbot
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from ordered_set import OrderedSet

from src.kvg.utils import PYTHON_VERSION_MAJOR, canonicalId
from src.kvg.xmlhandler import BasicHandler

if PYTHON_VERSION_MAJOR > 2:

    def unicode(s):
        return s

    unichr = chr


# Sample license header
LICENSE_STRING = """Copyright (C) 2009-2013 Lurch Apel.
This work is distributed under the conditions of the Creative Commons
Attribution-Share Alike 3.0 License. This means you are free:
* to Share - to copy, distribute and transmit the work
* to Remix - to adapt the work

Under the following conditions:
* Attribution. You must attribute the work by stating your use of KanjiVG in
  your own copyright header and linking to KanjiVG's website
  (http://kanjivg.tagaini.net)
* Share Alike. If you alter, transform, or build upon this work, you may
  distribute the resulting work only under the same or similar license to this
  one.

See http://creativecommons.org/licenses/by-sa/3.0/ for more details."""


def is_kanji(v):
    return (
        (v >= 0x4E00 and v <= 0x9FC3)
        or (v >= 0x3400 and v <= 0x4DBF)
        or (v >= 0xF900 and v <= 0xFAD9)
        or (v >= 0x2E80 and v <= 0x2EFF)
        or (v >= 0x20000 and v <= 0x2A6DF)
    )


def realord(s, pos=0):
    """Returns the unicode of a character in a unicode string, taking surrogate pairs into account"""
    if s is None:
        return None
    code = ord(s[pos])
    if code >= 0xD800 and code < 0xDC00:
        if len(s) <= pos + 1:
            print("realord warning: missing surrogate character")
            return 0
        code2 = ord(s[pos + 1])
        if code2 >= 0xDC00 and code < 0xE000:
            code = 0x10000 + ((code - 0xD800) << 10) + (code2 - 0xDC00)
    return code


def realchr(i):
    if i < 0x10000:
        return unichr(i)
    else:
        return unichr(((i - 0x10000) >> 10) + 0xD800) + unichr(0xDC00 + (i & 0x3FF))


class Kanji:
    """Describes a kanji. The root stroke group is accessible from the strokes member."""

    def __init__(self, code, variant=None):
        # Unicode of char being represented (standard str)
        self.code = canonicalId(code)
        # Variant of the character, if any
        self.variant = variant
        self.strokes = None

    def __repr__(self):
        return repr(vars(self))

    # String identifier used to uniquely identify the kanji
    def kId(self):
        ret = self.code
        if self.variant:
            ret += f"-{self.variant}"
        return ret

    def outputStrokesNumbers(self, out, indent=0):
        strokes = self.getStrokes()
        for cpt, stroke in enumerate(strokes, start=1):
            stroke.numberToSVG(out, cpt, indent + 1)

    def outputStrokes(self, out, indent=0):
        if self.strokes is not None:
            self.strokes.toSVG(out, self.kId(), [0], [1])

    def simplify(self):
        if self.strokes is not None:
            self.strokes.simplify()

    def getStrokes(self):
        if self.strokes is not None:
            return self.strokes.getStrokes()
        return []


class StrokeGr:
    """Describes a stroke group belonging to a kanji as closely as possible to the XML format. Sub-stroke groups or strokes are available in the.children member. They can either be of class StrokeGr or Stroke so their type should be checked."""

    def __init__(self, parent=None):
        self.parent = parent
        if parent:
            parent.children.append(self)
        # Element of StrokeGr
        self.element: str | None = None
        # A more common, safer element this one derives of
        self.original = None
        self.part: int | None = None
        self.number: int | None = None
        self.variant = False
        self.partial = False
        self.tradForm = False
        self.radicalForm = False
        self.position = None
        self.radical = None
        self.phon = None

        self.children = []

    def __repr__(self):
        return repr(vars(self))

    def setParent(self, parent):
        if self.parent is not None or parent is None:
            raise Exception(
                "Set parent should only be set once! There is no cleanup for old parents."
            )
        parent.children.append(self)
        self.parent = parent

    def toSVG(self, out, rootId, groupCpt=[0], strCpt=[1], indent=0):
        gid = rootId
        if groupCpt[0] != 0:
            gid += f"-g{str(groupCpt[0])}"
        groupCpt[0] += 1

        idString = f' id="kvg:{gid}"'
        eltString = f' kvg:element="{self.element}"' if self.element else ""
        variantString = ' kvg:variant="true"' if self.variant else ""
        partialString = ' kvg:partial="true"' if self.partial else ""
        origString = f' kvg:original="{self.original}"' if self.original else ""
        partString = ' kvg:part="%d"' % (self.part) if self.part else ""
        numberString = ' kvg:number="%d"' % (self.number) if self.number else ""
        tradFormString = ' kvg:tradForm="true"' if self.tradForm else ""
        radicalFormString = ' kvg:radicalForm="true"' if self.radicalForm else ""
        posString = f' kvg:position="{self.position}"' if self.position else ""
        radString = f' kvg:radical="{self.radical}"' if self.radical else ""
        phonString = f' kvg:phon="{self.phon}"' if self.phon else ""
        out.write(
            "\t" * indent
            + "<g%s%s%s%s%s%s%s%s%s%s%s%s>\n"
            % (
                idString,
                eltString,
                partString,
                numberString,
                variantString,
                origString,
                partialString,
                tradFormString,
                radicalFormString,
                posString,
                radString,
                phonString,
            )
        )

        for child in self.children:
            child.toSVG(out, rootId, groupCpt, strCpt, indent + 1)

        out.write("\t" * indent + "</g>\n")

    def components(self, simplified=True, recursive=False, level=0):
        ret = []
        childsComp = []
        for child in self.children:
            if isinstance(child, StrokeGr):
                found = False
                # Can we find the component in the child?
                if simplified and child.original:
                    ret.append(child.original)
                    found = True
                elif child.element:
                    ret.append(child.element)
                    found = True
                # If not, the components we are looking for are the child's
                # components - we also do that if we asked all the sub-components of the group
                if not found or recursive:
                    newLevel = level
                    if found:
                        newLevel += 1
                    childsComp += child.components(simplified, recursive, newLevel)
        if recursive and ret:
            ret = [level] + ret + childsComp
        return ret

    def simplify(self):
        for child in self.children:
            if isinstance(child, StrokeGr):
                child.simplify()
        if len(self.children) == 1 and isinstance(self.children[0], StrokeGr):
            child = self.children[0]
            # Check if there is no conflict
            if child.element and self.element and child.element != self.element:
                return
            if child.original and self.original and child.original != self.original:
                return
            # Parts cannot be merged
            if child.part and self.part and self.part != child.part:
                return
            if child.variant and self.variant and child.variant != self.variant:
                return
            if child.partial and self.partial and child.partial != self.partial:
                return
            if child.tradForm and self.tradForm and child.tradForm != self.tradForm:
                return
            if (
                child.radicalForm
                and self.radicalForm
                and child.radicalForm != self.radicalForm
            ):
                return
            # We want to preserve inner identical positions - we may have something at the top
            # of another top element, for instance.
            if child.position and self.position:
                return
            if child.radical and self.radical and child.radical != self.radical:
                return
            if child.phon and self.phon and child.phon != self.phon:
                return

            # Ok, let's merge!
            self.children = child.children
            if child.element:
                self.element = child.element
            if child.original:
                self.original = child.original
            if child.part:
                self.part = child.part
            if child.variant:
                self.variant = child.variant
            if child.partial:
                self.partial = child.partial
            if child.tradForm:
                self.tradForm = child.tradForm
            if child.radicalForm:
                self.radicalForm = child.radicalForm
            if child.position:
                self.position = child.position
            if child.radical:
                self.radical = child.radical
            if child.phon:
                self.phon = child.phon

    def getStrokes(self):
        ret = []
        for child in self.children:
            if isinstance(child, StrokeGr):
                ret += child.getStrokes()
            else:
                ret.append(child)
        return ret


class Stroke:
    """A single stroke, containing its type and (optionally) its SVG data."""

    def __init__(self, parent=None):
        self.element: str | None = None
        self.svg: str | None = None  # represents the path data string in the SVG
        self.number_pos = None
        self.position = None
        self.children = []

    def __repr__(self):
        return repr(vars(self))

    def number_to_svg(self, out, number, indent=0):
        if self.number_pos:
            out.write(
                "\t" * indent
                + '<text transform="matrix(1 0 0 1 %.2f %.2f)">%d</text>\n'
                % (self.number_pos[0], self.number_pos[1], number)
            )

    def toSVG(self, out, rootId, groupCpt, strCpt, indent=0):
        pid = f"{rootId}-s{str(strCpt[0])}"
        strCpt[0] += 1
        s = "\t" * indent + f'<path id="kvg:{pid}"'
        if self.element:
            s += f' kvg:type="{self.element}"'
        if self.svg:
            s += f' d="{self.svg}"'
        s += "/>\n"
        out.write(s)


class KanjisHandler(BasicHandler):
    """XML handler for parsing kanji files. It can handle single-kanji files or aggregation files. After parsing, the kanjis are accessible through the kanjis member, indexed by their svg file name."""

    def __init__(self):
        BasicHandler.__init__(self)
        self.kanji = None
        self.kanjis = {}
        self.group = None
        self.groups = []
        self.compCpt = {}
        self.metComponents = OrderedSet([])

    def handle_start_kanji(self, attrs):
        if self.kanji is not None:
            raise Exception("Kanji cannot be nested")
        if self.group is not None:
            raise Exception("Kanji cannot be inside a group")
        if len(self.groups) != 0:
            raise Exception("Previous kanji not closed correctly")
        idType, idVariantStr = str(attrs["id"]).split("_")
        if idType != "kvg:kanji":
            raise Exception("Each kanji should have id formatted as kvg:kanji_XXXXX.")
        idVariant = idVariantStr.split("-")
        self.kanji = Kanji(*idVariant)

    def handle_end_kanji(self):
        if self.group is not None:
            raise Exception("A group is not closed inside the kanji.")
        if len(self.groups) != 1:
            raise Exception("Kanji should have 1 root group.")
        if self.kanji is None:
            raise Exception("No kanji object to assign strokes to.")
        self.kanji.strokes = self.groups[0]
        self.kanjis[self.kanji.code] = self.kanji
        self.groups = []
        self.kanji = None

    def handle_start_g(self, attrs):
        if self.kanji is None:
            raise Exception("Stroke group must be inside a kanji")
        group = StrokeGr(self.group)

        # Now parse group attributes
        if "kvg:element" in attrs:
            group.element = unicode(attrs["kvg:element"])
        if "kvg:variant" in attrs:
            group.variant = str(attrs["kvg:variant"]).lower() == "true"
        if "kvg:partial" in attrs:
            group.partial = str(attrs["kvg:partial"]).lower() == "true"
        if "kvg:original" in attrs:
            group.original = unicode(attrs["kvg:original"])
        if "kvg:part" in attrs:
            group.part = int(attrs["kvg:part"])
        if "kvg:number" in attrs:
            group.number = int(attrs["kvg:number"])
        if "kvg:tradForm" in attrs and str(attrs["kvg:tradForm"]) == "true":
            group.tradForm = True
        if "kvg:radicalForm" in attrs and str(attrs["kvg:radicalForm"]) == "true":
            group.radicalForm = True
        if "kvg:position" in attrs:
            group.position = unicode(attrs["kvg:position"])
        if "kvg:radical" in attrs:
            group.radical = unicode(attrs["kvg:radical"])
        if "kvg:phon" in attrs:
            group.phon = unicode(attrs["kvg:phon"])

        self.group = group

        if group.element:
            self.metComponents.add(group.element)
        if group.original:
            self.metComponents.add(group.original)

        if group.number:
            if not group.part:
                print(f"{self.kanji.kId()}: Number specified, but part missing")
            # The group must exist already
            if group.part and group.part > 1:
                if (
                    group.element
                    and (group.element + str(group.number)) not in self.compCpt
                ):
                    print(f"{self.kanji.kId()}: Missing numbered group")
                elif (
                    group.element
                    and self.compCpt[group.element + str(group.number)]
                    != group.part - 1
                ):
                    print(f"{self.kanji.kId()}: Incorrectly numbered group")
            elif group.element and (group.element + str(group.number)) in self.compCpt:
                print(f"{self.kanji.kId()}: Duplicate numbered group")
            if group.element:
                self.compCpt[group.element + str(group.number)] = group.part
        elif group.part:
            # The group must exist already
            if group.element and group.element not in self.compCpt:
                if group.part and group.part > 1:
                    print(f"{self.kanji.kId()}: Incorrectly started multi-part group")
            elif (
                group.element
                and group.part
                and self.compCpt[group.element] != group.part - 1
            ):
                if group.part > 1:
                    print(f"{self.kanji.kId()}: Incorrectly splitted multi-part group")
            if group.element and group.part:
                self.compCpt[group.element] = group.part

    def handle_end_g(self):
        if self.group and self.group.parent is None:
            self.groups.append(self.group)
        if self.group:
            self.group = self.group.parent

    def handle_start_path(self, attrs):
        if self.kanji is None or self.group is None:
            raise Exception("Stroke must be inside a kanji and group!")
        stroke = Stroke(self.group)
        if "kvg:type" in attrs:
            stroke.element = unicode(attrs["kvg:type"])
        if "d" in attrs:
            stroke.svg = unicode(attrs["d"])
        self.group.children.append(stroke)


class SVGHandler(BasicHandler):
    """SVG handler for parsing final kanji files. It can handle single-kanji files or aggregation files. After parsing, the kanji are accessible through the kanjis member, indexed by their svg file name."""

    def __init__(self):
        BasicHandler.__init__(self)
        self.kanjis = {}
        self.current_kanji = None
        self.groups = []
        self.met_components = OrderedSet([])

    def handle_start_g(self, attrs):
        """Handle the start of a group element"""
        group = StrokeGr()

        # Special case for handling the root
        if len(self.groups) == 0:
            idType, idVariantStr = str(attrs["id"]).split("_")
            idVariant = idVariantStr.split("-")
            if idType == "kvg:StrokePaths":
                pass
            elif idType == "kvg:StrokeNumbers":
                return
            else:
                raise Exception(f"Invalid root group id type ({str(attrs['id'])})")
            self.current_kanji = Kanji(*idVariant)
            self.kanjis[self.current_kanji.code] = self.current_kanji
            self.compCpt = {}
        else:
            group.setParent(self.groups[-1])

        # Now parse group attributes
        if "kvg:element" in attrs:
            group.element = unicode(attrs["kvg:element"])
        if "kvg:variant" in attrs:
            group.variant = str(attrs["kvg:variant"]).lower() == "true"
        if "kvg:partial" in attrs:
            group.partial = str(attrs["kvg:partial"]).lower() == "true"
        if "kvg:original" in attrs:
            group.original = unicode(attrs["kvg:original"])
        if "kvg:part" in attrs:
            group.part = int(attrs["kvg:part"])
        if "kvg:number" in attrs:
            group.number = int(attrs["kvg:number"])
        if "kvg:tradForm" in attrs and str(attrs["kvg:tradForm"]) == "true":
            group.tradForm = True
        if "kvg:radicalForm" in attrs and str(attrs["kvg:radicalForm"]) == "true":
            group.radicalForm = True
        if "kvg:position" in attrs:
            group.position = unicode(attrs["kvg:position"])
        if "kvg:radical" in attrs:
            group.radical = unicode(attrs["kvg:radical"])
        if "kvg:phon" in attrs:
            group.phon = unicode(attrs["kvg:phon"])

        self.groups.append(group)

        if group.element:
            self.met_components.add(group.element)
        if group.original:
            self.met_components.add(group.original)

        if group.number:
            if not group.part:
                if self.current_kanji:
                    print(
                        f"{self.current_kanji.kId()}: Number specified, but part missing"
                    )
            # The group must exist already
            if group.part and group.part > 1:
                if (
                    group.element
                    and group.element + str(group.number) not in self.compCpt
                ):
                    if self.current_kanji:
                        print(f"{self.current_kanji.kId()}: Missing numbered group")
                elif (
                    group.element
                    and group.part
                    and self.compCpt[group.element + str(group.number)]
                    != group.part - 1
                ):
                    if self.current_kanji:
                        print(f"{self.current_kanji.kId()}: Incorrectly numbered group")
            elif group.element and (group.element + str(group.number)) in self.compCpt:
                if self.current_kanji:
                    print(f"{self.current_kanji.kId()}: Duplicate numbered group")
            if group.element and group.part:
                self.compCpt[group.element + str(group.number)] = group.part
        elif group.part:
            # The group must exist already
            if group.part and group.part > 1:
                if group.element and group.element not in self.compCpt:
                    if self.current_kanji:
                        print(
                            f"{self.current_kanji.kId()}: Incorrectly started multi-part group"
                        )
                elif group.element and self.compCpt[group.element] != group.part - 1:
                    if self.current_kanji:
                        print(
                            f"{self.current_kanji.kId()}: Incorrectly splitted multi-part group"
                        )
            if group.element and group.part:
                self.compCpt[group.element] = group.part

    def handle_end_g(self):
        if len(self.groups) == 0:
            return
        group = self.groups.pop()
        # End of kanji?
        if len(self.groups) == 1:  # index 1 - ignore root group
            if self.current_kanji:
                self.current_kanji.strokes = group
            self.current_kanji = None
            self.groups = []

    def handle_start_path(self, attrs):
        parent = None if len(self.groups) == 0 else self.groups[-1]
        stroke = Stroke(parent)
        if "kvg:type" in attrs:
            stroke.element = unicode(attrs["kvg:type"])
        if "d" in attrs:
            stroke.svg = unicode(attrs["d"])
        self.groups[-1].children.append(stroke)
