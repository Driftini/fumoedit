from datetime import date
from os import path
from pathlib import Path
import re
import yaml

SITE_ROOT = Path(".")  # Path to site root

class Picture:
    def __init__(self, collection):
        self.thumbnail_name = ""  # ext MUST be .jpg
        self.thumbnail_offset = ["center", "center"]
        self.variants = []
        self.collection = collection  # Reference to the post's collection

    def new_variant(self):
        v = PictureVariant(self.collection)
        self.variants.append(v)

        return v

    def get_collection(self):
        return self.collection[0]

    def get_thumbnail_path(self):
        return f"/assets/img/posts/{self.get_collection()}/thumbs/{self.thumbnail_name}"

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
        self.collection = collection  # Reference to the post's collection

    def get_collection(self):
        return self.collection[0]

    def get_path(self):
        return f"/assets/img/posts/{self.get_collection[0]}/{self.filename}"

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
            "file": self.get_path()
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
        self.collection = [None]
        self.set_collection("blog")

    def set_date(self, year, month, day):
        year, month, day = int(year), int(month), int(day)

        self.date = date(year, month, day)

    def new_picture(self):
        if self.is_picturepost():
            p = Picture(self.collection)
            self.pictures.append(p)

            return p

    def set_collection(self, collection):
        # Wrapped in an array so it can be passed by reference
        self.collection[0] = collection

    def get_collection(self):
        return self.collection[0]

    def is_picturepost(self):
        return self.get_collection() != "blog"

    def get_internal_name(self):
        # YYYY-mm-dd-id, used for the filename
        return f"{self.date.isoformat()}-{self.id}"

    def get_filename(self):
        # is this really needed anymore?
        return f"{self.get_internal_name()}.md"

    def get_thumbnail_path(self):
        return f"/assets/img/{self.get_collection()}/{self.thumbnail}"

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
            d.update({"thumbnail": self.get_thumbnail_path()})

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


def filename_valid(filename):
    if re.search("^\d{4}-\d{2}-\d{2}-.+(\.md)$", filename):
        return True
    else:
        return False


def save_post_file(post, folderpath):
    # Post files can be freely saved to any folder
    # (collection info may be lost because of poor design)
    with open(f"{folderpath}/{post.get_filename()}",
              mode="w", encoding="utf-8") as f:
        content = post.generate()
        f.write(content)
    
def load_post_file(filepath):
    basename = path.basename(filepath)

    if filename_valid(basename):
        with open(filepath, mode="r", encoding="utf-8") as f:
            content = f.read()

        content = content.split("---\n")
        props = yaml.load(content[1], yaml.Loader)
        body = content[2]

        # Post setup
        post = Post()

        # Setup post metadata (date, ID, collection)
        metadata = basename[:-3]  # trim file extension (always .md)
        metadata = metadata.split("-")  # split year, month, day and ID

        post.set_date(metadata[0], metadata[1], metadata[2])
        post.id = metadata[3]
        post.set_collection(Path(filepath).parts[-2])

        # Setup post properties
        post.title = props["title"]
        post.body = body
        if "thumbnail" in props:
            post.thumbnail = props["thumbnail"]

        # Setup post attachments
        if post.is_picturepost() and "pictures" in props:
            for p in props["pictures"]:
                picture_obj = post.new_picture()

                picture_obj.thumbnail_name = path.basename(p["thumbnail"])
                picture_obj.thumbnail_offset = p["thumbpos"].split(" ")

                for i in range(0, 2):
                    if picture_obj.thumbnail_offset[i] != "center":
                        # Shave off the "px" suffix
                        picture_obj.thumbnail_offset[i] = picture_obj.thumbnail_offset[i][:-2]

                if "variants" in p:
                    for v in p["variants"]:
                        variant_obj = picture_obj.new_variant()

                        variant_obj.filename = path.basename(v["file"])
                        if "label" in v:
                            variant_obj.label = v["label"]

        return post