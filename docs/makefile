all: build/napari-3d-counter.html
	cp build/napari-3d-counter.html ../../pnewstein.github.io

build/napari-3d-counter.md: ../README.md make_html.py
	python make_html.py

build/napari-3d-counter.html: build/napari-3d-counter.md template.html
	pandoc build/napari-3d-counter.md --table-of-contents=true --toc-depth=3 -s -o build/napari-3d-counter.html --template=template.html


