"""Create a Spark session with Apache Sedona (spatial functions) switched on.

Sedona adds spatial SQL functions to Spark, for example ST_Point, ST_Buffer,
ST_Contains and ST_DistanceSphere. The Sedona jar files are downloaded from Maven
the first time this runs, so you need an internet connection.

Versions must match each other:  Spark 3.5  +  Sedona 1.7.1

Only the main Sedona jar is needed for points, polygons and ST_Contains. The extra
geotools-wrapper jar is needed only for map projection functions such as ST_Transform.
"""
import os
import sys

# On Windows, Spark needs Hadoop's helper program winutils.exe. If it is saved in
# <project>/hadoop/bin/winutils.exe, use that folder (see docs/week2_spark_setup.md).
_HADOOP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hadoop")
if os.name == "nt" and "HADOOP_HOME" not in os.environ:
    if os.path.exists(os.path.join(_HADOOP, "bin", "winutils.exe")):
        os.environ["HADOOP_HOME"] = _HADOOP

# Make Spark use the same Python that runs this file.
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

SEDONA_PACKAGES = "org.apache.sedona:sedona-spark-shaded-3.5_2.12:1.7.1"


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
