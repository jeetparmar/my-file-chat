FROM python:3.9.6

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
    flac && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8501
COPY . /app
CMD ["streamlit", "run", "app.py", "--server.port=8501"]