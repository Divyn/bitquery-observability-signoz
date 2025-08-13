import asyncio
import time
from gql import gql
from gql.transport.websockets import WebsocketsTransport
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
import config
import signal

# --- OpenTelemetry setup ---
exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)  # pushes metrics to local collector
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("bitquery.stream.client")

# Instruments (we'll add network attributes on each add)
message_count = meter.create_counter("bitquery.messages", description="Messages received from Bitquery stream")
error_count = meter.create_counter("bitquery.errors", description="Errors in Bitquery stream subscription")
connection_count = meter.create_counter("bitquery.connections", description="Successful connections to Bitquery stream")

# Separate counters for each network
solana_message_count = meter.create_counter("bitquery.solana.messages", description="Messages received from Solana stream")
solana_error_count = meter.create_counter("bitquery.solana.errors", description="Errors in Solana stream subscription")
solana_connection_count = meter.create_counter("bitquery.solana.connections", description="Successful connections to Solana stream")

bsc_message_count = meter.create_counter("bitquery.bsc.messages", description="Messages received from Binance Smart Chain stream")
bsc_error_count = meter.create_counter("bitquery.bsc.errors", description="Errors in Binance Smart Chain stream subscription")
bsc_connection_count = meter.create_counter("bitquery.bsc.connections", description="Successful connections to Binance Smart Chain stream")

# Track last message time per network (optional internal state)
_last_msg_time = {"Solana": time.time(), "Binance Smart Chain": time.time()}

shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    print(" Ctrl+C received. Shutting down...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# --- GraphQL subscriptions ---
query_solana = gql("""
subscription {
  Trading {
    Tokens(
      where: {Token: {Network: {is: "Solana"}}, Interval: {Time: {Duration: {eq: 1}}}}
    ) {
      Token {
        Address
        Id
        IsNative
        Name
        Network
        Symbol
        TokenId
      }
      Block {
        Date
        Time
        Timestamp
      }
      Interval {
        Time {
          Start
          Duration
          End
        }
      }
      Volume {
        Base
        Quote
        Usd
      }
      Price {
        IsQuotedInUsd
        Ohlc {
          Close
          High
          Low
          Open
        }
        Average {
          ExponentialMoving
          Mean
          SimpleMoving
          WeightedSimpleMoving
        }
      }
    }
  }
}
""")

query_bsc = gql("""
subscription {
  Trading {
    Tokens(
      where: {Token: {Network: {is: "Binance Smart Chain"}}, Interval: {Time: {Duration: {eq: 1}}}}
    ) {
      Token {
        Address
        Id
        IsNative
        Name
        Network
        Symbol
        TokenId
      }
      Block {
        Date
        Time
        Timestamp
      }
      Interval {
        Time {
          Start
          Duration
          End
        }
      }
      Volume {
        Base
        Quote
        Usd
      }
      Price {
        IsQuotedInUsd
        Ohlc {
          Close
          High
          Low
          Open
        }
        Average {
          ExponentialMoving
          Mean
          SimpleMoving
          WeightedSimpleMoving
        }
      }
    }
  }
}
""")

async def run_stream(network_name: str, query):
    """
    Maintain a dedicated websocket transport for a network,
    auto-reconnect with backoff, and tag metrics with network.
    """
    attrs = {"network": network_name}
    
    # Select appropriate counters based on network
    if network_name == "Solana":
        network_message_count = solana_message_count
        network_error_count = solana_error_count
        network_connection_count = solana_connection_count
    elif network_name == "Binance Smart Chain":
        network_message_count = bsc_message_count
        network_error_count = bsc_error_count
        network_connection_count = bsc_connection_count
    else:
        # Fallback to generic counters with attributes
        network_message_count = message_count
        network_error_count = error_count
        network_connection_count = connection_count

    while not shutdown_event.is_set():
        transport = WebsocketsTransport(
            url=f"wss://streaming.bitquery.io/eap?token={config.BITQUERY_TOKEN}",
            headers={"Sec-WebSocket-Protocol": "graphql-ws"}
        )

        try:
            await transport.connect()
            print(f" Connected to Bitquery stream ({network_name})")
            network_connection_count.add(1)
            # Also increment the generic counter for backward compatibility
            connection_count.add(1, attributes=attrs)

            try:
                async for result in transport.subscribe(query):
                    _last_msg_time[network_name] = time.time()

                    # result may be dict-like; handle safely
                    data = getattr(result, "data", result) or {}
                    entries = (
                        data.get("Trading", {}).get("Tokens", [])
                        if isinstance(data, dict) else []
                    )
                    network_message_count.add(len(entries))
                    # Also increment the generic counter for backward compatibility
                    message_count.add(len(entries), attributes=attrs)

                    if shutdown_event.is_set():
                        break

            except Exception as e:
                print(f" Subscription error ({network_name}):", e)
                network_error_count.add(1)
                # Also increment the generic counter for backward compatibility
                error_count.add(1, attributes=attrs)

        except Exception as e:
            print(f" Connection error ({network_name}):", e)
            network_error_count.add(1)
            # Also increment the generic counter for backward compatibility
            error_count.add(1, attributes=attrs)
        finally:
            try:
                await transport.close()
            except Exception:
                pass
            print(f" Transport closed ({network_name})")
            # small backoff before reconnect if not shutting down
            if not shutdown_event.is_set():
                await asyncio.sleep(3)

async def main():
    # Run both subscriptions concurrently
    await asyncio.gather(
        run_stream("Solana", query_solana),
        run_stream("Binance Smart Chain", query_bsc),
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
