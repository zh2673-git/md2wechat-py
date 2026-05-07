from setuptools import setup, find_packages

setup(
    name="wechat-pub",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0",
        "markdown-it-py>=3.0",
        "pyyaml>=6.0",
        "jinja2>=3.0",
        "httpx>=0.25",
    ],
    entry_points={
        "console_scripts": [
            "wechat-pub=wechat_pub.cli.main:cli",
        ],
    },
    package_data={
        "wechat_pub": ["layout/**/*.yaml", "templates/**/*.html"],
    },
    python_requires=">=3.10",
)
