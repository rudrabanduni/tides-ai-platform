# Prompt to paste into ChatGPT (the conversation that has the TIDES criteria)

Copy everything inside the box below, paste it into the same ChatGPT conversation where you shared the
TIDES / LaunchIndex evaluation criteria, and send it. Then copy ChatGPT's whole answer back to Claude.

```
I need the TIDES IIT Roorkee startup evaluation rules I gave you earlier, written out exactly, so a
developer can build them into software. Do not invent anything. If something was never specified,
write "NOT SPECIFIED" instead of guessing.

Give me these sections, in this order:

1. SECTION WEIGHTAGE
   A table with: Section name | Weight (%) | Notes.
   Weights must add up to 100%. Use these six section names where they match what I gave you:
   - Problem & Solution
   - Market Opportunity
   - Founder & Team
   - Business Model & Commercialisation
   - Innovation & Impact
   - Financials & Incubation Support
   If my sections were named or grouped differently, list mine exactly and show how each maps to the six above.

2. CRITERIA INSIDE EACH SECTION
   For every section, list each criterion with: Criterion name | Weight within the section (% or points) |
   What a high score looks like | What a low score looks like.
   If criteria inside a section are equally weighted, say "equal".

3. SCORING SCALE
   The scale used per criterion (for example 0-10 or 1-5), and what each level means.

4. FINAL DECISION RULES
   The overall score thresholds for each outcome (for example: Incubate / Conditional / Defer / Reject),
   with the exact cut-off numbers.

5. MUST-HAVE / KNOCKOUT RULES
   Any rule that overrides the score (for example "no full-time founder = reject",
   "no prototype at Seed stage = conditional only"). Write NOT SPECIFIED if none.

6. STAGE OR SECTOR ADJUSTMENTS
   Whether expectations or weights change by startup stage (Idea, Prototype, MVP, Revenue...) or by sector
   (DeepTech, SaaS, CleanTech...). Give the exact rules or NOT SPECIFIED.

7. MISSING INFORMATION RULE
   How a criterion should be scored when the applicant did not provide the information
   (for example: score 0, exclude from the average, or flag for follow-up without penalty).

8. ANYTHING ELSE
   Any other rule, red flag, or priority I told you about that affects the final result.

Format the answer as clear tables and short bullet points. No essays.
```

## What happens next
Claude encodes these rules as the official scoring standard (versioned, shown in every report), so every
evaluation computes the weighted final score and recommendation from your rules instead of equal weights.
