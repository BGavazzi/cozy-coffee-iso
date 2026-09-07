"""Contact sheet for a game_factory batch; never modifies the sprite pixels."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('batch', type=Path)
ap.add_argument('--out', type=Path, required=True)
args = ap.parse_args()
rows = json.loads(args.batch.read_text())
sheet = Image.new('RGB', (8 * 192, len(rows) * 224), '#182329')
draw = ImageDraw.Draw(sheet)
for y, row in enumerate(rows):
    result = json.loads(Path(row['build']).read_text())
    draw.text((8, y * 224 + 4), result['recipe']['piece']['name'] + ' | ' + result['status'], fill='#ecede1')
    for frame in result['frames']:
        with Image.open(frame['path']) as source:
            thumb = source.convert('RGBA').resize((192, 192), Image.Resampling.NEAREST)
        sheet.paste(thumb, (frame['direction'] * 192, y * 224 + 25), thumb)
args.out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(args.out)
print(args.out)
