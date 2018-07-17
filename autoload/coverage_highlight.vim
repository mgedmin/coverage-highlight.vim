if !has("python") && !has("python3")
    echoerr "coverage-highlight.vim needs vim with Python support"
    finish
endif

let s:python = has('python3') ? 'python3' : 'python'
exec s:python "import vim, coverage_highlight"

function! coverage_highlight#highlight(arg)
    exec s:python "coverage_highlight.highlight(vim.eval('a:arg'))"
endf

function! coverage_highlight#highlight_all()
    exec s:python "coverage_highlight.highlight_all()"
endf

function! coverage_highlight#off()
    exec s:python "coverage_highlight.clear()"
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
        else
            highlight NoCoverageDefault ctermbg=darkred guibg=#5f0000
        endif
    else
        if &t_Co >= 256
            highlight NoCoverageDefault ctermbg=224 guibg=#ffcccc
        else
            highlight NoCoverageDefault ctermbg=gray guibg=#ffcccc
        endif
    endif
    highlight default link NoCoverage NoCoverageDefault
endf

call coverage_highlight#define_highlights()
