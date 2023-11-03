# notebooks:
# 	docker run -v $(PWD)/src/notebooks:/tmp/working -w=/tmp/working -p 8888:8888 --rm -it gcr.io/kaggle-images/python jupyter lab --no-browser --ip=0.0.0.0 --port=8888 --notebook-dir=/tmp/working --allow-root

DOCKER_IMAGE_NAME = blsa_sdm
DOCKER_RUN = docker run -v ${PWD}:/app -v ~/kaggle/kaggle.json:/app/.kaggle/kaggle.json -e KAGGLE_CONFIG_DIR=/app/.kaggle ${DOCKER_IMAGE_NAME}

build:
	docker build -t $(DOCKER_IMAGE_NAME) .

download_sabap2:
	$(DOCKER_RUN) python -m data.run download-sabap2

download_ebirds:
	$(DOCKER_RUN) python -m data.run download-ebirds

download_inat:
	$(DOCKER_RUN) python -m data.run download-inat

download_all:
	@echo "Downloading all datasets..."
	@echo "Downloading sabap2..."
	@make download_sabap2
	@echo "Downloading inat..."
	@make download_inat
	@echo "Downloading ebirds..."
	@make download_ebirds
	@echo "All datasets downloaded."

combine_sabab2:
	$(DOCKER_RUN) python -m data.run combine-sabap2

run-%:
	# Here you call the data.run module explicitly
	$(DOCKER_RUN) python -m data.run $*

model-%:
	# This new target uses the src.sdm.run module
	$(DOCKER_RUN) python -m src.sdm.run $*
