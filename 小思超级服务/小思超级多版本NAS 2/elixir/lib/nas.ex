defmodule Nas do
  @moduledoc """
  NAS 服务主模块

  提供：
  - 文件存储和管理
  - 多语言翻译支持（28种语言）
  - HTTP API服务

  默认端口：8098
  """

  @version "1.0.0"

  def version, do: @version

  def start do
    Application.ensure_all_started(:nas)
  end

  def stop do
    Application.stop(:nas)
  end

  def health_check do
    %{
      status: :ok,
      version: @version,
      timestamp: System.system_time(:millisecond),
      uptime: get_uptime()
    }
  end

  defp get_uptime do
    # 返回服务启动时间
    DateTime.utc_now()
  end
end