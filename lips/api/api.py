import requests
import math
from collections import defaultdict

# ── Endpoints ────────────────────────────────────────────────────────────────

OPENAI_URL           = "https://api.openai.com/v1/chat/completions"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
ANTHROPIC_URL        = "https://api.anthropic.com/v1/messages"
GEMINI_URL           = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
TOGETHER_URL         = "https://api.together.xyz/v1/chat/completions"
MISTRAL_URL          = "https://api.mistral.ai/v1/chat/completions"
DEEPSEEK_URL         = "https://api.deepseek.com/chat/completions"
GROQ_URL             = "https://api.groq.com/openai/v1/chat/completions"
CEREBRAS_URL         = "https://api.cerebras.ai/v1/chat/completions"
SAMBANOVA_URL        = "https://api.sambanova.ai/v1/chat/completions"
FIREWORKS_URL        = "https://api.fireworks.ai/inference/v1/chat/completions"
DEEPINFRA_URL        = "https://api.deepinfra.com/v1/openai/chat/completions"
HYPERBOLIC_URL       = "https://api.hyperbolic.xyz/v1/chat/completions"
LAMBDA_URL           = "https://api.lambda.ai/v1/chat/completions"
NOVITA_URL           = "https://api.novita.ai/v3/openai/chat/completions"
NEBIUS_URL           = "https://api.studio.nebius.com/v1/chat/completions"
FEATHERLESS_URL      = "https://api.featherless.ai/v1/chat/completions"
NSCALE_URL           = "https://inference.nscale.com/v1/chat/completions"
FRIENDLIAI_URL       = "https://inference.friendli.ai/v1/chat/completions"
OPENROUTER_URL       = "https://openrouter.ai/api/v1/chat/completions"
PERPLEXITY_URL       = "https://api.perplexity.ai/chat/completions"
XAI_URL              = "https://api.x.ai/v1/chat/completions"
COHERE_URL           = "https://api.cohere.com/v2/chat"
AI21_URL             = "https://api.ai21.com/studio/v1/chat/completions"
NVIDIA_NIM_URL       = "https://integrate.api.nvidia.com/v1/chat/completions"
HUGGINGFACE_URL      = "https://api-inference.huggingface.co/v1/chat/completions"
REPLICATE_URL        = "https://api.replicate.com/v1/models"
DATABRICKS_URL       = "https://adb-{workspace}.azuredatabricks.net/serving-endpoints/{model}/invocations"
CLOUDFLARE_URL       = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
ANYSCALE_URL         = "https://api.endpoints.anyscale.com/v1/chat/completions"
MOONSHOT_URL         = "https://api.moonshot.cn/v1/chat/completions"
MINIMAX_URL          = "https://api.minimax.chat/v1/text/chatcompletion_v2"
DASHSCOPE_URL        = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
VOLCANO_URL          = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
SCALEWAY_URL         = "https://api.scaleway.ai/v1/chat/completions"
NLP_CLOUD_URL        = "https://api.nlpcloud.io/v1/gpu/{model}/chatbot"
ALEPH_ALPHA_URL      = "https://api.aleph-alpha.com/complete"
PREDIBASE_URL        = "https://serving.app.predibase.com/v2/llm/generate"
OLLAMA_URL           = "http://localhost:11434/v1/chat/completions"
VLLM_URL             = "http://localhost:8000/v1/chat/completions"
LM_STUDIO_URL        = "http://localhost:1234/v1/chat/completions"

# ── Model sets by endpoint behaviour ─────────────────────────────────────────

ANTHROPIC_MODELS = {
    # current
    "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001",
    "claude-opus-4", "claude-sonnet-4",
    # legacy
    "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
}

RESPONSES_MODELS = {
    # GPT-5 family — /v1/responses, no temperature
    "gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.4-pro",
    "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-pro",
}

REASONING_MODELS = {
    # OpenAI o-series — no temperature, max_completion_tokens
    "o4", "o4-mini", "o4-mini-high", "o3", "o3-pro", "o3-mini",
    "o1", "o1-pro", "o1-mini",
    # DeepSeek reasoner
    "deepseek-reasoner",
}

# ── Provider → base URL ───────────────────────────────────────────────────────
# Key is the liteLLM prefix used in "prefix/model" strings.

PROVIDER_URLS = {
    "anthropic":    ANTHROPIC_URL,
    "openai":       OPENAI_URL,       # overridden per-model for /v1/responses
    "gemini":       GEMINI_URL,
    "vertex_ai":    GEMINI_URL,       # same compat layer
    "xai":          XAI_URL,
    "mistral":      MISTRAL_URL,
    "cohere":       COHERE_URL,
    "deepseek":     DEEPSEEK_URL,
    "perplexity":   PERPLEXITY_URL,
    "groq":         GROQ_URL,
    "cerebras":     CEREBRAS_URL,
    "sambanova":    SAMBANOVA_URL,
    "fireworks_ai": FIREWORKS_URL,
    "together_ai":  TOGETHER_URL,
    "deepinfra":    DEEPINFRA_URL,
    "hyperbolic":   HYPERBOLIC_URL,
    "lambda":       LAMBDA_URL,
    "novita":       NOVITA_URL,
    "nebius":       NEBIUS_URL,
    "featherless_ai": FEATHERLESS_URL,
    "nscale":       NSCALE_URL,
    "friendliai":   FRIENDLIAI_URL,
    "openrouter":   OPENROUTER_URL,
    "ai21":         AI21_URL,
    "nvidia_nim":   NVIDIA_NIM_URL,
    "huggingface":  HUGGINGFACE_URL,
    "replicate":    REPLICATE_URL,
    "databricks":   DATABRICKS_URL,
    "cloudflare":   CLOUDFLARE_URL,
    "anyscale":     ANYSCALE_URL,
    "moonshot":     MOONSHOT_URL,
    "minimax":      MINIMAX_URL,
    "dashscope":    DASHSCOPE_URL,
    "volcengine":   VOLCANO_URL,
    "scaleway":     SCALEWAY_URL,
    "nlp_cloud":    NLP_CLOUD_URL,
    "aleph_alpha":  ALEPH_ALPHA_URL,
    "predibase":    PREDIBASE_URL,
    "ollama":       OLLAMA_URL,
    "hosted_vllm":  VLLM_URL,
    "lm_studio":    LM_STUDIO_URL,
    # Azure handled separately (needs deployment name in URL)
    "azure":        OPENAI_URL,
    "azure_ai":     OPENAI_URL,
    "bedrock":      OPENAI_URL,       # placeholder — real bedrock uses boto3
    "sagemaker":    OPENAI_URL,
    "oci":          OPENAI_URL,
    "watsonx":      OPENAI_URL,
}

# ── Known short-name → actual payload model string ───────────────────────────
# Only needed where the key differs from what the API expects.
# Providers that use the model name verbatim need no entry here.

MODEL_NAME_MAP = {
    # Anthropic short keys (the frontend ships without date suffixes)
    "claude-haiku-4-5":          "claude-haiku-4-5-20251001",
    # Mistral convenience aliases
    "mistral-large":             "mistral-large-latest",
    "mistral-medium":            "mistral-medium-latest",
    "mistral-small":             "mistral-small-latest",
    # Together AI
    "llama-3.3-70b":             "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo",
    "llama-3.1-8b":              "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
}

# ── Response wrapper (liteLLM-compatible shape) ───────────────────────────────

class Message:
    def __init__(self, content, role="assistant"):
        self.content = content
        self.role    = role

class Choice:
    def __init__(self, message, finish_reason="stop", index=0):
        self.message      = message
        self.finish_reason = finish_reason
        self.index        = index

class Usage:
    def __init__(self, prompt_tokens=0, completion_tokens=0, total_tokens=0):
        self.prompt_tokens     = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens      = total_tokens

class CompletionResponse:
    """
    Mimics liteLLM ModelResponse so callers can use:
        response.choices[0].message.content
        response.usage.total_tokens
        response.model
    """
    def __init__(self, content, model, usage=None):
        self.choices = [Choice(Message(content))]
        self.model   = model
        self.usage   = usage or Usage()

    def __repr__(self):
        snippet = self.choices[0].message.content[:60]
        return f"CompletionResponse(model={self.model!r}, content={snippet!r}...)"

# ── Payload builders ──────────────────────────────────────────────────────────

def _build_anthropic_payload(model_name, messages, params):
    """Extract system message; pass the rest as {role, content} pairs.
    Skips any message whose content is empty/None — Anthropic rejects them."""
    system   = None
    filtered = []
    for m in messages:
        content = m.get("content")
        if m.get("role") == "system":
            if content:
                system = content
        else:
            if content or content == 0:   # keep numeric 0 but drop None/""
                filtered.append({"role": m["role"], "content": content})

    payload = {
        "model":      model_name,
        "max_tokens": params.get("max_tokens", 2000),
        "messages":   filtered,
    }
    if system:
        payload["system"] = system
    if "temperature" in params:
        payload["temperature"] = params["temperature"]
    return payload


def _build_responses_payload(model_name, messages, params):
    """/v1/responses: 'input' not 'messages'; no temperature support.
    Skips messages with empty/None content before joining."""
    input_text = "\n".join(
        f"{m['role'].capitalize()}: {m['content']}"
        for m in messages
        if m.get("content") or m.get("content") == 0
    )
    return {
        "model":             model_name,
        "input":             input_text,
        "max_output_tokens": params.get("max_tokens", 2000),
    }


def _build_reasoning_payload(model_name, messages, params):
    """o-series / deepseek-reasoner: no temperature, max_completion_tokens.
    Skips messages with empty/None content."""
    filtered = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m.get("content") or m.get("content") == 0
    ]
    return {
        "model":                 model_name,
        "messages":              filtered,
        "max_completion_tokens": params.get("max_tokens", 2000),
    }


def _build_standard_payload(model_name, messages, params):
    """Standard OpenAI-compatible chat/completions payload.
    Skips messages with empty/None content — Mistral and others reject them."""
    filtered = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
        if m.get("content") or m.get("content") == 0
    ]
    payload = {
        "model":      model_name,
        "messages":   filtered,
        "max_tokens": params.get("max_tokens", 2000),
    }
    if "temperature" in params:
        payload["temperature"] = params["temperature"]
    for extra in ("top_p", "stop", "presence_penalty", "frequency_penalty", "n"):
        if extra in params:
            payload[extra] = params[extra]
    return payload

# ── Response parsers ──────────────────────────────────────────────────────────

def _parse_anthropic(data):
    content = data["content"][0]["text"]
    u = data.get("usage", {})
    usage = Usage(
        prompt_tokens=u.get("input_tokens", 0),
        completion_tokens=u.get("output_tokens", 0),
        total_tokens=u.get("input_tokens", 0) + u.get("output_tokens", 0),
    )
    return content, usage


def _parse_responses(data):
    for item in data.get("output", []):
        if item.get("type") == "message":
            for block in item.get("content", []):
                if block.get("type") == "output_text":
                    u = data.get("usage", {})
                    usage = Usage(
                        prompt_tokens=u.get("input_tokens", 0),
                        completion_tokens=u.get("output_tokens", 0),
                        total_tokens=u.get("total_tokens", 0),
                    )
                    return block["text"], usage
    raise ValueError(f"No output_text found in /v1/responses payload: {data}")


def _parse_standard(data):
    content = data["choices"][0]["message"]["content"]
    u = data.get("usage", {})
    usage = Usage(
        prompt_tokens=u.get("prompt_tokens", 0),
        completion_tokens=u.get("completion_tokens", 0),
        total_tokens=u.get("total_tokens", 0),
    )
    return content, usage

# ── Header builder ────────────────────────────────────────────────────────────

def _build_headers(provider_prefix, api_key):
    headers = {"Content-Type": "application/json"}
    if provider_prefix == "anthropic":
        headers["x-api-key"]         = api_key
        headers["anthropic-version"] = "2023-06-01"
    elif provider_prefix == "openrouter":
        headers["Authorization"]  = f"Bearer {api_key}"
        headers["HTTP-Referer"]   = "https://lips.app"
        headers["X-Title"]        = "lips"
    elif provider_prefix == "friendliai":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-Friendli-Team"] = ""          # optional team ID
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers

# ── URL resolver ──────────────────────────────────────────────────────────────

def _resolve_url(provider_prefix, bare_model):
    """Return the correct endpoint URL for this provider+model combination."""
    if provider_prefix == "openai":
        if bare_model in RESPONSES_MODELS:
            return OPENAI_RESPONSES_URL
        return OPENAI_URL
    return PROVIDER_URLS.get(provider_prefix, OPENAI_URL)

# ── Main completion function ──────────────────────────────────────────────────

def completion(messages, api_key, stream=False, **generate_config):
    """
    Drop-in replacement for liteLLM's completion():

        response = completion(
            messages=messages,
            api_key=api_key,
            stream=False,
            **generate_config          # must include 'model'
        )

    Accepts liteLLM-style "provider/model" strings for every provider listed
    in the frontend PROVIDERS array, e.g.:
        "anthropic/claude-sonnet-4-6"
        "openai/gpt-5.5"
        "groq/llama-3.3-70b-versatile"
        "ollama/llama3.3"
        ...

    Returns a CompletionResponse with:
        .choices[0].message.content
        .usage.prompt_tokens / .completion_tokens / .total_tokens
        .model
    """
    if stream:
        raise NotImplementedError("stream=True is not supported in this implementation.")

    raw_model = generate_config.get("model")
    if not raw_model:
        raise ValueError("'model' must be provided in generate_config.")

    # ── Split "provider/model" ─────────────────────────────────────────────
    if "/" in raw_model:
        provider_prefix, bare_model = raw_model.split("/", 1)
    else:
        # Bare model name — infer provider from well-known prefixes
        bare_model      = raw_model
        provider_prefix = _infer_provider(bare_model)

    # ── Resolve actual model name sent in the payload ──────────────────────
    model_name = MODEL_NAME_MAP.get(bare_model, bare_model)

    # ── Routing flags ──────────────────────────────────────────────────────
    is_anthropic = provider_prefix == "anthropic"
    is_responses = (provider_prefix == "openai") and (bare_model in RESPONSES_MODELS)
    is_reasoning = (bare_model in REASONING_MODELS)

    # normalise config (drop the model key — builders receive it separately)
    params = {k: v for k, v in generate_config.items() if k != "model"}

    # ── Build payload ──────────────────────────────────────────────────────
    if is_anthropic:
        payload = _build_anthropic_payload(model_name, messages, params)
    elif is_responses:
        payload = _build_responses_payload(model_name, messages, params)
    elif is_reasoning:
        payload = _build_reasoning_payload(model_name, messages, params)
    else:
        payload = _build_standard_payload(model_name, messages, params)

    # ── Headers & URL ──────────────────────────────────────────────────────
    headers = _build_headers(provider_prefix, api_key)
    url     = _resolve_url(provider_prefix, bare_model)

    # ── Fire request ───────────────────────────────────────────────────────
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}") from e

    data = resp.json()

    # ── Parse response ─────────────────────────────────────────────────────
    if is_anthropic:
        content, usage = _parse_anthropic(data)
    elif is_responses:
        content, usage = _parse_responses(data)
    else:
        content, usage = _parse_standard(data)

    return CompletionResponse(content=content, model=raw_model, usage=usage)


def _infer_provider(bare_model: str) -> str:
    """
    Last-resort provider inference when no 'prefix/' is present.
    Checks well-known model name patterns in priority order.
    """
    m = bare_model.lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    if m.startswith("gemini"):
        return "gemini"
    if m.startswith("mistral") or m.startswith("codestral"):
        return "mistral"
    if m.startswith("deepseek"):
        return "deepseek"
    if m.startswith("grok"):
        return "xai"
    if m.startswith("command"):
        return "cohere"
    if m.startswith("llama") or m.startswith("meta-llama"):
        return "together_ai"
    if m.startswith("sonar"):
        return "perplexity"
    if m.startswith("moonshot"):
        return "moonshot"
    if m.startswith("qwen") or m.startswith("doubao"):
        return "dashscope"
    if m.startswith("jamba") or m.startswith("j2-"):
        return "ai21"
    if m.startswith("ibm/") or m.startswith("granite"):
        return "watsonx"
    # local fallbacks
    if m.startswith("phi") or m.startswith("gemma") or m.startswith("deepseek-r1"):
        return "ollama"
    return "openai"   # safe default


# ── Convenience helpers ───────────────────────────────────────────────────────

def chat(text, model="openai/gpt-5.5", api_key="", temperature=1.0, max_tokens=2000):
    """Single-turn convenience wrapper around completion()."""
    resp = completion(
        messages=[{"role": "user", "content": text}],
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def next_token_p(text, api_key=""):
    """Return a {token: probability} dict for the next token via gpt-4o-mini logprobs."""
    data = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model":        "gpt-4o-mini",
            "messages":     [{"role": "user", "content": text}],
            "max_tokens":   1,
            "logprobs":     True,
            "top_logprobs": 10,
        },
        timeout=60,
    ).json()
    entries = data["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    result  = defaultdict(float)
    for entry in entries:
        result[entry["token"]] = math.exp(entry["logprob"])
    return result