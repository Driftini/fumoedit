# Fumoedit
A simple Python module I plan to use as the backbone for [a proper editor](https://github.com/Driftini/fumoedit-qt) for [my website](https://driftini.github.io)'s posts.

## Post version glossary
* **V1**: introduced with FumoNet.
* **V2**: revision of V1 introduced with Smoothie's 2022 update.
    * Transition to YAML's simpler syntax (different indentation, no brackets).
    * Picture variants are moved from pictures' `lowres` and `maxres` properties to an array.
* **V3**: major restructuring introduced with FumoNet's 2023 redesign.
    * Picture thumbnails no longer have an horizontal offset.
    * Picture thumbnails' offset uses a percentage instead of pixels.
    * Picture variants removed.
    * Pictures' properties are now `thumbnail`, `thumbpos`, `original` and `label`.
    * Posts have tags.
    