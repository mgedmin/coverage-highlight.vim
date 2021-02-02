"""
" HACK to fore-reload it from vim with :source %
pyx import sys; sys.modules.pop("coverage_highlight", None); import coverage_highlight
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
            break  # prevent infinite loops in unlikely situations
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
        self.buffer = buf
        self.bufferid = buf.number
        # convert vim.List() to a regular list
        self.signs = list(buf.vars.get(
            'coverage-highlight.vim:coverage_signs', []))
        self.signid = max(self.signs) if self.signs else self.first_sign_id
        # convert vim.Dictionary() to a regular dictionary
        # convert keys to ints (vim.Dictionary() only allows string keys)
        # convert values from vim.List() to regular lists
        # convert list values from bytes to unicode (on Python 3)
        self.branch_targets = {
            int(line): [
                target.decode('UTF-8')
                if isinstance(target, bytes) and bytes is not str
                else target
                for target in targets
            ]
            for line, targets in buf.vars.get(
                'coverage-highlight.vim:branch_targets', {}).items()
        }
        self.last_row = buf.vars.get('coverage-highlight.vim:last_row', 0)
        self.last_row_signs = list(buf.vars.get(
            'coverage-highlight.vim:last_row_signs', []))

    @classmethod
    def number_of_buffers_with_coverage(cls):
        count = 0
        for buf in vim.buffers:
            signs = cls(buf)
            if signs.signs or signs.get_file_coverage():
                count += 1
        return count

    @classmethod
    def for_file(cls, filename):
        for buf in vim.buffers:
            try:
                if os.path.samefile(buf.name, filename):
                    return cls(buf)
            except (OSError, IOError):
                pass

    def get_file_coverage(self):
        return self.buffer.vars.get('coverage-highlight.vim:coverage', '')

    def set_file_coverage(self, coverage):
        if get_verbosity() >= 3:
            print('FILE COVERAGE: %r' % coverage)
        self.buffer.vars['coverage-highlight.vim:coverage'] = coverage

    @staticmethod
    def get_total_coverage():
        return vim.vars.get('coverage-highlight.vim:total_coverage', '')

    @staticmethod
    def set_total_coverage(coverage):
        if get_verbosity() >= 3:
            print('TOTAL COVERAGE: %r' % coverage)
        vim.vars['coverage-highlight.vim:total_coverage'] = coverage

    def _place(self, signs, lineno, name):
        self.signid += 1
        cmd = "sign place %d line=%d name=%s buffer=%s" % (
            self.signid, lineno, name, self.bufferid)
        vim.command(cmd)
        signs.append(self.signid)

    def place(self, lineno, name='NoCoverage'):
        self._place(self.signs, lineno, name)

    def place_branch(self, src_lineno, dst_lineno):
        if src_lineno not in self.branch_targets:
            self.branch_targets[src_lineno] = []
            self.place(src_lineno, name='NoBranchCoverage')
        self.branch_targets[src_lineno].append(dst_lineno)

    def get_branch_targets(self, lineno, default=None):
        return self.branch_targets.get(lineno, default)

    def place_branch_target_signs(self, targets):
        for lineno in targets:
            # skip 'exit' and any possible future non-numeric targets
            if str(lineno).isdigit():
                self._place(self.last_row_signs, int(lineno),
                            'NoBranchCoverageTarget')

    def clear(self):
        for sign in self.signs:
            cmd = "sign unplace %d" % sign
            vim.command(cmd)
        self.signs = []
        self.branch_targets = {}
        self.clear_last_row_signs()

    def clear_last_row_signs(self):
        for sign in self.last_row_signs:
            cmd = "sign unplace %d" % sign
            vim.command(cmd)
        self.last_row_signs = []

    def save(self):
        self.buffer.vars['coverage-highlight.vim:coverage_signs'] = self.signs
        self.buffer.vars['coverage-highlight.vim:branch_targets'] = {
            str(lineno): targets
            for lineno, targets in self.branch_targets.items()
        }
        self.save_last_row()

    def save_last_row(self):
        self.buffer.vars['coverage-highlight.vim:last_row'] = self.last_row
        self.buffer.vars['coverage-highlight.vim:last_row_signs'] = (
            self.last_row_signs
        )

    def __iter__(self):
        info = vim.bindeval('getbufinfo(%d)' % self.bufferid)[0]
        for sign in info.get('signs', []):
            if sign['name'] in (b'NoCoverage', b'NoBranchCoverage'):
                yield sign

    def iter_ranges(self):
        signs = iter(self)
        first = last = None
        for sign in signs:
            if last is None:
                first = last = sign['lnum']
            elif sign['lnum'] == last + 1:
                last += 1
            else:
                yield (first, last)
                first = last = sign['lnum']
        if last is not None:
            yield (first, last)

    def find_current_range(self, line):
        for first, last in self.iter_ranges():
            if first <= line <= last:
                return first, last
        return None

    def find_next_range(self, line):
        # Rewrite using self.iter_ranges() maybe?
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
        # Rewrite using self.iter_ranges() maybe?
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
        else:
            if last is not None:
                prev_range = (first, last)
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
    signs.save()


def parse_coverage_number(line):
    # src/foo/bar/baz/qq/__init__     146    136    93%   170-177, 180-184
    # we should return '93'
    return line.rpartition('%')[0].rpartition(' ')[-1].rpartition('\t')[-1]


def get_echospace():
    # The margin (12) was determined empirically as the smallest value
    # that avoids a 'Press enter to continue...' message.
    # v:echospace exists since vim 8.1.1913 and removes the need to guess.
    return int(vim.eval('exists("v:echospace") ? v:echospace : &columns - 12'))


def parse_coverage_output(output, filename):
    # Example output without branch coverage:
    # Name                          Stmts   Exec  Cover   Missing
    # -----------------------------------------------------------
    # src/foo/bar/baz/qq/__init__     146    136    93%   170-177, 180-184

    # Example output with branch coverage:
    # Name                          Stmts   Miss Branch BrPart  Cover   Missing
    # -------------------------------------------------------------------------
    # src/foo/bar/baz/qq/__init__     146    136     36      4    93%   170-177, 180-184

    if not output:
        print("Got no output!")
        return
    filename = os.path.relpath(filename)
    filename_no_ext = os.path.splitext(filename)[0]
    signs = Signs()
    expect_one_of = (
        filename + ' ',
        './' + filename + ' ',
        filename_no_ext + ' ',
        './' + filename_no_ext + ' ',
    )
    for line in output.splitlines():
        if line.startswith(expect_one_of):
            # Truncate to avoid the 'Press enter to continue...' message
            truncate_to = get_echospace()
            if len(line) <= truncate_to or get_verbosity() >= 1:
                print(line)
            else:
                print(line[:truncate_to - 3] + '...')
            line = line[len(filename_no_ext) + 1:].lstrip()
            signs.set_file_coverage(parse_coverage_number(line))
            missing = line.rpartition('%')[-1]
            if missing and missing.strip():
                signs.clear()
                parse_lines(missing, signs)
                signs.save()
            break
    else:
        print("Failed to parse coverage report!")
        print("Expected it to start with %s" % repr(filename_no_ext + ' '))
        print("Full output:")
        print(output)


def parse_full_coverage_output(output):
    if not output and get_verbosity() >= 1:
        print("Got no output!")
        return
    # skip header
    output = iter(output.splitlines())
    for line in output:
        if get_verbosity() >= 3:
            print(line)
        if line.startswith('--------'):
            break
    n_files = 0
    for line in output:
        if get_verbosity() >= 3:
            print(line)
        if line.startswith('--------'):
            break
        filename = line.split()[0]
        if not os.path.exists(filename):
            # this is unexpected
            if get_verbosity() >= 1:
                print("Skipping %s: no such file" % filename)
            continue
        signs = Signs.for_file(filename)
        if signs is None:
            # Vim can't place signs on files that are not loaded into buffers
            if get_verbosity() >= 1:
                print("Skipping %s: not loaded in any buffer" % filename)
            continue
        if get_verbosity() >= 2:
            print(line)
        n_files += 1
        coverage = parse_coverage_number(line)
        signs.set_file_coverage(coverage)
        signs.clear()
        missing = line.rpartition('%')[-1]
        if missing and missing.strip():
            parse_lines(missing, signs)
        signs.save()
    total = ''
    if n_files == 1:
        total = coverage
    for line in output:
        if line.startswith('TOTAL'):
            total = line.split()[-1]  # 'nn%'
            print('Total coverage: {}'.format(total))
    Signs.set_total_coverage(total.rstrip('%'))


@lazyredraw
def parse_lines(formatted_list, signs):
    for item in formatted_list.split(','):
        if '->' in item:
            # skip missed branches
            src, dst = item.split('->')
            signs.place_branch(int(src), dst)
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
    if os.path.exists('.coverage'):
        return '.'
    where = os.path.dirname(filename)
    while True:
        if os.path.exists(os.path.join(where, '.coverage')):
            debug("Found %s" % os.path.join(where, '.coverage'))
            return where or os.curdir
        if os.path.dirname(where) == where:
            debug("Did not find .coverage in any parent directory")
            return None
        where = os.path.dirname(where)


def run_coverage_report(coverage_script, coverage_dir, args=[]):
    print("Running %s report -m %s" % (os.path.relpath(coverage_script), ' '.join(args)))
    if os.path.exists(coverage_script):
        command = [os.path.abspath(coverage_script)]
    else:
        # things like "python3 -m coverage"
        command = shlex.split(coverage_script)
    output = subprocess.Popen(command + ['report', '-m'] + args,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              cwd=coverage_dir).communicate()[0]
    if not isinstance(output, str):
        output = output.decode('UTF-8', 'replace')
    return output


def clear(clear_total=True):
    signs = Signs()
    signs.set_file_coverage('')
    signs.clear()
    signs.save()
    if clear_total:
        signs.set_total_coverage('')


def toggle():
    signs = Signs()
    if signs.signs:
        clear()
    else:
        highlight()


def highlight(arg=''):
    clear(clear_total=False)
    if arg.endswith('.report'):
        parse_cover_file(arg)
    elif arg:
        filename = os.path.relpath(vim.current.buffer.name)
        if '%' not in arg:
            # hack because our parser expects "nn%" before the line ranges
            fake_output = filename + ' % ' + arg
        else:
            fake_output = arg
        parse_coverage_output(fake_output, filename)
    else:
        filename = vim.current.buffer.name
        if not filename:
            error("Current buffer has no name.")
            return
        coverage_dir = find_coverage_file_for(filename)
        if coverage_dir:
            coverage_script = find_coverage_script()
            if not coverage_script:
                error("Could not find the 'coverage' script.")
                return
            relfilename = os.path.relpath(filename, coverage_dir)
            output = run_coverage_report(coverage_script, coverage_dir, [relfilename])
            parse_coverage_output(output, relfilename)
        else:
            modulename = filename2module(filename)
            filename = find_coverage_report(modulename)
            if os.path.exists(filename):
                print("Using %s" % filename)
                parse_cover_file(filename)
            else:
                error('Neither .coverage nor %s found.' % filename)
    cursor_moved(force=True)


def highlight_all():
    coverage_script = find_coverage_script()
    if not coverage_script:
        error("Could not find the 'coverage' script.")
        return
    filename = vim.current.buffer.name
    coverage_dir = find_coverage_file_for(filename)
    if not coverage_dir:
        error('Could not find .coverage for %s.' % filename)
        return
    output = run_coverage_report(coverage_script, coverage_dir)
    parse_full_coverage_output(output)
    cursor_moved(force=True)


def jump_to_next():
    signs = Signs()
    row, col = vim.current.window.cursor
    next_range = signs.find_next_range(row)
    if next_range is None:
        current_range = signs.find_current_range(row)
        if current_range is not None:
            # if we're at the very last range, jump to the last line
            first, last = current_range
            if row != last:
                vim.command("normal! %dG" % last)
                return
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
        current_range = signs.find_current_range(row)
        if current_range is not None:
            # if we're at the very first range, jump to the first line
            first, last = current_range
            if row != first:
                vim.command("normal! %dG" % first)
                return
        print("No higlighted lines above cursor")
        return
    first, last = prev_range
    # jump to first line so it's visible, then jump back to last line
    # (this does not always work the way I want but eh)
    vim.command("normal! %dG" % first)
    vim.command("normal! %dG" % last)
    print("{}-{}".format(first, last) if first != last else first)


def cursor_moved(force=False):
    signs = Signs()
    row, col = vim.current.window.cursor
    if row != signs.last_row or force:
        signs.clear_last_row_signs()
        signs.last_row = row
        targets = signs.get_branch_targets(row)
        if targets:
            print(
                "Line %d: missing branch%s to %s" % (
                    row,
                    "es" if len(targets) > 1 else "",
                    ', '.join(map(str, targets)))
            )
            signs.place_branch_target_signs(targets)
        signs.save_last_row()
