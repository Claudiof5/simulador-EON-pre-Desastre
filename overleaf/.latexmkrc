# Always rebuild so a stale failure in .fdb_latexmk cannot
# make latexmk exit 12 on "nothing to do".
# Write to out/ so Preview/Chrome locking overleaf/problema.pdf
# does not make pdflatex return 2.
# Full path: LaTeX Workshop on Cmd+S does not inherit /Library/TeX/texbin.
$pdf_mode = 1;
$go_mode = 1;
$out_dir = 'out';
$pdflatex = '/Library/TeX/texbin/pdflatex -synctex=1 -interaction=nonstopmode -file-line-error %O %S';
