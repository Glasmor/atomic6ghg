.PHONY: all_tests unittests integration e2e typecheckers clean linters
.SHELL: /bin/zsh

AWS_SECRETS=~/dev/glasmor/.aws-secrets
AWS_REGION=us-west-2
AWS_ECR=079289496000.dkr.ecr.us-west-2.amazonaws.com


help_text:=" \
	atomic6ghg makefile commands:\n\n \
	Usage: make [-kn] [command] [variables] \n \
	Commands: \n \
	\tall_tests         Run unittests, integration, e2e, linters and typecheckers. \n \
	\t                      Use option -k to \"keep going\" on fail. \n \
	\tblack             Format source files under the calculator package with Black. \n \
	\tclean             Remove stray files generated during test runs. \n \
    \tdist              Build Python wheel of the calculator package. \n \
    \tlocal_dist        Build wheel and deploy it locally. \n \
    \tlinters           Run Pylint over the sources under calculator. Settings in myproject.toml. \n \
    \tpip               Generate requirements.txt and dev-requirements.txt from pyproject.toml. \n \
    \t                      Syncronizes the latest package versions with activated venv. \n \
    \tunittests         Run the PyTest runner over the tests in calculator/tests/unittests. \n \
    "

help:
	@echo ${help_text}

all_tests: unittests linters typecheckers
	# usage: make -k all_tests
	# alt usage: make -k

local_dist:
	python3 -m build --wheel --outdir ./dist . ; \
	pip install -e atomic6ghg

linters:
	export PYTHONPATH=${PYTHONPATH}:${PWD}/atomic6ghg ; \
	cd atomic6ghg ; \
	pylint --disable=logging ./atomic6ghg

typecheckers:
	mypy ./atomic6ghg

unittests:
	export PYTHONPATH=${PYTHONPATH}:${PWD}/atomic6ghg ; \
	cd atomic6ghg/tests ; \
	pytest  --tb=no

clean:
	rm -rdf .pytest_cache

pip: pyproject.toml
	pip-compile -o requirements.txt --resolver=backtracking -v pyproject.toml
	pip-compile --extra dev -o dev-requirements.txt --resolver=backtracking -v pyproject.toml
	pip-sync requirements.txt dev-requirements.txt

dist: requirements.txt pyproject.toml manifest.in
	python -m build --wheel --outdir ./dist .

black:
	black -l 125 atomic6ghg
