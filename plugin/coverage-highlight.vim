" File: coverage-highlight.vim
" Author: Marius Gedminas <marius@gedmin.as>
" Version: 3.3
" Last Modified: 2021-02-04

if !exists("g:coverage_script")
    let g:coverage_script = ""
endif

sign define NoCoverage text=↣ texthl=NoCoverage linehl=NoCoverage
sign define NoBranchCoverage text=↦ texthl=NoBranchCoverage linehl=NoBranchCoverage
sign define NoBranchCoverageTarget text=⇥ texthl=NoBranchCoverageTarget linehl=NoBranchCoverageTarget

command! -nargs=* -complete=file -bar HighlightCoverage
            \ call coverage_highlight#highlight(<q-args>)
command! -bar HighlightCoverageForAll call coverage_highlight#highlight_all()
command! -bar HighlightCoverageOff call coverage_highlight#off()
command! -bar ToggleCoverage call coverage_highlight#toggle()

command! -bar NextUncovered call coverage_highlight#next()
command! -bar PrevUncovered call coverage_highlight#prev()

augroup CoverageHighlight
  autocmd!
  autocmd ColorScheme * call coverage_highlight#define_highlights()
augroup END
