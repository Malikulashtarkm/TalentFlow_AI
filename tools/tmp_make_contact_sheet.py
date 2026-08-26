from PIL import Image, ImageDraw
from pathlib import Path
folder = Path(r'D:\TalentFlow_AI\tmp_midsem_render')
imgs = [Image.open(p).convert('RGB') for p in sorted(folder.glob('page-*.png'), key=lambda p: int(p.stem.split('-')[1]))]
w, h, margin, cols = 255, 330, 20, 3
rows = (len(imgs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (w + margin) + margin, rows * (h + 50) + margin), 'white')
d = ImageDraw.Draw(sheet)
for i, img in enumerate(imgs):
    img.thumbnail((w, h))
    x = margin + (i % cols) * (w + margin)
    y = margin + (i // cols) * (h + 50)
    sheet.paste(img, (x, y))
    d.text((x, y + img.height + 5), f'Page {i+1}', fill=(0,0,0))
sheet.save(folder / 'contact_sheet.png')
