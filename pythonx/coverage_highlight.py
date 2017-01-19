"""
" HACK to fore-reload it from vim with :source %
let s:python = has('python3') ? 'python3' : 'python'
execute s:python 'import sys; sys.modules.pop("coverage_highlight", None); import coverage_highlight'
finish
"""
import os
import shlex
import subprocess
import vim


def get_verbosity():
    return int(vim.eval('&verbose'))


def debug(msg):
    if get_verbosity() >= 2:
        print(msg)


def error(msg):
    vim.command("echohl ErrorMsg")
    vim.command("echomsg '%s'" % msg.replace("'", "''"))
    vim.command("echohl None")


def filename2module(filename):
    pkg = os.path.splitext(os.path.abspath(filename))[0]
    root = os.path.dirname(pkg)
    while os.path.exists(os.path.join(root, '__init__.py')):
        new_root = os.path.dirname(root)
        if new_root == root:
            break  # prevent infinite loops in crazy systems
        else:
            root = new_root
    pkg = pkg[len(root) + len(os.path.sep):].replace('/', '.')
    return pkg


def find_coverage_report(modulename):
    filename = 'coverage/%s.cover' % modulename
    root = os.path.abspath(os.path.curdir)
    if os.path.exists(os.path.join(root, 'parts', 'test', 'working-directory')):
        # zope.testrunner combined with zc.buildout
        root = os.path.join(root, 'parts', 'test', 'working-directory')
    elif os.path.exists(os.path.join(root, 'parts', 'test')):
        # different version of zope.testrunner
        root = os.path.join(root, 'parts', 'test')
    while not os.path.exists(os.path.join(root, filename)):
        new_root = os.path.dirname(root)
        if new_root == root:
            break  # prevent infinite loops in crazy systems
        else:
            root = new_root
    return os.path.join(root, filename)


class Signs(object):

    first_sign_id = 17474  # random number to avoid clashes with other plugins

    def __init__(self, buf=None):
        if buf is None:
            buf = vim.current.buffer
        self.bufferid = buf.number
        if 'coverage_signs' not in buf.vars:
            buf.vars['coverage_signs'] = []
        self.signs = buf.vars['coverage_signs']
        self.signid = max(self.signs) if self.signs else self.first_sign_id

    def place(self, lineno):
        self.signid += 1
        cmd = "sign place %d line=%d name=NoCoverage buffer=%s" % (
                    self.signid, lineno, self.bufferid)
        vim.command(cmd)
        self.signs.extend([self.signid])

    def clear(self):
        for sign in self.signs:
            cmd = "sign unplace %d" % sign
            vim.command(cmd)
        del self.signs[:]

    def __iter__(self):
        info = vim.bindeval('getbufinfo("%")')[0]
        for sign in info['signs']:
            if sign['name'] == b'NoCoverage':
                yield sign

    def find_next_range(self, line):
        signs = iter(self)
        for sign in signs:
            if sign['lnum'] == line:
                line += 1
            if sign['lnum'] > line:
                break
        else:
            return None
        first = last = sign['lnum']
        for sign in signs:
            if sign['lnum'] == last + 1:
                last += 1
        return first, last

    def find_prev_range(self, line):
        signs = iter(self)
        prev_range = None
        first = last = None
        for sign in signs:
            if last is None:
                first = last = sign['lnum']
            elif sign['lnum'] == last + 1:
                last += 1
            else:
                prev_range = (first, last)
                first = last = sign['lnum']
            if sign['lnum'] >= line:
                break
        return prev_range


def lazyredraw(fn):
    def wrapped(*args, **kw):
        oldvalue = vim.eval('&lazyredraw')
        try:
            vim.command('set lazyredraw')
            return fn(*args, **kw)
        finally:
            vim.command('let &lazyredraw = %s' % oldvalue)
    return wrapped


@lazyredraw
def parse_cover_file(filename):
    signs = Signs()
    with open(filename) as f:
        for lineno, line in enumerate(f, 1):
            if line.startswith('>>>>>>'):
                signs.place(lineno)


def parse_coverage_output(output, filename):
    # Example output without branch coverage:
    # Name                          Stmts   Exec  Cover   Missing
    # -----------------------------------------------------------
    # src/foo/bar/baz/qq/__init__     146    136    93%   170-177, 180-184

    # Example output with branch coverage:
    # Name                          Stmts   Miss Branch BrPart  Cover   Missing
    # -------------------------------------------------------------------------
    # src/foo/bar/baz/qq/__init__     146    136     36      4    93%   170-177, 180-184

    last_line = output.splitlines()[-1]
    filename = os.path.relpath(filename)
    filename_no_ext = os.path.splitext(filename)[0]
    signs = Signs()
    expect_one_of = (
        filename + ' ',
        './' + filename + ' ',
        filename_no_ext + ' ',
        './' + filename_no_ext + ' ',
    )
    if last_line.startswith(expect_one_of):
        # The margin (15) was determined empirically as the smallest value
        # that avoids a 'Press enter to continue...' message
        truncate_to = int(vim.eval('&columns')) - 15
        if len(last_line) <= truncate_to or get_verbosity() >= 1:
            print(last_line)
        else:
            print(last_line[:truncate_to] + '...')
        last_line = last_line[len(filename_no_ext) + 1:].lstrip()
        missing = last_line.rpartition('%')[-1]
        if missing and missing.strip():
            parse_lines(missing, signs)
    else:
        print("Got confused by %s" % repr(last_line))
        print("Expected it to start with %s" % repr(filename_no_ext + ' '))
        print("Full output:")
        print(output)


@lazyredraw
def parse_lines(formatted_list, signs):
    for item in formatted_list.split(', '):
        if '->' in item:
            # skip missed branches
            continue
        if '-' in item:
            lo, hi = item.split('-')
        else:
            lo = hi = item
        lo, hi = int(lo), int(hi)
        for lineno in range(lo, hi+1):
            signs.place(lineno)


def program_in_path(program):
    path = os.environ.get("PATH", os.defpath).split(os.pathsep)
    path = [os.path.join(dir, program) for dir in path]
    path = [True for file in path if os.path.isfile(file)]
    return bool(path)


def find_coverage_script():
    override = vim.eval('g:coverage_script')
    if override:
        return override
    if program_in_path('coverage'):
        # assume it was easy_installed
        return 'coverage'
    # Vagrant means I can't rely on bin/coverage working even if it exists, so
    # prefer a globally-installed one if possible.
    if os.path.exists('bin/coverage'):
        return os.path.abspath('bin/coverage')


def find_coverage_file_for(filename):
    where = os.path.dirname(filename)
    while True:
        if os.path.exists(os.path.join(where, '.coverage')):
            debug("Found %s" % os.path.join(where, '.coverage'))
            return where or os.curdir
        if os.path.dirname(where) == where:
            debug("Did not find .coverage in any parent directory")
            return None
        where = os.path.dirname(where)


def clear():
    signs = Signs()
    signs.clear()


def highlight(arg):
    clear()
    if arg.endswith('.report'):
        parse_cover_file(arg)
    elif arg:
        filename = vim.current.buffer.name
        if '%' not in arg:
            # hack because our parser expects "nn%" before the line ranges
            fake_output = filename + ' % ' + arg
        else:
            fake_output = arg
        parse_coverage_output(fake_output, filename)
    else:
        filename = vim.current.buffer.name
        coverage_script = find_coverage_script()
        coverage_dir = find_coverage_file_for(filename)
        if coverage_script and coverage_dir:
            relfilename = os.path.relpath(filename, coverage_dir)
            print("Running %s report -m %s" % (os.path.relpath(coverage_script), relfilename))
            if os.path.exists(coverage_script):
                command = [coverage_script]
            else:
                command = shlex.split(coverage_script)
            output = subprocess.Popen(command + ['report', '-m', relfilename],
                                      stdout=subprocess.PIPE, cwd=coverage_dir).communicate()[0]
            if not isinstance(output, str):
                output = output.decode('UTF-8', 'replace')
            parse_coverage_output(output, relfilename)
        else:
            modulename = filename2module(filename)
            filename = find_coverage_report(modulename)
            if os.path.exists(filename):
                print("Using %s" % filename)
                parse_cover_file(filename)
            else:
                error('Neither .coverage nor %s found.' % filename)


def jump_to_next():
    signs = Signs()
    row, col = vim.current.window.cursor
    next_range = signs.find_next_range(row)
    if next_range is None:
        print("No higlighted lines below cursor")
        return
    first, last = next_range
    # jump to last line so it's visible, then jump back to 1st line
    # (this does not always work the way I want but eh)
    vim.command("normal! %dG" % last)
    vim.command("normal! %dG" % first)
    print("{}-{}".format(first, last) if first != last else first)


def jump_to_prev():
    signs = Signs()
    row, col = vim.current.window.cursor
    prev_range = signs.find_prev_range(row)
    if prev_range is None:
        print("No higlighted lines above cursor")
        return
    first, last = prev_range
    # jump to first line so it's visible, then jump back to last line
    # (this does not always work the way I want but eh)
    vim.command("normal! %dG" % first)
    vim.command("normal! %dG" % last)
    print("{}-{}".format(first, last) if first != last else first)
