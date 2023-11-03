FROM python:3.11-slim

# Install necessary packages
RUN pip install pandas numpy click pyarrow requests kaggle tqdm scikit-learn

# Set working directory
WORKDIR /app

# Set default command for debugging
CMD ["bash"]
