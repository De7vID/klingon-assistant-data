BOOK=book-en
CONTENT=content-en

default: $(BOOK).pdf

$(BOOK).pdf : $(BOOK).tex $(CONTENT).tex
	xelatex $(BOOK)

$(CONTENT).tex : ../*.xml
	./generate-latex.py > content-en.tex

view :	$(BOOK).pdf
	evince $(BOOK).pdf &

clean :
	-rm $(BOOK).pdf $(CONTENT).tex
