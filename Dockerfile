FROM python:3.12
# Or any preferred Python version.
ADD r2p.py .
ADD requirements.txt .
ADD config.yml .
RUN pip install -r requirements.txt
CMD ["python", "./r2p.py"]
# Or enter the name of your unique directory and parameter set.
