"""Help pages: What's new, Installation, License."""

from src.version import (ANALYSIS_AUTHOR, APP_NAME, APP_VERSION, CONTACT_EMAIL, GUI_AUTHOR, SOURCE_DOI,
                         SOURCE_REPOSITORY)


class whats_new:
    TITLE = "What's new"

    @staticmethod
    def content():
        return f"""
<h1 id="top">What's new</h1>
<h2 id="v2-0-1">Since version 2.0.0</h2>
<ul>
<li><b>macOS version</b>: a <code>.dmg</code> for Apple Silicon and for Intel Macs, built automatically for every
release (see <i>Installation</i>).</li>
<li><b>Fixed parameters</b> (step 3): tick <i>Fixed</i> to hold a parameter at its p0 during the fit; only the
others are fitted. Fixed values are marked in the results, report and Excel export and saved in the project.</li>
<li><b>Better initial guesses</b>: <i>Estimate p0</i> now searches the rate constants on a grid with the amplitudes
and offset solved exactly, then refines them – the fit starts next to the minimum (e.g. the three-phase fit of the
example with the multi-start check: 10 s → 0.1 s). Optionally run before every fit.</li>
<li><b>Binary Chirascan files (*.dsx)</b> are read directly – kinetics and spectra – next to the CSV export. A
measurement present as both is loaded once; damaged files are reported and skipped.</li>
<li><b>Spectra</b>: wavelength scans saved with the kinetics (sample, buffer background, baselines) are recognised,
listed in step 1 and drawn in the new plot <i>Spectra</i> – CD or HV, absorbance, …; baseline subtraction; points
with too high HV hidden; kinetics wavelengths marked. Saved in the project and exported to Excel (sheet
<i>Spectra</i>). Previously a spectrum CSV in the folder was read as kinetics.</li>
<li>The <b>extinction coefficient from the sequence</b> (step 2): type the oligonucleotide sequence and the length and
ε per nucleotide are calculated (nearest-neighbour method at 260 nm after Gray et al., Methods Enzymol. 246, 19–34,
1995; inosine and abasic sites supported). Saved in the
project and listed in the Excel export.</li>
<li>The Excel export contains only the <b>traces that were averaged</b>; unticked traces (and files with no
ticked trace) are no longer exported.</li>
<li><b>Concentration entered directly</b> (step 2, <i>Sample</i>) as an alternative to the absorbance: in µM, before
mixing or in the cell. The strand concentration (before mixing and in the cell) is now shown in both cases and listed
in the Excel export.</li>
<li><b>Δε per strand or per nucleotide</b> (step 2, <i>Conversion</i>): per strand (whole sequence) remains the
default.</li>
<li><code>setup_environment.bat</code>: a fresh Python environment for running from the source code, with a desktop
shortcut.</li>
</ul>
<h2 id="v2-0-0">Version 2.0.0</h2>
<p>The first release of {APP_NAME}, the graphical application of the repository
<i>chirascan-stopped-flow-cd-kinetics</i>. Version 1.0.0 of the repository was the Jupyter notebook
<i>G4_stopped_flow_kinetic_analysis</i> ({ANALYSIS_AUTHOR}); its analysis is used unchanged and gives the
same numbers (checked against the notebook's reference results by the tests). The notebook stays in the
repository.</p>
<ul>
<li>Loading of Chirascan CSV files (folder, files, drag &amp; drop), metadata table, choice of repeats by
tick boxes.</li>
<li>Trimming, baseline subtraction and conversion to Δε with immediate plots; sequence presets.</li>
<li>All five models of the notebook with editable p0 and bounds, p0 estimation, multi-start check,
background fitting, fit of all models at once.</li>
<li>Model comparison table (ΔAIC, ΔBIC), F-tests 1 vs 2 and 2 vs 3 exponentials.</li>
<li>Excel export identical in layout to the notebook; CSV, PNG and text outputs; projects (.sfkx).</li>
<li>Help: quick start, user guide, models and statistics, quick help (orange ?) and help search (F1).</li>
<li>Projects (.sfkx) with copies of the data, all fits, F-tests, the report and the window state.</li>
<li>Automatic saving with crash recovery; confirmation before closing.</li>
<li>The numbers are verified against the reference workbook of the notebook (tests/test_analysis.py).</li>
</ul>
"""


class installation:
    TITLE = "Installation"

    @staticmethod
    def content():
        return f"""
<h1 id="top">Installation</h1>
<h2 id="installer">With the installer (Windows)</h2>
<p>Run <code>Setup_for_{APP_NAME}_ver_{APP_VERSION}.exe</code> and follow the wizard. It installs the program
into <i>Program Files</i>, creates a Start menu entry (with the uninstaller) and optionally a desktop icon and
the association of project files (<code>.sfkx</code>). Uninstall from the Start menu or from Windows
<i>Settings &rsaquo; Apps</i>.</p>

<h2 id="macos">macOS</h2>
<p>Download <code>{APP_NAME}_{APP_VERSION}_macOS_AppleSilicon.dmg</code> (Macs with an M1 or newer chip) or
<code>…_macOS_Intel.dmg</code> (older Intel Macs) from the release on GitHub; macOS 11 or newer. Open the
<code>.dmg</code> and drag <b>{APP_NAME}</b> onto <b>Applications</b>.</p>
<p>The app is not signed with an Apple developer certificate, so macOS blocks the first start: open it, click
<b>Done</b>, then in <i>System Settings &rsaquo; Privacy &amp; Security</i> click <b>Open Anyway</b>. After that it
opens normally. On the Mac, the shortcuts written here with Ctrl use <b>Cmd (⌘)</b>, e.g. Cmd+O, Cmd+S.
Automatic saves, the log and these help pages are in <code>~/Library/Application Support/{APP_NAME}</code>;
to uninstall, move the app to the Bin.</p>

<h2 id="source">From the source code</h2>
<pre>git clone https://github.com/Filip-droid/chirascan-stopped-flow-cd-kinetics.git
cd chirascan-stopped-flow-cd-kinetics
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python main.py</pre>
<p>Required: Python 3.10 or newer, PyQt5, numpy, scipy, pandas, matplotlib, xlsxwriter (openpyxl and pytest
for the tests).</p>

<h2 id="tests">Tests</h2>
<pre>python -m pytest</pre>
<p>The tests compare the results with the reference workbook of the original notebook.</p>

<h2 id="build">Building the installer</h2>
<p>Install PyInstaller (<code>pip install pyinstaller</code>) and Inno Setup 6, then run
<code>BuildInstaller.bat</code> in the project folder. The installer is written to <code>installer\\</code>.</p>
<p>The macOS app is built on GitHub's Mac machines by <code>.github/workflows/build-macos.yml</code> when a release
is published (or by hand under <i>Actions &rsaquo; Build macOS app &rsaquo; Run workflow</i>); the
<code>.dmg</code> files are attached to the release.</p>
"""


class license:
    TITLE = "License"

    @staticmethod
    def content():
        return f"""
<h1 id="top">License</h1>
<pre>MIT License

Copyright (c) 2026 Institute of Biophysics of the Czech Academy of Sciences

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</pre>
<h2 id="credits">Credits and citation</h2>
<p>Analysis: {ANALYSIS_AUTHOR} (Institute of Biophysics of the Czech Academy of Sciences / Masaryk University),
<a href="{SOURCE_REPOSITORY}">{SOURCE_REPOSITORY}</a>, DOI {SOURCE_DOI}.<br>
Graphical interface: {GUI_AUTHOR} ({CONTACT_EMAIL}).</p>
<p>If you use this software, please cite the original analysis (see CITATION.cff).</p>
"""
