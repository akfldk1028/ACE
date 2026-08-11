"""Stack two archive sheets into one before/after comparison."""

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
PANELS = [
    ("c183-uijeongbu-multivol-archive.png",
     "BEFORE  -  coverage on the ground plate only:  3 floors [158, 608, 608]  ->  flat plates, 0 of 47 selected"),
    ("c195-probe-archive.png",
     "AFTER   -  coverage bounds every plate:        5 floors [275 x 5]        ->  buildings, 3 selected"),
]
BAND = 46
ROWS = 2  # keep the top two rows of each sheet


def main():
    panels = []
    for name, caption in PANELS:
        image = Image.open(HERE / name)
        # Each sheet is 4 rows of 300px tiles under a 30px title.
        crop = image.crop((0, 30, image.width, 30 + ROWS * 300))
        panels.append((crop, caption))

    width = max(crop.width for crop, _ in panels)
    height = sum(crop.height + BAND for crop, _ in panels)
    sheet = Image.new("RGB", (width, height), (247, 247, 245))
    draw = ImageDraw.Draw(sheet)

    y = 0
    for crop, caption in panels:
        draw.rectangle([0, y, width, y + BAND], fill=(16, 22, 34))
        draw.text((14, y + 16), caption, fill=(235, 238, 245))
        sheet.paste(crop, (0, y + BAND))
        y += BAND + crop.height

    out = HERE / "uijeongbu-before-after.png"
    sheet.save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
