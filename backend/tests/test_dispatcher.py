from app.ai.dispatcher import AgentDispatcher, LogicalRole


def test_logical_roles_enumerated():
    expected = {
        "classifier", "summarizer", "extractor",
        "generator", "judge", "validator", "transcriber",
    }
    actual = {role.value for role in LogicalRole}
    assert actual == expected


def test_dispatcher_resolves_role_to_provider_and_model():
    dispatcher = AgentDispatcher()
    provider, model = dispatcher.resolve(LogicalRole.EXTRACTOR)
    assert provider is not None
    assert model is not None


def test_dispatcher_uses_haiku_for_classifier():
    dispatcher = AgentDispatcher()
    _, model = dispatcher.resolve(LogicalRole.CLASSIFIER)
    assert "haiku" in model.lower()


def test_dispatcher_uses_sonnet_for_extractor():
    dispatcher = AgentDispatcher()
    _, model = dispatcher.resolve(LogicalRole.EXTRACTOR)
    assert "sonnet" in model.lower()
