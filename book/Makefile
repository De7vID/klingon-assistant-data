BOOK=book-en
CONTENT=content-en

default: $(BOOK).pdf

$(BOOK).pdf : $(BOOK).tex $(CONTENT).tex
	pdflatex $(BOOK)

$(CONTENT).tex : ../*.xml
	./generate-latex.py > content-en.tex
	sed -i "s/déjà/d\\\'{e}j\\\\\`{a}/g" content-en.tex
	sed -i 's/Saarbrücken/Saarbr\\"{u}cken/g' content-en.tex

view :	$(BOOK).pdf
	evince $(BOOK).pdf &

clean :
	-rm $(BOOK).pdf $(CONTENT).tex
