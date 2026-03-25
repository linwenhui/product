#!/usr/bin/env python3
"""Merge comic pages into PDF"""
import os
import sys
from PIL import Image

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 merge-to-pdf.py <comic-dir> [output.pdf]")
        sys.exit(1)

    comic_dir = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(comic_dir, f"{os.path.basename(comic_dir)}.pdf")

    # Find all page files
    import re
    page_pattern = re.compile(r'^(\d+)-(cover|page)(-[\w-]+)?\.(png|jpg|jpeg)$')

    pages = []
    for f in sorted(os.listdir(comic_dir)):
        match = page_pattern.match(f)
        if match:
            pages.append({
                'filename': f,
                'path': os.path.join(comic_dir, f),
                'index': int(match.group(1))
            })

    if not pages:
        print(f"No comic pages found in: {comic_dir}")
        sys.exit(1)

    pages.sort(key=lambda x: x['index'])

    print(f"Found {len(pages)} pages in: {comic_dir}\n")

    # Load images
    images = []
    for page in pages:
        print(f"Loading: {page['filename']}")
        img = Image.open(page['path'])
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        images.append(img)

    # Save PDF
    if images:
        images[0].save(
            output,
            save_all=True,
            append_images=images[1:],
            resolution=150.0,
            quality=95
        )
        print(f"\nCreated: {output}")
        print(f"Total pages: {len(images)}")

if __name__ == '__main__':
    main()
