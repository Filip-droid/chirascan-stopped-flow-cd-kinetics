"""Help page: Models and statistics."""

TITLE = "Models and statistics"


def content():
    return """
<h1 id="top">Models and statistics</h1>
<p class="lead">What is fitted and how every number of the report is calculated. The models are
phenomenological descriptions of the observed signal: an exponential phase should not by itself be
interpreted as a unique molecular intermediate without independent experimental support.</p>

<h2 id="models">Models</h2>
<h3 id="association">Association (rising) models</h3>
<div class="eq">y = Σ<sub>i</sub> A<sub>i</sub> (1 − e<sup>−k<sub>i</sub> t</sup>) + y0, &nbsp; i = 1, 2 or 3</div>
<p>y0 is the signal at t = 0, A<sub>i</sub> ≥ 0 the amplitudes, k<sub>i</sub> ≥ 0 the rate constants (s⁻¹).
The asymptote (t → ∞) is y0 + ΣA<sub>i</sub>; its confidence interval is not reported.</p>
<h3 id="decay">Decay models</h3>
<div class="eq">one phase: y = (y0 − asymptota) e<sup>−kt</sup> + asymptota</div>
<div class="eq">two phases: y = A1 e<sup>−k1 t</sup> + A2 e<sup>−k2 t</sup> + asymptota</div>
<p>In the one-phase decay y0 and the asymptote are free (it can also describe a rise); only k ≥ 0. In the
two-phase decay y0 = A1 + A2 + asymptota; its standard error follows from the covariance matrix by the delta
method.</p>
<p>Default initial guesses (p0) are those of the original analysis of G-quadruplex folding; they can be
changed for every model (see <a href="help://user_guide#p0">Initial guesses and bounds</a>).</p>

<h2 id="fitting">Fitting</h2>
<p>Bounded non-linear least squares (<code>scipy.optimize.curve_fit</code>, trust-region reflective
algorithm, at most 10 000 function evaluations). All points have equal weight.</p>

<h2 id="ci">Confidence intervals</h2>
<p>The 95 % confidence interval of a parameter p is p ± t<sub>0.975, n−p</sub> · SE, where SE is the square
root of the diagonal of the covariance matrix and t the Student quantile with n − p degrees of freedom
(n points, p parameters). It assumes independent, normally distributed errors – see
<a href="#dw">Durbin-Watson</a>.</p>

<h2 id="tau">Time constants and half-lives</h2>
<p>τ = 1/k and t½ = ln 2 / k (s). Their intervals follow from the interval of k (a monotonic
transformation): τ ∈ (1/k<sub>upper</sub>, 1/k<sub>lower</sub>); not given when the interval of k
includes 0.</p>

<h2 id="gof">Goodness of fit</h2>
<table>
<tr><th>Statistic</th><th>Definition</th><th>Meaning</th></tr>
<tr><td>R²</td><td>1 − SS<sub>res</sub>/SS<sub>tot</sub></td><td>fraction of the variance explained</td></tr>
<tr><td>RMSD</td><td>√(SS<sub>res</sub>/n)</td><td>typical deviation, in Δε units</td></tr>
<tr><td id="aic">AIC</td><td>n ln(SS<sub>res</sub>/n) + 2p</td><td>lower is better; penalises parameters</td></tr>
<tr><td>BIC</td><td>n ln(SS<sub>res</sub>/n) + p ln n</td><td>as AIC, stronger penalty</td></tr>
<tr><td>AIC, BIC (Gaussian log-likelihood)</td><td>−2 ln L + 2p, −2 ln L + p ln n, σ² = SS<sub>res</sub>/(n−p)</td><td>in the report; differences between models are the same</td></tr>
<tr><td id="dw">Durbin-Watson</td><td>Σ(e<sub>i</sub> − e<sub>i−1</sub>)² / Σe<sub>i</sub>²</td><td>≈ 2 uncorrelated residuals; ≪ 2 positive autocorrelation</td></tr>
<tr><td>Lag-1 autocorrelation</td><td>Σe<sub>i</sub>e<sub>i−1</sub> / Σe<sub>i</sub>²</td><td>≈ 0 is good</td></tr>
</table>
<p>Strong autocorrelation of the residuals means a systematic misfit (a missing phase, a drift) or correlated
noise; the confidence intervals are then too narrow.</p>

<h2 id="multistart">Multi-start check</h2>
<p>A fit can end in a local minimum. The model is refitted from N starting points p0·e<sup>ε</sup>,
ε ~ N(0, 0.5²) (random generator seeded with 0 – the result is reproducible). The report says how many of them
converged, how many reached the same minimum (SS<sub>res</sub> within 10⁻⁶ relative) and warns when a lower
minimum was found: then use different p0.</p>

<h2 id="warnings">Fit warnings</h2>
<ul>
<li><b>Covariance matrix not finite</b> – some parameters are not determined by the data (e.g. two equal
rate constants); the confidence intervals are undefined.</li>
<li><b>Parameter at its lower bound</b> – e.g. an amplitude of 0: that phase is probably not present.</li>
<li><b>95 % CI of k includes zero</b> – the rate constant is poorly determined.</li>
</ul>

<h2 id="ftest">F-test of nested models</h2>
<div class="eq">F = [(SS<sub>simple</sub> − SS<sub>complex</sub>) / (p<sub>c</sub> − p<sub>s</sub>)] / [SS<sub>complex</sub> / (n − p<sub>c</sub>)]</div>
<p>with p<sub>c</sub> − p<sub>s</sub> and n − p<sub>c</sub> degrees of freedom; p-value from the F distribution.
p &lt; 0.05 means that the extra exponential improves the fit more than expected by chance. A p-value below
10⁻³⁰⁰ underflows to 0 and is reported as &lt; 1e-300. With thousands of points even small systematic
improvements are significant – judge the size of the improvement and the residuals too.</p>

<h2 id="residuals">Residual smoothing</h2>
<p>The smoothed residuals are a Savitzky-Golay filter (window 51 points, polynomial order 3 by default) of the
residuals – a guide to the eye for systematic deviations; they do not enter any statistic.</p>
"""
