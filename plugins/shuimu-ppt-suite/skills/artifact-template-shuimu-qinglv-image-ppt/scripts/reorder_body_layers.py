#!/usr/bin/env python3
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

ET.register_namespace("p", P_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("r", R_NS)


def slide_sort_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def reorder_slide(data: bytes, name: str) -> tuple[bytes, bool]:
    root = ET.fromstring(data)
    tree = root.find(f".//{{{P_NS}}}spTree")
    if tree is None:
        raise ValueError(f"Missing p:spTree in {name}")

    body_pictures = []
    for child in list(tree):
        if child.tag != f"{{{P_NS}}}pic":
            continue
        transform = child.find(f"./{{{P_NS}}}spPr/{{{A_NS}}}xfrm")
        offset = transform.find(f"{{{A_NS}}}off") if transform is not None else None
        extent = transform.find(f"{{{A_NS}}}ext") if transform is not None else None
        is_full_slide = (
            offset is not None
            and extent is not None
            and int(offset.get("x", "-1")) == 0
            and int(offset.get("y", "-1")) == 0
            and int(extent.get("cx", "0")) >= 12_000_000
            and int(extent.get("cy", "0")) >= 6_700_000
        )
        if is_full_slide:
            body_pictures.append(child)

    if len(body_pictures) != 1:
        raise ValueError(
            f"Expected exactly one generated body picture in {name}; found {len(body_pictures)}"
        )

    body = body_pictures[0]
    tree.remove(body)
    children = list(tree)
    insert_at = 0
    for index, child in enumerate(children):
        if child.tag in {f"{{{P_NS}}}nvGrpSpPr", f"{{{P_NS}}}grpSpPr"}:
            insert_at = index + 1
    tree.insert(insert_at, body)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), True


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: reorder_body_layers.py <deck.pptx>")

    deck = Path(sys.argv[1]).resolve()
    if not deck.is_file() or deck.suffix.lower() != ".pptx":
        raise SystemExit(f"Missing PPTX: {deck}")

    with zipfile.ZipFile(deck, "r") as source:
        names = source.namelist()
        slide_names = sorted(
            [
                name
                for name in names
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ],
            key=slide_sort_key,
        )
        if not slide_names:
            raise SystemExit("PPTX contains no slide XML files")

        modified = {}
        for name in slide_names:
            modified[name], _ = reorder_slide(source.read(name), name)

        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{deck.stem}-layers-", suffix=".pptx", dir=deck.parent
        )
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w") as target:
                for info in source.infolist():
                    data = modified.get(info.filename, source.read(info.filename))
                    target.writestr(info, data)
            os.replace(temporary, deck)
        finally:
            temporary.unlink(missing_ok=True)

    print(json.dumps({"slidesReordered": len(slide_names)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
