FROM python:3.12-slim
LABEL org.opencontainers.image.source=https://github.com/mdiluz/matchy
LABEL org.opencontainers.image.description="Matchy matches matchees"
LABEL org.opencontainers.image.licenses=Unlicense

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "py/matchy.py"]