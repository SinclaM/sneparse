# Check that given variables are set and all have non-empty values,
# die with an error otherwise.
#
# Params:
#   1. Variable name(s) to test.
#   2. (optional) Error message to print.
#
# https://stackoverflow.com/a/10858332
check_defined = \
    $(strip $(foreach 1,$1, \
        $(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
    $(if $(value $1),, \
      $(error Undefined $1$(if $2, ($2))))

# Run all tests
test:
	@python3 -m unittest discover tests/

# Run the pipeline
pipeline:
	@:$(call check_defined, EPOCH) # ensure that the EPOCH is specified before starting the pipeline
	scripts/build_catalog_db.py
	scripts/cross_match.py
	rm -rf "resources/images/epoch${EPOCH}_categorized"
	rm -rf "resources/images/epoch${EPOCH}_cross_matches"
	mkdir "resources/images/epoch${EPOCH}_categorized"
	mkdir "resources/images/epoch${EPOCH}_cross_matches"
	scripts/image_driver.sh
	scripts/prepare_categories.py "resources/images/epoch${EPOCH}_cross_matches" "resources/images/epoch${EPOCH}_categorized"

# Visualize package dependency tree.
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
