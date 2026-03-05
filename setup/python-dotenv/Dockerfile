FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN conda install python=3.11 -y

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY python-dotenv ./python-dotenv
RUN pip install --no-cache-dir -e ./python-dotenv/
COPY experiments/python-dotenv ./experiments

RUN mkdir ./results
RUN chmod +x /workspace/experiments/chainmap_load_test/run.sh
CMD ["bash", "/workspace/experiments/chainmap_load_test/run.sh"]
