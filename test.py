import asyncio
import time
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
import config
import signal

# Set up OpenTelemetry
exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True) #It pushes metrics to local collector at localhost:4317
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)
meter = metrics.get_meter("bitquery.stream.client")

# Define metrics
message_count = meter.create_counter("bitquery.messages", description="Messages received from Bitquery stream")
error_count = meter.create_counter("bitquery.errors", description="Errors in Bitquery stream subscription")
connection_count = meter.create_counter("bitquery.connections", description="Successful connections to Bitquery stream")
# last_message_time = meter.create_observable_gauge(
#     name="bitquery.last_message_unix",
#     callbacks=[],
#     description="Last received message timestamp (epoch seconds)"
# )

# Internal tracker for last message time
_last_msg_time = time.time()

shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    print(" Ctrl+C received. Shutting down...")
    shutdown_event.set()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)
# Define the subscription query
query = gql("""
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
        Name
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


async def main():
    global _last_msg_time

    while not shutdown_event.is_set():
        transport = WebsocketsTransport(
            url="wss://streaming.bitquery.io/eap?token=" + config.BITQUERY_TOKEN,
            headers={"Sec-WebSocket-Protocol": "graphql-ws"}
        )

        try:
            await transport.connect()
            print(" Connected to Bitquery stream")
            connection_count.add(1)

            async def subscribe_and_print():
                global _last_msg_time
                try:
                    async for result in transport.subscribe(query):
                        message_count.add(1)
                        _last_msg_time = time.time()
                        if shutdown_event.is_set():
                            break
                except Exception as e:
                    print(" Subscription error:", e)
                    error_count.add(1)

            # def update_last_msg_time(observer):
            #     observer.observe(_last_msg_time)

            # last_message_time._callbacks.append(update_last_msg_time)

            await subscribe_and_print()

        except Exception as e:
            print(" Connection error:", e)
            error_count.add(1)
        finally:
            await transport.close()
            print(" Transport closed")
            await asyncio.sleep(3)  # Backoff before reconnect



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
