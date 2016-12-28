if !has("python") && !has("python3")
    echoerr "coverage-highlight.vim needs vim with Python support"
    finish
endif

let s:python = has('python3') ? 'python3' : 'python'
exec s:python "import coverage_highlight"

function coverage_highlight#highlight(arg)
    call coverage_highlight#off()
    exec s:python "coverage_highlight.highlight(vim.eval('a:arg'))"
endf

function coverage_highlight#off()
    " TODO: do it right!
    sign unplace *
endf
