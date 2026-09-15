FROM python:3.14-slim
RUN apt-get update
WORKDIR /enterprise_data_agent
COPY src/ ./src/
COPY data/ ./data/
COPY benchmarks/ ./benchmarks/
COPY .gitignore .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python","-m","src.api.main"]
