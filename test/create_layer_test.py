import pytest

from create_layer import run


def test_create_xgboost_arm_layer():
    run(["-l", "xgboost", "-r", "3.11", "-a", "arm64"])


@pytest.mark.parametrize("layer", ["xgboost"])
def test_create_layer_python3_12(layer: str):
    run(["-l", layer, "-r", "3.12"])


@pytest.mark.parametrize("bucket", ["test-bucket"])
@pytest.mark.skip
def test_publish(bucket: str):
    run(["-l", "sklearn", "-s", "true", "-p", "true", "-b", bucket])
