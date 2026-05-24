FROM jupyter/scipy-notebook:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}
RUN pip install --no-cache-dir \
    pandas==2.2.2 \
    numpy==1.26.4 \
    scikit-learn==1.5.1 \
    sqlalchemy==2.0.32 \
    psycopg2-binary==2.9.9 \
    boto3==1.34.162 \
    pyarrow==17.0.0 \
    s3fs==2024.6.1 \
    matplotlib==3.9.2 \
    seaborn==0.13.2 \
    joblib==1.4.2

WORKDIR /home/jovyan/work
