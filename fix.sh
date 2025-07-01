# 先保存当前PATH到临时变量
OLD_PATH=$PATH

# 处理PATH，去重且保证顺序
clean_path() {
  local IFS=:
  local -a arr=($OLD_PATH)
  local -A seen=()
  local new_path=""
  for dir in "${arr[@]}"; do
    # 去除前后空白
    dir="$(echo -e "$dir" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    # 忽略空路径和重复路径
    if [[ -n "$dir" && -z "${seen[$dir]}" ]]; then
      seen[$dir]=1
      if [[ -z "$new_path" ]]; then
        new_path="$dir"
      else
        new_path="$new_path:$dir"
      fi
    fi
  done
  echo "$new_path"
}

# 运行函数，得到清理后的PATH
export PATH=$(clean_path)

# 把虚拟环境的bin放前面（假设你激活了环境）
if [[ -n "$CONDA_PREFIX" ]]; then
  export PATH="$CONDA_PREFIX/bin:$PATH"
fi

# 把 ~/.local/bin 放最后，避免抢优先级
export PATH=$(echo "$PATH" | tr ':' '\n' | grep -v "$HOME/.local/bin" | paste -sd ':'):$HOME/.local/bin

# 显示新PATH确认
echo "Cleaned PATH:"
echo $PATH | tr ':' '\n' | nl
