" File: coverage-highlight.vim
" Author: Marius Gedminas <marius@gedmin.as>
" Version: 1.0
" Last Modified: 2016-12-28
"
" Overview
" --------
" Vim script to highlight Python code coverage report results.
"
" Installation
" ------------
" Copy this file to $HOME/.vim/plugin directory
"
" Usage with Ned Batchelder's coverage.py
" ---------------------------------------
" Produce a coverage report with coverage (it's assumed that either it's in
" $PATH, or in $PWD/bin/coverage).  Open a source file.  Use :HighlightCoverage
" to load coverage info, and :HighlightCoverageOff to turn it off.
"
" You can also provide the missing lines directly on the command line,
" eg. :HighlightCoverage NN-NN,NN-NN,NN-NN
"
" You can override the coverage script name with
"
"   let g:coverage_script = 'python3 -m coverage'
"
" or similar.
"
" Usage with Python's trace.py
" ----------------------------
" Produce a coverage report with Python's trace.py.  Open a source file.
" Load the highlighting with :HighlightCoverage filename/to/coverage.report
" Turn off the highlighting with :HighlightCoverageOff.
"
" Usage with zope.testrunner
" --------------------------
" Produce a coverage report with bin/test --coverage=coverage.  Open a source
" file.  Use :HighlightCoverage to load coverage info, and
" :HighlightCoverageOff to turn it off.
"
" zope.testrunner uses trace.py behind the scenes, and this plugin looks for
" the reports in ./coverage or ./parts/test/working-directory/coverage and
" is able to compute the right filename.

if !exists("g:coverage_script")
    let g:coverage_script = ""
endif

if &t_Co > 8
    hi default NoCoverage ctermbg=224 guibg=#ffcccc
else
    hi default NoCoverage ctermbg=gray guibg=#ffcccc
endif
sign define NoCoverage text=>> texthl=NoCoverage linehl=NoCoverage

command! -nargs=* -complete=file -bar HighlightCoverage
            \ call coverage_highlight#highlight(<q-args>)

command! -bar HighlightCoverageOff
            \ call coverage_highlight#off()
