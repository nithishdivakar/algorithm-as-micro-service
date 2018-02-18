

run:
	redis-server &
	python3 run_micro_service.py

install_redis:
	sh install_redis.sh
