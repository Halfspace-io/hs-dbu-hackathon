Copyright © 2022 by Halfspace. All rights reserved

Getting started
============
Follow the steps in this README to get you up and running.

## 0 Don't clone this repo! 
Instead of cloning this repository, please create a new repository for your team based on this template. You can do this by clicking the green "Use this template" button at the top right of this page.

**Remeber to make it private so that other teams cannot see your work! ;-) (and to not violate any data rights)**  

## 1 Install  python packages  
If you do not already have a python version installed otherwise you can go to [their download page](https://www.python.org/downloads/). 
You can install the required packages into you global python installation by writing `pip install -r requirements.txt`, but we recommend using a virtual environment manager.

To use a virtual environment, you can make use of onw of the two options below:

### 1.1. Install virtual environment with venv (standard Python way)

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - **On macOS/Linux:** `source venv/bin/activate`
   - **On Windows:** `venv\Scripts\activate`

3. **Install packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Make sure your IDE is using the new virtual environment as the python interpreter.** 

### 1.2. Optional: Install virtual environment with UV (the new python management tool)

UV is a new python management tool. You can check a demo of basic usage [here](https://docs.astral.sh/uv/).

1. Install uv (check this [page](https://docs.astral.sh/uv/getting-started/installation/) for more details):
* MacOs and Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
* Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Verify that the command `uv --version` is recognized.

The dependencies are managed by uv, that installs everything (including python) in a local environment.

1) In the root of this project (where this README is) run `uv sync` in your terminal. 
3) Test again that everything is running by importing the dataloder.
    1. Open a python shell in the created virtual environment by running `uv run python` in your shell.
    2. Try to import your package in that python sheel: `>>> from src.data_loader import DataLoader`.

If all these steps work, the installation was succesfull! 
    
*Note: The sync command will create a virtual environment in your repo (in .venv) and will install all the dependencies in that environment. You can start a python shell from that enviroment with `uv run python`. If using PyCharm or VSCode, make sure this virtual environment is the one used by the python entrepeter of PyCharm or VScode.

## 2. Introduction to the data 
Go to [intro.ipynb](intro.ipynb) to start exploring the data! 
