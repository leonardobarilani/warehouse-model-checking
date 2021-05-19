.PHONY: open clean pdf debug

pdf: build/report.pdf

debug: build/report.tex

build/report.pdf: main.md sections/*.md assets/eisvogel.tex assets/* | build
	pandoc -s -o $@ \
	-f markdown main.md sections/*.md \
	--template=assets/eisvogel.tex --listings --number-sections \
	--pdf-engine=pdflatex

build/report.tex: main.md sections/*.md assets/eisvogel.tex assets/* | build
	pandoc -s -o $@ \
	-f markdown main.md sections/*.md \
	--template=assets/eisvogel.tex --listings --number-sections \
	--pdf-engine=pdflatex

build:
	mkdir $@

open: build/report.pdf
	xdg-open $< > /dev/null

clean:
	rm -r build/
