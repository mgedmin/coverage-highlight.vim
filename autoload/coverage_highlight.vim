if !has("python") && !has("python3")
    echoerr "coverage-highlight.vim needs vim with Python support"
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

function! coverage_highlight#off()
    exec s:python "coverage_highlight.clear()"
    " bug: this disables coverage highlighting for one buffer only, but
    " disables CusorMoved autocommands for all buffers
    augroup CovergeHighlight
      au!
    augroup END
endf

function! coverage_highlight#toggle()
    exec s:python "coverage_highlight.toggle()"
    " XXX: remove the cursor_moved autocommand?
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
        else
            highlight NoCoverageDefault ctermbg=darkred guibg=#5f0000
            highlight link NoBranchCoverageDefault NoCoverageDefault
        endif
    else
        if &t_Co >= 256
            highlight NoCoverageDefault ctermbg=224 guibg=#ffcccc
            highlight NoBranchCoverageDefault ctermbg=223 guibg=#ffcccc
        else
            highlight NoCoverageDefault ctermbg=gray guibg=#ffcccc
            highlight link NoBranchCoverageDefault NoCoverageDefault
        endif
    endif
    highlight default link NoCoverage NoCoverageDefault
    highlight default link NoBranchCoverage NoBranchCoverageDefault
endf

call coverage_highlight#define_highlights()
