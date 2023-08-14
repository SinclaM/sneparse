# Run all tests
test:
	@python3 -m unittest discover tests/

# Run the pipeline
pipeline:
	scripts/build_catalog_db.py
	scripts/cross_match.py
	$(RM) -r resources/images/categorized
	$(RM) resources/images/cross_matches/*.png
	mkdir resources/images/categorized
	scripts/image_driver.sh
	scripts/prepare_categories.py resources/images/cross_matches resources/images/categorized

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
