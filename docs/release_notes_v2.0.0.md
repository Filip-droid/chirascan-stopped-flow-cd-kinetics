# StoppedFlowKinetiX 2.0.0 – graphical application for stopped-flow CD kinetics

This release adds **StoppedFlowKinetiX**, a Windows desktop application for analysing Chirascan stopped-flow
circular dichroism kinetics. The analysis is that of the notebook `G4_stopped_flow_kinetic_analysis.ipynb`
v1.0.0, unchanged: the same models, statistics and Excel export, and the same numbers, which the automated
tests check against the notebook's reference results. The notebook stays in the repository.

## Installation

Download **`Setup_for_StoppedFlowKinetiX_ver_2.0.0.exe`** below and run it. Python is not needed.
The installer is not code-signed, so Windows SmartScreen may warn: click **More info › Run anyway**.

To run from source instead: `pip install -r requirements.txt` and `python main.py` (Python 3.10+).

## What's new

- **Graphical interface in five steps**: Data → Process → Fit → Compare → Export, with live plots.
- **Data**: loading of Chirascan CSV files (folder, files, drag & drop), a metadata table, and tick boxes to
  choose the repeats to average.
- **Processing**: trimming of dead-time points, baseline subtraction and conversion to Δε, with sequence
  presets.
- **Fitting**:
  - one-, two- and three-phase association and one- and two-phase decay models
  - editable initial guesses and bounds, and estimation of the initial guesses from the data
  - fitting in the background, or all models at once
- **Results**: parameters with 95 % CI, τ and half-lives, R², RMSD, AIC, BIC, Durbin-Watson, a multi-start
  check and fit warnings.
- **Comparison**: a model table (ΔAIC, ΔBIC), F-tests of nested models (1 vs 2 and 2 vs 3 exponentials) and a
  plot of all fits.
- **Export**: the single-sheet Excel workbook of the notebook, a CSV data table, PNG plots and a text report.
- **Projects (`.sfkx`)**: one file that keeps the copies of the data files, all settings, fits, F-tests, the
  report and the window state.
- **Safety**: automatic saving with crash recovery, and a question before closing when there are unsaved
  changes.
- **Help**: a quick start, a user guide, a page on models and statistics, the input format and a FAQ, plus
  quick help (orange **?**) for every part of the window and help search (**F1**).

## Authors

Filip Křikava (analysis) and Jan Palacký (graphical application), Institute of Biophysics of the Czech Academy
of Sciences.
