"""Shared settings of the tests (pytest loads this file first)."""


# ---------------------------------------------------------------------------
# Log of the last test run: tools/logs/tests_last_run.txt
# Written by these hooks however the tests are started (pytest in a terminal,
# the desktop shortcut "Run tests", VS Code's Testing panel). One line per test,
# written as it goes - so even a run that stops suddenly shows the last test -
# then the errors of the failed tests and the totals.
# ---------------------------------------------------------------------------
import datetime as _rl_dt
import platform as _rl_platform
import sys as _rl_sys

_rl = {'file': None, 'counts': {}, 'errors': []}


def pytest_sessionstart(session):
    if getattr(_rl_sys, 'frozen', False) or hasattr(session.config, 'workerinput'):
        return
    try:
        folder = session.config.rootpath / 'tools' / 'logs'
        folder.mkdir(parents=True, exist_ok=True)
        fh = open(folder / 'tests_last_run.txt', 'w', encoding='utf-8')
        fh.write('Test run %s\nPython %s  %s\nCommand: pytest %s\n\n' % (
            _rl_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), _rl_platform.python_version(),
            _rl_sys.executable, ' '.join(session.config.invocation_params.args)))
        fh.flush()
        _rl['file'] = fh
    except Exception:
        _rl['file'] = None


def pytest_runtest_logstart(nodeid, location):
    if _rl['file']:
        _rl['file'].write(nodeid + ' ... ')
        _rl['file'].flush()


def pytest_runtest_logreport(report):
    fh = _rl['file']
    if not fh:
        return
    if report.when == 'call' or (report.when == 'setup' and not report.passed):
        word = 'ERROR' if (report.when == 'setup' and report.failed) else report.outcome.upper()
        fh.write('%s (%.2f s)\n' % (word, report.duration))
        _rl['counts'][word] = _rl['counts'].get(word, 0) + 1
    elif report.when == 'teardown' and report.failed:
        fh.write('    ERROR after the test (teardown)\n')
        _rl['counts']['ERROR'] = _rl['counts'].get('ERROR', 0) + 1
    if report.failed:
        _rl['errors'].append((report.nodeid, report.when, report.longreprtext))
    fh.flush()


def pytest_sessionfinish(session, exitstatus):
    fh = _rl['file']
    if not fh:
        return
    for nodeid, when, text in _rl['errors']:
        fh.write('\n' + '=' * 70 + '\n%s  (%s)\n%s\n' % (nodeid, when, text))
    totals = ', '.join('%d %s' % (n, w.lower()) for w, n in sorted(_rl['counts'].items()))
    fh.write('\nFinished %s: %s (exit status %s)\n' % (
        _rl_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), totals or 'no tests', int(exitstatus)))
    fh.close()
    _rl['file'] = None
