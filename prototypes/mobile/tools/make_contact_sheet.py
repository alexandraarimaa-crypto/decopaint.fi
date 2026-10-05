from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / "previews"
OUTPUT = PREVIEWS / "00-mobile-concept-overview.png"
ITEMS = [
    ("01-home.png", "01  HOME"),
    ("02-menu.png", "02  MENU"),
    ("03-category.png", "03  CATEGORY"),
    ("04-product.png", "04  PRODUCT"),
    ("05-checkout.png", "05  CHECKOUT"),
]

background = (238, 237, 231)
card = (249, 248, 244)
ink = (18, 23, 19)
green = (8, 125, 67)
tile_width = 390
tile_height = 710
gap = 22
margin = 30
header_height = 62
columns = 3
rows = 2

canvas = Image.new(
    "RGB",
    (
        margin * 2 + columns * tile_width + (columns - 1) * gap,
        margin * 2 + rows * tile_height + (rows - 1) * gap,
    ),
    background,
)
draw = ImageDraw.Draw(canvas)
font = ImageFont.load_default(size=18)

for index, (filename, label) in enumerate(ITEMS):
    column = index % columns
    row = index // columns
    left = margin + column * (tile_width + gap)
    top = margin + row * (tile_height + gap)
    draw.rounded_rectangle(
        (left, top, left + tile_width, top + tile_height),
        radius=18,
        fill=card,
    )
    draw.text((left + 18, top + 20), label, font=font, fill=green)

    source = Image.open(PREVIEWS / filename).convert("RGB")
    phone_crop = source.crop((640, 0, 1090, 895))
    phone_crop.thumbnail((tile_width - 24, tile_height - header_height - 16))
    image_left = left + (tile_width - phone_crop.width) // 2
    image_top = top + header_height
    canvas.paste(phone_crop, (image_left, image_top))

canvas.save(OUTPUT, optimize=True)
print(OUTPUT)
