"""
Crop and box-downscale a PNG, with nothing but the standard library.

Only used to build web/icons/*.png from the SVG sources: headless Chromium can
rasterize the SVG but not reliably at an exact size, so we render generously
and crop/scale here rather than adding Pillow as a dependency for three icons.

Usage:
    python3 tools/png_tool.py in.png out.png --crop 512 --scale 256
"""
import argparse
import struct
import zlib


def read_png(path):
    """Return (width, height, rgba_bytes) for an 8-bit RGB/RGBA PNG."""
    data = path_bytes(path)
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")

    pos = 8
    width = height = None
    channels = 4
    idat = bytearray()
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        chunk = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        if chunk == b"IHDR":
            width, height, depth, color_type = struct.unpack(">IIBB", body[:10])
            if depth != 8 or color_type not in (2, 6):
                raise ValueError(f"unsupported PNG: depth={depth} color_type={color_type}")
            channels = 3 if color_type == 2 else 4
        elif chunk == b"IDAT":
            idat += body
        elif chunk == b"IEND":
            break
        pos += 12 + length

    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    out = bytearray(width * height * 4)
    previous = bytearray(stride)

    # Undo the per-scanline filters (PNG spec 9.2). Each line starts with a
    # filter-type byte, then `stride` filtered bytes.
    pos = 0
    for y in range(height):
        filter_type = raw[pos]
        pos += 1
        line = bytearray(raw[pos : pos + stride])
        pos += stride
        for x in range(stride):
            a = line[x - channels] if x >= channels else 0
            b = previous[x]
            c = previous[x - channels] if x >= channels else 0
            if filter_type == 1:
                line[x] = (line[x] + a) & 0xFF
            elif filter_type == 2:
                line[x] = (line[x] + b) & 0xFF
            elif filter_type == 3:
                line[x] = (line[x] + (a + b) // 2) & 0xFF
            elif filter_type == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pred) & 0xFF
        for x in range(width):
            src = x * channels
            dst = (y * width + x) * 4
            out[dst : dst + 3] = line[src : src + 3]
            out[dst + 3] = line[src + 3] if channels == 4 else 255
        previous = line

    return width, height, out


def path_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def write_png(path, width, height, rgba):
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (None): these are tiny, so don't optimise
        raw += rgba[y * width * 4 : (y + 1) * width * 4]

    def chunk(tag, body):
        payload = tag + body
        return struct.pack(">I", len(body)) + payload + struct.pack(">I", zlib.crc32(payload))

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(png)


def crop(width, height, rgba, size):
    out = bytearray(size * size * 4)
    for y in range(size):
        src = (y * width) * 4
        out[y * size * 4 : (y + 1) * size * 4] = rgba[src : src + size * 4]
    return out


def box_scale(size, rgba, target):
    """Average each source block into one target pixel - good enough, and much
    better than nearest-neighbour on an icon with thin white strokes."""
    factor = size / target
    out = bytearray(target * target * 4)
    for ty in range(target):
        y0, y1 = int(ty * factor), max(int(ty * factor) + 1, int((ty + 1) * factor))
        for tx in range(target):
            x0, x1 = int(tx * factor), max(int(tx * factor) + 1, int((tx + 1) * factor))
            totals = [0, 0, 0, 0]
            count = 0
            for sy in range(y0, min(y1, size)):
                base = sy * size * 4
                for sx in range(x0, min(x1, size)):
                    p = base + sx * 4
                    totals[0] += rgba[p]
                    totals[1] += rgba[p + 1]
                    totals[2] += rgba[p + 2]
                    totals[3] += rgba[p + 3]
                    count += 1
            dst = (ty * target + tx) * 4
            for i in range(4):
                out[dst + i] = totals[i] // count
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("dest")
    parser.add_argument("--crop", type=int, required=True, help="square crop from the top-left")
    parser.add_argument("--scale", type=int, help="box-downscale the crop to this size")
    args = parser.parse_args()

    width, height, rgba = read_png(args.source)
    if width < args.crop or height < args.crop:
        raise SystemExit(f"source {width}x{height} is smaller than the {args.crop}px crop")

    pixels = crop(width, height, rgba, args.crop)
    size = args.crop
    if args.scale and args.scale != size:
        pixels = box_scale(size, pixels, args.scale)
        size = args.scale

    write_png(args.dest, size, size, pixels)
    print(f"{args.dest}: {size}x{size}")


if __name__ == "__main__":
    main()
