
find /tmp/layer/python/ -type f -name "*.so" | xargs -r
rm -rf /tmp/layer/python/sklearn/datasets
find /tmp/layer/python/ -path "**/*.dist-info/*" -delete
find /tmp/layer/python/ -name "*fortran*.so" -delete
find /tmp/layer/python/ -name "*.pyc" -delete
find /tmp/layer/python/ -name "*.dat" -delete
find /tmp/layer/python/ -path "**/__pycache__/*" -delete
find /tmp/layer/python/ -path "**/tests/*" -delete
find /tmp/layer/python/ -path "**/tests/*" -delete
find /tmp/layer/python/ -path "**/test/*" -delete

find /tmp/layer/python/ -path "**/examples/*" -delete
find /tmp/layer/python/ -path "**/docs/*" -delete
find /tmp/layer/python/ -path "**/doc/*" -delete
