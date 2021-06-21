.PHONY: open clean pdf debug stuff

pdf: build/report.pdf

debug: build/report.tex

stuff: assets/eisvogel.tex build/warehouse_layout.pdf  assets/*

build/report.pdf: main.md sections/*.md stuff | build
	pandoc -s -o $@ \
	-f markdown main.md sections/*.md \
	--template=assets/eisvogel.tex --listings --number-sections \
	--pdf-engine=pdflatex

build/report.tex: main.md sections/*.md stuff | build
	pandoc -s -o $@ \
	-f markdown main.md sections/*.md \
	--template=assets/eisvogel.tex --listings --number-sections \
	--pdf-engine=pdflatex

build/warehouse_layout.pdf: build/warehouse_layout.tex | build
	pdflatex --output-directory=build $<

build/warehouse_layout.tex: scripts/warehouse_layout.py | build
	$< > $@

build:
	mkdir $@

open: build/report.pdf
	xdg-open $< > /dev/null

clean:
	rm -r build/
