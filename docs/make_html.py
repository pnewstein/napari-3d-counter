"""
This script modifies the README.md to prepare to become html
"""

import re
from pathlib import Path


tip_html = """
<div>
<h4> TIP:</h4>
<p>\\1</p>
</div>
"""

video_html = """
<video controls>
  <source src="\\1" type="video/mp4"></source>
  Your browser does not support the video tag.
</video>

"""


def main():
    readme = Path("../README.md").read_text()
    # Turn TIP into a special div
    readme = re.sub(r">\s*\[!TIP\]\s*\n>(.*)\n", tip_html, readme)
    # turn all loose links into vidoes
    readme = re.sub(
        r"\n(https://github\.com/pnewstein/napari-3d-counter/assets/.*)\n",
        video_html,
        readme,
    )
    out_path = Path("build/napari-3d-counter.md")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(readme)


if __name__ == "__main__":
    main()
