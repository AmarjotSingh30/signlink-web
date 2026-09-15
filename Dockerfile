# Use Python 3.11 to match your laptop and TensorFlow requirements
FROM python:3.11

# Set up the working folder inside the cloud server
WORKDIR /app

# Copy your requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your project files
COPY . .

# Hugging Face Spaces requires web apps to run on port 7860
EXPOSE 7860

# Start the Flask server using Gunicorn on the correct port
CMD ["gunicorn", "-b", "0.0.0.0:7860", "web_app:app"]