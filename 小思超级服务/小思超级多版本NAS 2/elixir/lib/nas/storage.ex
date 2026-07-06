defmodule Nas.Storage do
  use Agent

  def start_link(_opts) do
    Agent.start_link(fn -> %{} end, name: __MODULE__)
  end

  @doc """
  获取配置的存储根路径
  """
  defp get_root_path do
    case Nas.Config.load() do
      {:ok, config} -> Map.get(config, "storage_path", System.tmp_dir!())
      {:error, _} -> System.tmp_dir!()
    end
  end

  @doc """
  规范化路径，防止目录遍历攻击
  """
  defp normalize_path(path) do
    root = get_root_path()
    full_path = Path.join(root, path)

    # 确保路径在根目录内
    if String.starts_with?(Path.expand(full_path), Path.expand(root)) do
      {:ok, full_path}
    else
      {:error, "无效的路径"}
    end
  end

  @doc """
  列出文件
  """
  def list_files(path \\ "/") do
    case normalize_path(path) do
      {:ok, full_path} ->
        if File.dir?(full_path) do
          files =
            File.ls!(full_path)
            |> Enum.map(fn name ->
              file_path = Path.join(full_path, name)
              stat = File.stat!(file_path)

              %{
                name: name,
                path: Path.join(path, name),
                type: if(stat.type == :directory, do: "directory", else: "file"),
                size: stat.size,
                modified: stat.mtime,
                accessed: stat.atime
              }
            end)

          {:ok, files}
        else
          {:error, "路径不是目录"}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  @doc """
  获取文件内容
  """
  def get_file(path) do
    case normalize_path(path) do
      {:ok, full_path} ->
        if File.exists?(full_path) and not File.dir?(full_path) do
          case File.read(full_path) do
            {:ok, content} -> {:ok, content, Path.basename(full_path)}
            {:error, reason} -> {:error, "读取失败: #{reason}"}
          end
        else
          {:error, "文件不存在"}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  @doc """
  保存文件
  """
  def save_file(path, filename, content) do
    case normalize_path(path) do
      {:ok, dir_path} ->
        full_path = Path.join(dir_path, filename)

        # 确保目录存在
        File.mkdir_p!(dir_path)

        case File.write(full_path, content) do
          :ok -> {:ok, full_path}
          {:error, reason} -> {:error, "保存失败: #{reason}"}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  @doc """
  删除文件或目录
  """
  def delete_file(path) do
    case normalize_path(path) do
      {:ok, full_path} ->
        if File.dir?(full_path) do
          File.rm_rf(full_path)
        else
          File.rm(full_path)
        end
        |> case do
          {:ok, _} -> :ok
          {:error, reason, _} -> {:error, "删除失败: #{reason}"}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  @doc """
  创建目录
  """
  def create_directory(path, name) do
    case normalize_path(path) do
      {:ok, dir_path} ->
        full_path = Path.join(dir_path, name)

        case File.mkdir(full_path) do
          :ok -> :ok
          {:error, reason} -> {:error, "创建目录失败: #{reason}"}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  @doc """
  重命名文件或目录
  """
  def rename_file(old_path, new_name) do
    case normalize_path(old_path) do
      {:ok, full_old_path} ->
        parent_dir = Path.dirname(full_old_path)
        full_new_path = Path.join(parent_dir, new_name)

        case File.rename(full_old_path, full_new_path) do
          :ok -> :ok
          {:error, reason} -> {:error, "重命名失败: #{reason}"}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  @doc """
  移动文件或目录
  """
  def move_file(source, destination) do
    with {:ok, source_path} <- normalize_path(source),
         {:ok, dest_path} <- normalize_path(destination) do
      case File.rename(source_path, dest_path) do
        :ok -> :ok
        {:error, reason} -> {:error, "移动失败: #{reason}"}
      end
    else
      {:error, reason} -> {:error, reason}
    end
  end

  @doc """
  复制文件或目录
  """
  def copy_file(source, destination) do
    with {:ok, source_path} <- normalize_path(source),
         {:ok, dest_path} <- normalize_path(destination) do
      if File.dir?(source_path) do
        # 复制目录
        case File.cp_r(source_path, dest_path) do
          {:ok, _} -> :ok
          {:error, reason, _} -> {:error, "复制失败: #{reason}"}
        end
      else
        # 复制文件
        dest_dir = Path.dirname(dest_path)
        File.mkdir_p!(dest_dir)

        case File.copy(source_path, dest_path) do
          {:ok, _} -> :ok
          {:error, reason} -> {:error, "复制失败: #{reason}"}
        end
      end
    else
      {:error, reason} -> {:error, reason}
    end
  end

  @doc """
  搜索文件
  """
  def search_files(path \\ "/", keyword) do
    case normalize_path(path) do
      {:ok, full_path} ->
        results =
          Path.wildcard(Path.join([full_path, "**", "*#{keyword}*"]))
          |> Enum.map(fn file_path ->
            relative = Path.relative_to(file_path, get_root_path())
            stat = File.stat!(file_path)

            %{
              name: Path.basename(file_path),
              path: relative,
              type: if(stat.type == :directory, do: "directory", else: "file"),
              size: stat.size,
              modified: stat.mtime
            }
          end)

        {:ok, results}

      {:error, reason} ->
        {:error, reason}
    end
  end

  @doc """
  获取文件信息
  """
  def get_file_info(path) do
    case normalize_path(path) do
      {:ok, full_path} ->
        if File.exists?(full_path) do
          stat = File.stat!(full_path)

          info = %{
            name: Path.basename(full_path),
            path: path,
            type: if(stat.type == :directory, do: "directory", else: "file"),
            size: stat.size,
            modified: stat.mtime,
            accessed: stat.atime,
            created: stat.ctime,
            mode: stat.mode,
            links: stat.links
          }

          {:ok, info}
        else
          {:error, "文件不存在"}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end
end