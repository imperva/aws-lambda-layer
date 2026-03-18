find /tmp/layer/python/ -path "**/*.dist-info/*" -delete
find /tmp/layer/python/ -name "*.pyc" -delete
find /tmp/layer/python/ -path "**/__pycache__/*" -delete
find /tmp/layer/python/ -path "**/tests/*" -delete
find /tmp/layer/python/ -path "**/test/*" -delete
find /tmp/layer/python/ -path "**/*.so.debug" -delete
find /tmp/layer/python/ -name "*.c" -delete
find /tmp/layer/python/ -name "*.h" -delete
# Remove pandas I/O modules not needed for basic dataframe operations
rm -rf /tmp/layer/python/pandas/io/sas
rm -rf /tmp/layer/python/pandas/io/excel
rm -rf /tmp/layer/python/pandas/io/formats
rm -rf /tmp/layer/python/pandas/io/json/table_schema.py
# Remove test data and examples
find /tmp/layer/python/pandas -name "data" -type d -exec rm -rf {} + 2>/dev/null || true