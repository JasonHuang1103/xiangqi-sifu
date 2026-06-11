# Xiangqi-Sifu

## Vision

Build a Xiangqi platform that progresses through three layers:

```text
Engine Layer
    "What is the best move?"

↓

Explanation Layer
    "Why is the best move better?"

↓

Personalization Layer
    "Why do YOU keep making this mistake?"
```

---

# Phase 1 — Engine-Based Review MVP

**Timeline:** 1–2 weeks

## Goal

Build a reliable Xiangqi game analyzer.

No AI coach.
No natural-language explanations.

Only trusted engine analysis.

## Core Deliverable

Upload a Xiangqi game:

```text
.xqf
.xml
.pgn
.iccs
```

and obtain:

```text
Move list

Evaluation graph

Best move per position

Mistake timeline

Engine report
```

## Tasks

### Data

- [ ] Collect 50–500 sample games
- [ ] Build parser abstraction
- [ ] Normalize all games into a common format
- [ ] Generate FEN/state sequence

Target:

```text
Correctness > Coverage
```

### Engine

- [ ] Integrate Pikafish
- [ ] Analyze every position
- [ ] Store:
  - evaluation
  - best move
  - principal variation (PV)
  - search depth

Compute:

```text
eval_loss

classification:
    inaccuracy
    mistake
    blunder
```

### Database

Design schema:

```text
Game
Position
Move
Evaluation
Mistake
```

Store:

```text
FEN

Played move

Best move

PV

Eval

Metadata
```

### Frontend

- [ ] Upload game
- [ ] View move list
- [ ] View evaluation graph
- [ ] View mistake timeline
- [ ] Jump to critical positions

## Success Criteria

```text
User uploads game

↓

System analyzes game

↓

System identifies mistakes

↓

Results stored in database

↓

Analysis reproducible
```

---

# Side Quest / Phase 1.5 — Xiangqi-R1-Inspired LoRA Training

**Timeline:** 2–6 weeks for an MVP adapter; longer if RL refinement is added.

## Goal

Train a lightweight Xiangqi explanation adapter that converts Pikafish ground truth into short, faithful coaching explanations.

This is **not exact Xiangqi-R1 replication**. The public Xiangqi-R1 materials do not provide the official LoRA checkpoint, exact base model, or full training dataset. The objective is to build a **Xiangqi-R1-inspired adapter** tailored to Xiangqi-Sifu:

```text
Faithful explanations of why Pikafish's preferred move is better.
```

## Default Model Strategy

Start with:

```text
Qwen/Qwen3.5-2B
```

Reason:

```text
MacBook-friendly first experiment
lower training cost
faster iteration
good enough for explanation dataset validation
```

Keep Qwen/Qwen3.5-4B as the first quality upgrade if 2B is too weak. Reserve Qwen/Qwen3.5-9B for later cloud GPU training after the dataset and verifier are proven.

## Architecture

```text
WXF / PGN games
    ↓
Parser + FEN generator
    ↓
Pikafish analysis
    ↓
Training sample builder
    ↓
SFT dataset
    ↓
LoRA fine-tuning
    ↓
Evaluation benchmark
    ↓
Candidate explanation model
```

## Training Dataset

Each training example should contain:

```text
Input:
    FEN
    side to move
    played move
    Pikafish best move
    PV(best)
    PV(played)
    eval_before
    eval_after
    eval_loss
    severity

Output:
    short explanation
    why best move is better
    confidence
```

Target:

```text
50k–500k Pikafish-grounded explanation samples
```

For the first adapter, prefer conservative explanation targets:

```text
Reason: after the played move, the position shifted from
slightly better for Red to near equal, and the mover lost 180 cp.

Better move: Pikafish recommends h0g2, with PV h0g2 b9c7.

Confidence: Medium
```

Do not train the adapter to invent unsupported tactical themes. Unsupported claims should be filtered by the verifier before being used as training targets.

## Milestones

### MVP Adapter

Use supervised fine-tuning only.

Tasks:

- [x] Generate initial Pikafish-grounded explanation JSONL review slice.
- [x] Define the prompt template for explanation training.
- [x] Create a small validation set marked for human review.
- [x] Add validation benchmark tooling for format, best-move, eval-loss, and verifier checks.
- [x] Add adapter export tooling for manifest and model-card generation after training.
- [x] Sanity-review the validation set before MVP training.
- [x] Fine-tune Qwen/Qwen3.5-2B with LoRA on the 450-record MVP slice.
- [x] Evaluate MVP faithfulness with the automatic verifier and one real adapter inference check.
- [x] Export an adapter usable by the Phase 2 explanation provider.

Success target:

```text
Given engine analysis, the adapter produces short explanations
that mention the best move, eval loss, and a cautious reason.
```

### Advanced Adapter

Add optional RL/GRPO-style refinement after the supervised adapter works.

Reward signals:

```text
format validity
best-move consistency
eval consistency
PV consistency
unsupported-claim penalty
```

This step should be deferred until the MVP adapter and verifier provide enough evidence that RL refinement is worth the added complexity.

## Deliverables

```text
data/training/explanations/*.jsonl

prompt template for explanation training

LoRA training script/config

trained adapter checkpoint

evaluation benchmark

model card / training notes

inference adapter compatible with Phase 2
```

## Success Criteria

```text
Training samples generated from trusted engine analysis

↓

LoRA adapter trained on explanation targets

↓

Adapter produces readable explanation candidates

↓

Verifier rejects unsupported or inconsistent explanations

↓

Phase 2 can use the adapter as an explanation provider
```

---

# Phase 2 — Explanation Engine

**Timeline:** 2–6 weeks

## Goal

Convert engine outputs into coaching explanations.

Phase 2 assumes an explanation provider is available. That provider can be the Phase 1.5 Xiangqi-R1-inspired LoRA adapter, a general local model, or another compatible explanation backend.

## Architecture

```text
Pikafish
    ↓
Ground Truth

Xiangqi-R1-inspired adapter / explanation provider
    ↓
Explanation Candidate

Verifier
    ↓
Verified Explanation
```

## Core Deliverable

Instead of:

```text
Move 17
Eval loss: 320
```

User sees:

```text
Move 17 was a blunder.

Pikafish prefers 马八进七.

In the engine continuation,
your horse becomes vulnerable and Black
obtains a material advantage.

Confidence: Medium
```

## Tasks

### Explanation Dataset

Generate examples containing:

```text
Position

Played move

Best move

PV(best)

PV(played)

Eval delta
```

Target:

```text
50k–500k explanation samples
```

### Xiangqi-R1 Integration

Input:

```text
Position

Engine analysis

PVs
```

Output:

```text
Natural language explanation
```

### Verification Layer

Verify:

- [x] Does explanation match evaluation?
- [ ] Does explanation match PV?
- [x] Does explanation claim unsupported facts?

Classification:

```text
PASS
FAIL
UNCERTAIN
```

### Evaluation Benchmark

Create a human-rated benchmark for explanation quality.

Metrics:

```text
faithfulness

usefulness

hallucination rate

coaching quality
```

## Success Criteria

```text
Engine explanation generated

↓

Explanation consistent with engine

↓

Verified explanations can be stored and reviewed in CLI/UI reports

↓

Useful to human players
```

---

# Phase 3 — Knowledge Base + Personalized Coach

**Timeline:** 1–3 months

## Goal

Turn isolated explanations into long-term coaching.

## Core Deliverable

System answers:

```text
What mistakes do I repeatedly make?

What should I study next?

Which master games can help me?
```

## Data Expansion

Aggregate:

```text
master games

online games

tournaments
```

Target:

```text
100k–500k games

5–20 million positions
```

## Knowledge Base

For every position, store:

```text
move frequency

win rate

draw rate

loss rate

representative games

similar positions
```

### Phase 3A — Opening / Position Explorer Backend

Current MVP scope:

- [x] Normalize raw `.pgns` corpora into per-game JSONL records.
- [x] Build a SQLite knowledge-base schema for games, positions, moves, and representative examples.
- [x] Store position occurrence counts.
- [x] Store move frequency and result statistics.
- [x] Query top moves from a FEN.
- [x] Query representative games from a FEN and optional move.
- [x] Process the complete dpxq corpus into `data/processed/dpxq_99813games/games.jsonl`.
- [x] Build the full 140k-game public knowledge database.
- [ ] Add frontend/API views for opening explorer queries.

Capabilities:

- [x] Position search
- [x] Opening explorer backend
- [ ] Similar-position retrieval
- [x] Historical continuation lookup backend

## User Memory

Track:

```text
all analyzed games

mistakes

improvement history

study history
```

## Pattern Mining

Detect recurring weaknesses:

```text
missed tactics

opening weaknesses

endgame weaknesses

king safety issues

piece coordination issues
```

Rank by:

```text
frequency

severity

recent trend
```

## Recommendation Engine

Given:

```text
weakness = cannon tactics
```

Retrieve:

```text
similar mistakes

master games

training positions

flashcards
```

## Personalized Coach

Generate:

```text
weekly reports

monthly reports

training plans
```

Example:

```text
Past 30 days

52 games analyzed

Top recurring weaknesses:

1. Cannon forks
2. Rook endgames
3. King safety

Recommended study focus:

Central Cannon structures
```

## Success Criteria

```text
System identifies weaknesses

↓

Retrieves relevant examples

↓

Suggests targeted study

↓

User improves over time
```

---

# Phase 4 — Research / Publication Version

**Timeline:** 1–6 months

## Goal

Transform Xiangqi-Sifu from a coaching tool into a research platform.

## Research Questions

- [ ] Can engine-grounded LLMs explain Xiangqi decisions?
- [ ] Can explanation faithfulness be measured automatically?
- [ ] Can coaching be personalized through memory?
- [ ] Can retrieval improve explanation quality?
- [ ] Can player improvement be predicted?

## Potential Paper Topics

### Xiangqi-Sifu

```text
Engine-Grounded Personalized Coaching for Xiangqi
```

### Explanation Benchmark

```text
Evaluating Faithfulness of LLM Explanations
for Engine-Based Board Game Analysis
```

### Memory-Augmented Coaching

```text
Memory-Augmented Personalized Training
for Xiangqi Players
```

## Long-Term Architecture

```text
                +----------------+
                |   Pikafish     |
                | Ground Truth   |
                +--------+-------+
                         |
                         v
                +----------------+
                |  Xiangqi-R1    |
                | Explanation    |
                +--------+-------+
                         |
                         v
                +----------------+
                |    Verifier    |
                | Faithfulness   |
                +--------+-------+
                         |
                         v
                +----------------+
                | Knowledge Base |
                +--------+-------+
                         |
                         v
                +----------------+
                | User Memory    |
                +--------+-------+
                         |
                         v
                +----------------+
                | Personalized   |
                | Coach          |
                +----------------+
```

## End Vision

```text
Phase 1:
    What is the best move?

Phase 2:
    Why is the best move better?

Phase 3:
    Why do I keep making this mistake?

Phase 4:
    Can we model and accelerate player improvement?
```
