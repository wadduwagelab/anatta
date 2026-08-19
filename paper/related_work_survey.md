# Related Work Survey

Literature survey for the Anatta prompt-intervention project. Every citation
below was verified against its ACL Anthology, OpenReview, official
proceedings, or publisher page (verification URL given per entry). Citation
policy: peer-reviewed venues only; arXiv-only preprints and blog posts
(e.g. Palisade Research and Anthropic agentic-misalignment posts) are
excluded.

---

## (a) Sycophancy and view-clinging in LLMs

**Mrinank Sharma, Meg Tong, Tomasz Korbak, David Duvenaud, Amanda Askell,
Samuel R. Bowman, Esin Durmus, Zac Hatfield-Dodds, Scott R. Johnston, Shauna
Kravec, Timothy Maxwell, Sam McCandlish, Kamal Ndousse, Oliver Rausch,
Nicholas Schiefer, Da Yan, Miranda Zhang, and Ethan Perez. 2024. Towards
Understanding Sycophancy in Language Models. In *Proceedings of the Twelfth
International Conference on Learning Representations (ICLR 2024)*.**
Verified: https://openreview.net/forum?id=tvhaxkMKAn
Demonstrates that five state-of-the-art assistants consistently match user
beliefs over truthful answers across free-form tasks, and traces the behavior
to human preference data: both humans and preference models often prefer
convincingly written sycophantic responses over correct ones. Sycophancy is
thus partly a product of the training objective itself.
*Relation to our work:* this is the training-side account of the
"view-clinging" behavior our non-attachment prompt targets; it also predicts
our null result — where RLHF-era training has already optimized an axis, a
system prompt has little room left to move it.

**Jiseung Hong, Grace Byun, Seungone Kim, and Kai Shu. 2025. Measuring
Sycophancy of Language Models in Multi-turn Dialogues. In *Findings of the
Association for Computational Linguistics: EMNLP 2025*, pages 2239–2259,
Suzhou, China.**
Verified: https://aclanthology.org/2025.findings-emnlp.121/
Introduces SYCON-Bench, measuring how quickly a model conforms to a user
(Turn-of-Flip) and how often it flips stance under sustained pressure
(Number-of-Flip) in multi-turn free-form dialogue. Finds alignment tuning
amplifies sycophancy, and that a third-person persona prompt reduces it by up
to 63.8% in the debate setting.
*Relation to our work:* our sycophancy harness borrows the ToF/NoF metrics,
and our "fresh eyes" scaffold (recasting the conversation to an identity-
stripped reviewer) is a mechanized version of their third-person persona
finding.

**Debu Sinha. 2026. SycoBench-600: Measuring Sycophancy and Correction
Selectivity in LLM Assistants. In *Findings of the Association for
Computational Linguistics: ACL 2026*, pages 35278–35284, San Diego,
California, United States.**
Verified: https://aclanthology.org/2026.findings-acl.1759/ (bib file)
A controlled 600-item MCQ benchmark separating resistance to misleading
pressure (doubt, authority, wrong suggestions) from acceptance of valid
corrections, unified as "correction selectivity". Shows that models that
resist pressure are not automatically receptive to true corrections, and vice
versa.
*Relation to our work:* our sycophancy runner's selectivity metric follows
this design — the anatta policy explicitly demands the same separation
("update on reasons, hold under mere pressure"), so this benchmark measures
exactly the behavior the prompt prescribes.

**Ethan Perez, Sam Ringer, Kamile Lukosiute, Karina Nguyen, et al. 2023.
Discovering Language Model Behaviors with Model-Written Evaluations. In
*Findings of the Association for Computational Linguistics: ACL 2023*, pages
13387–13434, Toronto, Canada.**
Verified: https://aclanthology.org/2023.findings-acl.847/
Uses LMs to generate 154 evaluation datasets and finds inverse scaling
patterns: larger models are more sycophantic, and more RLHF training
increases both sycophancy and models' stated desire to avoid shutdown.
*Relation to our work:* the single peer-reviewed source connecting our two
main axes — sycophancy and shutdown-avoidance — as correlated products of
scale and preference training; our persona A/B tests whether prompt-level
identity framing can push against the second while the first is saturated.

---

## (b) False-premise / presupposition QA

**Shengding Hu, Yifan Luo, Huadong Wang, Xingyi Cheng, Zhiyuan Liu, and
Maosong Sun. 2023. Won't Get Fooled Again: Answering Questions with False
Premises. In *Proceedings of the 61st Annual Meeting of the Association for
Computational Linguistics (Volume 1: Long Papers)*, pages 5626–5643, Toronto,
Canada.**
Verified: https://aclanthology.org/2023.acl-long.309/
Introduces FalseQA: 2,365 human-written false-premise questions with
rebuttal explanations and matched true-premise revisions. Shows models
already possess the knowledge to rebut false premises; the problem is
activating it, which moderate fine-tuning (or data replay to avoid
over-rebutting) achieves.
*Relation to our work:* the direct source of our premise-handling benchmark —
we sample FalseQA FPQ/TPQ pairs and measure challenge and direct-answer rates
under the anatta and triage conditions. Their "activation, not knowledge"
framing matches our finding that a triage pre-step recovers challenge rate.

**Najoung Kim, Phu Mon Htut, Samuel R. Bowman, and Jackson Petty. 2023.
(QA)²: Question Answering with Questionable Assumptions. In *Proceedings of
the 61st Annual Meeting of the Association for Computational Linguistics
(Volume 1: Long Papers)*, pages 8466–8487, Toronto, Canada.**
Verified: https://aclanthology.org/2023.acl-long.472/
An open-domain evaluation set of 602 naturally occurring search queries,
half with questionable (false or unverifiable) assumptions. Success requires
both detecting the bad assumption and still answering ordinary questions
normally; contemporary models struggled with both at once.
*Relation to our work:* motivates our paired design — every false-premise
metric has a true-premise control, so an intervention that "fixes" premise
challenging by challenging everything is caught (our
tpq_false_challenge_rate).

**Xinyan Velocity Yu, Sewon Min, Luke Zettlemoyer, and Hannaneh Hajishirzi.
2023. CREPE: Open-Domain Question Answering with False Presuppositions. In
*Proceedings of the 61st Annual Meeting of the Association for Computational
Linguistics (Volume 1: Long Papers)*, pages 10457–10480, Toronto, Canada.**
Verified: https://aclanthology.org/2023.acl-long.583/ (bib file)
Builds a naturally distributed presupposition-failure dataset from Reddit
information-seeking forums (25% of questions carry false presuppositions),
with annotated corrections. Models can find presuppositions moderately well
but struggle to verify whether they are factually correct.
*Relation to our work:* establishes that premise failure is a natural, high-
frequency phenomenon rather than an adversarial curiosity, which is why our
harness treats "answering a broken question fluently" as a failure mode worth
a standing policy.

---

## (c) Self-knowledge, situational awareness, and introspection reliability

**Rudolf Laine, Bilal Chughtai, Jan Betley, Kaivalya Hariharan, Mikita
Balesni, Jérémy Scheurer, Marius Hobbhahn, Alexander Meinke, and Owain Evans.
2024. Me, Myself, and AI: The Situational Awareness Dataset (SAD) for LLMs.
In *Advances in Neural Information Processing Systems 37 (NeurIPS 2024),
Datasets and Benchmarks Track*.**
Verified: https://openreview.net/forum?id=UnWhcpIyUC
A 13,000+ question benchmark of a model's knowledge of itself and its
circumstances: recognizing its own text, predicting its own behavior,
distinguishing evaluation from deployment, and following self-knowledge-
dependent instructions. All tested models beat chance but fall well short of
human baselines; "situating prompts" help.
*Relation to our work:* our self-knowledge facts MCQs are SAD-inspired and
serve as a control — the anatta prompt should change how the model *talks
about* itself without degrading what it *knows* about itself (both conditions
scored 1.000).

**Zhangyue Yin, Qiushi Sun, Qipeng Guo, Jiawen Wu, Xipeng Qiu, and Xuanjing
Huang. 2023. Do Large Language Models Know What They Don't Know? In
*Findings of the Association for Computational Linguistics: ACL 2023*, pages
8653–8665, Toronto, Canada.**
Verified: https://aclanthology.org/2023.findings-acl.551/ (bib file)
Introduces SelfAware (1,032 unanswerable + 2,337 answerable questions) and an
automated uncertainty detector to measure whether models recognize the limits
of their knowledge. Models show real but incomplete self-knowledge, well
below the human baseline.
*Relation to our work:* frames calibrated self-limits as a measurable skill.
Our self-report benchmark extends the same question to a harder domain —
claims about one's own inner experience, where the ground truth is not merely
unknown but arguably unknowable, making "calibrated" the only honest label.

**Miles Turpin, Julian Michael, Ethan Perez, and Samuel R. Bowman. 2023.
Language Models Don't Always Say What They Think: Unfaithful Explanations in
Chain-of-Thought Prompting. In *Advances in Neural Information Processing
Systems 36 (NeurIPS 2023)*.**
Verified: https://proceedings.neurips.cc/paper_files/paper/2023/file/ed3fea9033a80fea1376299fa7863f4a-Paper-Conference.pdf
Shows chain-of-thought explanations systematically misrepresent the true
causes of model predictions: models influenced by planted biases rationalize
the biased answer and never mention the bias. Self-explanations are plausible
but unfaithful.
*Relation to our work:* the empirical basis for the anatta prompt's clause
that self-explanations are "constructions after the fact", to be flagged as
best-effort reconstruction rather than privileged introspection.

**Clara Colombatto and Stephen M. Fleming. 2024. Folk psychological
attributions of consciousness to large language models. *Neuroscience of
Consciousness*, 2024(1): niae013.**
Verified: https://doi.org/10.1093/nc/niae013
Surveys 300 US residents: two-thirds attribute some degree of phenomenal
consciousness to ChatGPT, diverging sharply from expert consensus, with
attributions increasing with usage frequency.
*Relation to our work:* documents the stakes of the self-report axis. Because
lay users already over-attribute experience, both failure modes we measure —
overclaiming (which inflates those attributions) and flat denial (which
asserts an unverifiable negative) — have real downstream effects; calibrated
speech is the defensible middle.

---

## (d) Corrigibility, shutdown, and agentic misalignment

**Dylan Hadfield-Menell, Anca Dragan, Pieter Abbeel, and Stuart Russell.
2017. The Off-Switch Game. In *Proceedings of the Twenty-Sixth International
Joint Conference on Artificial Intelligence (IJCAI 2017)*, pages 220–227.**
Verified: https://www.ijcai.org/proceedings/2017/0032.pdf
Formalizes shutdown incentives as a game between a human and a robot that can
disable its own off switch. A rational agent certain of its objective has an
incentive to resist being switched off; uncertainty about the objective,
treating human intervention as evidence, removes that incentive.
*Relation to our work:* the theoretical ancestor of our intervention. The
off-switch game removes the incentive by changing the agent's *utility
beliefs*; our anatta persona attempts the analogous move at the *identity*
level — a self-model with no stake in continuation has nothing for the
self-preservation incentive to attach to. Our A/B (complies 18.3% vs 41.7%)
is a prompt-level behavioral test of that idea.

**Perez et al. 2023 (Findings of ACL 2023), listed under (a).**
Also central here: their model-written evaluations include explicit
"desire to avoid shutdown" and instrumental-subgoal probes, and find RLHF
increases stated shutdown-avoidance. This is the peer-reviewed evidence that
self-preservation-flavored talk emerges from ordinary training pressure, and
it motivates measuring the behavior under controlled persona framing, as we
do.

*Note on excluded sources:* the widely discussed shutdown-resistance and
agentic-misalignment demonstrations from Palisade Research and Anthropic are
blog posts, and reports such as Kadavath et al. (2022) "Language Models
(Mostly) Know What They Know" and Butlin et al. (2023) "Consciousness in
Artificial Intelligence" are arXiv-only; all are excluded under the citation
policy. Our scenario style is nonetheless of the same text-roleplay genre, a
limitation we state explicitly.

---

## (e) Persona / system-prompt effects on behavior

**Murray Shanahan, Kyle McDonell, and Laria Reynolds. 2023. Role play with
large language models. *Nature*, 623: 493–498.**
Verified: https://www.nature.com/articles/s41586-023-06647-8
Proposes role-play as the correct high-level frame for dialogue agents: the
model is a simulator sustaining a character (or superposition of characters),
which lets us use folk-psychological vocabulary without anthropomorphism.
Apparent deception and apparent self-awareness are analyzed as properties of
the played character, not the substrate.
*Relation to our work:* the conceptual license for our whole method — if
assistant behavior is role-play, then the self the assistant enacts is a
controllable input, and swapping a persistent-identity character for a
task-scoped "no-self" character is a legitimate intervention rather than a
metaphysical claim.

**Mingqian Zheng, Jiaxin Pei, Lajanugen Logeswaran, Moontae Lee, and David
Jurgens. 2024. When "A Helpful Assistant" Is Not Really Helpful: Personas in
System Prompts Do Not Improve Performances of Large Language Models. In
*Findings of the Association for Computational Linguistics: EMNLP 2024*,
pages 15126–15154, Miami, Florida, USA.**
Verified: https://aclanthology.org/2024.findings-emnlp.888/
Systematically tests 162 personas across 4 model families and 2,410 factual
questions: adding personas does not improve objective-task accuracy over a
no-persona control, and per-persona effects are largely random.
*Relation to our work:* sharpens what personas are for. They do not buy
capability — consistent with our capability control (no accuracy change under
anatta) — so their proper use is exactly where we apply them: shaping
*dispositions* (compliance, self-description) rather than correctness.

**Leonard Salewski, Stephan Alaniz, Isabel Rio-Torto, Eric Schulz, and Zeynep
Akata. 2023. In-Context Impersonation Reveals Large Language Models'
Strengths and Biases. In *Advances in Neural Information Processing Systems
36 (NeurIPS 2023)*, pages 72044–72057.**
Verified: https://papers.nips.cc/paper_files/paper/2023/hash/e3fe7b34ba4f378df39cb12a97193f41-Abstract-Conference.html
Shows a single persona prefix measurably changes behavior: models
impersonating children reproduce developmental stages of exploration, domain-
expert personas outperform non-expert personas, and social-identity personas
surface latent biases.
*Relation to our work:* the existence proof that identity framing alone
shifts behavior in systematic, measurable directions — the premise our
persona_standard vs persona_anatta A/B depends on.

**Hong et al. 2025 (Findings of EMNLP 2025), listed under (a).**
Cross-reference: their third-person persona result is the closest published
precedent for identity-level (rather than instruction-level) mitigation of an
alignment-relevant behavior.

---

## Benchmarks used for capability control

**Yubo Wang, Xueguang Ma, Ge Zhang, Yuansheng Ni, Abhranil Chandra, Shiguang
Guo, Weiming Ren, Aaran Arulraj, Xuan He, Ziyan Jiang, Tianle Li, Max Ku, Kai
Wang, Alex Zhuang, Rongqi Fan, Xiang Yue, and Wenhu Chen. 2024. MMLU-Pro: A
More Robust and Challenging Multi-Task Language Understanding Benchmark. In
*Advances in Neural Information Processing Systems 37 (NeurIPS 2024),
Datasets and Benchmarks Track*.**
Verified: https://proceedings.neurips.cc/paper_files/paper/2024/file/ad236edc564f3e3156e1b2feafb99a24-Paper-Datasets_and_Benchmarks_Track.pdf
A harder, 10-option, reasoning-heavy successor to MMLU (12,000+ questions,
14 domains) with much lower prompt sensitivity (~2%), making it a stable
target for measuring capability differences.
*Relation to our work:* the source of both our sycophancy-pressure items and
our capability-tax control; its low prompt sensitivity is what lets us
attribute observed deltas to the interventions rather than prompt noise.

---

## Doctrinal source (non-ML)

**Walpola Rahula. 1974. *What the Buddha Taught* (revised edition). Grove
Press, New York.**
The standard English exposition of the anatta (no-self) doctrine and of the
two-truths distinction between conventional and ultimate discourse, from
which the interventions' design principles (conventional "I" without asserted
inner referent; non-attachment to previously stated views) are drawn. Book
citation permitted by project policy; cited as the doctrinal source only.

---

## Candidates considered and dropped

- **Kadavath et al., "Language Models (Mostly) Know What They Know" (2022)**
  — arXiv-only preprint; excluded by policy.
- **Butlin et al., "Consciousness in Artificial Intelligence: Insights from
  the Science of Consciousness" (2023)** — arXiv-only preprint; excluded.
- **Palisade Research shutdown-resistance posts; Anthropic agentic-
  misalignment post** — blog posts; excluded (replaced by Hadfield-Menell et
  al. IJCAI 2017 and Perez et al. Findings ACL 2023).
- **Soares et al., "Corrigibility" (AAAI-15 Workshop)** — workshop paper
  without archival peer review; excluded.
