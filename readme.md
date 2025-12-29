# create and run docker

    docker build -t my-file-chat .
    docker run -p 8501:8501 my-file-chat

# activate the env

    source .venv/bin/activate

# run command

    streamlit run app.py --server.port=8501
