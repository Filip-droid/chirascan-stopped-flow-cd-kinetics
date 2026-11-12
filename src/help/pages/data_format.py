"""Help page: Input data format."""

TITLE = "Input data format"


def content():
    return """
<h1 id="top">Input data format</h1>
<p class="lead">The program reads the CSV export ("ProDataCSV") of the Chirascan Pro-Data software for
stopped-flow kinetics.</p>

<h2 id="header">Header (metadata)</h2>
<p>These lines are read (missing ones are shown empty):</p>
<table>
<tr><th>Line</th><th>Example</th><th>Used for</th></tr>
<tr><td><code>#Date:</code></td><td>#Date: 2026/07/02</td><td>metadata</td></tr>
<tr><td><code>#Temperature:</code></td><td>#Temperature: 24.95 C</td><td>metadata</td></tr>
<tr><td><code>#Pathlength:</code></td><td>#Pathlength: 10</td><td>CD path length in mm (conversion to Δε)</td></tr>
<tr><td>line with <code>Wavelength:</code> and <code>Bandwidth</code></td>
<td>Wavelength,Wavelength: 265nm,,Bandwidth: 3nm</td><td>metadata</td></tr>
</table>

<h2 id="data-block">Data block</h2>
<pre>Data:

CircularDichroism
Wavelength:,265
Time,Repeat
,0,1,2,3,
0.1,4.4345,4.65776,4.50674,4.81189
0.2,8.29301,7.48822,7.95599,7.81467
…</pre>
<p>The block starts after the keyword <code>Data:</code> at the first numeric line and ends at the first empty
line. The first column is the time (s), the others the CD signal (mdeg) of the repeats. Columns that contain
only zeros (unused repeats) or only empty values, and a column named <code>HV</code> (detector high voltage),
are dropped. The traces are named <i>CD kinetics 1, 2, …</i> in the order of the file.</p>
<p class="note">The data must not contain missing values: an empty line inside the data ends the block.</p>

<h2 id="multiple">Several files</h2>
<p>Several files can be loaded and their traces averaged together, when they have the same number of points
(the same time axis) and the same path length. The Excel export lists the metadata and the original data of the traces that were
averaged; unticked traces, and files none of whose traces is ticked, are not exported.</p>

<h2 id="export-chirascan">Exporting from Pro-Data</h2>
<p>In the Pro-Data Viewer, export the kinetic measurement as CSV (all repeats in one file). Keep the header –
the program needs at least the <code>Data:</code> block; without <code>#Pathlength:</code> enter the CD path
length manually in step 2.</p>
"""
