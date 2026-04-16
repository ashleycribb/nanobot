from nanobot.providers.registry import find_by_model

def test_find_by_model_basic():
    """Test basic keyword matching."""
    spec = find_by_model("claude-3-opus")
    assert spec is not None
    assert spec.name == "anthropic"

def test_find_by_model_case_insensitive():
    """Test case-insensitive matching."""
    spec = find_by_model("GPT-4")
    assert spec is not None
    assert spec.name == "openai"

def test_find_by_model_substring():
    """Test matching by keyword as substring."""
    spec = find_by_model("deepseek-chat")
    assert spec is not None
    assert spec.name == "deepseek"

def test_find_by_model_no_match():
    """Test when no provider matches the model name."""
    spec = find_by_model("unknown-llm-100b")
    assert spec is None

def test_find_by_model_skips_gateway():
    """Test that gateways are skipped in find_by_model."""
    # aihubmix is in PROVIDERS with keywords=("aihubmix",) but is_gateway=True
    spec = find_by_model("aihubmix-model")
    assert spec is None

def test_find_by_model_skips_local():
    """Test that local providers are skipped in find_by_model."""
    # vllm is in PROVIDERS with keywords=("vllm",) but is_local=True
    spec = find_by_model("vllm-llama-3")
    assert spec is None

def test_find_by_model_other_providers():
    """Test a few more standard providers."""
    spec = find_by_model("kimi-v1")
    assert spec is not None
    assert spec.name == "moonshot"

    spec = find_by_model("qwen-max")
    assert spec is not None
    assert spec.name == "dashscope"

    spec = find_by_model("gemini-pro")
    assert spec is not None
    assert spec.name == "gemini"
