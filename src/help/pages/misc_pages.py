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
<li>The <b>extinction coefficient from the sequence</b> (step 2): type the oligonucleotide sequence and the length and
ε per nucleotide are calculated (nearest-neighbour method at 260 nm after Gray et al., Methods Enzymol. 246, 19–34,
1995; inosine and abasic sites supported). Saved in the
project and listed in the Excel export.</li>
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
