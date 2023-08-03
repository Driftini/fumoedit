from datetime import date
from os import path
import re
import yaml


class Picture:
    def __init__(self, collection):
        self.thumbnail_name = ""
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
        return f"/assets/img/posts/{self.get_collection()}/{self.filename}"

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

        # Internal name of the post's collection (posts, walls...)
        self.collection = [None]
        self.set_collection("posts")

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
        return self.get_collection() != "posts"

    def get_internal_name(self):
        # YYYY-mm-dd-id, used for the filename
        return f"{self.date.isoformat()}-{self.id}"

    def get_filename(self):
        # is this really needed anymore?
        return f"{self.get_internal_name()}.md"

    def get_thumbnail_path(self):
        return f"/assets/img/posts/{self.get_collection()}/{self.thumbnail}"

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
    # Verify if filename follows the YYYY-MM-DD-ID.md format
    if re.search("^\d{4}-\d{2}-\d{2}-.+(\.md)$", filename):
        return True
    else:
        return False


def get_foldername(filepath):
    return filepath.split("/")[-2]


def post_to_file(post, folderpath):
    # Post files can be freely saved to any folder
    # (collection info may be lost because of poor design)
    folderpath = path.normpath(folderpath)

    with open(f"{folderpath}/{post.get_filename()}",
              mode="w", encoding="utf-8") as f:
        content = post.generate()
        f.write(content)


def post_from_file(filepath):
    basename = path.basename(filepath)

    if filename_valid(basename):
        with open(filepath, mode="r", encoding="utf-8") as f:
            file_content = f.read()

        try:
            compat_mode = False
            parts = file_content.split("---\n", 2)

            if "[" in parts[1]:
                # Square brackets were used in pre-FumoEdit posts,
                # whose indentation breaks PyYAML and that have
                # a slightly different structure (hardcoded variant names)
                compat_mode = True

            if compat_mode:
                # Remove indentation to make the file readable by PyYAML
                lines = parts[1].split("\n")
                parts[1] = ""

                for line in lines:
                    parts[1] += line.lstrip() + "\n"

            props = yaml.load(parts[1], yaml.Loader)
            body = parts[2]
            body = body[:-1]  # Erase trailing newline

            # Setup post metadata (date, ID, collection)
            metadata = basename[:-3]  # trim file extension (always .md)
            metadata = metadata.split("-")  # split year, month, day and ID

            post = Post()
            post.set_date(metadata[0], metadata[1], metadata[2])
            post.id = metadata[3]

            # Retrieve collection from the post's containing folder's name
            collection_name = get_foldername(filepath)
            collection_name = collection_name[1:]  # shave off the underscore

            post.set_collection(collection_name)

            # Setup post properties
            post.title = props["title"]
            post.body = body
            if "thumbnail" in props:
                thumbpath_prefix = f"/assets/img/posts/{post.get_collection()}/"
                post.thumbnail = props["thumbnail"].removeprefix(thumbpath_prefix)

            # Setup post attachments
            if post.is_picturepost() and "pictures" in props:
                for p in props["pictures"]:
                    picture_obj = post.new_picture()

                    picture_obj.thumbnail_name = path.basename(p["thumbnail"])
                    picture_obj.thumbnail_offset = p["thumbpos"].split(" ")

                    for i in range(0, 2):
                        if picture_obj.thumbnail_offset[i] != "center":
                            # Shave off the "px" suffix, if present
                            if "px" in picture_obj.thumbnail_offset[i]:
                                picture_obj.thumbnail_offset[i] = picture_obj.thumbnail_offset[i][:-2]

                            picture_obj.thumbnail_offset[i] = int(
                                picture_obj.thumbnail_offset[i]
                            )

                    if not compat_mode:
                        if "variants" in p:
                            for v in p["variants"]:
                                variant_obj = picture_obj.new_variant()

                                variant_obj.filename = path.basename(v["file"])
                                if "label" in v:
                                    variant_obj.label = v["label"]
                    else:
                        # Pre-FumoEdit posts' pictures didn't have a variant
                        # list, instead using the following names
                        outdated_names = ["lowres", "maxres"]

                        for n in outdated_names:
                            if n in p:
                                variant_obj = picture_obj.new_variant()

                                variant_obj.filename = path.basename(
                                    p[n]["file"]
                                )
                                if "label" in p[n]:
                                    variant_obj.label = p[n]["label"]
            return post
        except yaml.scanner.ScannerError:
            raise
        except (KeyError, AttributeError):
            raise
    else:
        raise PostNameError


# Exceptions

class PostNameError(Exception):
    pass
