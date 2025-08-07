# List of Commmands and Other Notes

## Installation

```
curl -LO https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.116.0/otelcol-contrib_0.116.0_darwin_amd64.tar.gz

mkdir otelcol-contrib
tar -xvzf otelcol-contrib_0.116.0_darwin_amd64.tar.gz -C otelcol-contrib

```

## Running

```
./otelcol-contrib --config ./config.yaml
```

## Python Stream Test

```
pip install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-api gql

```

```
python3 test.py
```


```
lsof -i :4317
```