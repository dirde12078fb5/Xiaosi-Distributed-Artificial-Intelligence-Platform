open System
open System.IO
open System.Text
open Microsoft.AspNetCore
open Microsoft.AspNetCore.Builder
open Microsoft.AspNetCore.Hosting
open Microsoft.AspNetCore.Http
open Microsoft.Extensions.Configuration
open Microsoft.Extensions.DependencyInjection
open Microsoft.Extensions.Logging
open Giraffe
open Newtonsoft.Json
open Newtonsoft.Json.Linq

// 语言翻译映射
module Languages =
    let translations = 
        dict [
            ("zh", {| name = "中文"; welcome = "欢迎使用NAS服务" |})
            ("en", {| name = "English"; welcome = "Welcome to NAS Service" |})
            ("ja", {| name = "日本語"; welcome = "NASサービスへようこそ" |})
            ("ko", {| name = "한국어"; welcome = "NAS 서비스에 오신 것을 환영합니다" |})
            ("es", {| name = "Español"; welcome = "Bienvenido al servicio NAS" |})
            ("fr", {| name = "Français"; welcome = "Bienvenue dans le service NAS" |})
            ("de", {| name = "Deutsch"; welcome = "Willkommen beim NAS-Service" |})
            ("it", {| name = "Italiano"; welcome = "Benvenuto nel servizio NAS" |})
            ("pt", {| name = "Português"; welcome = "Bem-vindo ao serviço NAS" |})
            ("ru", {| name = "Русский"; welcome = "Добро пожаловать в службу NAS" |})
            ("ar", {| name = "العربية"; welcome = "مرحباً بك في خدمة NAS" |})
            ("hi", {| name = "हिन्दी"; welcome = "NAS सेवा में आपका स्वागत है" |})
            ("bn", {| name = "বাংলা"; welcome = "NAS সেবায় স্বাগতম" |})
            ("pa", {| name = "ਪੰਜਾਬੀ"; welcome = "NAS ਸੇਵਾ ਵਿੱਚ ਜੀ ਆਇਆਂ ਨੂੰ" |})
            ("vi", {| name = "Tiếng Việt"; welcome = "Chào mừng đến với dịch vụ NAS" |})
            ("th", {| name = "ไทย"; welcome = "ยินดีต้อนรับสู่บริการ NAS" |})
            ("id", {| name = "Bahasa Indonesia"; welcome = "Selamat datang di layanan NAS" |})
            ("ms", {| name = "Bahasa Melayu"; welcome = "Selamat datang ke perkhidmatan NAS" |})
            ("tr", {| name = "Türkçe"; welcome = "NAS servisine hoş geldiniz" |})
            ("pl", {| name = "Polski"; welcome = "Witamy w usłudze NAS" |})
            ("nl", {| name = "Nederlands"; welcome = "Welkom bij de NAS-service" |})
            ("sv", {| name = "Svenska"; welcome = "Välkommen till NAS-tjänsten" |})
            ("da", {| name = "Dansk"; welcome = "Velkommen til NAS-tjenesten" |})
            ("no", {| name = "Norsk"; welcome = "Velkommen til NAS-tjenesten" |})
            ("fi", {| name = "Suomi"; welcome = "Tervetuloa NAS-palveluun" |})
            ("cs", {| name = "Čeština"; welcome = "Vítejte ve službě NAS" |})
            ("el", {| name = "Ελληνικά"; welcome = "Καλώς ήρθατε στην υπηρεσία NAS" |})
            ("he", {| name = "עברית"; welcome = "ברוכים הבאים לשירות NAS" |})
        ]

// 配置类型
type NasConfig = {
    Port: int
    StoragePath: string
    MaxFileSize: int64
    AllowedExtensions: string list
    JwtSecret: string
    DefaultLanguage: string
}

// 文件信息类型
type FileInfo = {
    Name: string
    Path: string
    Size: int64
    Modified: DateTime
    IsDirectory: bool
}

// API响应类型
type ApiResponse<'T> = {
    Success: bool
    Data: 'T option
    Message: string option
    Language: string option
}

// 配置管理
module Config =
    let load (basePath: string) =
        let configPath = Path.Combine(basePath, "..", "config", "config.json")
        if File.Exists(configPath) then
            let json = File.ReadAllText(configPath, Encoding.UTF8)
            let jObj = JObject.Parse(json)
            {
                Port = 
                    match jObj.["port"] with
                    | null -> 8099
                    | v -> v.Value<int>()
                StoragePath = 
                    match jObj.["storagePath"] with
                    | null -> "./storage"
                    | v -> v.Value<string>()
                MaxFileSize = 
                    match jObj.["maxFileSize"] with
                    | null -> 104857600L
                    | v -> v.Value<int64>()
                AllowedExtensions = 
                    match jObj.["allowedExtensions"] with
                    | null -> [".txt"; ".pdf"; ".jpg"; ".png"; ".doc"; ".docx"]
                    | extObj ->
                        match extObj.["values"] with
                        | null -> [".txt"; ".pdf"; ".jpg"; ".png"; ".doc"; ".docx"]
                        | arr -> [ for v in arr :?> JArray -> v.Value<string>() ]
                JwtSecret = 
                    match jObj.["jwtSecret"] with
                    | null -> "default-secret-key"
                    | v -> v.Value<string>()
                DefaultLanguage = 
                    match jObj.["defaultLanguage"] with
                    | null -> "zh"
                    | v -> v.Value<string>()
            }
        else
            {
                Port = 8099
                StoragePath = "./storage"
                MaxFileSize = 104857600L
                AllowedExtensions = [".txt"; ".pdf"; ".jpg"; ".png"; ".doc"; ".docx"]
                JwtSecret = "default-secret-key"
                DefaultLanguage = "zh"
            }

// 存储管理
module Storage =
    let ensureDirectory (path: string) =
        if not (Directory.Exists(path)) then
            Directory.CreateDirectory(path) |> ignore

    let listFiles (storagePath: string) (relativePath: string) =
        let fullPath = Path.Combine(storagePath, relativePath.TrimStart('/'))
        if Directory.Exists(fullPath) then
            Directory.GetFiles(fullPath)
            |> Array.map (fun f ->
                let info = FileInfo(f)
                {|
                    Name = info.Name
                    Path = f.Substring(storagePath.Length).Replace('\\', '/')
                    Size = info.Length
                    Modified = info.LastWriteTime
                    IsDirectory = false
                |})
            |> Array.append (
                Directory.GetDirectories(fullPath)
                |> Array.map (fun d ->
                    let info = DirectoryInfo(d)
                    {|
                        Name = info.Name
                        Path = d.Substring(storagePath.Length).Replace('\\', '/')
                        Size = 0L
                        Modified = info.LastWriteTime
                        IsDirectory = true
                    |})
            )
            |> Array.toList
        else
            []

    let uploadFile (storagePath: string) (relativePath: string) (content: byte[]) (config: NasConfig) =
        let fileName = Path.GetFileName(relativePath)
        let ext = Path.GetExtension(fileName).ToLower()
        if not (List.contains ext config.AllowedExtensions) then
            Error (sprintf "文件扩展名 %s 不允许" ext)
        elif content.Length > int config.MaxFileSize then
            Error (sprintf "文件大小超过限制 %d 字节" config.MaxFileSize)
        else
            let fullPath = Path.Combine(storagePath, relativePath.TrimStart('/'))
            let dir = Path.GetDirectoryName(fullPath)
            ensureDirectory dir
            File.WriteAllBytes(fullPath, content)
            Ok fullPath

    let downloadFile (storagePath: string) (relativePath: string) =
        let fullPath = Path.Combine(storagePath, relativePath.TrimStart('/'))
        if File.Exists(fullPath) then
            Some (File.ReadAllBytes(fullPath))
        else
            None

    let deleteFile (storagePath: string) (relativePath: string) =
        let fullPath = Path.Combine(storagePath, relativePath.TrimStart('/'))
        if File.Exists(fullPath) then
            File.Delete(fullPath)
            true
        else
            false

    let createDirectory (storagePath: string) (relativePath: string) =
        let fullPath = Path.Combine(storagePath, relativePath.TrimStart('/'))
        ensureDirectory fullPath
        fullPath

// HTTP处理器
module Handlers =
    let getConfig (ctx: HttpContext) =
        ctx.GetService<NasConfig>()

    let getLanguage (ctx: HttpContext) =
        match ctx.TryGetQueryStringValue "lang" with
        | Some lang -> if Languages.translations.ContainsKey(lang) then lang else "zh"
        | None -> (getConfig ctx).DefaultLanguage

    let jsonResp data =
        json data

    let handleGetInfo : HttpHandler =
        fun (next: HttpFunc) (ctx: HttpContext) ->
            let config = getConfig ctx
            let lang = getLanguage ctx
            let translation = Languages.translations.[lang]
            let response = {|
                Success = true
                Data = {|
                    Version = "1.0.0"
                    Port = config.Port
                    StoragePath = config.StoragePath
                    Language = translation.name
                |}
                Message = translation.welcome
                Language = lang
            |}
            jsonResp response next ctx

    let handleListFiles : HttpHandler =
        fun (next: HttpFunc) (ctx: HttpContext) ->
            let config = getConfig ctx
            let path = ctx.GetQueryStringValue("path") |> Option.defaultValue "/"
            let files = Storage.listFiles config.StoragePath path
            let response = {|
                Success = true
                Data = files
                Message = None
                Language = getLanguage ctx
            |}
            jsonResp response next ctx

    let handleUpload : HttpHandler =
        fun (next: HttpFunc) (ctx: HttpContext) ->
            task {
                let config = getConfig ctx
                use memoryStream = new MemoryStream()
                do! ctx.Request.Body.CopyToAsync(memoryStream)
                let bytes = memoryStream.ToArray()
                let path = ctx.GetQueryStringValue("path") |> Option.defaultValue "/uploaded.dat"
                match Storage.uploadFile config.StoragePath path bytes config with
                | Ok savedPath ->
                    let response = {|
                        Success = true
                        Data = savedPath
                        Message = "文件上传成功"
                        Language = getLanguage ctx
                    |}
                    return! jsonResp response next ctx
                | Error err ->
                    let response = {|
                        Success = false
                        Data = None
                        Message = err
                        Language = getLanguage ctx
                    |}
                    return! jsonResp response next ctx
            }

    let handleDownload : HttpHandler =
        fun (next: HttpFunc) (ctx: HttpContext) ->
            task {
                let config = getConfig ctx
                let path = ctx.GetQueryStringValue("path")
                match path with
                | Some p ->
                    match Storage.downloadFile config.StoragePath p with
                    | Some bytes ->
                        ctx.SetContentType "application/octet-stream"
                        ctx.SetHttpHeader("Content-Disposition", sprintf "attachment; filename=\"%s\"" (Path.GetFileName(p)))
                        ctx.SetStatusCode 200
                        do! ctx.WriteBytesAsync(bytes)
                        return Some ctx
                    | None ->
                        ctx.SetStatusCode 404
                        return! text "文件不存在" next ctx
                | None ->
                    ctx.SetStatusCode 400
                    return! text "缺少path参数" next ctx
            }

    let handleDelete : HttpHandler =
        fun (next: HttpFunc) (ctx: HttpContext) ->
            let config = getConfig ctx
            let path = ctx.GetQueryStringValue("path")
            match path with
            | Some p ->
                if Storage.deleteFile config.StoragePath p then
                    let response = {|
                        Success = true
                        Data = None
                        Message = "文件删除成功"
                        Language = getLanguage ctx
                    |}
                    jsonResp response next ctx
                else
                    ctx.SetStatusCode 404
                    text "文件不存在" next ctx
            | None ->
                ctx.SetStatusCode 400
                text "缺少path参数" next ctx

    let handleCreateDir : HttpHandler =
        fun (next: HttpFunc) (ctx: HttpContext) ->
            let config = getConfig ctx
            let path = ctx.GetQueryStringValue("path")
            match path with
            | Some p ->
                let dir = Storage.createDirectory config.StoragePath p
                let response = {|
                    Success = true
                    Data = dir
                    Message = "目录创建成功"
                    Language = getLanguage ctx
                |}
                jsonResp response next ctx
            | None ->
                ctx.SetStatusCode 400
                text "缺少path参数" next ctx

    let handleGetLanguages : HttpHandler =
        fun (next: HttpFunc) (ctx: HttpContext) ->
            let langs = 
                Languages.translations
                |> Seq.map (fun kv -> {| Code = kv.Key; Name = kv.Value.name |})
                |> Seq.toList
            let response = {|
                Success = true
                Data = langs
                Message = None
                Language = getLanguage ctx
            |}
            jsonResp response next ctx

// Web应用配置
module WebApp =
    let webApp : HttpHandler =
        choose [
            GET >=> choose [
                route "/" >=> text "NAS Service - F# Implementation"
                route "/api/info" >=> Handlers.handleGetInfo
                route "/api/files" >=> Handlers.handleListFiles
                route "/api/download" >=> Handlers.handleDownload
                route "/api/languages" >=> Handlers.handleGetLanguages
            ]
            POST >=> choose [
                route "/api/upload" >=> Handlers.handleUpload
                route "/api/mkdir" >=> Handlers.handleCreateDir
            ]
            DELETE >=> choose [
                route "/api/delete" >=> Handlers.handleDelete
            ]
            RequestErrors.NOT_FOUND "未找到资源"
        ]

// 主程序
[<EntryPoint>]
let main args =
    let basePath = AppDomain.CurrentDomain.BaseDirectory
    let config = Config.load basePath
    
    // 确保存储目录存在
    Storage.ensureDirectory config.StoragePath
    
    // 配置WebHost
    let webHost = 
        WebHost.CreateDefaultBuilder(args)
            .ConfigureServices(fun services ->
                services
                    .AddGiraffe()
                    .AddSingleton<NasConfig>(config)
                |> ignore)
            .Configure(fun app env ->
                app.UseGiraffe WebApp.webApp)
            .UseUrls(sprintf "http://0.0.0.0:%d" config.Port)
            .Build()
    
    printfn "NAS服务已启动，端口: %d" config.Port
    printfn "存储路径: %s" config.StoragePath
    printfn "默认语言: %s" config.DefaultLanguage
    
    webHost.Run()
    0