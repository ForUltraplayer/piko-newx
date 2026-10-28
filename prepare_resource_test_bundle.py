# @file prepare_resource_test_bundle.py
# @author: ForUltraplayer
# @brief Package a Korean resource-only test bundle from an official Piko release.

from argparse import ArgumentParser
from collections import Counter
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


def prepare_resource_test_bundle(
    original: Path,
    output: Path,
    bundle_name: str = "Piko Korean Resource Test",
    bundle_version: str = "3.66.0-ko-resource.1",
) -> dict:
    """Preserve executable entries and add translations used by the original bundle."""
    if original.resolve() == output.resolve():
        raise ValueError("The original release must be preserved")
    catalog = ElementTree.parse(
        Path(__file__).resolve().parent / "locales/ko/newx/strings.xml"
    ).getroot()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(original) as source:
        manifest = source.read("META-INF/MANIFEST.MF").decode("utf-8")
        version = re.search(r"(?m)^Version: ([^\r\n]+)", manifest)
        if version is None or version.group(1) != "3.66.0":
            raise ValueError("This resource test requires the official Piko 3.66.0 bundle")
        english = {
            node.attrib["name"]: node.text or ""
            for node in ElementTree.fromstring(source.read("addresources/values/newx/strings.xml"))
            if node.get("translatable") != "false"
        }
        translated = ElementTree.Element("resources")
        tokens = re.compile(r"%(?:\d+\$)?[a-zA-Z%]|\{[^{}]+\}")
        for node in catalog:
            name = node.attrib["name"]
            if name in english:
                if Counter(tokens.findall(node.text or "")) != Counter(tokens.findall(english[name])):
                    raise ValueError(f"Invalid Korean format tokens: {name}")
                translated.append(node)
        if len(translated) != len(english):
            raise ValueError("The Korean catalog does not cover the official bundle")
        ElementTree.indent(translated, space="    ")
        korean = b'<?xml version="1.0" encoding="utf-8"?>\n' + ElementTree.tostring(translated, encoding="utf-8") + b"\n"
        manifest = re.sub(r"(?m)^Name: [^\r\n]+", f"Name: {bundle_name}", manifest)
        manifest = re.sub(r"(?m)^Version: [^\r\n]+", f"Version: {bundle_version}", manifest)
        manifest = re.sub(r"(?m)^Description: [^\r\n]+", "Description: Korean settings resources; original executable code", manifest)
        manifest = re.sub(r"(?m)^Source: [^\r\n]+", "Source: https://github.com/ForUltraplayer/piko-newx", manifest)
        with ZipFile(output, "w") as target:
            for entry in source.infolist():
                if entry.filename == "addresources/values-ko-rKR/newx/strings.xml":
                    continue
                data = manifest.encode("utf-8") if entry.filename == "META-INF/MANIFEST.MF" else source.read(entry.filename)
                target.writestr(entry, data)
            target.writestr("addresources/values-ko-rKR/newx/strings.xml", korean)

    with ZipFile(original) as source, ZipFile(output) as target:
        if target.testzip() is not None:
            raise ValueError("Output bundle failed its ZIP integrity check")
        executable = [name for name in source.namelist() if name.endswith((".class", ".dex", ".mpe"))]
        if not all(source.read(name) == target.read(name) for name in executable):
            raise ValueError("The resource test bundle must preserve all executable entries")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return {"translated_strings": len(translated), "executable_entries_preserved": len(executable), "sha256": digest}


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--name", default="Piko Korean Resource Test")
    parser.add_argument("--version", default="3.66.0-ko-resource.1")
    arguments = parser.parse_args()
    print(prepare_resource_test_bundle(arguments.original, arguments.output, arguments.name, arguments.version))
