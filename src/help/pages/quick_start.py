"""Help page: Quick start."""

TITLE = "Quick start"


def content():
    return """
<h1 id="top">Quick start</h1>
<p class="lead">Five steps from the Chirascan CSV export to the Excel workbook with the fitted rate
constants. The tabs on the left of the main window are these steps; the plots on the right follow
the tab you are on.</p>

<div class="steps">
<div class="step" id="qs-1"><span class="num">1</span><div>
<h3>Data</h3>
<p><b>File &rsaquo; Open folder…</b> (Ctrl+O) loads every Chirascan file of a folder (spectra in it go to the plot <i>Spectra</i>);
<b>Add files…</b> adds single files (<code>*.csv</code> or the binary <code>*.dsx</code>). You can also drag files or a folder onto the window.
Want to try first? Press <b>Load example</b>.</p>
<p>In <b>Traces to average</b> untick the repeats you do not want (a bubble, a failed shot). The
plot <i>Raw traces</i> shows the unticked ones faint.</p></div></div>

<div class="step" id="qs-2"><span class="num">2</span><div>
<h3>Processing</h3>
<p>Set the number of points to <b>remove from the beginning</b> (instrument dead time; the plot
<i>Trimming</i> shows the first 50 points with the removed ones crossed out) and from the end.</p>
<p>Fill the <b>sample</b>: sequence length, ε per nucleotide (or pick a preset), the absorbance of
the <b>unmixed</b> solution and the <b>baseline</b> (buffer, mdeg). The CD path length is read from
the CSV header. The <i>Δε kinetics</i> plot shows the converted trace.</p></div></div>

<div class="step" id="qs-3"><span class="num">3</span><div>
<h3>Fit</h3>
<p>Choose a model (one-, two-, three-phase association, one- or two-phase decay), check the initial
guesses p0, press <b>Fit</b> (F5) – or <b>Fit all models</b> (Ctrl+F5). The fit and its residuals
are plotted, the parameters with 95 % confidence intervals fill the table below the plot and the
full report goes to the <i>Report</i> tab.</p></div></div>

<div class="step" id="qs-4"><span class="num">4</span><div>
<h3>Compare</h3>
<p>The <i>Model comparison</i> table lists R², RMSD, AIC, BIC and Durbin-Watson of every fitted
model; ΔAIC / ΔBIC are relative to the best one. <b>Run both</b> F-tests to see whether a second
or third exponential improves the fit significantly.</p></div></div>

<div class="step" id="qs-5"><span class="num">5</span><div>
<h3>Export</h3>
<p>Pick the model to export and press <b>Export to Excel</b> (Ctrl+E). The workbook has the same
layout as the original notebook. Save the analysis with <b>File &rsaquo; Save project</b> to reopen
it later with all settings.</p></div></div>
</div>

<h2 id="qs-help">Getting help</h2>
<ul>
<li>The orange <span class="q">?</span> buttons give a short help on each part of the window, with a link
to the full section of the <a href="help://user_guide">User guide</a>.</li>
<li><b>F1</b> searches all help pages at once; <b>Shift+F1</b> opens the quick help of the step you are on.</li>
<li><a href="help://models">Models and statistics</a> explains the equations and every number of the
report.</li>
</ul>
"""
