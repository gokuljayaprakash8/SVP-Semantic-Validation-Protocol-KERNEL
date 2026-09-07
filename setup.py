from setuptools import setup, find_packages

setup(
    name="svp_kernel",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.141.1",
        "fastembed==0.8.0",
        "huggingface-hub==1.26.0",
        "numpy==2.5.1",
        "onnxruntime==1.28.0",
        "pydantic==2.13.4",
        "PyYAML==6.0.3",
        "requests==2.34.2",
        "scikit-learn==1.9.0",
        "uvicorn==0.52.1",
    ],
    author="SVP Infrastructure Labs",
    description="Zero-Trust Semantic Validation Protocol for AI Agents",
    url="https://github.com/gokuljayaprakash8/SVP-Semantic-Vector-Protocol-KERNEL",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12,<3.13",
)
