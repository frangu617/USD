# Assignment 5.1: Written answers

These answers describe the saved run in `AAI_500_M5_Assignment_Completed.ipynb`.

### EDA interpretation
Patients with heart disease tend to be older: their median age is 57 years, compared with 51 years in the no-disease group, although the distributions overlap. The ASY chest-pain category has a higher observed disease frequency (79.0%) than ATA (13.9%), NAP (35.5%), or TA (43.5%), and ASY describes the recorded chest-pain category rather than the absence of disease. Flat ST slope and exercise-induced angina are associated with higher disease frequencies; the Flat/angina group has 90.4% disease compared with 71.8% for Flat/no angina. The maximum achieved heart rate is lower in the disease group (median 126 versus 150 beats/min), with substantial overlap between groups. These are associations in a selected sample, not independent causal effects or population risk estimates.

### Final structure choice
I select the constrained hill-climbing graph because it permits multiple dependencies while explicitly preventing symptoms or test findings from pointing into age or sex. Chow–Liu forces every variable into one connected tree, which can impose clinically awkward links and cannot express multiple parents for a finding. Limiting hill climbing to three parents also reduces sparse CPTs and keeps local relationships inspectable. This is a clinically motivated modeling preference made before test evaluation; the remaining learned arrows are statistical factorizations, not established causal directions.

### Answers to queries a-e

**Query a:** For a patient aged 60 or above with Flat ST slope, the network estimates a 80.96% probability of heart disease. Other features are unobserved and marginalized, so this is not the probability for a fully described patient.

**Query b:** Adding exercise-induced angina gives a probability of 91.19%, 10.23 percentage points higher than query a. This quantifies how the network updates the same partial patient profile after additional evidence, not the causal effect of angina.

**Query c:** For cholesterol at least 240 mg/dL and maximum achieved HR below 120 beats/min, the estimated probability is 68.75%. These fixed bin definitions determine which evidence is entered; age, symptoms, and the remaining features are marginalized.

**Query d:** For atypical angina (ATA) and no exercise-induced angina, the estimated probability is 10.32%. This describes the joint evidence pattern and does not mean that either feature rules out disease.

**Query e:** With age 60+, Flat ST slope, exercise-induced angina, and Oldpeak at least 2, the estimated probability is 89.63%, 1.56 percentage points lower than query b. Although the prompt calls this a full diagnostic, several features remain unspecified, and the result is a model estimate rather than a definitive diagnosis.

Matching-patient counts describe support for each evidence combination. The model can differ from the raw subgroup frequency because it uses a factorized distribution and smoothing; sparse groups warrant extra caution.

In query e, the added High Oldpeak evidence lowers the estimate slightly rather than increasing it. The model does not impose monotonic risk effects, and only 23 patients have this complete evidence combination; this result should therefore be interpreted in light of the learned dependencies, smoothing, and limited subgroup support.

### Classifier results and interpretation

The held-out classifier achieves **87.32% accuracy** and **0.9394 ROC AUC**, compared with **55.43% accuracy** for always predicting the training majority class. At the specified threshold it produces 138 true positives, 103 true negatives, 20 false positives, and 15 false negatives. AUC measures ranking discrimination rather than probability calibration; one split in this small sample does not establish performance in another hospital or population.

## 5. Discussion
### Why might a hospital prefer the Bayesian network?
A cardiologist can inspect this network's graph, conditional probability tables, and the way additional evidence changes a patient's modeled probability. The network also supports inference with partially observed patient features instead of requiring every input, and its assumptions can be reviewed with domain experts. Those properties may support clinical review, auditability, and communication even if another model has 3–5 percentage points higher accuracy. However, a preference should also consider false-negative and false-positive costs, calibration, subgroup performance, and external validation; an interpretable graph does not automatically establish causality or safety.

### Real-world example in 2025
**Infermedica** is a medical triage and care-navigation company whose inference engine uses modified Bayesian networks alongside other machine-learning methods. It updates assessments using symptoms, risk factors, and demographic information, asks follow-up questions, and recommends an appropriate level of care. Its real-world use in 2025 is documented by a publication describing Healthdirect Australia's national virtual front door; this is deployed triage support, rather than a claim that the classroom model is clinically validated. Sources: [Infermedica's inference-engine description](https://infermedica.com/inference-engine) and [McMahon and McInerney (2025), deployment publication listed on Infermedica's research page](https://infermedica.com/research-studies).

### Technical references
- [pgmpy 1.0 HillClimbSearch](https://pgmpy.org/_modules/pgmpy/estimators/HillClimbSearch.html)
- [pgmpy TreeSearch: Chow–Liu and TAN](https://pgmpy.org/_modules/pgmpy/estimators/TreeSearch.html)
- [KaggleHub loading documentation](https://github.com/Kaggle/kagglehub#load-dataset)

### Limitations
Discretization discards measurement detail, results depend on the graph and smoothing choices, and treating unknown measurements as a category may capture collection practices. Learned arrows are associations; no causal discovery claim is made. The split is reproducible but comes from the same dataset, with no external validation or calibration study.