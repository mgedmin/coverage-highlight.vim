if !has("python") && !has("python3")
    echoerr "coverage-highlight.vim needs vim with Python support"
    finish
endif
if !exists("*pyxeval")
    echoerr "coverage-highlight.vim needs vim 8.0.0251 or newer"
    finish
endif

let s:python = has('python3') ? 'python3' : 'python'
exec s:python "import vim, coverage_highlight"

function! coverage_highlight#highlight(arg)
    exec s:python "coverage_highlight.highlight(vim.eval('a:arg'))"
    augroup CovergeHighlight
      au! * <buffer>
      au CursorMoved <buffer> exec s:python "coverage_highlight.cursor_moved()"
    augroup END
endf

function! coverage_highlight#highlight_all()
    exec s:python "coverage_highlight.highlight_all()"
    augroup CovergeHighlight
      au!
      au CursorMoved * exec s:python "coverage_highlight.cursor_moved()"
    augroup END
endf

function! coverage_highlight#clean_up_autocommands()
    let remaining = pyxeval("coverage_highlight.Signs.number_of_buffers_with_coverage()")
    if remaining == 0
        augroup CovergeHighlight
          au!
        augroup END
    endif
endf

function! coverage_highlight#off()
    exec s:python "coverage_highlight.clear()"
    call coverage_highlight#clean_up_autocommands()
endf

function! coverage_highlight#toggle()
    exec s:python "coverage_highlight.toggle()"
    call coverage_highlight#clean_up_autocommands()
endf

function! coverage_highlight#get_total(...)
    let format = a:0 >= 1 ? a:1 : '%s%%'
    let coverage = pyxeval("coverage_highlight.Signs.get_total_coverage()")
    if coverage != ""
        let coverage = printf(format, coverage)
    endif
    return coverage
endf

function! coverage_highlight#get_current(...)
    let format = a:0 >= 1 ? a:1 : '%s%%'
    let coverage = pyxeval("coverage_highlight.Signs().get_file_coverage()")
    if coverage != ""
        let coverage = printf(format, coverage)
    endif
    return coverage
endf

function! coverage_highlight#next()
    exec s:python "coverage_highlight.jump_to_next()"
endf

function! coverage_highlight#prev()
    exec s:python "coverage_highlight.jump_to_prev()"
endf

function! coverage_highlight#define_highlights()
    if &background == 'dark'
        if &t_Co >= 256
            highlight NoCoverageDefault ctermbg=52 guibg=#5f0000
            highlight link NoBranchCoverageDefault NoCoverageDefault
            highlight NoBranchCoverageTargetDefault ctermbg=94 guibg=#875f00
        else
            highlight NoCoverageDefault ctermbg=darkred guibg=#5f0000
            highlight NoBranchCoverageDefault ctermbg=darkred guibg=#5f0000
            highlight NoBranchCoverageTargetDefault ctermbg=3 guibg=#c3a000
        endif
    else
        if &t_Co >= 256
            highlight NoCoverageDefault ctermbg=224 guibg=#ffd7d7
            highlight NoBranchCoverageDefault ctermbg=223 guibg=#ffd7af
            highlight NoBranchCoverageTargetDefault ctermbg=222 guibg=#ffd787
        else
            highlight NoCoverageDefault ctermbg=gray guibg=#ffcccc
            highlight link NoBranchCoverageDefault NoCoverageDefault
            highlight link NoBranchCoverageTargetDefault NoCoverageDefault
        endif
    endif
    highlight default link NoCoverage NoCoverageDefault
    highlight default link NoBranchCoverage NoBranchCoverageDefault
    highlight default link NoBranchCoverageTarget NoBranchCoverageTargetDefault
endf

call coverage_highlight#define_highlights()
