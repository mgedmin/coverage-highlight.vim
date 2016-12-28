coverage-highlight.vim
----------------------

Vim plugin to highlight source code lines that lack test coverage.

Currently only supports two different Python tools:

- coverage.py
- trace.py (obsolete)


Usage
-----

1. Generate some coverage data (a ``.coverage`` file) by running your tests
with ``coverage run`` (or by using the appropriate test runner plugin).

2. Open a source file in vim

3. ``:HighlightCoverage``


Commands
--------

:HighlightCoverage
    Highlight untested source code lines.

    Tries to find the corresponding coverage report by looking for
    files named ``.coverage`` here (or in parent directories).

    Also looks for looking for files named ``coverage/<module>.report``
    to support ``trace.py`` reports, which are produced by zope.testrunner
    if you specify ``--coverage=coverage``.

:HighlightCoverage NN-NN,NN-NN,NN,...
    Highlight the specified source code lines and ranges.

    The format matches that produced by ``coverage report -m``, so you
    can copy & paste the ranges to the Vim command line from a web page,
    instead of having to hunt down and download ``.coverage`` files.

:HighlightCoverage <filename>.report
    Highlight untested source code lines from a trace.py report.

    Report files are just source code files indented with the number of
    executions or '>>>>>>' for uncovered lines prepended at the left
    margin.

:HighlightCoverageOff
    Turns off coverage highlighting


Settings
--------

g:coverage_script
    Default: autodetect

    Name of the script that can produce reports.  Example ::

        let g:coverage_script = 'python3 -m coverage'

    By default it looks for ``coverage`` in your PATH, and if not found,
    it looks for ``bin/coverage`` relative to the current working
    directory.


Requirements
------------

Vim with Python/Python3 support.
