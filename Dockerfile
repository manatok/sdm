# Use a specific version of the python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies for GDAL, gcc, g++, make, and Python dev headers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install the Python packages from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set default command for debugging
CMD ["bash"]
