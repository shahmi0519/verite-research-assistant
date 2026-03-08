FROM python:3.10.0

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files
COPY . .


EXPOSE 8080

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
