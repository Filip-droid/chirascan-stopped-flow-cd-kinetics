"""Help page: Troubleshooting (FAQ)."""

TITLE = "Troubleshooting (FAQ)"


def content():
    return """
<h1 id="top">Troubleshooting (FAQ)</h1>

<h2 id="faq-load">A file does not load</h2>
<p>The message names the file and the reason. Most often it is not a Chirascan CSV export, the
<code>Data:</code> block is missing, or the data contain an empty line or a non-numeric value. See
<a href="help://data_format">Input data format</a>. Other files of the folder are loaded anyway.</p>

<h2 id="faq-pathlength">"The path length was not found in the CSV header"</h2>
<p>The files have no <code>#Pathlength:</code> line, or the selected files have different path lengths.
Untick <i>from the CSV header</i> in step 2 and enter the CD path length (cm) yourself, or select files
measured in the same cell.</p>

<h2 id="faq-points">"The selected traces have different numbers of points"</h2>
<p>Traces from files with different time axes cannot be averaged point by point. Select traces of files
measured with the same settings.</p>

<h2 id="faq-fit-fails">The fit fails ("no convergence")</h2>
<ul>
<li>Press <b>Estimate p0</b> – or set p0 by hand: amplitudes about the size of the signal change, rate
constants about 1 / (time of the phase in s).</li>
<li>Check the sign: the association models need a <b>rising</b> signal (amplitudes ≥ 0); for a falling
signal use a decay model.</li>
<li>Remove more dead-time points (step 2) if the first points are off.</li>
<li>A model with more phases than the data show often fails or gives amplitudes at 0 – use fewer phases.</li>
</ul>

<h2 id="faq-lower-minimum">"WARNING: a LOWER minimum was found"</h2>
<p>The multi-start check found a better fit from another starting point. <b>Use fit as p0</b> does not
help here – change p0 (e.g. <b>Estimate p0</b>, or swap fast and slow rate constants) and fit again until the
check reports <i>no lower minimum found</i>.</p>

<h2 id="faq-outdated">The fit is marked "outdated" / cannot be exported</h2>
<p>The selection of traces, trimming or conversion was changed after the fit – it belongs to other data. Fit
the model again (F5, or Ctrl+F5 for all).</p>

<h2 id="faq-excel">"Cannot write … Close the file if it is open in Excel"</h2>
<p>The workbook is open in Excel. Close it there, or export under another name.</p>

<h2 id="faq-help">The help does not open</h2>
<p>Help pages are opened in your default web browser from the folder
<code>%LOCALAPPDATA%\\StoppedFlowKinetiX\\help_pages</code>. If nothing happens, open a page from that folder
by double-click, and check that a default browser is set in Windows.</p>

<h2 id="faq-log">Reporting a problem</h2>
<p><b>Help &rsaquo; Open log file</b> shows the program's log; please attach it (and, if possible, the CSV
file) to a bug report.</p>
"""
