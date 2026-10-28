# @file prepare_release.py
# @author: ForUltraplayer
# @brief Prepare signed Korean resource release assets without publishing them.

from argparse import ArgumentParser
import base64
from ctypes import Structure, POINTER, byref, c_ubyte, c_uint32, c_void_p, c_wchar_p, cast, create_string_buffer, windll
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
from tarfile import open as open_tar
from zipfile import ZipFile, ZIP_DEFLATED

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

from prepare_resource_test_bundle import prepare_resource_test_bundle


class DataBlob(Structure):
    _fields_ = [("size", c_uint32), ("data", POINTER(c_ubyte))]


def protect_key(data: bytes, decrypt: bool = False) -> bytes:
    """Use Windows DPAPI for the current account; plaintext keys never go to disk."""
    buffer = create_string_buffer(data)
    source = DataBlob(len(data), cast(buffer, POINTER(c_ubyte)))
    output = DataBlob()
    if decrypt:
        windll.crypt32.CryptUnprotectData.argtypes = [POINTER(DataBlob), c_void_p, c_void_p, c_void_p, c_void_p, c_uint32, POINTER(DataBlob)]
        success = windll.crypt32.CryptUnprotectData(byref(source), None, None, None, None, 1, byref(output))
    else:
        windll.crypt32.CryptProtectData.argtypes = [POINTER(DataBlob), c_wchar_p, c_void_p, c_void_p, c_void_p, c_uint32, POINTER(DataBlob)]
        success = windll.crypt32.CryptProtectData(byref(source), "Piko NewX Korean signing key", None, None, None, 1, byref(output))
    if not success:
        raise OSError("Windows could not protect or recover the release signing key")
    try:
        return bytes(output.data[:output.size])
    finally:
        windll.kernel32.LocalFree.argtypes = [c_void_p]
        windll.kernel32.LocalFree.restype = c_void_p
        windll.kernel32.LocalFree(output.data)


def verify_signature(path: Path) -> str:
    """Verify MorpheSig1 using the empty-comment archive digest from the official format."""
    data = path.read_bytes()
    with ZipFile(BytesIO(data)) as archive:
        parts = archive.comment.decode("ascii").split(" ")
    if len(parts) != 3 or parts[0] != "MorpheSig1":
        raise ValueError("The prepared bundle has no valid Morphe signature comment")
    comment = " ".join(parts).encode("ascii")
    unsigned = data[:-len(comment) - 2] + b"\0\0"
    message = b"MorpheSig1" + hashlib.sha256(unsigned).digest()
    Ed25519PublicKey.from_public_bytes(base64.b64decode(parts[1], validate=True)).verify(
        base64.b64decode(parts[2], validate=True), message
    )
    return parts[1]


def prepare_release(original: Path, upstream_source: Path, version: str, key_file: Path) -> Path:
    if re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        raise ValueError("Use a three-part release version without a leading v")
    original_digest = hashlib.sha256(original.read_bytes()).hexdigest()
    if original_digest != "070d90cf271e959c98acc864d631e7200ad124ad8f26b14365b73ec47fd93620":
        raise ValueError("The input differs from the verified official Piko 3.66.0 bundle")
    source_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=upstream_source, check=True, capture_output=True, text=True).stdout.strip()
    if source_commit != "48af8e1a7438e6d4d2f18ebe894acdcc0eeb7272":
        raise ValueError("The corresponding source checkout is not the verified upstream commit")
    root = Path(__file__).resolve().parent
    output = root / "dist" / f"release-v{version}"
    output.mkdir(parents=True, exist_ok=True)
    bundle = output / f"piko-newx-korean-{version}.mpp"
    result = prepare_resource_test_bundle(original, bundle, "Piko NewX Korean", version)
    if key_file.exists():
        key = Ed25519PrivateKey.from_private_bytes(protect_key(key_file.read_bytes(), decrypt=True))
    else:
        key = Ed25519PrivateKey.generate()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_bytes(protect_key(key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())))
    public_bytes = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    public_key = base64.b64encode(public_bytes).decode("ascii")
    unsigned = bundle.read_bytes()
    with ZipFile(BytesIO(unsigned)) as archive:
        if archive.comment:
            raise ValueError("Release bundling must produce an empty archive comment before signing")
    signature = key.sign(b"MorpheSig1" + hashlib.sha256(unsigned).digest())
    comment = f"MorpheSig1 {public_key} {base64.b64encode(signature).decode('ascii')}".encode("ascii")
    bundle.write_bytes(unsigned[:-2] + len(comment).to_bytes(2, "little") + comment)
    if verify_signature(bundle) != public_key:
        raise ValueError("Release signature did not match the selected public key")
    (output / "public-key.txt").write_text(public_key + "\n", encoding="utf-8")
    fingerprint = hashlib.sha256(public_bytes).hexdigest()[:16]
    fingerprint = " ".join(fingerprint[index:index + 4] for index in range(0, 16, 4))
    base_url = f"https://github.com/ForUltraplayer/piko-newx/releases/download/v{version}"
    metadata = {
        "version": f"v{version}",
        "download_url": f"{base_url}/{bundle.name}",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "description": "Piko NewX Korean: 469 translated settings strings, based on Piko 3.66.0.",
        "public_key": public_key,
        "app_version": "12.37.2-prod.01",
        "piko_commit": "48af8e1a7438e6d4d2f18ebe894acdcc0eeb7272",
    }
    (output / "patches-bundle.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_zip = output / f"piko-newx-korean-{version}-source.zip"
    archive = subprocess.run(["git", "archive", "HEAD"], cwd=upstream_source, check=True, capture_output=True).stdout
    build_instructions = (
        "# Corresponding source\n\n"
        "This release adds Korean resources to the official Piko 3.66.0 bundle.\n"
        "The original executables are unchanged; this is not a build of the pending 85-string source patch.\n\n"
        "The pristine corresponding Piko source is in upstream/piko/. See its LICENSE and NOTICE.\n"
        "Download the official patches-3.66.0.mpp from https://github.com/crimera/piko-newx/releases/tag/v3.66.0.\n"
        f"Its SHA-256 must be {hashlib.sha256(original.read_bytes()).hexdigest()}.\n"
        "Run python prepare_resource_test_bundle.py patches-3.66.0.mpp output.mpp "
        f"--name \"Piko NewX Korean\" --version {version}.\n"
        "This reproduces the resource overlay and manifest; production signing requires the maintainer's private key.\n"
        "MorpheSig1 is an Ed25519 signature in the ZIP comment, as defined by MorpheApp/morphe-patcher.\n"
    )
    with ZipFile(source_zip, "w", ZIP_DEFLATED) as target, open_tar(fileobj=BytesIO(archive)) as sources:
        for member in sources:
            if member.isfile():
                content = sources.extractfile(member)
                if content is not None:
                    target.writestr("upstream/piko/" + member.name, content.read())
        target.write(root / "prepare_resource_test_bundle.py", "prepare_resource_test_bundle.py")
        target.write(root / "prepare_release.py", "prepare_release.py")
        with ZipFile(bundle) as release:
            target.writestr("locales/ko/newx/strings.xml", release.read("addresources/values-ko-rKR/newx/strings.xml"))
        target.writestr("BUILD.md", build_instructions)
    # The wrapper initially wrote the unsigned hash; replace it after adding the signature.
    bundle.with_suffix(".mpp.sha256").unlink()
    checksums = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [bundle, source_zip, output / "public-key.txt", output / "patches-bundle.json"]}
    (output / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in checksums.items()), encoding="utf-8")
    report = {
        "release": f"v{version}",
        "upstream_release": "v3.66.0",
        "upstream_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "bundle_sha256": checksums[bundle.name],
        "translated_strings": result["translated_strings"],
        "executable_entries_preserved": result["executable_entries_preserved"],
        "public_key": public_key,
        "fingerprint": fingerprint,
        "validation": {"signature": "passed", "runtime_menu": "user reported success on the resource test bundle", "pending_source_strings": 85},
        "publication": "prepared locally; not published",
    }
    (output / "release-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "translated_strings": 469, "fingerprint": fingerprint}, ensure_ascii=False))
    return output


if __name__ == "__main__":
    parser = ArgumentParser(description="Prepare signed local release artifacts without publishing")
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--original", type=Path, default=Path("bins/upstream-release/patches-3.66.0.mpp"))
    parser.add_argument("--upstream-source", type=Path, default=Path("bins/source/piko"))
    parser.add_argument("--key-file", type=Path, default=Path("bins/signing/ed25519.dpapi"))
    arguments = parser.parse_args()
    prepare_release(arguments.original, arguments.upstream_source, arguments.version, arguments.key_file)
