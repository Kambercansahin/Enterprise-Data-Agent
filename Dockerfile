FROM python:3.14-slim
RUN apt-get update
WORKDIR /enterprise_data_agent
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY data/ ./data/
COPY benchmarks/ ./benchmarks/

CMD ["python","-m","src.api.main"]
