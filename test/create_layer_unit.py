import pytest
from create_layer import _get_platform, _format_size

def test_get_platform():
    assert _get_platform("arm64") == "manylinux2014_aarch64"
    assert _get_platform("x86_64") == "manylinux2014_x86_64"
    with pytest.raises(ValueError, match="Unknown architecture: unknown"):
        _get_platform("unknown")

def test_format_size():
    assert _format_size(500) == "500.00 B"
    assert _format_size(1024) == "1.00 KiB"
    assert _format_size(1048576) == "1.00 MiB"
    assert _format_size(1073741824) == "1.00 GiB"
    assert _format_size(1099511627776) == "1.00 TiB"
    assert _format_size(1125899906842624) == "1.00 PiB"