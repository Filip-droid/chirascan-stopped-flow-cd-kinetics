# Stopped-flow CD kinetic analysis of G-quadruplex folding

A Jupyter notebook for analysing stopped-flow circular dichroism (CD) kinetic traces exported from a Chirascan instrument. The workflow averages selected repeats, subtracts a baseline, converts CD signal from mdeg to molar circular dichroism (Δε), fits exponential kinetic models, compares nested models, and exports results to a single Excel workbook.

## Features

- Imports Chirascan CSV exports and extracts measurement metadata
- Plots individual kinetic traces for visual inspection
- Selects and averages chosen repeats
- Removes user-defined points at the beginning and end of the trace
- Subtracts a baseline and converts mdeg to Δε
- Fits one-, two-, and three-phase association models
- Fits one- and two-phase decay models
- Reports fitted parameters, 95% confidence intervals, time constants, and half-lives
- Calculates R², RMSD, AIC, BIC, Durbin-Watson statistic, and lag-1 residual autocorrelation
- Performs F-tests for nested comparisons: one vs two and two vs three exponentials
- Uses a reproducible multi-start check to help identify local minima
- Exports metadata, settings, fit results, diagnostics, figures, and data tables to one Excel worksheet

## Repository contents

```text
G4_stopped_flow_kinetic_analysis.ipynb  Main analysis notebook
example/                                Example Chirascan CSV input data
expected_results_TT3T_10K.xlsx          Reference Excel output for the example data
README.md                               This documentation
LICENSE                                 MIT License
CITATION.cff                            Citation metadata
```

The notebook contains saved example outputs so that its workflow and expected results can be inspected without running it.

## Requirements

- Python 3.11 or newer recommended
- Jupyter Notebook or JupyterLab
- `numpy`
- `pandas`
- `scipy`
- `matplotlib`
- `xlsxwriter`

Install the dependencies with:

```bash
pip install numpy pandas scipy matplotlib xlsxwriter jupyter
```

## Quick start

1. Clone or download this repository.
2. Open `G4_stopped_flow_kinetic_analysis.ipynb` in Jupyter Notebook or JupyterLab.
3. Run the cells from top to bottom.
4. For the included demonstration, leave the first-cell setting as:

```python
directory = r"example"
```

5. To analyse your own data, place compatible Chirascan CSV files in a directory and replace `directory` with its path.
6. Adjust the input settings, trace selection, trimming, baseline, absorbance, sequence length, and extinction coefficient as appropriate for the experiment.
7. Run the desired model-fit cells, select `MODEL_TO_EXPORT`, and run the final export cell.

The Excel workbook is written to the selected data directory. Close an existing workbook with the same name in Excel before re-running the export.

## Workflow

1. **Load data** — reads all CSV files in `directory`, extracts metadata, and plots the raw kinetic traces.
2. **Select, average, and trim** — set `chosen_columns`, then remove unsuitable points from the beginning and/or end of the averaged trace.
3. **Baseline subtraction and conversion** — subtracts the baseline and converts mdeg to Δε using the entered absorbance, sequence length, extinction coefficient, and optical path lengths.
4. **Model fitting** — run any of the available association or decay model cells. Results are stored independently, so fitting one model does not overwrite another.
5. **Model comparison** — run the nested F-test cells for one vs two and two vs three exponential association models where appropriate.
6. **Excel export** — exports the selected fitted model only when it matches the currently analysed data.

## Input format

The notebook is designed for CSV exports from a Chirascan stopped-flow CD instrument. It expects a metadata header and a `Data:` block containing a time column and one or more CD kinetic traces. The CD-cell path length is read from the `Pathlength` field in the CSV header unless overridden in the notebook.

## Notes on model selection

Use residual plots and model-comparison metrics together rather than relying on a single statistic. AIC and BIC penalise additional parameters, while the nested F-tests assess whether a more complex exponential association model improves the fit relative to a simpler nested model. Strong residual autocorrelation or a Durbin-Watson statistic far below 2 can indicate systematic misfit or correlated noise; in that situation, parameter confidence intervals may be too narrow.

The models are phenomenological descriptions of the observed kinetic signal. An exponential phase should not by itself be interpreted as a unique molecular intermediate without independent experimental support.

## Reproducibility

The notebook keeps saved outputs from the included example data. The Excel export records analysis inputs, input-file metadata, fit results, goodness-of-fit statistics, F-tests performed on the current data, software versions, and fit/residual figures.

## Citation

If you use this software, please cite it using the metadata in [`CITATION.cff`](CITATION.cff).

## License

This project is released under the [MIT License](LICENSE).