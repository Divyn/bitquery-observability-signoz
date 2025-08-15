# Bitquery Price Feed APIs with Monitor

## List of Commands

### OpenTelemetry Installation

```
curl -LO https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.116.0/otelcol-contrib_0.116.0_darwin_amd64.tar.gz

mkdir otelcol-contrib
tar -xvzf otelcol-contrib_0.116.0_darwin_amd64.tar.gz -C otelcol-contrib

```

### Running The OTel Monitor

```
./otelcol-contrib --config ./config.yaml
```

### Python Stream Test

```
python3 sub_test.py
```

### End OTel Process if Running Post Monitoring
```
lsof -i :4317
kill -9 PID
```
