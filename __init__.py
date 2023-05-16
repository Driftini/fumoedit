import datetime
import pathlib
import yaml


class Picture:
    def __init__(self, path="/assets/idk.jpg",
                 offset=("center", "center"), variants=[]):
        self.thumbnail_path = path
        self.thumbnail_offset = offset
        self.variants = variants

    def get_full_offset(self):
        x = self.thumbnail_offset[0]
        y = self.thumbnail_offset[1]

        if x != "center":
            x = f"{x}px"
        if y != "center":
            y = f"{y}px"

        return f"{x} {y}"

    def get_variants_dicts(self):
        dicts = []

        for v in self.variants:
            dicts.append(v.get_dict())

        return dicts

    def get_dict(self):
        d = {
            "thumbnail": self.thumbnail_path,
            "thumbpos": self.get_full_offset(),
            "variants": self.get_variants_dicts()
        }
        return d

    def generate(self):
        gen = yaml.dump(self.get_dict())
        return gen


class PictureVariant:
    def __init__(self, path="/gggah.png", label=""):
        self.path = path
        self.label = label

    def has_label(self):
        if len(self.label) > 0:
            return True
        else:
            return False

    def get_label(self):
        if self.has_label():
            return "<no label>"
        else:
            return self.label

    def get_dict(self):
        d = {
            "file": self.path
        }

        if self.has_label():
            d.update({"label": self.label})

        return d


class Post:
    def __init__(self, is_picturepost=False):
        self.id = "blankpost"  # Used in the internal name
        self.title = "Blank Post"  # Display name
        self.thumbnail = ""  # Optional, thumbnail path/name???
        self.date = datetime.date.today()
        self.body = ""

        self.is_picturepost = is_picturepost  # Used in the generation method
        if self.is_picturepost:
            self.pictures = []  # Attached pictures

    def set_date(self, year, month, day):
        year = str(year).rjust(4, "0")
        month = str(month).rjust(2, "0")
        day = str(day).rjust(2, "0")

        isoformat = f"{year}-{month}-{day}"

        self.date = datetime.date.fromisoformat(isoformat)

    def get_internal_name(self):
        # YYYY-mm-dd-id, used for the filename
        return f"{self.date.isoformat()}-{self.id}"

    def get_filename(self):
        return f"{self.get_internal_name()}.md"

    def get_excerpt(self):
        # Trimmed body, used in collection index pages
        body_substring = self.body.slice(0, 500)

        return f"{body_substring}..."

    def get_pictures_dicts(self):
        dicts = []

        for p in self.pictures:
            dicts.append(p.get_dict())

        return dicts

    def get_dict(self):
        d = {
            "title": self.title
        }

        if self.is_picturepost:
            d.update({"pictures": self.get_pictures_dicts()})

        if len(self.thumbnail) > 0:
            d.update({"thumbnail": self.thumbnail})

        return d

    def get_frontmatter(self):
        fm = yaml.dump(self.get_dict())
        fm = fm[:-1]  # erase trailing newline

        return fm

    def generate(self):
        gen = f"""\
---
{self.get_frontmatter()}
---
{self.body}
"""

        return gen


def load_post_file():
    pass
