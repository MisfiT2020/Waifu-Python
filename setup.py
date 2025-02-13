from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.MD").read_text()

setup(
    name="waifu-python",
    version="1.7.1",
    packages=find_packages(),
    install_requires=["httpx"],
    author="Misfit",
    description="A project born out of boredom, designed to simplify and reduce the code related to the Waifu API.",
    url="https://github.com/MisfiT2020/Waifu-Python",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    )
