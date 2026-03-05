FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN conda install python=3.11 -y

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the whoosh-reloaded source and install it (editable install so that
# optimization branches checked out inside the container are reflected immediately)
COPY whoosh-reloaded/ ./whoosh-reloaded/
RUN pip install --no-cache-dir -e ./whoosh-reloaded/

# Copy experiment scripts and result output directories
COPY experiments/whoosh-reloaded/ ./experiments/
RUN mkdir -p /results

CMD ["bash"]
