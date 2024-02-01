ARG LAYER_FILE
ARG LAMBDA_BASE_IMAGE
FROM public.ecr.aws/lambda/python:${LAMBDA_BASE_IMAGE} AS build-stage0
ARG LAYER_FILE
COPY requirements.txt .
RUN pip install --platform=manylinux_2_17_x86_64 --only-binary=:all: -r requirements.txt -t /tmp/python/

FROM alpine
ARG LAYER_FILE
RUN apk --no-cache add zip
COPY --from=build-stage0 /tmp/python/ /tmp/layer/python/
WORKDIR /tmp/
COPY cleanup.sh .
RUN chmod +x ./cleanup.sh && ./cleanup.sh

WORKDIR /tmp/layer/
RUN mkdir /tmp/output_file/ && zip -r9 /tmp/output_file/${LAYER_FILE} .
CMD cp /tmp/output_file/* /outputs/