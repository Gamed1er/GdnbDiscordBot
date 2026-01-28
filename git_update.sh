#!/bin/bash

# 檢查是否有輸入參數，如果沒有就給一個預設值
if [ -z "$1" ]; then
  MESSAGE="Update: $(date +'%Y-%m-%d %H:%M:%S')"
else
  MESSAGE="$1"
fi

echo "--- 正在加入檔案 ---"
git add .

echo "--- 提交說明: $MESSAGE ---"
git commit -m "$MESSAGE"

echo "--- 推送到 GitHub ---"
git push