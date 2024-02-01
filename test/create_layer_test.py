import os
import pytest

from create_layer import get_layer_folder, run


def test_get_layers_folder():
    assert get_layer_folder("sklearn").endswith(os.path.join("layers", "sklearn"))
    assert os.path.exists(get_layer_folder("sklearn"))


def test_create_layer():
    run(["-l", "sklearn"])


@pytest.mark.parametrize("bucket", ["test-bucket"])
@pytest.mark.skip
def test_full_flow(bucket: str):
    run(["-l", "sklearn", "-p", "true", "-b", bucket])