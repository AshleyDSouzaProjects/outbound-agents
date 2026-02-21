# 7 AI Agents for B2B Outbound Sales

Turn a company spreadsheet into personalized multi-channel outbound sequences — automatically.

Drop in a list of company names (that's it — just names), run one command, and get back enriched data, scored leads, prospect profiles, personalized opening lines, and full 7-touch sequences ready to load into your outreach tool.

---

## Quick Start

### 1. Clone this repo
```bash
git clone https://github.com/YOUR_USERNAME/brisbane-agents.git
cd brisbane-agents
```

### 2. Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```

### 3. (Optional) Configure your ICP
Edit `input/icp-config.csv` with your product info, target industries, company size range, value props, and case studies. This makes the hook writer and sequence builder write copy specific to what you sell.

Skip this step to run in generic mode — you can always add it later.

### 4. Add your company data
Drop your CSV into `input/`. The minimum requirement is a column with company names:

```csv
company_name
Acme Corp
Globex Industries
```

The Signal Scraper will auto-enrich missing data via web search. If you already have enriched data, include all 8 columns and the enrichment step is skipped.

### 5. Run the pipeline
```bash
claude
/outbound-pipeline input/my-companies.csv
```

If enrichment was needed, you'll get a chance to review the researched data before the pipeline continues. Output files appear in `output/`.

---

## The 7 Agents

| Agent | What It Does | Value |
|-------|-------------|-------|
| **Signal Scraper** | Auto-enriches sparse CSVs via web search, then extracts buying signals | Just paste company names — it handles the rest |
| **Lead Prioritizer** | Scores leads 1-100 and assigns tiers | Work the right accounts first — TIER_1 today, TIER_2 this week |
| **Prospect Profiler** | Builds a full prospect picture | 60-second read before you ever reach out |
| **Hook Writer** | Crafts personalized opening lines | Max 120 characters, confidence-scored, bad lines flagged for review |
| **Sequence Builder** | Writes 7-touch, 21-day sequences | Multi-channel cadences with a unique angle at every step |
| **Reply Classifier** | Reads responses and classifies intent | 7 categories (interested → auto-reply) with suggested next actions |
| **Meeting Prep** | Generates pre-call briefs | Under 500 words with time-blocked agendas and tailored discovery questions |

---

## Pipeline Flow

```
Your CSV (even just company names)
  │
  ▼
┌──────────────────────┐
│   Signal Scraper     │  Auto-enriches via web search (if needed)
│  → 0-enriched.csv    │  then detects buying signals
│  → 1-signals.csv     │  (one row per signal)
└────────┬─────────────┘
         ▼
   ┌─── Review ───┐     ← You review enriched data before continuing
   └──────┬───────┘
          ▼
┌──────────────────────┐
│   Lead Prioritizer   │  Scores 1-100, assigns tiers
│  → 2-prioritized.csv │  (one row per company)
└────────┬─────────────┘
         ▼
┌──────────────────────┐
│  Prospect Profiler   │  Builds 60-sec profiles
│  → 3-profiles.csv    │  (one row per company)
└────────┬─────────────┘
         ▼
┌──────────────────────┐
│     Hook Writer      │  120-char opening lines
│  → 4-hooks.csv       │  (one row per company)
└────────┬─────────────┘
         ▼
┌──────────────────────┐
│  Sequence Builder    │  7-touch, 21-day cadences
│  → 5-sequences.csv   │  (7 rows per company)
└──────────────────────┘
```

**Reply Classifier** and **Meeting Prep** run independently — use them anytime.

---

## ICP Configuration

Edit `input/icp-config.csv` to customize the pipeline for your product:

| Field | What It Controls |
|-------|-----------------|
| `product_name` | Used in sequence sign-offs |
| `product_description` | Helps lead prioritizer score tech stack alignment |
| `target_industries` | Industries scored higher in lead prioritization |
| `target_company_size_min/max` | Replaces the default 50-500 employee sweet spot |
| `key_value_props` | Hook writer and sequence builder reference these |
| `common_objections` | Sequence builder pre-handles these in later steps |
| `case_studies` | Used as social proof in email sequences |
| `sender_name/title/company` | Email sign-offs in sequences |

Without this file, agents run in generic mode — still functional, just not product-specific.

---

## Input Columns

The only required column is `company_name`. Everything else is optional — the Signal Scraper will research missing data automatically.

| Column | Required? | Description |
|--------|-----------|-------------|
| `company_name` | Yes | Company name |
| `industry` | No | Industry or vertical |
| `employee_count` | No | Number of employees |
| `job_postings` | No | Current open roles |
| `recent_news` | No | Press, announcements, events |
| `tech_stack` | No | Technologies in use |
| `funding_info` | No | Funding rounds and amounts |
| `linkedin_activity` | No | Recent LinkedIn activity |

---

## Output Files

| File | Contents | Rows |
|------|----------|------|
| `output/0-enriched.csv` | Auto-researched company data (only if enrichment was needed) | One per company |
| `output/1-signals.csv` | Buying signals with type, strength, and recommended angle | Multiple per company |
| `output/2-prioritized.csv` | Scored leads with priority tiers and reasoning | One per company |
| `output/3-profiles.csv` | Prospect profiles with talking points and pain points | One per company |
| `output/4-hooks.csv` | Opening lines with confidence scores | One per company |
| `output/5-sequences.csv` | Full 7-step sequences with subjects, bodies, and notes | 7 per company |

---

## Exporting to Outreach Tools

### Instantly
1. Open Instantly → Campaigns → Create Campaign
2. Import `output/5-sequences.csv` as your sequence steps
3. Map columns: `body` → Email Body, `subject` → Subject Line
4. Filter by `channel` = "Email" (steps 1, 3, 5, 6) for email-only sequences
5. LinkedIn steps (2, 4, 7) are manual — use them as task reminders

### Apollo
1. Go to Sequences → Create Sequence
2. Import the CSV — Apollo accepts CSV uploads for sequence steps
3. Map: `subject` → Subject, `body` → Body, `day` → Send Day
4. Create separate steps for Email and LinkedIn touchpoints
5. Set step delays based on the `day` column

### Outreach.io
1. Sequences → Create → Import from CSV
2. Map `step_number` to Step Order, `channel` to Step Type, `day` to Day
3. Email steps import directly; LinkedIn steps become manual tasks

### Other tools (Salesloft, Lemlist, Woodpecker)
The CSV format is standard — most tools accept CSV imports with subject/body/day columns. Filter `channel` = "Email" if the tool is email-only.

---

## Running Individual Agents

You don't have to run the full pipeline. Ask Claude to run any agent directly:

```
"Run the signal scraper on input/my-companies.csv"
"Score and prioritize the leads in output/1-signals.csv"
"Classify the replies in input/sample-replies.csv"
"Prep me for the meetings in input/sample-meetings.csv"
```

Claude picks the right agent automatically.

---

## Sample Data

**Pipeline input:** `input/sample-companies.csv` — 5 companies with full data

**Standalone agent inputs:**
- `input/sample-replies.csv` — 5 reply examples for the Reply Classifier
- `input/sample-meetings.csv` — 2 meeting examples for Meeting Prep

**Example output:** The `examples/` directory contains complete pipeline output from a 4-company test run so you can see what each stage produces before running it yourself.

---

## Customization

These agents work out of the box, but you can adapt them:

- **Your product context** — edit `input/icp-config.csv` to make all output specific to what you sell
- **ICP scoring** — edit `.claude/agents/lead-prioritizer.md` to change scoring weights
- **Sequence cadence** — edit `.claude/agents/sequence-builder.md` to adjust the 21-day / 7-touch structure
- **Opening line style** — edit `.claude/agents/hook-writer.md` to add or remove banned phrases
- **Reply categories** — edit `.claude/agents/reply-classifier.md` to add custom categories for your workflow

Each agent is a single `.md` file — easy to read, easy to change.

---

Built with [Claude Code](https://claude.ai/code)
