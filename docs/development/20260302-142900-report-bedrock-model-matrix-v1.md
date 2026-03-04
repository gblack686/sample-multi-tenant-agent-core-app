# AWS Bedrock Model Cost & Specialty Matrix (Non-Claude)

> **Constraint**: No Anthropic/Claude models in Bedrock — client requirement.
> Strands SDK + BedrockModel is the orchestration layer.

**Region**: us-east-1 | **Pricing**: On-demand serverless | **Date**: 2026-03-02

---

## Quick Reference — Best Picks for Strands Agents

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| Cost-optimized agentic | **Nova Micro** | $0.035/$0.14, tool use + streaming, fastest |
| Balanced agentic (default) | **Nova Lite** | $0.06/$0.24, tool use + streaming, good quality |
| Complex reasoning | **Nova Pro** | $0.80/$3.20, strongest Nova, full tool support |
| Best open-weight agentic | **Llama 4 Scout 17B** | $0.17/$0.66, tool use + streaming, MoE architecture |
| Coding / technical | **Devstral 2 135B** | $0.40/$2.00, code-focused Mistral variant |
| Multimodal (vision) | **Llama 3.2 90B Vision** | $2.00/$2.00, image+text, tool use |
| Maximum capability | **Nova Premier** | $2.50/$12.50, largest Nova, complex tasks |

---

## Full Model Matrix

### Amazon Nova Family

```
Model               Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
─────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
Nova Micro            $0.035       $0.14        Yes        Yes            128K      Speed, simple tasks
Nova Lite             $0.06        $0.24        Yes        Yes            300K      Balanced, multimodal
Nova Pro              $0.80        $3.20        Yes        Yes            300K      Complex reasoning
Nova Premier          $2.50       $12.50        Yes        Yes            1M        Maximum capability
```

**Notes**: All Nova models support tool use + streaming tool use — ideal for Strands agent loops.
Nova Lite/Pro accept image+video+document inputs. Nova Micro is text-only.

---

### Meta Llama 4 (MoE Architecture)

```
Model                    Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
──────────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
Llama 4 Scout 17B         $0.17        $0.66        Yes        Yes            10M       Long-context, MoE
Llama 4 Maverick 17B      $0.24        $0.97        Yes        Yes            1M        Reasoning, MoE
```

**Notes**: Both are Mixture-of-Experts (17B active / 109B total for Scout, 17B active / 400B+ for Maverick).
Full tool use + streaming support. Scout has a 10M token context window — largest on Bedrock.

---

### Meta Llama 3.x Family

```
Model                       Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
─────────────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
Llama 3.2 1B Instruct        $0.10        $0.10        No         No             128K      Ultra-light, edge
Llama 3.2 3B Instruct        $0.15        $0.15        No         No             128K      Light, edge
Llama 3.2 11B Vision         $0.35        $0.35        Yes        Yes            128K      Multimodal
Llama 3.2 90B Vision         $2.00        $2.00        Yes        Yes            128K      Multimodal, strong
Llama 3.1 8B Instruct        $0.22        $0.22        Yes        No             128K      Fast, light tasks
Llama 3.1 70B Instruct       $0.72        $0.72        Yes        No             128K      Balanced reasoning
Llama 3.1 405B Instruct      $5.32       $16.00        Yes        No             128K      Maximum Llama 3
Llama 3.3 70B Instruct       $0.72        $0.72        Yes        No             128K      Improved 3.1 70B
```

**Notes**: Llama 3.2 1B/3B do NOT support tool use — cannot be used with Strands agent loops.
Llama 3.2 11B/90B are vision models with full tool support. Llama 3.3 70B is the sweet spot for Llama 3.x.

---

### Mistral Family

```
Model                    Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
──────────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
Mistral Small 24.09       $1.00        $3.00        Yes        No             32K       Fast, European
Mistral Large 2 (24.07)  $2.00        $6.00        Yes        No             128K      Reasoning
Mistral Large (24.02)    $4.00       $12.00        Yes        No             32K       Legacy
Pixtral Large 25.02      ~$2.00       ~$6.00        Yes        No             128K      Multimodal
Devstral 2 135B           $0.40        $2.00        Yes        No             128K      Coding specialist
```

**Notes**: Mistral Large 3 and Ministral 3B/8B/14B announced Dec 2025 but pricing not yet confirmed
on Bedrock. Devstral 2 is a coding-focused model — strong candidate for technical review tasks.
No Mistral models support streaming tool use on Bedrock.

---

### DeepSeek

```
Model                Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
──────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
DeepSeek R1           $1.35        $5.40        No*        No             128K      Deep reasoning (CoT)
```

**Notes**: *DeepSeek R1 is a reasoning model that uses chain-of-thought. Tool use support on Bedrock
is limited/not confirmed. Best for complex analytical tasks, not multi-step agent loops.

---

### Cohere

```
Model                Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
──────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
Command R              $0.50        $1.50        Yes        Yes            128K      RAG, enterprise
Command R+             $2.50        $7.50        Yes        Yes            128K      RAG, complex tasks
```

**Notes**: Cohere models are strong for RAG (retrieval-augmented generation) and enterprise search.
Full tool use + streaming support.

---

### AI21

```
Model                   Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
─────────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
Jamba 1.5 Mini            $0.20        $0.40        Yes        Yes            256K      Long-context, fast
Jamba 1.5 Large           $2.00        $8.00        Yes        Yes            256K      Long-context, strong
Jamba-Instruct (v1)       $0.50        $0.70        No         No             256K      Legacy, no tools
```

**Notes**: Jamba uses SSM+Transformer hybrid architecture — efficient on long contexts (256K native).
Jamba-Instruct v1 does NOT support tool use.

---

### Other Models

```
Model                    Input $/1M   Output $/1M   Tool Use   Stream Tools   Context   Specialty
──────────────────────── ──────────── ───────────── ────────── ────────────── ───────── ──────────────────
NVIDIA Nemotron           $0.06        $0.24        No*        No             128K      Synthetic data
Google Gemma 3 4B         $0.04        $0.08        No*        No             128K      Ultra-light
Google Gemma 3 12B        $0.10        $0.20        No*        No             128K      Light
Google Gemma 3 27B        $0.23        $0.38        No*        No             128K      Balanced
Qwen 3 32B                $0.20        $0.78        No*        No             128K      Multilingual
Writer Palmyra X4/X5      TBD          TBD          Yes        No             128K      Enterprise writing
```

**Notes**: *Tool use support not confirmed for these models on Bedrock Converse API.
Check official docs before using with Strands agents.

---

## Strands Agent Compatibility Matrix

For Strands Agents SDK, the model MUST support the Bedrock Converse API **tool use** feature.
Models without tool use cannot participate in agent loops (tool calls will fail silently or error).

### Tier 1 — Full Strands Support (Tool Use + Streaming Tool Use)

Best for multi-turn agent conversations with real-time streaming:

```
Nova Micro         $0.035/$0.14     Cheapest agentic option
Nova Lite          $0.06/$0.24      Best value agentic
Nova Pro           $0.80/$3.20      Complex agentic reasoning
Nova Premier       $2.50/$12.50     Maximum capability
Llama 4 Scout      $0.17/$0.66      Best open-weight agentic
Llama 4 Maverick   $0.24/$0.97      Strong open-weight agentic
Llama 3.2 11B      $0.35/$0.35      Multimodal agentic
Llama 3.2 90B      $2.00/$2.00      Strong multimodal agentic
Cohere Command R   $0.50/$1.50      RAG-focused agentic
Cohere Command R+  $2.50/$7.50      Strong RAG agentic
Jamba 1.5 Mini     $0.20/$0.40      Long-context agentic
Jamba 1.5 Large    $2.00/$8.00      Long-context strong agentic
```

### Tier 2 — Partial Strands Support (Tool Use, No Streaming)

Works with Strands but no streaming during tool loops:

```
Llama 3.1 8B       $0.22/$0.22      Fast, light tasks
Llama 3.1 70B      $0.72/$0.72      Balanced reasoning
Llama 3.3 70B      $0.72/$0.72      Improved Llama 3.1
Llama 3.1 405B     $5.32/$16.00     Maximum Llama 3
Mistral Small      $1.00/$3.00      European, multilingual
Mistral Large 2    $2.00/$6.00      Strong reasoning
Devstral 2         $0.40/$2.00      Code specialist
Pixtral Large      ~$2.00/~$6.00    Multimodal
Writer Palmyra     TBD/TBD          Enterprise writing
```

### Tier 3 — No Tool Use (Cannot Use with Strands Agents)

```
Llama 3.2 1B       $0.10/$0.10      No tool use
Llama 3.2 3B       $0.15/$0.15      No tool use
DeepSeek R1        $1.35/$5.40      Reasoning only, no tools
Jamba-Instruct v1  $0.50/$0.70      Legacy, no tools
NVIDIA Nemotron    $0.06/$0.24      No confirmed tool use
Google Gemma 3     $0.04-$0.23      No confirmed tool use
Qwen 3 32B         $0.20/$0.78      No confirmed tool use
```

---

## Cost Comparison — Blended Rate

Assumes 3:1 input:output ratio (typical for agentic conversations).
Blended = (3 * input + 1 * output) / 4 per 1M tokens.

```
Rank  Model                 Blended $/1M   Tool Use
────  ────────────────────  ─────────────  ──────────
 1    Nova Micro              $0.061        Full
 2    Nova Lite               $0.105        Full
 3    Llama 4 Scout 17B       $0.293        Full
 4    Jamba 1.5 Mini          $0.250        Full
 5    Llama 3.1 8B            $0.220        Partial
 6    Llama 4 Maverick 17B    $0.423        Full
 7    Devstral 2 135B         $0.800        Partial
 8    Llama 3.3 70B           $0.720        Partial
 9    Cohere Command R        $0.750        Full
10    Nova Pro                $1.400        Full
11    Mistral Small           $1.500        Partial
12    Llama 3.2 90B Vision    $2.000        Full
13    Mistral Large 2         $3.000        Partial
14    Cohere Command R+       $3.750        Full
15    Nova Premier            $5.000        Full
16    Jamba 1.5 Large         $3.500        Full
17    Llama 3.1 405B          $7.990        Partial
```

---

## EAGLE POC Recommendation

For the Strands POC (`spike/strands-poc`), replace the prohibited Claude Haiku model:

| Option | Model ID | Cost | Rationale |
|--------|----------|------|-----------|
| **A (Recommended)** | `us.amazon.nova-lite-v1:0` | $0.06/$0.24 | Cheapest model with quality comparable to Haiku. Full tool support. |
| B | `us.amazon.nova-micro-v1:0` | $0.035/$0.14 | Cheapest overall but text-only, less nuanced. |
| C | `us.meta.llama4-scout-17b-instruct-v1:0` | $0.17/$0.66 | Best open-weight option. MoE architecture. |
| D | `us.amazon.nova-pro-v1:0` | $0.80/$3.20 | For complex multi-step reasoning tasks. |

**For eval tests**: Nova Lite is the closest quality match to Claude Haiku at similar price point.
The 5-indicator keyword check in Test 21 should pass with any Tier 1 model.

---

## Sources

- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Amazon Nova Pricing](https://aws.amazon.com/nova/pricing/)
- [Bedrock Converse API — Supported Features](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference-supported-models-features.html)
- [Amazon Bedrock Pricing Explained — Caylent](https://caylent.com/blog/amazon-bedrock-pricing-explained)
- [Bifrost LLM Cost Calculator](https://www.getmaxim.ai/bifrost/llm-cost-calculator)
- [pricepertoken.com Bedrock Endpoints](https://pricepertoken.com/endpoints/bedrock)
- [nOps — Bedrock Llama Pricing](https://www.nops.io/blog/now-supporting-bedrock-llama/)
- [Llama 4 on Amazon Bedrock — AWS Blog](https://aws.amazon.com/blogs/aws/llama-4-models-from-meta-now-available-in-amazon-bedrock-serverless/)
- [Mistral Large 3 on Bedrock — AWS What's New](https://aws.amazon.com/about-aws/whats-new/2025/12/mistral-large-3-ministral-3-family-available-amazon-bedrock/)
