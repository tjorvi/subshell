.PHONY: image demos tapes bundle

IMG=subshell-demo-tools

# Directory variables
ASSETS_DIR=./assets
TAPES_DIR=./demo/tmp/tapes

# Valid prompt sets per user mode (aligned with SUBSHELL_USER_MODE logic)
USER_MODES=demo starship ohmyzsh p10k

CONTAINER=docker buildx
# CONTAINER=container


.PHONY: image tapes tapes-demo tapes-starship tapes-ohmyzsh tapes-p10k \
	screenshots screenshots-all clean-tapes \
	screenshot-zsh-default screenshot-zsh-default-blankline \
	screenshot-fish-default screenshot-fish-default-blankline \
	screenshot-zsh-starship screenshot-fish-starship \
	screenshot-zsh-ohmyzsh screenshot-zsh-ohmyzsh-blankline \
	screenshot-zsh-powerlevel10k screenshots-init \
	screenshot-zsh-default-outside screenshot-zsh-default-outside-blankline \
	screenshot-fish-default-outside screenshot-fish-default-outside-blankline \
	screenshot-zsh-starship-outside screenshot-fish-starship-outside \
	screenshot-zsh-ohmyzsh-outside screenshot-zsh-ohmyzsh-outside-blankline \
	screenshot-zsh-powerlevel10k-outside

bundle:
	just bundle

image: bundle
	$(CONTAINER) build -f demo/Dockerfile.demo -t $(IMG) .

tapes: tapes-demo tapes-starship tapes-ohmyzsh tapes-p10k

# Generate tapes for default (demo) user (default prompts only)
tapes-demo: image
	$(CONTAINER) run --rm \
		--entrypoint /usr/bin/python3 \
		-v $(PWD):/workspace \
		--user demo \
		-e SUBSHELL_USER_MODE=demo \
		-w /workspace \
		$(IMG) demo/generate_tapes.py

# Generate tapes for starship user (starship prompts)
tapes-starship: image
	docker run --rm \
		--entrypoint /usr/bin/python3 \
		-v $(PWD):/workspace \
		--user demo-starship \
		-e SUBSHELL_USER_MODE=starship \
		-w /workspace \
		$(IMG) demo/generate_tapes.py

# Generate tapes for oh-my-zsh user
tapes-ohmyzsh: image
	docker run --rm \
		--entrypoint /usr/bin/python3 \
		-v $(PWD):/workspace \
		--user demo-oh-my-zsh \
		-e SUBSHELL_USER_MODE=ohmyzsh \
		-w /workspace \
		$(IMG) demo/generate_tapes.py

# Generate tapes for powerlevel10k user
tapes-p10k: image
	docker run --rm \
		--entrypoint /usr/bin/python3 \
		-v $(PWD):/workspace \
		--user demo-oh-my-zsh-p10k \
		-e SUBSHELL_USER_MODE=p10k \
		-w /workspace \
		$(IMG) demo/generate_tapes.py

clean-tapes:
	rm -rf $(TAPES_DIR) && mkdir -p $(TAPES_DIR)

test: screenshots

.PHONY: approve-screenshots
approve-screenshots: screenshots
	pytest -k test_prompt_screenshots --approve-screenshots

.PHONY: list-unapproved pending-screenshots
list-unapproved:
	python3 scripts/list_unapproved.py || true

pending-screenshots:
	ls -1 tests/pending || true

# Helper to ensure assets directory exists with correct permissions
screenshots-init:
	@mkdir -p $(ASSETS_DIR) && chmod 0777 $(ASSETS_DIR)

# Individual screenshot targets (depend only on needed tape generation)
 screenshot-zsh-default: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.default.tape

 screenshot-zsh-default-blankline: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.default.blankline.tape || true

 screenshot-fish-default: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.fish.default.tape

 screenshot-fish-default-blankline: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.fish.default.blankline.tape || true

 screenshot-zsh-starship: image tapes-starship screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-starship \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.starship.tape

 screenshot-fish-starship: image tapes-starship screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-starship \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.fish.starship.tape

 screenshot-zsh-ohmyzsh: image tapes-ohmyzsh screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-oh-my-zsh \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.ohmyzsh.tape

 screenshot-zsh-ohmyzsh-blankline: image tapes-ohmyzsh screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-oh-my-zsh \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.ohmyzsh.blankline.tape || true

 screenshot-zsh-powerlevel10k: image tapes-p10k screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-oh-my-zsh-p10k \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.powerlevel10k.tape

# Outside root variants
 screenshot-zsh-default-outside: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.default.outside.tape

 screenshot-zsh-default-outside-blankline: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.default.outside.blankline.tape || true

 screenshot-fish-default-outside: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.fish.default.outside.tape

 screenshot-fish-default-outside-blankline: image tapes-demo screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.fish.default.outside.blankline.tape || true

 screenshot-zsh-starship-outside: image tapes-starship screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-starship \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.starship.outside.tape

 screenshot-fish-starship-outside: image tapes-starship screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-starship \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.fish.starship.outside.tape

 screenshot-zsh-ohmyzsh-outside: image tapes-ohmyzsh screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-oh-my-zsh \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.ohmyzsh.outside.tape

 screenshot-zsh-ohmyzsh-outside-blankline: image tapes-ohmyzsh screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-oh-my-zsh \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.ohmyzsh.outside.blankline.tape || true

 screenshot-zsh-powerlevel10k-outside: image tapes-p10k screenshots-init
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD)/assets:/workspace/assets \
		-v $(TAPES_DIR):/tapes \
		-v ./dist:/dist \
		--user demo-oh-my-zsh-p10k \
		-w /workspace \
		$(IMG) ./run-demos.sh /tapes/test.zsh.powerlevel10k.outside.tape

# Aggregate target (kept for backwards compatibility)
screenshots: \
	screenshot-zsh-default \
	screenshot-zsh-default-blankline \
	screenshot-fish-default \
	screenshot-fish-default-blankline \
	screenshot-zsh-starship \
	screenshot-fish-starship \
	screenshot-zsh-ohmyzsh \
	screenshot-zsh-ohmyzsh-blankline \
	screenshot-zsh-powerlevel10k \
	screenshot-zsh-default-outside \
	screenshot-zsh-default-outside-blankline \
	screenshot-fish-default-outside \
	screenshot-fish-default-outside-blankline \
	screenshot-zsh-starship-outside \
	screenshot-fish-starship-outside \
	screenshot-zsh-ohmyzsh-outside \
	screenshot-zsh-ohmyzsh-outside-blankline \
	screenshot-zsh-powerlevel10k-outside

screenshots-all: clean-tapes screenshots


demos: image tapes
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v ./assets:/output   \
		-v ./demo/tmp/tapes:/tapes \
		-v ./dist:/dist       \
		$(IMG)                \
		-lc './run-demos.sh'

# .PHONY: demo-all smoke-ohmyzsh
# demo-all: demos

# smoke-ohmyzsh: demo-env
# 	$(RUN_IN) -lc '\
# 	  echo "ZSH loaded: $$ZSH"; \
# 	  python3 bundle.py; \
# 	  export PATH="$${PATH}:/workspace/dist"; \
# 	  cd /tmp/subshell-demo; \
# 	  SUBSHELL_ROOT=. SUBSHELL_PROMPT="[smoke]" subshell -c "pwd && exit" || true'

# # verify (golden snapshot)
# .PHONY: test-tape update-snapshots render

# test-tape: demo-env
# 	$(RUN_IN) -lc '\
# 	  mkdir -p assets /tmp/tapes && \
# 	  # make a fast-speed flow and a temp test that points to it\n\
# 		sed -E "s/^Set TypingSpeed .*/Set TypingSpeed $(FAST_SPEED)/" demo/tapes/flow.tape > /tmp/tapes/flow.fast.tape && \
# 	  sed -E "s#^Source .*#Source /tmp/tapes/flow.fast.tape#" demo/tapes/test.tape > /tmp/tapes/test.fast.tape && \
# 	  timeout $(FAST_TIMEOUT) vhs /tmp/tapes/test.fast.tape'
# 	diff -u snapshots/compose-lifecycle.ascii assets/compose-lifecycle.ascii

# update-snapshots: demo-env
# 	$(RUN_IN) -lc '\
# 	  mkdir -p assets /tmp/tapes && \
# 		sed -E "s/^Set TypingSpeed .*/Set TypingSpeed $(FAST_SPEED)/" demo/tapes/flow.tape > /tmp/tapes/flow.fast.tape && \
# 	  sed -E "s#^Source .*#Source /tmp/tapes/flow.fast.tape#" demo/tapes/test.tape > /tmp/tapes/test.fast.tape && \
# 	  timeout $(FAST_TIMEOUT) vhs /tmp/tapes/test.fast.tape'
# 	mkdir -p snapshots && cp assets/compose-lifecycle.ascii snapshots/

# # render the README video
# render: demo-env
# 	$(RUN_IN) -lc '\
# 	  mkdir -p assets /tmp/tapes && \
# 	  # pretty-speed nested flow + temp render pointing to it\n\
# 		sed -E "s/^Set TypingSpeed .*/Set TypingSpeed $(PRETTY_SPEED)/" demo/tapes/flow.tape > /tmp/tapes/flow.pretty.tape && \
# 	  sed -E "s#^Source .*#Source /tmp/tapes/flow.pretty.tape#" demo/tapes/render.tape > /tmp/tapes/render.pretty.tape && \
# 	  timeout $(PRETTY_TIMEOUT) vhs /tmp/tapes/render.pretty.tape'
