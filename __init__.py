from datetime import date
import pathlib
import yaml

SITE_ROOT = ""  # Path to site root

class Picture:
    def __init__(self, collection):
        self.thumbnail_name = ""
        self.thumbnail_offset = ["center", "center"]
        self.variants = []
        self.collection = collection # Reference to the post's collection

    def new_variant(self):
        self.variants.append(PictureVariant(self.collection))

    def get_thumbnail_path(self):
        return f"{SITE_ROOT}/assets/img/posts/{self.collection}/thumbs/{self.thumbnail_name}.jpg"

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
            "thumbnail": self.get_thumbnail_path(),
            "thumbpos": self.get_full_offset(),
            "variants": self.get_variants_dicts()
        }
        return d

    def generate(self):
        gen = yaml.dump(self.get_dict())
        return gen


class PictureVariant:
    def __init__(self, collection):
        self.filename = ""
        self.label = ""
        self.collection = collection # Reference to the post's collection

    def get_path(self):
        return f"{SITE_ROOT}/assets/img/posts/{self.collection}/{self.filename}"

    def has_label(self):
        if len(self.label) > 0:
            return True
        else:
            return False

    def get_label(self):
        if self.has_label():
            return self.label
        else:
            return "<no label>"

    def get_dict(self):
        d = {
            "file": self.path
        }

        if self.has_label():
            d.update({"label": self.label})

        return d


class Post:
    def __init__(self):
        self.id = "blankpost"  # Used in the internal name
        self.title = "Blank Post"  # Display name
        self.thumbnail = ""  # Optional, thumbnail path/name???
        self.date = date.today()
        self.body = ""
        self.pictures = []  # Attached pictures

        # Internal name of the post's collection (blog, walls...)
        self.collection = "blog"

    def set_date(self, year, month, day):
        self.date = date(year, month, day)

    def new_picture(self):
        if self.is_picturepost():
            self.pictures.append(Picture(self.collection))

    def is_picturepost(self):
        return self.collection != "blog"  # and len(self.pictures) > 0

    def get_internal_name(self):
        # YYYY-mm-dd-id, used for the filename
        return f"{self.date.isoformat()}-{self.id}"

    def get_filename(self):
        # is this really needed anymore?
        return f"{self.get_internal_name()}.md"

    def get_full_path(self):
        return f"{SITE_ROOT}/{self.collection}/{self.get_filename()}"

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

        if self.is_picturepost():
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
