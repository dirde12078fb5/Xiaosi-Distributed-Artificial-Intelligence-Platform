defmodule Nas.Config do
  @moduledoc """
  配置文件读取模块
  支持 ../config/config.json 配置文件
  """

  @config_path "../config/config.json"

  @doc """
  加载配置文件
  """
  def load do
    config_path = get_config_path()

    case File.read(config_path) do
      {:ok, content} ->
        case Jason.decode(content) do
          {:ok, config} -> {:ok, config}
          {:error, _} -> {:error, "配置文件格式错误"}
        end

      {:error, reason} ->
        {:error, "无法读取配置文件: #{reason}"}
    end
  end

  @doc """
  获取配置值
  """
  def get(key, default \\ nil) do
    case load() do
      {:ok, config} -> Map.get(config, key, default)
      {:error, _} -> default
    end
  end

  @doc """
  获取配置路径
  """
  defp get_config_path do
    # 获取当前应用目录
    app_dir = Application.app_dir(:nas, "priv")

    # 计算配置文件的绝对路径
    config_path =
      if Path.type(@config_path) == :relative do
        Path.join([app_dir, "..", "..", "..", @config_path])
        |> Path.expand()
      else
        @config_path
      end

    config_path
  end

  @doc """
  重新加载配置
  """
  def reload do
    load()
  end
end