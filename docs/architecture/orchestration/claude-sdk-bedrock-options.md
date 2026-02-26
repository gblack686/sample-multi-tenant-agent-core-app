# Claude SDK + Bedrock: Model Options

## Can we use non-Claude models (e.g. Gemini) via the Anthropic SDK on Bedrock?

**No.** Two constraints prevent this:

### 1. Anthropic SDK is Claude-only
Even when pointed at Bedrock as a backend, the SDK uses Bedrock's `InvokeModel` API scoped to Anthropic's Claude model IDs. It does not support calling other providers' models.

### 2. Gemini is not on Bedrock
Google's proprietary Gemini models are not available as Bedrock foundation models. Bedrock does host Google's **open-weight Gemma** models, but not Gemini.

## Models available on Bedrock (as of Feb 2026)

~100 serverless models from:
- **Anthropic** — Claude Opus, Sonnet, Haiku
- **Meta** — Llama
- **Mistral** — Mistral Large 3, Ministral 3
- **Cohere** — Command R/R+
- **AI21 Labs** — Jamba
- **Stability AI** — Stable Diffusion
- **Amazon** — Titan, Nova
- **Google** — Gemma (open-weight only, not Gemini)
- **OpenAI** — added late 2025

## Using non-Claude models on Bedrock

Use the AWS SDK directly instead of the Anthropic SDK:
- `boto3` (Python) or `@aws-sdk/client-bedrock-runtime` (JS/TS)
- **Bedrock Converse API** provides a unified interface across all Bedrock-hosted models

## Sources

- [Supported foundation models in Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- [Amazon Bedrock adds 18 fully managed open weight models](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-bedrock-fully-managed-open-weight-models/)
- [Gemini to AWS Bedrock Model Recommendations](https://www.nops.io/blog/gemini-to-aws-bedrock-recommendations/)
- [Claude by Anthropic - Models in Amazon Bedrock](https://aws.amazon.com/bedrock/anthropic/)
