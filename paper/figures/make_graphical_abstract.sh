#!/bin/sh
# Render graphical_abstract.html to the files submitted to SoftwareX:
# a 2656 x 1062 px PNG/TIFF (twice the 1328 x 531 px minimum) and a vector PDF.
set -e
cd "$(dirname "$0")"
url="file://$PWD/graphical_abstract.html"
chrome=${CHROME:-google-chrome}
"$chrome" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --allow-file-access-from-files --force-device-scale-factor=2 \
  --window-size=1328,531 --screenshot="$PWD/graphical_abstract.png" "$url"
"$chrome" --headless=new --disable-gpu --no-sandbox --allow-file-access-from-files \
  --no-pdf-header-footer --print-to-pdf="$PWD/graphical_abstract.pdf" "$url"
python3 -c "
from PIL import Image
im = Image.open('graphical_abstract.png').convert('RGB')
assert im.size == (2656, 1062), im.size
im.save('graphical_abstract.tiff', compression='tiff_lzw', dpi=(519, 519))
"
