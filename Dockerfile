FROM laudio/pyodbc:1.0.38

WORKDIR sorgulayici
COPY src/ .
RUN yes | pip install -r requirements.txt

CMD ["python3", "./main.py"]
