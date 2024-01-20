from datetime import date
from os import path
import re
import yaml

CURRENT_POST_VERSION = 3


class Collection:
    def __init__(self, id, label):
        self.id = id
        self.label = label
        # img_id only really exists because
        # of blog using both "posts" and "blog"

    def get_post_path(self):
        return f"/_{self.id}"

    def get_img_path(self):
        if self.id == "posts":
            return f"/assets/img/posts/blog"
        else:
            return f"/assets/img/posts/{self.id}"


COLLECTIONS = {
    "posts": Collection("posts", "Blog"),
    "artwork": Collection("artwork", "Artwork")
}


class Picture:
    def __init__(self, collection):
        self.original_filename = ""
        self.thumbnail_filename = ""
        self.thumbnail_offset = 50
        self.label = ""
        self.collection = collection  # Reference to the post's collection

    def get_original_path(self):
        return f"{self.collection.get_img_path()}/{self.original_filename}"

    def get_thumbnail_path(self):
        return f"{self.collection.get_img_path()}/thumbs/{self.thumbnail_filename}"

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
            "thumbnail": self.get_thumbnail_path(),
            "thumbpos": self.thumbnail_offset,
            "original": self.get_original_path(),
        }

        if self.has_label():
            d.update({"label": self.label})

        return d

    def generate(self):
        gen = yaml.dump(self.get_dict())
        return gen


class Post:
    def __init__(self, collection):
        self.id = "blankpost"  # Used in the internal name
        self.title = "Blank Post"  # Display name
        self.priority_thumbnail = ""  # Optional thumbnail override
        self.date = date.today()
        self.body = ""
        self.tags = []
        self.pictures = []  # Attached pictures
        self.collection = collection

    def set_date(self, year, month, day):
        year, month, day = int(year), int(month), int(day)

        self.date = date(year, month, day)

    def new_picture(self):
        if self.is_picturepost():
            p = Picture(self.collection)
            self.pictures.append(p)

            return p

    def is_picturepost(self):
        return self.collection.id != "posts"

    def get_internal_name(self):
        # YYYY-mm-dd-id, used for the filename
        return f"{self.date.isoformat()}-{self.id}"

    def get_filename(self):
        # is this really needed anymore?
        return f"{self.get_internal_name()}.md"

    def get_prioritythumbnail_path(self):
        return f"{self.collection.get_img_path()}/thumbs/{self.priority_thumbnail}"

    def get_pictures_dicts(self):
        dicts = []

        for p in self.pictures:
            dicts.append(p.get_dict())

        return dicts

    def get_dict(self):
        d = {
            "title": self.title,
            "version": CURRENT_POST_VERSION
        }

        if self.is_picturepost():
            d.update({"pictures": self.get_pictures_dicts()})

        if len(self.priority_thumbnail) > 0:
            d.update({"prioritythumb": self.get_prioritythumbnail_path()})

        if len(self.tags) > 0:
            d.update({"tags": self.tags})

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


def post_to_file(post, folderpath):
    # Post files can be freely saved to any folder
    # (collection info may be lost because of poor design)
    folderpath = path.normpath(folderpath)

    with open(f"{folderpath}/{post.get_filename()}",
              mode="w", encoding="utf-8") as f:
        content = post.generate()
        f.write(content)


def post_from_file(filepath):
    # Determine the version of the given post file,
    # and call the according post_from_vX method
    basename = path.basename(filepath)

    if filename_valid(basename):
        with open(filepath, mode="r", encoding="utf-8") as f:
            file_content = f.read()

        try:
            parts = file_content.split("---\n", 2)
            parts.pop(0)
            # The split stops at index 2 to account
            # for separators in the post body (---)

            # First part is front matter,
            # second part is post body

            # First of all, check whether or not the post is up to date
            post_version = CURRENT_POST_VERSION

            if (
                "[" in parts[0]
                or "maxres" in parts[0]
                or "lowres" in parts[0]
            ):
                # Square brackets were used in pre-FumoEdit (V1) posts,
                # whose indentation breaks PyYAML and that have
                # hardcoded variant names (lowres/maxres)
                post_version = 1
            elif (
                "variants:" in parts[0]
                or "thumbnail" in yaml.load(parts[0], yaml.Loader)
            ):
                # Picture variants and the "thumbnail" POST (not picture)
                # property were last used in pre-redesign (V2) posts
                post_version = 2

            if post_version < CURRENT_POST_VERSION:
                # If the post needs to be upgraded from an older version,
                # make a backup before upgrading
                with open(f"{filepath}.bak",
                          mode="w", encoding="utf-8") as f:
                    f.write(file_content)

                # Upgrade the post one version at a time,
                # until it's fully up to date
                while post_version < CURRENT_POST_VERSION:
                    exec(f"parts[0] = upgrade_from_v{post_version}({parts})")
                    post_version += 1

            # Now that the post is up to date, it can be loaded normally
            props = yaml.load(parts[0], yaml.Loader)
            body = parts[1]
            body = body[:-1]  # Erase trailing newline

            # Setup post metadata (date, ID, collection)
            metadata = basename[:-3]  # trim file extension (always .md)
            metadata = metadata.split("-")  # split year, month, day and ID

            # Retrieve collection from the post's containing folder's name
            collection_name = path.dirname(filepath).split("/")[-1]
            collection_name = collection_name[1:]  # shave off the underscore

            post = Post(COLLECTIONS[collection_name])
            post.set_date(metadata[0], metadata[1], metadata[2])
            post.id = metadata[3]

            # Setup post properties
            post.title = props["title"]
            post.body = body
            if "prioritythumb" in props:
                post.priority_thumbnail = path.basename(props["prioritythumb"])

            if "tags" in props:
                post.tags = props["tags"]

            # Setup post attachments
            if post.is_picturepost() and "pictures" in props:
                for p in props["pictures"]:
                    picture_obj = post.new_picture()

                    picture_obj.original_filename = path.basename(p["original"])
                    picture_obj.thumbnail_filename = path.basename(p["thumbnail"])
                    picture_obj.thumbnail_offset = p["thumbpos"]

                    if "label" in p:
                        picture_obj.label = p["label"]

            return post
        except yaml.scanner.ScannerError:
            raise
        except (KeyError, AttributeError):
            raise
    else:
        raise PostNameError


def upgrade_from_v1(parts):
    # Remove indentation to make the file readable by PyYAML
    lines = parts[0].split("\n")
    parts[0] = ""

    for line in lines:
        parts[0] += line.lstrip() + "\n"

    # Replace hardcoded variant names with the variants list
    hardcoded_names = ["lowres", "maxres"]

    props = yaml.load(parts[0], yaml.Loader)

    if "pictures" in props:
        for p in props["pictures"]:
            p["variants"] = []

            for n in hardcoded_names:
                if n in p:
                    p["variants"].append(p[n])
                    p.pop(n)

    parts[0] = yaml.dump(props)

    return parts[0]


def upgrade_from_v2(parts):
    # Set every picture's V3 properties based on the first
    # variant's properties, while discarding any additional variants
    # Finally, rename priority thumbnail property

    props = yaml.load(parts[0], yaml.Loader)

    if "pictures" in props:
        for p in props["pictures"]:
            p["thumbpos"] = 50
            # Thumbnail offset gets reset to 50%,
            # since double px offsets have been dropped

            p["original"] = path.basename(p["variants"][0]["file"])

            if ("label" in p["variants"][0]):
                p["label"] = p["variants"][0]["label"]

            p.pop("variants")

    if "thumbnail" in props:
        props["prioritythumb"] = props["thumbnail"]
        del props["thumbnail"]

    parts[0] = yaml.dump(props)

    return parts[0]


# Exceptions

class PostNameError(Exception):
    pass
