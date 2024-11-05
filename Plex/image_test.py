from PIL import Image, ImageFilter

test_file = "test.png"

test_types = ['jpg', 'png', 'webp']

with Image.open(test_file) as new_poster:
    new_poster = new_poster.convert("RGB").resize((1000, 1500), Image.LANCZOS)

    for t_type in test_types:
        for i in range(0, 100, 5):
            temp = f"temp_{i}.{t_type}"
            new_poster.save(temp, quality=i)
