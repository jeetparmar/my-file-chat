# create and run docker

    docker build -t my-file-chat .
    docker run -p 8501:8501 my-file-chat

# requirement install command

    pip3 install --no-cache-dir -r requirements.txt

# activate the env

    source .venv/bin/activate

# run command

    streamlit run app.py --server.port=8501
