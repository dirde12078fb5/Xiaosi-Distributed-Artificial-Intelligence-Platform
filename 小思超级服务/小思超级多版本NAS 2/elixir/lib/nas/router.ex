defmodule Nas.Router do
  use Plug.Router

  plug(:match)
  plug(:dispatch)

  # 获取文件列表
  post "/api/list" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    path = Map.get(params, :path, "/")

    case Nas.Storage.list_files(path) do
      {:ok, files} ->
        send_resp(conn, 200, Jason.encode!(%{success: true, data: files}))

      {:error, reason} ->
        send_resp(conn, 400, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 下载文件
  post "/api/download" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    path = Map.get(params, :path, "")

    case Nas.Storage.get_file(path) do
      {:ok, content, filename} ->
        conn
        |> put_resp_content_type("application/octet-stream")
        |> put_resp_header("content-disposition", "attachment; filename=\"#{filename}\"")
        |> send_resp(200, content)

      {:error, reason} ->
        send_resp(conn, 404, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 上传文件
  post "/api/upload" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    path = Map.get(params, :path, "/")
    filename = Map.get(params, :filename, "")
    content = Map.get(params, :content, "")

    case Nas.Storage.save_file(path, filename, content) do
      {:ok, _} ->
        send_resp(conn, 200, Jason.encode!(%{success: true}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 删除文件
  post "/api/delete" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    path = Map.get(params, :path, "")

    case Nas.Storage.delete_file(path) do
      :ok ->
        send_resp(conn, 200, Jason.encode!(%{success: true}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 创建文件夹
  post "/api/mkdir" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    path = Map.get(params, :path, "/")
    name = Map.get(params, :name, "")

    case Nas.Storage.create_directory(path, name) do
      :ok ->
        send_resp(conn, 200, Jason.encode!(%{success: true}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 重命名
  post "/api/rename" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    old_path = Map.get(params, :oldPath, "")
    new_name = Map.get(params, :newName, "")

    case Nas.Storage.rename_file(old_path, new_name) do
      :ok ->
        send_resp(conn, 200, Jason.encode!(%{success: true}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 移动文件
  post "/api/move" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    source = Map.get(params, :source, "")
    destination = Map.get(params, :destination, "")

    case Nas.Storage.move_file(source, destination) do
      :ok ->
        send_resp(conn, 200, Jason.encode!(%{success: true}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 复制文件
  post "/api/copy" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    source = Map.get(params, :source, "")
    destination = Map.get(params, :destination, "")

    case Nas.Storage.copy_file(source, destination) do
      :ok ->
        send_resp(conn, 200, Jason.encode!(%{success: true}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 搜索文件
  post "/api/search" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    keyword = Map.get(params, :keyword, "")
    path = Map.get(params, :path, "/")

    case Nas.Storage.search_files(path, keyword) do
      {:ok, files} ->
        send_resp(conn, 200, Jason.encode!(%{success: true, data: files}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 获取文件信息
  post "/api/info" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    path = Map.get(params, :path, "")

    case Nas.Storage.get_file_info(path) do
      {:ok, info} ->
        send_resp(conn, 200, Jason.encode!(%{success: true, data: info}))

      {:error, reason} ->
        send_resp(conn, 404, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 翻译接口
  post "/api/translate" do
    {:ok, body, conn} = Plug.Conn.read_body(conn)
    params = Jason.decode!(body, keys: :atoms)
    text = Map.get(params, :text, "")
    from_lang = Map.get(params, :from, "auto")
    to_lang = Map.get(params, :to, "en")

    case Nas.Translation.translate(text, from_lang, to_lang) do
      {:ok, translated} ->
        send_resp(conn, 200, Jason.encode!(%{success: true, data: translated}))

      {:error, reason} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: reason}))
    end
  end

  # 获取支持的语言列表
  get "/api/languages" do
    languages = Nas.Translation.get_supported_languages()
    send_resp(conn, 200, Jason.encode!(%{success: true, data: languages}))
  end

  # 获取配置
  get "/api/config" do
    case Nas.Config.load() do
      {:ok, config} ->
        send_resp(conn, 200, Jason.encode!(%{success: true, data: config}))

      {:error, _} ->
        send_resp(conn, 500, Jason.encode!(%{success: false, error: "配置文件加载失败"}))
    end
  end

  # 健康检查
  get "/api/health" do
    send_resp(conn, 200, Jason.encode!(%{status: "ok", timestamp: System.system_time(:millisecond)}))
  end

  # 404处理
  match _ do
    send_resp(conn, 404, Jason.encode!(%{success: false, error: "接口不存在"}))
  end
end