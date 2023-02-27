# Install all packages, including our own editable package.
install: 
	@pip3 install -r requirements.txt
	@pip3 install -e .

# List all installed packages.
# We don't add our own editable package because
# pip dumps it as a git URL and not a relative path.
freeze:
	@pip3 freeze | sed '/^-e.*/d'

# Run all tests
test:
	@python3 -m unittest discover tests/

# Visualize package dependency tree>
# `pipdeptree` must be installed and in the $PATH.
tree:
	@pipdeptree --python `whereis -q python`

clean:
	# Delete all __pycache__ folders
	find . -type d -name __pycache__ -exec rm -r {} \+
	
	# Delete logs
	$(RM) -f sneparse/resources/logs/*.txt
