# create and run docker

    docker build -t my-file-chat .
    docker run -p 8501:8501 my-file-chat

# create an env

    python3 -m venv .venv

# activate the env

    source .venv/bin/activate

# requirement install command

    pip3 install --no-cache-dir -r requirements.txt
    pip install --upgrade pip

# run command

    streamlit run app.py --server.port=8501

## here are demo screens

<div align="center">
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0;">
        <div>
            <img src="./Documentation/img/screen1.png" alt="Screen 1" style="width: 100%; border-radius: 8px;    box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        </div>
        <div>
            <img src="./Documentation/img/screen2.png" alt="Screen 2" style="width: 100%; border-radius: 8px;    box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        </div>
    </div>
</div>
