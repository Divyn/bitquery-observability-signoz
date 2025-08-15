# Bitquery Price Feed APIs with Monitor

A real-time cryptocurrency price feed monitoring system using Bitquery GraphQL subscriptions and OpenTelemetry for metrics collection and monitoring.

A detailed breakdown of how this works is described in this [tutorial](https://divyn.github.io/docs/Personal_Blog/Web3/blockchain-data-observability-opentelemetry)

## Prerequisites

- **Python 3.7+** (Python 3.8+ recommended)
- **macOS/Linux** (tested on macOS 24.6.0)
- **Bitquery API Token** - Get your token from [Bitquery](https://bitquery.io/)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Divyn/bitquery-observability-signoz.git
cd signoz-bitquery
```

### 2. Install Python Dependencies

```bash
pip3 install gql opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc
```

### 3. Install OpenTelemetry Collector

```bash
curl -LO https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.116.0/otelcol-contrib_0.116.0_darwin_amd64.tar.gz

mkdir otelcol-contrib
tar -xvzf otelcol-contrib_0.116.0_darwin_amd64.tar.gz -C otelcol-contrib
```

## Configuration

### 1. Set Up Bitquery API Token

Edit `config.py` and replace the placeholder token with your actual Bitquery OAuth token. You can generate it [here](https://account.bitquery.io/user/api_v2/access_tokens)

```python
BITQUERY_TOKEN="your_actual_bitquery_token_here"
```

**Important**: Never commit your actual API token to version control. Consider using environment variables:

```bash
export BITQUERY_TOKEN="your_actual_bitquery_token_here"
```

### 2. OpenTelemetry Collector Configuration

The system uses a local OpenTelemetry collector running on port 4317. The collector configuration is handled automatically by the Python code.

## Usage

### 1. Start the OpenTelemetry Collector

```bash
./otelcol-contrib --config ./config.yaml
```

**Note**: If you don't have a `config.yaml` file, the collector will use default settings. The Python code is configured to send metrics to `http://localhost:4317`.

### 2. Run the Python Stream Monitor

In a new terminal:

```bash
python3 sub_test.py
```

This will:

- Connect to Bitquery's WebSocket streams for Solana and Binance Smart Chain
- Subscribe to real-time trading data
- Send metrics to the OpenTelemetry collector
- Display connection status and message counts

### 3. Monitor the System

The system will continuously:

- Stream real-time cryptocurrency trading data
- Collect metrics on message counts, errors, and connections
- Auto-reconnect on connection failures
- Tag metrics by network (Solana, Binance Smart Chain)

## Expected Output

When running successfully, you should see:

```
Connected to Bitquery stream (Solana)
Connected to Bitquery stream (Binance Smart Chain)
```

The system will continuously receive and process trading data, incrementing various metrics counters.

## Stopping the System

### End Python Process

Press `Ctrl+C` in the terminal running `sub_test.py`

### End OpenTelemetry Collector

```bash
lsof -i :4317
kill -9 PID
```

## Troubleshooting

### Common Issues

1. **Import Errors**

   - Ensure all Python dependencies are installed: `pip3 install gql opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc`

2. **Connection Refused on Port 4317**

   - Make sure the OpenTelemetry collector is running before starting the Python script
   - Check if port 4317 is available: `lsof -i :4317`

3. **Authentication Errors**

   - Verify your Bitquery OAuth token is correct in `config.py`
   - Ensure the token has the necessary permissions for streaming data

4. **WebSocket Connection Issues**
   - Check your internet connection
   - Verify the Bitquery streaming endpoint is accessible
   - Ensure your OAuth token is valid and not expired

## Support

For issues related to:

- **Bitquery API**: Contact Bitquery support
- **OpenTelemetry**: Check OpenTelemetry documentation
- **This Project**: Open an issue in the repository
