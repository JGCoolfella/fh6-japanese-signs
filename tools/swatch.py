"""Read/write FH6 .swatchbin ('burG') textures. Layout from fh6upscale's FORMAT.md."""
import struct

import numpy as np
import texture2ddecoder
from PIL import Image

# format code -> (name, bytes per 4x4 block, decoder)
FORMATS = {
    0: ("BC1", 8, texture2ddecoder.decode_bc1),
    3: ("BC4", 8, texture2ddecoder.decode_bc4),
    5: ("BC5", 16, texture2ddecoder.decode_bc5),
    9: ("BC7", 16, texture2ddecoder.decode_bc7),
}


def parse(data):
    if data[:4] != b"burG":
        raise ValueError("not a swatchbin")
    header_size = struct.unpack_from("<I", data, 8)[0]
    width, height = struct.unpack_from("<II", data, 76)
    mips = data[90]
    fmt = struct.unpack_from("<I", data, 116)[0]
    return {"header_size": header_size, "width": width, "height": height, "mips": mips, "format": fmt}


def to_image(data):
    info = parse(data)
    if info["format"] not in FORMATS:
        raise ValueError(f"unsupported format code {info['format']}")
    _, block, decode = FORMATS[info["format"]]
    w, h = info["width"], info["height"]
    size = max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * block
    start = info["header_size"]
    raw = decode(data[start:start + size], w, h)  # BGRA
    arr = np.frombuffer(raw, np.uint8).reshape(h, w, 4)[:, :, [2, 1, 0, 3]]
    return Image.fromarray(arr, "RGBA"), info
