"""Create a Spark session with Apache Sedona (spatial functions) switched on.

Sedona adds spatial SQL functions to Spark, for example ST_Point, ST_Buffer,
ST_Contains and ST_DistanceSphere. The Sedona jar files are downloaded from Maven
the first time this runs, so you need an internet connection.

Versions must match each other:
    Spark 3.5  +  Sedona 1.7.1  +  geotools-wrapper 1.7.1-28.5
"""
import os
import sys

# Make Spark use the same Python that runs this file.
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

SEDONA_PACKAGES = ",".join(
    [
        "org.apache.sedona:sedona-spark-shaded-3.5_2.12:1.7.1",
        "org.datasyslabs:geotools-wrapper:1.7.1-28.5",
    ]
)


def get_spark(app_name="GeoPulse", driver_memory="4g", shuffle_partitions=16):
    """Return a SparkSession that can run Sedona spatial SQL."""
    from sedona.spark import SedonaContext

    builder = (
        SedonaContext.builder()
        .appName(app_name)
        .master("local[*]")  # use all CPU cores on this computer
        .config("spark.jars.packages", SEDONA_PACKAGES)
        .config("spark.driver.memory", driver_memory)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.ui.showConsoleProgress", "false")
    )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return SedonaContext.create(spark)
