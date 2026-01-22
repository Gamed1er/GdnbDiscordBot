docker stop gdnb_bot && docker rm gdnb_bot
git pull
docker build -t my_discord_bot .
docker run -d \
  --name gdnb_bot \
  --user 1000:1000 \
  --restart always \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  my_discord_bot
