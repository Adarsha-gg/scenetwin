# ADQA VA / NU split (new method)

Question counts: {'VA': 82, 'NU': 0, 'mixed': 2, 'other': 6}

| bucket   |        rho |             p |   n |   n_questions |
|:---------|-----------:|--------------:|----:|--------------:|
| VA       |   0.797029 |   5.52834e-17 |  72 |             4 |
| NU       | nan        | nan           |   0 |           nan |
| mixed    |   0.516398 |   0.190116    |   8 |             4 |
| all      |   0.788834 |   1.90139e-16 |  72 |             4 |

## Interpretation

ADQA (Kala et al. EMNLP 2025) argues AD eval must separate **visual appreciation**
from **narrative understanding** on coherent multi-minute segments.
If VA ρ >> NU ρ, CLIP grounding dominates; if NU lags, we need plot-level ADQA.