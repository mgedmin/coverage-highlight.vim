" File: coverage-highlight.vim
" Author: Marius Gedminas <marius@gedmin.as>
" Version: 3.4
" Last Modified: 2021-04-02
" Contributors: Louis Cochen <louis.cochen@protonmail.ch>

let g:coverage_script = get(g:, 'coverage_script', '')

let g:coverage_sign = get(g:, 'coverage_sign', '↣')
let g:coverage_sign_branch = get(g:, 'coverage_sign_branch', '↦')
let g:coverage_sign_branch_target = get(g:, 'coverage_sign_branch_target', '⇥')

if g:coverage_sign == ''
  sign define NoCoverage linehl=NoCoverage
else
  execute 'sign define NoCoverage text=' . g:coverage_sign
        \ . ' texthl=NoCoverage linehl=NoCoverage'
endif

if g:coverage_sign_branch == ''
  sign define NoBranchCoverage linehl=NoBranchCoverage
else
  execute 'sign define NoBranchCoverage text=' . g:coverage_sign_branch
        \ . ' texthl=NoBranchCoverage linehl=NoBranchCoverage'
endif

if g:coverage_sign_branch_target == ''
  sign define NoBranchCoverageTarget linehl=NoBranchCoverageTarget
else
  execute 'sign define NoBranchCoverageTarget text=' . g:coverage_sign_branch_target
        \ . ' texthl=NoBranchCoverageTarget linehl=NoBranchCoverageTarget'
endif

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
