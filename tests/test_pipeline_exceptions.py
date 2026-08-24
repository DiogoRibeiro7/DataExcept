from dataexcept.pipeline_exceptions import (
    ExternalServiceError,
    FeatureEngineeringError,
    PipelineNotificationError,
    PreprocessingError,
    RetryLimitExceededError,
    ServiceAuthenticationError,
    StorageError,
)


def test_preprocessing_error_message():
    err = PreprocessingError("clean", details="bad csv")
    assert "clean" in str(err)
    assert "bad csv" in str(err)


def test_feature_engineering_error_inherits():
    err = FeatureEngineeringError("age", reason="missing")
    assert isinstance(err, PreprocessingError)
    assert "age" in str(err)


def test_storage_error_default_message():
    err = StorageError("/tmp/data", "write")
    assert str(err) == "Storage write failed at location: '/tmp/data'."


def test_notification_error_payload():
    err = PipelineNotificationError("email", {"to": "a@b"})
    assert err.payload == {"to": "a@b"}
    assert "email" in str(err)


def test_retry_limit_exceeded_error():
    err = RetryLimitExceededError("op", 3)
    assert "3" in str(err)


def test_external_service_error_subclass():
    err = ServiceAuthenticationError("svc")
    assert isinstance(err, ExternalServiceError)
    assert "Authentication" in str(err)
