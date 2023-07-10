# Run all tests
test:
	@python3 -m unittest discover tests/

# Visualize package dependency tree>
# `pipdeptree` must be installed and in the $PATH.
tree:
	@pipdeptree --python `whereis -q python`

# Send changes to Quest mirror
put:
	rsync -vhra . ${QUEST_PROJECT_DIR} --include='**.gitignore' --exclude='/.git' --filter=':- .gitignore'

clean:
	# Delete all __pycache__ folders
	find . -type d -name __pycache__ -exec rm -r {} \+
	
	# Delete logs
	$(RM) -f resources/logs/*.txt
