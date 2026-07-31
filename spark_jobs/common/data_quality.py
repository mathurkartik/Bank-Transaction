from pyspark.sql import DataFrame
from pyspark.sql.functions import col, current_timestamp, lit, when
import logging
import os

logger = logging.getLogger(__name__)

def validate_and_quarantine(df: DataFrame, primary_keys: list, validation_rules: list, entity_name: str, base_path: str = "data") -> tuple[DataFrame, DataFrame]:
    """
    Validates a PySpark DataFrame based on primary key constraints and custom validation rules.
    Diverts invalid rows to a quarantine path and returns (valid_df, quarantined_df).
    
    :param df: Input PySpark DataFrame
    :param primary_keys: List of column names that must not be null
    :param validation_rules: List of boolean PySpark expressions (Column objects) representing valid rules
    :param entity_name: Name of the dataset entity (e.g. 'transactions', 'loans')
    :param base_path: Base data storage directory
    :return: (valid_df, quarantined_df)
    """
    try:
        if df is None or len(df.columns) == 0:
            logger.warning(f"Empty DataFrame passed to validate_and_quarantine for {entity_name}")
            return df, None

        # Build condition for non-null primary keys
        pk_condition = None
        for pk in primary_keys:
            if pk in df.columns:
                cond = col(pk).isNotNull()
                pk_condition = cond if pk_condition is None else (pk_condition & cond)

        # Build combined condition for rules
        rule_condition = None
        for rule in validation_rules:
            rule_condition = rule if rule_condition is None else (rule_condition & rule)

        # Total valid condition
        valid_condition = lit(True)
        if pk_condition is not None:
            valid_condition = valid_condition & pk_condition
        if rule_condition is not None:
            valid_condition = valid_condition & rule_condition

        valid_df = df.filter(valid_condition)
        quarantined_df = df.filter(~valid_condition).withColumn("quarantine_timestamp", current_timestamp()) \
                           .withColumn("quarantine_entity", lit(entity_name))

        quarantine_count = quarantined_df.count()
        valid_count = valid_df.count()

        logger.info(f"🔍 Quality Gate [{entity_name}]: {valid_count} valid records, {quarantine_count} quarantined records.")

        if quarantine_count > 0:
            quarantine_output_path = f"{base_path}/quarantine/{entity_name}"
            quarantined_df.write.mode("append").parquet(quarantine_output_path)
            logger.warning(f"⚠️ Saved {quarantine_count} quarantined records to {quarantine_output_path}")

        return valid_df, quarantined_df

    except Exception as e:
        logger.error(f"❌ Error during data quality validation for {entity_name}: {str(e)}")
        # In case of validation execution failure, fallback to returning original dataframe
        return df, None
