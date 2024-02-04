
# Creating a Python AWS Lambda layer for scikit-learn, xgboost or any other custom layer
Skit-learn is a very popular python machine learning library. It is used for ML operations like training, testing, inference and more. We wanted to use it as part of an AWS Lambda function. it is not a part of the basic python packages, and unlike the pandas library - there is no AWS provided lambda layer for it.
We found it hard to create the missing layer we needed. We decided to document the process to help others creating and updating scikit-learn based layers, or any other custom AWS lambda layers like xgboost, which is also included in this repo.

To create a layer use the command line interface:

```python src/create_layer.py -l sklearn```

To create sckit-learn layer for arm64 architecture use the following command:

```python src/create_layer.py -l sklearn -a arm64```

This process is not clean from errors. You have to choose the right runtime and platform and in some cases you have to define library versions. In addition, deleting files from the zipped resources file can break your lambda function at runtime. You can use the command line interface to publish the layer and test it.

```python src/create_layer.py -l sklearn -p true -bucket your-s3-bucket```

Use the following command to view all command line interface options:

```python src/create_layer.py -h```

Use this repo to create your own scikit-learn layer, xgboost layer or any other custom layer you need. It is also possible to contribute and add configuration for other useful layers.

# Layer creation 
We use the following configuration to avoid compatability issues:
The base python image according to our lambda runtime - using the same python runtime, and pip installer saved us from compatibility errors in later stages. You can browse the available tags here: https://gallery.ecr.aws/lambda/python
In the requirements installation we used the platform directive to install the chosen platform’s artifacts. See the available downloads for scikit-learn as example: https://pypi.org/project/scikit-learn/#files

We used the only-binary directive to avoid adding source files since we want to keep the layer small.
We used a multi-stage build to have the tools for updating the resources we installed. In the second stage of the build we deleted data from the installed resources and zipped the resources to a layer.zip file

The command line interface allows you to choose a layer and run its creation process. It also analyzes and lists the largest files, largest folders and largest size according to file types. This information is useful for removing unnecessary resources from the layer.


# Layer configuration
A layer configuration consists of two files:
1. requirement.txt - defines the python requirements needed for the layer
2. cleanup.sh - a script for cleaning up the image from unnecessary resources
You can add your own layer by creating a new layer folder with the layer configuration files described

