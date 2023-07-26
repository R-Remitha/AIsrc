# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev build-essential

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -sL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y nodejs

# Install NPM dependencies and build the ReactJS app
WORKDIR /app/client
RUN npm install && \
    npm run build

# Copy ReactJS build to Flask app's static folder
WORKDIR /app
RUN mkdir -p /app/static
COPY /client/build /app/static

# Expose ports
EXPOSE 3000 9999

# Start the Flask app and serve the ReactJS build files
CMD ["python", "app.py"]
