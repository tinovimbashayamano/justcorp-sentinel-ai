from unittest.mock import Mock

import pytest

from backend.app.services import model_registry


@pytest.fixture(autouse=True)
def clear_registry_cache():
    model_registry.clear_model_registry_cache()
    yield
    model_registry.clear_model_registry_cache()


def create_valid_pipeline_mock():
    model = Mock()
    model.named_steps = {
        "preprocessor": Mock(),
        "classifier": Mock(),
    }
    model.predict_proba = Mock()
    model.feature_names_in_ = [
        "TransactionAmt",
        "ProductCD",
    ]
    return model


def test_resolve_model_path_returns_absolute_path():
    model_path = model_registry.resolve_model_path(
        "ml/model_artifacts/test.joblib"
    )

    assert model_path.is_absolute()
    assert model_path.name == "test.joblib"


def test_validate_model_pipeline_accepts_valid_pipeline():
    model = create_valid_pipeline_mock()

    model_registry.validate_model_pipeline(model)


def test_validate_model_pipeline_rejects_missing_named_steps():
    model = Mock(spec=[])

    with pytest.raises(
        model_registry.ModelRegistryError,
        match="named_steps",
    ):
        model_registry.validate_model_pipeline(model)


def test_validate_model_pipeline_rejects_missing_classifier():
    model = Mock()
    model.named_steps = {
        "preprocessor": Mock(),
    }
    model.predict_proba = Mock()

    with pytest.raises(
        model_registry.ModelRegistryError,
        match="classifier",
    ):
        model_registry.validate_model_pipeline(model)


def test_get_fraud_model_loads_model_once(
    monkeypatch,
    tmp_path,
):
    model_file = tmp_path / "fraud_model.joblib"
    model_file.write_bytes(b"test")

    model = create_valid_pipeline_mock()
    joblib_load = Mock(return_value=model)

    monkeypatch.setattr(
        model_registry,
        "resolve_model_path",
        lambda configured_path=None: model_file,
    )
    monkeypatch.setattr(
        model_registry.joblib,
        "load",
        joblib_load,
    )

    first_model = model_registry.get_fraud_model()
    second_model = model_registry.get_fraud_model()

    assert first_model is model
    assert second_model is model
    assert first_model is second_model
    joblib_load.assert_called_once_with(model_file)


def test_get_fraud_model_raises_when_artifact_missing(
    monkeypatch,
    tmp_path,
):
    missing_file = tmp_path / "missing.joblib"

    monkeypatch.setattr(
        model_registry,
        "resolve_model_path",
        lambda configured_path=None: missing_file,
    )

    with pytest.raises(
        model_registry.ModelRegistryError,
        match="artifact not found",
    ):
        model_registry.get_fraud_model()


def test_get_model_input_features_uses_pipeline_metadata(
    monkeypatch,
):
    model = create_valid_pipeline_mock()

    monkeypatch.setattr(
        model_registry,
        "get_fraud_model",
        lambda: model,
    )

    result = model_registry.get_model_input_features()

    assert result == [
        "TransactionAmt",
        "ProductCD",
    ]


def test_registry_returns_pipeline_components(
    monkeypatch,
):
    preprocessor = Mock()
    classifier = Mock()

    model = Mock()
    model.named_steps = {
        "preprocessor": preprocessor,
        "classifier": classifier,
    }

    monkeypatch.setattr(
        model_registry,
        "get_fraud_model",
        lambda: model,
    )

    assert (
        model_registry.get_fraud_preprocessor()
        is preprocessor
    )
    assert (
        model_registry.get_fraud_classifier()
        is classifier
    )
