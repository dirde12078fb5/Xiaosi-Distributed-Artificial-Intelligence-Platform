defmodule Nas.Application do
  use Application

  @impl true
  def start(_type, _args) do
    port = Application.get_env(:nas, :port, 8098)

    children = [
      {Plug.Cowboy, scheme: :http, plug: Nas.Router, options: [port: port]},
      Nas.Storage,
      Nas.Translation
    ]

    opts = [strategy: :one_for_one, name: Nas.Supervisor]
    Supervisor.start_link(children, opts)
  end
end