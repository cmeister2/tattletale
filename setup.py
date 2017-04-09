from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="tattletale",
    version="0.1.0",
    description="An internet reconnaissance tool",
    long_description=readme(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Security",
    ],
    keywords="tattletale",
    url="http://github.com/cmeister2/tattletale",
    author="cmeister2",
    author_email="cmeister2@gmail.com",
    license="MIT",
    packages=["tattletale"],
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
