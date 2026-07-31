import json
import time
import random
import uuid
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_mock_transaction():
    """Generates realistic synthetic banking transaction events with high entropy UUIDv4 keys."""
    branches = [f"BR_{i:03d}" for i in range(1, 63)]
    event_types = ["CARD_TRANSACTION", "CUSTOMER_ONBOARDED", "EMI_PAYMENT_EVENT", "NEW_BRANCH_OPENED"]
    event_type = random.choices(event_types, weights=[0.80, 0.10, 0.08, 0.02])[0]

    unique_uuid = uuid.uuid4().hex.upper()
    
    if event_type == "CARD_TRANSACTION":
        txn_types = ["DEPOSIT", "WITHDRAWAL", "PAYMENT", "TRANSFER", "PURCHASE"]
        return {
            "event_type": "CARD_TRANSACTION",
            "transaction_id": f"TXN-{unique_uuid[:12]}",
            "customer_id": f"CUST-{unique_uuid[12:20]}",
            "branch_id": random.choice(branches),
            "amount": round(random.uniform(15.50, 48500.75), 2),
            "transaction_type": random.choice(txn_types),
            "interchange_fee_earned": round(random.uniform(5.0, 25.0), 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }
    elif event_type == "CUSTOMER_ONBOARDED":
        return {
            "event_type": "CUSTOMER_ONBOARDED",
            "customer_id": f"CUST-{unique_uuid[:10]}",
            "credit_score": random.randint(350, 800),
            "customer_segment": random.choice(["BASIC", "STANDARD", "PREMIUM"]),
            "branch_id": random.choice(branches),
            "initial_balance": round(random.uniform(5000.0, 250000.0), 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }
    elif event_type == "EMI_PAYMENT_EVENT":
        return {
            "event_type": "EMI_PAYMENT_EVENT",
            "loan_id": f"LN-{unique_uuid[:10]}",
            "customer_id": f"CUST-{unique_uuid[10:18]}",
            "emi_amount": round(random.uniform(5000.0, 45000.0), 2),
            "status": random.choice(["PAID", "PAID", "PAID", "MISSED"]),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }
    else:  # NEW_BRANCH_OPENED
        new_b_num = len(branches) + 1
        return {
            "event_type": "NEW_BRANCH_OPENED",
            "branch_id": f"BR_{new_b_num:03d}",
            "opening_date": datetime.now().strftime("%Y-%m-%d"),
            "monthly_cost": 1500000,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        }

def run_kafka_producer(bootstrap_servers='localhost:9092', topic='bank.transactions.v1', tps=7.5, max_events=100):
    """
    Publishes high-volume synthetic transactions to Kafka (400-500 txns/min ~ 7.5 TPS).
    Fallback to stdout log if broker is unavailable.
    """
    producer = None
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logger.info(f"✅ Connected to Kafka broker at {bootstrap_servers}. Streaming at {tps*60:.0f} txns/min to topic '{topic}'...")
    except Exception as e:
        logger.warning(f"⚠️ Kafka Broker unavailable ({str(e)}). Running in High-Volume Simulated Streaming Mode ({tps*60:.0f} txns/min)...")

    events_sent = 0
    try:
        while events_sent < max_events:
            txn = generate_mock_transaction()
            if producer:
                producer.send(topic, value=txn)
                logger.info(f"🚀 Sent [{txn['event_type']}]: {txn.get('transaction_id', txn.get('customer_id'))}")
            else:
                logger.info(f"📡 High-Volume Event [{txn['event_type']}]: {txn.get('transaction_id', txn.get('customer_id'))}")

            events_sent += 1
            time.sleep(1.0 / tps)

        if producer:
            producer.flush()
            producer.close()
        logger.info(f"✅ Streamed {events_sent} high-volume transaction events successfully.")

    except KeyboardInterrupt:
        logger.info("🛑 Producer stopped by user.")

if __name__ == "__main__":
    # 7.5 TPS = 450 transactions / minute
    run_kafka_producer(tps=7.5, max_events=50)
