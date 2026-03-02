FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN conda install python=3.11 -y

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["bash"]
