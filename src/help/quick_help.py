# src/help/quick_help.py
"""The short texts of the orange "?" buttons: key -> (title, (page, anchor of
the full help), HTML). Shown in a small window with a button to the full
help section."""

QUICK_HELP = {
    "files": ("Input files", ("user_guide", "files"), """
<p><b>Open folder…</b> loads every Chirascan <code>*.csv</code> file of a folder; <b>Add CSV files…</b> adds
files to those already loaded. Dragging files or a folder onto the window works too.
<b>Load example</b> opens the TT3T example of the original analysis.</p>
<p>The table shows what was read from each file's header: date, temperature, path length (mm), wavelength,
bandwidth and the number of traces (repeats). Select a row and press <b>Remove file</b> to drop it.</p>"""),

    "traces": ("Traces to average", ("user_guide", "traces"), """
<p>Tick the repeats to average; untick those that are clearly wrong (an air bubble, a failed shot). Unticked traces disappear from
the plot <i>Raw traces</i> (<b>Show unticked traces</b> draws them faint grey); <i>Average</i> shows the ticked traces and their mean.</p>
<p>The time axis of the first ticked trace is used, so all ticked traces must have the same number of
points.</p>"""),

    "trimming": ("Trimming", ("user_guide", "trimming"), """
<p><b>Remove from the beginning</b>: points measured within the dead time of the instrument (mixing not
finished). The left half of the <i>Trimming</i> plot shows the first 50 points; removed ones are crossed out
in red. <b>Remove from the end</b>: e.g. a drifting end (0 = keep all).</p>"""),

    "sample": ("Sample", ("user_guide", "sample"), """
<p>For the concentration of the strand: <b>sequence length</b> N and the average <b>ε per nucleotide</b>
(strand ε = N·ε), the <b>absorbance of the unmixed solution</b> and the path length of its cuvette.</p>
<p>Easiest: type the <b>sequence</b> 5'→3' – N and ε are calculated from it (nearest-neighbour method, 260 nm;
I = inosine, X = abasic site). Or pick a <b>preset</b> of the original study, or type N and ε yourself.</p>
<p>Know the concentration already? Set <b>Concentration from</b> to <b>entered directly</b> and type it in µM –
before mixing (syringe) or in the cell (after 1:1 mixing). The absorbance and ε are then not used.</p>
<p>The 1:1 mixing of the stopped-flow halves the concentration – the program accounts for it.</p>"""),

    "cd_measurement": ("CD measurement", ("user_guide", "cd-measurement"), """
<p><b>Path length (CD)</b> of the stopped-flow cell – by default from <code>#Pathlength:</code> of the CSV
header (mm); untick to enter it in cm. <b>Baseline</b>: CD of the buffer alone at the same wavelength (mdeg),
subtracted before the conversion.</p>"""),

    "conversion": ("Conversion to Δε", ("user_guide", "conversion"), """
<p>Δε = (θ − baseline) · N·ε·l<sub>abs</sub> / (32980 · 0.5 · A · l<sub>CD</sub>), in M⁻¹ cm⁻¹ per strand
(whole sequence). <b>Δε expressed</b> switches to <b>per nucleotide</b> (divided by N); with it, press
<b>Estimate p0</b> before fitting.
The plot <i>Δε kinetics</i> shows the result – the data that are fitted. A red message says what is missing
when the conversion cannot be made.</p>"""),

    "model": ("Model", ("models", "models"), """
<p>Association models (one, two, three phases) for a <b>rising</b> signal: y = ΣA<sub>i</sub>(1 −
e<sup>−k<sub>i</sub>t</sup>) + y0. Decay models (one, two phases) for a <b>falling</b> signal.</p>
<p>Start with the simplest model and add phases while the fit, residuals, AIC/BIC and the F-test improve
(step 4).</p>"""),

    "p0": ("Initial guesses and bounds", ("user_guide", "p0"), """
<p>The fit starts from <b>p0</b> and keeps each parameter within its <b>lower</b> and <b>upper</b> bound
(double-click to edit; <code>inf</code> = no bound). Amplitudes and rate constants are ≥ 0.</p>
<p><b>Estimate p0</b> guesses the values from the data, <b>Use fit as p0</b> takes the fitted values,
<b>Reset p0</b> returns to the original analysis. Rate constant ≈ 1 / (duration of the phase in s).</p>"""),

    "fit_options": ("Fit options", ("user_guide", "fit-options"), """
<p><b>Multi-start check</b>: the model is refitted from this many randomly perturbed p0; the report warns if
a lower minimum exists (0 = off). <b>Residual smoothing window</b>: Savitzky-Golay window of the smoothed
residuals (plot only). A <b>logarithmic time axis</b> shows fast and slow phases together.</p>"""),

    "run_fit": ("Running the fit", ("user_guide", "run-fit"), """
<p><b>Fit</b> (F5) fits the chosen model, <b>Fit all models</b> (Ctrl+F5) all five. The results – parameters
with 95 % confidence intervals, τ, half-lives, R², RMSD, AIC, BIC, Durbin-Watson – are in the tables under the
plot and in the Report. Warnings are shown in red.</p>
<p>A fit belongs to the data it was made on: change the processing and it is marked outdated.</p>"""),

    "comparison": ("Model comparison", ("user_guide", "comparison"), """
<p>The table <i>Model comparison</i> lists all models fitted to the current data. Lower AIC/BIC is better: a
difference of 2 is evidence, 6 strong evidence. Durbin-Watson far below 2 means a systematic misfit.
<b>Show all fits</b> draws them together.</p>"""),

    "ftest": ("F-test of nested models", ("models", "ftest"), """
<p>Does a second (or third) exponential improve the fit more than expected by chance? Both models are fitted
from the p0 shown (the original analysis values, comma-separated) and compared by the extra-sum-of-squares
F-test. p &lt; 0.05: the more complex model is significantly better.</p>"""),

    "excel": ("Excel export", ("user_guide", "excel"), """
<p>Exports the chosen model (fitted to the current data) with metadata, inputs, parameters with CI, goodness
of fit, F-tests, software versions, figures and all data to one sheet <i>Results</i> – the layout of the
original notebook. Close the file in Excel before exporting to it again.</p>"""),

    "other_outputs": ("Other outputs", ("user_guide", "other-outputs"), """
<p><b>Data table (CSV)</b>: Δε with the fits and residuals of all models. <b>All plots (PNG)</b>: every plot
into a folder. <b>Report (TXT)</b>: the text report. <b>Save project</b>: files and settings to reopen the
analysis later.</p>"""),
}

# step tab index -> quick help shown by Shift+F1
STEP_HELP = ["files", "trimming", "model", "comparison", "excel"]
