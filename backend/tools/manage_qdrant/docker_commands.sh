# No cache build
docker build --no-cache -t insert-db .

# Example commands to run the container
docker run \
  --env-file ~/src/python/.env_mini \
  -v /Users/timhazed/tmp/output_test:/app/input \
  -e PYTHONUNBUFFERED=1 \
  insert-db \
  --input "/app/input/chunked/doc_0005"