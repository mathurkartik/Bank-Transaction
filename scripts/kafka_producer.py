import json
import time
import random
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_mock_transaction():
    """Generates a realistic synthetic banking transaction event."""
    branches = [f"BR_{i:03d}" for i in range(1, 51)]
    txn_types = ["DEPOSIT", "WITHDRAWAL", "PAYMENT", "TRANSFER", "PURCHASE"]

    return {
        "transaction_id": f"TXN_STREAM_{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"KAGGLE_C{random.randint(100000, 999999)}",
        "branch_id": random.choice(branches),
        "amount": round(random.uniform(50.0, 75000.0), 2),
        "transaction_type": random.choice(txn_types),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def run_kafka_producer(bootstrap_servers='localhost:9092', topic='bank.transactions.v1', tps=2, max_events=100):
    """
    Publishes synthetic transactions to Kafka. Fallback to stdout log if broker is unavailable.
    """
    producer = None
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info(f"✅ Connected to Kafka broker at {bootstrap_servers}. Streaming to topic '{topic}'...")
    except Exception as e:
        logger.warning(f"⚠️ Kafka Broker unavailable ({str(e)}). Running in Dry-Run / Simulated Streaming Mode...")

    events_sent = 0
    try:
        while events_sent < max_events:
            txn = generate_mock_transaction()
            if producer:
                producer.send(topic, value=txn)
                logger.info(f"🚀 Sent to Kafka topic [{topic}]: {txn['transaction_id']} - ₹{txn['amount']}")
            else:
                logger.info(f"📡 [Simulated Kafka Event]: {txn}")

            events_sent += 1
            time.sleep(1.0 / tps)

        if producer:
            producer.flush()
            producer.close()
        logger.info(f"✅ Streamed {events_sent} transaction events successfully.")

    except KeyboardInterrupt:
        logger.info("🛑 Producer stopped by user.")

if __name__ == "__main__":
    run_kafka_producer(tps=2, max_events=50)
