find /tmp/layer/python/ -type f -name "*.so" | xargs -r
find /tmp/layer/python/ -path "**/*.dist-info/*" -delete
find /tmp/layer/python/ -name "*.pyc" -delete
find /tmp/layer/python/ -name "*.dat" -delete
find /tmp/layer/python/ -path "**/__pycache__/*" -delete
find /tmp/layer/python/ -path "**/tests/*" -delete
find /tmp/layer/python/ -path "**/tests/*" -delete
find /tmp/layer/python/ -path "**/test/*" -delete