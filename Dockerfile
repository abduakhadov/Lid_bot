FROM python:3.11-slim

# Python muhitini optimallashtirish
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Bog'liqliklarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodni nusxalash
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]
