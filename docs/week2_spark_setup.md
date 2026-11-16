# Week 2 Setup: PySpark and Apache Sedona

Week 2 needs to find which of millions of pings fall inside a store's 500 m area. Doing this
on one core would be slow, so we use **Apache Spark** (distributed computing) with
**Apache Sedona** (adds spatial functions such as `ST_Point` and `ST_DistanceSphere`).

## What you need

| Tool | Version | Why |
|---|---|---|
| Java (JDK) | 17 | Spark runs on Java |
| PySpark | 3.5.3 | Spark for Python |
| Apache Sedona | 1.7.1 | Spatial functions for Spark |

## Step 1: Install Java 17

Open PowerShell and run:

```
winget install EclipseAdoptium.Temurin.17.JDK
```

Close VS Code completely and open it again, so the new Java is found. Check it:

```
java -version
```

It should show version 17.

## Step 2: Install the Python packages

```
pip install -r requirements-spark.txt
```

## Step 3: Test it

```
python spark/test_sedona.py
```

The first run downloads the Sedona jar files, so it needs internet and takes a minute or two.
Expected result (the meters can differ by 1 or 2, depending on the Earth model):

```
device_id | store_id | meters | inside_500m
D1        | S01      | 78     | true
D2        | S01      | 428    | true
D3        | S01      | 2968   | false
TEST PASSED
```

## How it works

`spark/spark_session.py` creates a Spark session and switches on Sedona. All later Spark
scripts use `get_spark()` from this file.

## Common problems

| Problem | Fix |
|---|---|
| `JAVA_HOME is not set` or `java` not found | Install Java (Step 1) and restart VS Code |
| Java 21 or newer is installed | Spark 3.5 works best with Java 17. Install 17. |
| Download of jar files fails | Check the internet connection and run again |
| `winutils` or `HADOOP_HOME` warning on Windows | Safe to ignore for reading and counting. It matters only when writing files. |
