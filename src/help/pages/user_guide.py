"""Help page: User guide (the full manual). Every section has an id: the quick
help, the search and links jump to it."""

TITLE = "User guide"


def content():
    return """
<h1 id="top">User guide</h1>
<p class="lead">StoppedFlowKinetiX analyses stopped-flow circular dichroism (CD) kinetics exported from
an Applied Photophysics <b>Chirascan</b>: it averages the chosen repeats, removes the dead-time points,
subtracts the baseline, converts the signal from mdeg to molar circular dichroism Δε, fits one-, two-
and three-exponential models, compares them and exports everything to Excel. The analysis is the one of
the Jupyter notebook <i>G4_stopped_flow_kinetic_analysis</i> by Filip Křikava – the same equations,
the same statistics, the same numbers.</p>

<div class="toc"><b>Contents</b>
<ol>
<li><a href="#window">The main window</a></li>
<li><a href="#files">Step 1 – Input files</a>, <a href="#traces">traces to average</a>, <a href="#spectra">spectra</a></li>
<li><a href="#trimming">Step 2 – Trimming</a>, <a href="#sample">sample</a>,
    <a href="#cd-measurement">CD measurement</a>, <a href="#conversion">conversion to Δε</a></li>
<li><a href="#model">Step 3 – Model</a>, <a href="#p0">initial guesses and bounds</a>,
    <a href="#fit-options">fit options</a>, <a href="#run-fit">running the fit</a>,
    <a href="#results">results</a></li>
<li><a href="#comparison">Step 4 – Model comparison</a>, <a href="#ftest">F-test</a></li>
<li><a href="#excel">Step 5 – Excel export</a>, <a href="#other-outputs">other outputs</a></li>
<li><a href="#project">Projects</a>, <a href="#autosave">automatic saving</a></li>
<li><a href="#plots">Working with the plots</a></li>
<li><a href="#shortcuts">Keyboard shortcuts</a></li>
<li><a href="#references">References</a></li>
</ol></div>

<h2 id="window">1. The main window</h2>
<p>On the <b>left</b> are five tabs – the steps of the analysis, in order: <b>Data</b>,
<b>Processing</b>, <b>Fit</b>, <b>Compare</b>, <b>Export</b>. On the <b>right</b> are the plots (one tab
each: Raw traces, Average, Trimming, Δε kinetics, Fit &amp; residuals, All fits, F-test) and under them
three result tabs: <b>Fit parameters</b>, <b>Model comparison</b> and <b>Report</b>. Opening a step
shows the plot that belongs to it. The divider between the plots and the tables, and between the left
and right side, can be dragged.</p>
<p>Every change is applied at once: change a number of points, the absorbance or the selection of traces
and the averaged and converted kinetics are recomputed immediately. Fits made before such a change are
kept but marked <span class="old">outdated</span> – they belong to other data and cannot be exported
until the model is fitted again.</p>

<h2 id="files">2. Step 1 – Input files</h2>
<p><b>Open folder…</b> (Ctrl+O) loads every Chirascan file of a folder – the CSV export (<code>*.csv</code>) or
the binary file the instrument saves (<code>*.dsx</code>) – and <b>Add files…</b>
(Ctrl+Shift+O) adds individual files to those already loaded; dragging files or a folder from Explorer
onto the window does the same. <b>Load example</b> opens the example of the original analysis (TT3T,
4 repeats, 265 nm). <b>Remove file</b> removes the file selected in the table, <b>Clear all</b>
removes everything.</p>
<p>The table shows the metadata read from each file's header: measurement date, temperature, path
length (mm), wavelength and bandwidth (nm) and the number of traces (repeats). Columns of unused repeats
(all zeros) and the detector high-voltage column (HV) are left out. See
<a href="help://data_format">Input data format</a> for what the file must contain.</p>
<p>Each file is recognised by its content: kinetic measurements (a time axis) go to the table and the traces,
<b>spectra</b> (wavelength scans) to the list <a href="#spectra">Spectra</a>. The Chirascan saves a measurement as
<code>name00000.dsx</code> and its export as <code>name00000.csv</code>; when both are there, only one is loaded
(the CSV, or the .dsx when the CSV cannot be read). A damaged file is reported and skipped; the others load.</p>

<h3 id="traces">Traces to average</h3>
<p>Every trace of every file is listed with a tick box; ticked traces are averaged. A newly loaded file
has all its traces ticked. Untick a repeat that is clearly wrong – it disappears from the plot
<i>Raw traces</i> (tick <b>Show unticked traces</b> to see it faint grey and dashed), the plot <i>Average</i> shows the ticked ones and their mean. <b>Select all</b> /
<b>Select none</b> tick or untick everything; a click on a file's own box ticks all its traces.</p>
<p class="note">The averaged trace uses the time axis of the <b>first</b> ticked trace. Traces of
different files can be averaged, but they must have the same number of points (the same time axis);
otherwise the program says so.</p>

<h3 id="spectra">Spectra</h3>
<p>The spectra measured with the kinetics – the sample's CD spectrum (for example before and after adding a
ligand), the buffer background, baselines at the start or the end – are listed with their wavelength range,
temperature and date and drawn in the plot <i>Spectra</i>. They are for viewing only: they do not enter the
average, the fits or the F-tests. Tick the spectra to draw; <b>Remove</b> drops the one selected.</p>
<ul>
<li><b>Show</b> – the quantity plotted against the wavelength: circular dichroism (mdeg), or the HV (detector
voltage), absorbance, … recorded with it.</li>
<li><b>Subtract</b> – a spectrum (buffer, background, baseline) subtracted from all the others; it is interpolated
onto their wavelengths, so the steps need not match.</li>
<li><b>Hide points with HV above</b> (default 900 V) – where the sample or buffer absorbs strongly, little light
reaches the photomultiplier, its voltage (HV) rises to the limit and the CD is noise (a spike, for example near
253 nm with dGTP). These wavelengths are left out and the plot says how many; choose <b>Show: HV</b> to see the
detector voltage with the limit.</li>
<li><b>Mark kinetics wavelengths</b> – dashed lines at the wavelengths of the loaded kinetics (e.g. 265 and 297 nm).</li>
</ul>
<p>The spectra (with copies of their files) and these choices are saved in the project. The Excel export adds a
sheet <i>Spectra</i> with the spectra as drawn (wavelength and value columns) and the plot.</p>

<h2 id="trimming">3. Step 2 – Trimming</h2>
<p><b>Remove from the beginning</b>: points measured within the instrument dead time are meaningless
(mixing is not finished) and are removed. The left half of the plot <i>Trimming</i> shows the first 50
points of the average with the removed ones crossed out in red. The default, 1 point, is that of the
original analysis. <b>Remove from the end</b>: e.g. when the end of the trace drifts (0 = keep all).</p>

<h3 id="sample">Sample</h3>
<p id="concentration"><b>Concentration from</b> chooses how the strand concentration is obtained:</p>
<ul>
<li><b>absorbance (A, sequence length, ε)</b> – the default, as in the original analysis: c = A / (N·ε·l<sub>abs</sub>)
from the absorbance of the unmixed solution and the fields below;</li>
<li><b>entered directly</b> – type the strand concentration in µM and choose whether it is the concentration
<b>before mixing</b> (in the syringe) or <b>in the cell</b> (after the 1:1 mixing, i.e. half). The absorbance, its
path length and ε are then not used and greyed out; the sequence length is still used for Δε per nucleotide.</li>
</ul>
<p>Under the fields the program shows the strand concentration before mixing and in the cell, whichever way it
was obtained.</p>
<ul>
<li><b>Sequence (5'→3')</b>, optional: type or paste the oligonucleotide sequence and the <b>sequence
length</b> and <b>ε per nucleotide</b> are calculated from it by the nearest-neighbour method at 260 nm:
ε(strand) = 2 · Σ ε(doublets) − Σ ε(internal mononucleotides), i.e. twice the sum over all overlapping
doublets minus the mononucleotides except the two terminal ones (<a href="#ref-gray1995">Gray et al., 1995</a>). Letters A, C, G, T, U; <b>I</b> (inosine) is counted as G;
<b>X</b> (abasic site) is left out of the calculation but counts in the length, so that length × ε per nucleotide
is the ε of the strand. Spaces, dashes and the 5'/3' marks are ignored, so
<code>5'-GGG TTA GGG-3'</code> works. Under the field are the length, ε per nucleotide and ε of the strand; a red
message names letters that cannot be used. While a sequence is given, the length, ε and preset fields are filled
from it and locked; clear the sequence to enter them yourself. The sequence is saved in the project and listed in
the Excel export.</li>
<li><b>Preset</b> fills the sequence length and ε of the sequences of the original study (TTT, TT2T,
TT3T, TT4T, TT5T, T3T3T3, 1/x TT3T). Changing a value by hand sets the preset back to <i>(custom)</i>.</li>
<li><b>Sequence length</b> N (nt) and <b>ε per nucleotide</b> (M⁻¹ cm⁻¹ nt⁻¹): the molar extinction
coefficient of the strand is N·ε.</li>
<li><b>Absorbance (unmixed)</b>: the absorbance of the oligonucleotide solution <b>before</b> mixing
(e.g. measured on the Specord). The 1:1 mixing in the stopped-flow halves the concentration – the factor
0.5 in the conversion.</li>
<li><b>Path length (absorbance)</b>: of the cuvette used for the absorbance (1 cm by default).</li>
</ul>

<h3 id="cd-measurement">CD measurement</h3>
<p><b>Path length (CD)</b> of the stopped-flow cell: with <i>from the CSV header</i> ticked it is read from
the <code>#Pathlength:</code> line of the files (in mm; shown here in cm). All selected files must have the
same path length. Untick it to type the value yourself (e.g. a 1 mm cell when the header is wrong).</p>
<p><b>Baseline</b> (mdeg): the CD signal of the buffer alone (e.g. LiOH) at the same wavelength; it is
subtracted from the averaged trace before the conversion.</p>

<h3 id="conversion">Conversion to Δε</h3>
<div class="eq">Δε = (θ − baseline) · N·ε·l<sub>abs</sub> / (32980 · 0.5 · A · l<sub>CD</sub>)</div>
<p>θ is the averaged ellipticity in mdeg, 32980 converts mdeg to differential absorbance ΔA, the
concentration c = A / (N·ε·l<sub>abs</sub>) follows from the absorbance of the unmixed solution and 0.5
accounts for the 1:1 mixing. In general, Δε = (θ − baseline) / (32980 · c<sub>cell</sub> · l<sub>CD</sub>) with
c<sub>cell</sub> the strand concentration in the cell (M); with the concentration <b>entered directly</b> this
form is used.</p>
<p id="delta-eps-basis"><b>Δε expressed</b> chooses the unit of the result:</p>
<ul>
<li><b>per strand (whole sequence)</b> – the default and the unit of the original analysis: Δε per mole of strands,
in M⁻¹ cm⁻¹. N·ε is the extinction coefficient of the whole sequence.</li>
<li><b>per nucleotide</b> – Δε per mole of nucleotides: the per-strand value divided by the sequence length N
(factor = ε·l<sub>abs</sub> / (32980 · 0.5 · A · l<sub>CD</sub>)). Convenient for comparing sequences of
different length.</li>
</ul>
<p>The choice is saved in the project, shown on the plot axes and listed in the Excel export. Changing it changes
the data, so earlier fits become outdated. The default p0 of the models suit Δε per strand; with per nucleotide
the values are N times smaller – press <b>Estimate p0</b> before fitting. The factor is shown under the formula; a
red message tells what is missing when the conversion cannot be made. <b>Reset to defaults</b> sets the
values of the original analysis (TT3T, A = 1.6079, baseline 0.42 mdeg).</p>

<h2 id="model">4. Step 3 – Model</h2>
<p>Five models are available (details in <a href="help://models">Models and statistics</a>):</p>
<table>
<tr><th>Model</th><th>Equation</th><th>Use for</th></tr>
<tr><td>One phase association</td><td>y = A(1 − e<sup>−kt</sup>) + y0</td><td>rising signal, one phase</td></tr>
<tr><td>Two phase association</td><td>y = A1(1 − e<sup>−k1t</sup>) + A2(1 − e<sup>−k2t</sup>) + y0</td><td>two phases</td></tr>
<tr><td>Three phase association</td><td>… + A3(1 − e<sup>−k3t</sup>) + y0</td><td>three phases</td></tr>
<tr><td>One phase decay</td><td>y = (y0 − asymptota)e<sup>−kt</sup> + asymptota</td><td>falling (or rising) signal, one phase</td></tr>
<tr><td>Two phase decay</td><td>y = A1e<sup>−k1t</sup> + A2e<sup>−k2t</sup> + asymptota</td><td>falling signal, two phases</td></tr>
</table>

<h3 id="p0">Initial guesses (p0) and bounds</h3>
<p>Non-linear least squares needs a starting point. The table lists every parameter with its initial
guess <b>p0</b> and its <b>lower</b> and <b>upper</b> bound; double-click a cell to edit it
(<code>inf</code> / <code>-inf</code> = unbounded). Amplitudes and rate constants are ≥ 0 by default,
offsets are free. A value outside its bounds is refused.</p>
<ul>
<li><b>Reset p0</b>: the values of the original analysis for this model.</li>
<li><b>Use fit as p0</b>: the fitted values of this model become the new p0 (to refine or to check that
the fit returns to the same minimum).</li>
<li><b>Estimate p0</b>: amplitudes, offset and rate constants guessed from the data (the start and end
level, and the times where the signal covers ~20, 50 and 80 % of its change) – useful for new data where
the defaults are far off.</li>
</ul>
<p>Each model keeps its own p0, also in a saved project.</p>

<h3 id="fit-options">Fit options</h3>
<ul>
<li><b>Multi-start check</b> (default 5): after the fit, the model is refitted from this many randomly
perturbed copies of p0 (log-normal, σ = 0.5, seeded – reproducible). The report says how many converged,
how many reached the same minimum and warns when a <b>lower</b> minimum exists – then change p0.
0 switches the check off (faster).</li>
<li><b>Residual smoothing window</b>: Savitzky-Golay window (points, odd, polynomial order 3) of the
smoothed residuals drawn over the residuals – it shows systematic deviations. For the plot only; the
window is shortened automatically for short traces.</li>
<li><b>Show smoothed residuals</b>, <b>Logarithmic time axis</b>: plot settings (a log time axis makes
fast and slow phases visible together).</li>
</ul>

<h3 id="run-fit">Running the fit</h3>
<p><b>Fit</b> (F5) fits the chosen model, <b>Fit all models</b> (Ctrl+F5) all five, one after another. The
fit runs in the background: the window stays usable and the status bar shows progress. Every fit is
stored under its model name, so fits of different models do not overwrite each other; fitting the same
model again replaces its result.</p>

<h3 id="results">Results</h3>
<p>The plot <i>Fit &amp; residuals</i> shows the data with the fit (top) and the residuals with their
smoothed course (bottom). The tab <b>Fit parameters</b> lists y0, amplitudes, rate constants, the
asymptote, τ = 1/k and half-lives t½ = ln 2/k with their 95 % confidence intervals, and the goodness of
fit (R², RMSD, AIC, BIC, Durbin-Watson, lag-1 autocorrelation). Warnings (a parameter at its bound, a
confidence interval of k including zero, a lower minimum found by the multi-start check) are shown in
red. The <b>Report</b> tab collects the full text output of every fit and F-test. The copy buttons put the
tables on the clipboard as tab-separated text – paste them into Excel.</p>

<h2 id="comparison">5. Step 4 – Model comparison</h2>
<p>The table <b>Model comparison</b> lists every model fitted to the current data: R², RMSD, AIC, ΔAIC,
BIC, ΔBIC (relative to the lowest value), Durbin-Watson, lag-1 autocorrelation, the number of parameters
and the number of warnings. The best AIC and BIC are bold. <b>Show all fits</b> draws all of them over the
data, with their residuals.</p>
<p>Rules of thumb (from the original notebook): an increase of R² by 0.01 or more and a decrease of RMSD by
10 % or more may be significant; a decrease of AIC/BIC by 2 points is evidence, by 6 or more strong
evidence for the better model; a Durbin-Watson statistic far below 2 means autocorrelated residuals and
too narrow confidence intervals. Use the residual plots together with the numbers.</p>

<h3 id="ftest">F-test of nested models</h3>
<p>The extra-sum-of-squares F-test asks whether the more complex of two nested models (one with more
exponentials) reduces the residual sum of squares more than expected by chance. Two comparisons are
available: <b>1 vs 2 exponentials</b> and <b>2 vs 3 exponentials</b> (association models). Both models are
fitted from the p0 shown here – those of the original analysis, which differ from the p0 of step 3; edit
them as comma-separated numbers. <b>Run F-test</b> runs the chosen comparison, <b>Run both</b> (F6) both.
The result (F, degrees of freedom, p-value) is shown, written to the report and included in the Excel
export; the plot <i>F-test</i> shows both fits and their residuals. p &lt; 0.05: the more complex model
improves the fit significantly.</p>

<h2 id="excel">6. Step 5 – Excel export</h2>
<p>Choose the <b>model to export</b> (only models fitted to the current data are offered) and the file
(by default <code>results CD.xlsx</code> in the folder of the first CSV file) and press <b>Export to
Excel</b> (Ctrl+E). The workbook has one sheet, <i>Results</i>, laid out as by the notebook:</p>
<ul>
<li>left (columns A–F): metadata of every CSV file, analysis inputs (selected traces, trimming, sample,
path lengths, baseline, conversion factor, p0), fit results with 95 % CI, goodness of fit, equation,
multi-start check and warnings, F-tests made on the current data, software versions, and the fit and
residual figures;</li>
<li>right (from column J): the original data (mdeg) of the <b>traces that were averaged</b> – unticked traces
are left out, and so is a file none of whose traces is ticked – and the converted kinetics with the fit and
residuals.</li>
</ul>
<p class="note">Close the workbook in Excel before exporting to the same file again – Windows does not let
a program overwrite an open file.</p>

<h3 id="other-outputs">Other outputs</h3>
<ul>
<li><b>Data table (CSV)</b>: time, Δε, and the fit and residuals of every model fitted to the current
data – for plotting in Origin, GraphPad, etc.</li>
<li><b>All plots (PNG)</b>: every plot saved into a folder you choose (300 dpi).</li>
<li><b>Report (TXT)</b>: the text of the Report tab.</li>
<li>Each plot can also be copied (<span class="icon">copy</span> button above it) or saved in any format
(PNG, SVG, PDF) on its own.</li>
</ul>

<h2 id="project">7. Projects</h2>
<p><b>File &rsaquo; Save project</b> (Ctrl+S) writes a <code>.sfkx</code> file (compressed JSON) with
<b>everything</b> of the analysis:</p>
<ul>
<li>a <b>copy of every CSV file</b> (with its original path) – the project opens even when the data were moved,
renamed or deleted;</li>
<li>the selected traces, trimming, sample and conversion settings;</li>
<li>p0 and bounds of every model, the F-test starting values, the fit options;</li>
<li><b>all fits</b> (parameters, confidence intervals, statistics, fitted curves, residuals), the
<b>F-tests</b> and the text of the <b>Report</b>;</li>
<li>the state of the window: open step, plot and result tab, the model shown, plot options (smoothed
residuals, log time axis, unticked traces), the chosen F-test and the export settings.</li>
</ul>
<p><b>Open project</b> restores all of it: the tables, plots and the Excel export are available at once,
without fitting again. The CSV files are read from their place when they are unchanged; when one was deleted,
moved or edited, the copy stored in the project is used and the program says so. Not stored: the window size
and position, the list of recent projects and the automatic-saving interval (settings of the program, not of
an analysis). Projects of earlier versions still open. The last projects are under
<b>File &rsaquo; Recent projects</b>.</p>

<h3 id="autosave">Automatic saving and crash recovery</h3>
<p>While you work, the whole analysis (the same content as a project) is saved automatically every few
minutes – only when something has changed, never while a fit is running. Choose the interval (off, 2, 5, 10 or
20 minutes; default 5) under <b>File &rsaquo; Automatic saving</b>; the status bar shows <i>Saved automatically
at …</i>. If the program ends unexpectedly (a crash, a power cut), it offers at the next start to
<b>Restore</b> the work, <b>Discard</b> it or ask again later (<b>Not now</b>). Restored work counts as
unsaved – save it as a project. When the program is closed normally, the automatic save is deleted: it does not
replace <b>Save project</b>. The files are in <code>%LOCALAPPDATA%\\StoppedFlowKinetiX\\autosave</code>.</p>
<h3 id="closing">Closing the program</h3>
<p>When the analysis has unsaved changes, closing the program offers <b>Save and close</b>, <b>Close without
saving</b> or <b>Cancel</b>. Otherwise it asks for confirmation; tick <b>Do not ask again</b> to stop that
question (unsaved changes are still offered for saving). <b>File &rsaquo; Ask before closing</b> switches the
question on and off.</p>

<h2 id="plots">8. Working with the plots</h2>
<p>Every plot has the matplotlib toolbar: <b>Home</b> (original view), <b>Back/Forward</b>, <b>Pan</b>,
<b>Zoom</b> (draw a rectangle), <b>Subplots</b> (margins) and <b>Save</b>; and the program's buttons
<b>Copy</b> (to the clipboard, as an image) and <b>Save image</b>. Coordinates under the mouse are shown at
the right of the toolbar.</p>

<h2 id="shortcuts">9. Keyboard shortcuts</h2>
<table>
<tr><th>Key</th><th>Action</th></tr>
<tr><td>Ctrl+O / Ctrl+Shift+O</td><td>Open folder / add CSV files</td></tr>
<tr><td>Ctrl+S / Ctrl+Shift+S / Ctrl+Shift+P</td><td>Save project / save as / open project</td></tr>
<tr><td>Ctrl+1 … Ctrl+5</td><td>Go to step 1 … 5</td></tr>
<tr><td>Ctrl+R</td><td>Recompute the processing</td></tr>
<tr><td>F5 / Ctrl+F5</td><td>Fit the chosen model / fit all models</td></tr>
<tr><td>F6</td><td>Run both F-tests</td></tr>
<tr><td>Ctrl+E</td><td>Export to Excel</td></tr>
<tr><td>F1 / Shift+F1</td><td>Search the help / quick help for this step</td></tr>
<tr><td>Ctrl+Q</td><td>Exit</td></tr>
</table>

<h2 id="references">References</h2>
<p id="ref-gray1995">Gray D.M., Hung S.H., Johnson K.H. (1995) Absorption and circular dichroism spectroscopy of
nucleic acid duplexes and triplexes. <i>Methods Enzymol.</i> 246, 19–34.
<a href="https://doi.org/10.1016/0076-6879(95)46005-5">doi:10.1016/0076-6879(95)46005-5</a> – the
nearest-neighbour calculation of the extinction coefficient (step 2, <a href="#sample">Sample</a>).</p>

"""
