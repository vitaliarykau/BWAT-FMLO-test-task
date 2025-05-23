.PHONY: build up down logs ps prune clean-all restart
DOCKER=podman
# Build and run containers
build:
	${DOCKER} compose build

up:
	${DOCKER} compose up

# Stop and remove containers, networks, images, and volumes
down:
	${DOCKER} compose down

# View logs
logs:
	${DOCKER} compose logs -f

# List containers
ps:
	${DOCKER} compose ps

# Prune system
prune:
	${DOCKER} system prune -a -f

# Clean all: stop containers, remove containers, networks, volumes, and prune system
clean-all: down prune 
restart: build up