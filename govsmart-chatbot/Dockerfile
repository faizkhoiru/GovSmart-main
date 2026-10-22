FROM python:3.12-slim
RUN adduser --disabled-password --gecos "" govsmart
WORKDIR /app
# Mode ekstraktif: numpy saja. LLM lewat HTTP bila LLM_BASE_URL di-set.
# Torch/sentence-transformers hanya untuk rebuild index, bukan runtime tanya.
COPY requirements-docker.txt requirements.txt
COPY service.py .
COPY scripts/chatbot.py scripts/retriever.py scripts/
RUN mkdir -p /app/data && chown -R govsmart:govsmart /app
RUN pip install --no-cache-dir -r requirements.txt
USER govsmart
EXPOSE 8001
HEALTHCHECK --interval=10s --timeout=2s --retries=30 --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health', timeout=1)"
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8001"]
