# VLM-as-judge cross-provider results

## Leaderboard vs SceneTwin ensemble

| Model | In-bench rho | T3 wins | External rho | T3 wins | Combined rho | T3 wins |
|---|---:|---|---:|---|---:|---|
| SceneTwin ensemble (CLIP+ADQA) | 0.9290 | 54/54 | 0.8730 | 173/180 | 0.8860 | 227/234 |
| anthropic/claude-sonnet-4-6 | 0.7129 | 44/54 | 0.7146 | 151/180 | 0.7127 | 195/234 |
| gemini/gemini-2.5-pro | 0.7558 | 43/54 | 0.7341 | 155/180 | 0.7358 | 198/234 |
| openai/gpt-5 | 0.7268 | 45/54 | 0.7395 | 161/180 | 0.7354 | 206/234 |

### Headline gap
SceneTwin ensemble beats the best VLM-as-judge by **+0.150 rho** on the combined corpus (n=312).
