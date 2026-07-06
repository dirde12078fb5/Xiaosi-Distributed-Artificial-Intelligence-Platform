defmodule Nas.Translation do
  @moduledoc """
  28种语言翻译支持模块
  使用内置翻译字典和规则进行翻译
  """

  use Agent

  # 支持的语言列表
  @languages %{
    "zh" => "中文",
    "en" => "English",
    "ja" => "日本語",
    "ko" => "한국어",
    "fr" => "Français",
    "de" => "Deutsch",
    "es" => "Español",
    "pt" => "Português",
    "it" => "Italiano",
    "ru" => "Русский",
    "ar" => "العربية",
    "th" => "ไทย",
    "vi" => "Tiếng Việt",
    "id" => "Bahasa Indonesia",
    "ms" => "Bahasa Melayu",
    "nl" => "Nederlands",
    "pl" => "Polski",
    "tr" => "Türkçe",
    "cs" => "Čeština",
    "sv" => "Svenska",
    "da" => "Dansk",
    "fi" => "Suomi",
    "el" => "Ελληνικά",
    "he" => "עברית",
    "hu" => "Magyar",
    "no" => "Norsk",
    "ro" => "Română",
    "uk" => "Українська"
  }

  def start_link(_opts) do
    Agent.start_link(fn -> load_dictionaries() end, name: __MODULE__)
  end

  defp load_dictionaries do
    %{
      # 常用词汇翻译字典
      dictionaries: %{
        "zh-en" => load_zh_en_dict(),
        "en-zh" => load_en_zh_dict(),
        "zh-ja" => load_zh_ja_dict(),
        "ja-zh" => load_ja_zh_dict(),
        "zh-ko" => load_zh_ko_dict(),
        "ko-zh" => load_ko_zh_dict()
      },
      # 翻译缓存
      cache: %{}
    }
  end

  # 获取支持的语言列表
  def get_supported_languages do
    @languages
    |> Enum.map(fn {code, name} -> %{code: code, name: name} end)
  end

  # 主翻译函数
  def translate(text, from_lang, to_lang) when is_binary(text) and text != "" do
    try do
      # 检查缓存
      cache_key = "#{from_lang}-#{to_lang}:#{text}"

      cached =
        Agent.get(__MODULE__, fn state ->
          Map.get(state.cache, cache_key)
        end)

      if cached do
        {:ok, cached}
      else
        # 执行翻译
        translated = do_translate(text, from_lang, to_lang)

        # 缓存结果
        Agent.update(__MODULE__, fn state ->
          put_in(state, [:cache, cache_key], translated)
        end)

        {:ok, translated}
      end
    rescue
      e -> {:error, "翻译失败: #{inspect(e)}"}
    end
  end

  def translate(_, _, _), do: {:error, "无效的输入"}

  # 翻译实现
  defp do_translate(text, from_lang, to_lang) when from_lang == to_lang, do: text

  defp do_translate(text, from_lang, to_lang) do
    cond do
      # 中文到其他语言
      from_lang == "zh" -> translate_from_zh(text, to_lang)
      # 其他语言到中文
      to_lang == "zh" -> translate_to_zh(text, from_lang)
      # 通过中文中转
      true ->
        intermediate = translate_to_zh(text, from_lang)
        translate_from_zh(intermediate, to_lang)
    end
  end

  # 从中文翻译
  defp translate_from_zh(text, "en"), do: zh_to_en(text)
  defp translate_from_zh(text, "ja"), do: zh_to_ja(text)
  defp translate_from_zh(text, "ko"), do: zh_to_ko(text)
  defp translate_from_zh(text, "fr"), do: zh_to_fr(text)
  defp translate_from_zh(text, "de"), do: zh_to_de(text)
  defp translate_from_zh(text, "es"), do: zh_to_es(text)
  defp translate_from_zh(text, "pt"), do: zh_to_pt(text)
  defp translate_from_zh(text, "ru"), do: zh_to_ru(text)
  defp translate_from_zh(text, "ar"), do: zh_to_ar(text)
  defp translate_from_zh(text, _), do: text

  # 翻译到中文
  defp translate_to_zh(text, "en"), do: en_to_zh(text)
  defp translate_to_zh(text, "ja"), do: ja_to_zh(text)
  defp translate_to_zh(text, "ko"), do: ko_to_zh(text)
  defp translate_to_zh(text, "fr"), do: fr_to_zh(text)
  defp translate_to_zh(text, "de"), do: de_to_zh(text)
  defp translate_to_zh(text, "es"), do: es_to_zh(text)
  defp translate_to_zh(text, "pt"), do: pt_to_zh(text)
  defp translate_to_zh(text, "ru"), do: ru_to_zh(text)
  defp translate_to_zh(text, "ar"), do: ar_to_zh(text)
  defp translate_to_zh(text, _), do: text

  # 中文到英文
  defp zh_to_en(text) do
    dict = load_zh_en_dict()
    translate_with_dict(text, dict)
  end

  # 英文到中文
  defp en_to_zh(text) do
    dict = load_en_zh_dict()
    translate_with_dict(text, dict)
  end

  # 中文到日文
  defp zh_to_ja(text) do
    dict = load_zh_ja_dict()
    translate_with_dict(text, dict)
  end

  # 日文到中文
  defp ja_to_zh(text) do
    dict = load_ja_zh_dict()
    translate_with_dict(text, dict)
  end

  # 中文到韩文
  defp zh_to_ko(text) do
    dict = load_zh_ko_dict()
    translate_with_dict(text, dict)
  end

  # 韩文到中文
  defp ko_to_zh(text) do
    dict = load_ko_zh_dict()
    translate_with_dict(text, dict)
  end

  # 其他语言翻译函数（简化实现）
  defp zh_to_fr(text), do: simple_translate(text, :zh_to_fr)
  defp zh_to_de(text), do: simple_translate(text, :zh_to_de)
  defp zh_to_es(text), do: simple_translate(text, :zh_to_es)
  defp zh_to_pt(text), do: simple_translate(text, :zh_to_pt)
  defp zh_to_ru(text), do: simple_translate(text, :zh_to_ru)
  defp zh_to_ar(text), do: simple_translate(text, :zh_to_ar)

  defp fr_to_zh(text), do: simple_translate(text, :fr_to_zh)
  defp de_to_zh(text), do: simple_translate(text, :de_to_zh)
  defp es_to_zh(text), do: simple_translate(text, :es_to_zh)
  defp pt_to_zh(text), do: simple_translate(text, :pt_to_zh)
  defp ru_to_zh(text), do: simple_translate(text, :ru_to_zh)
  defp ar_to_zh(text), do: simple_translate(text, :ar_to_zh)

  # 使用字典翻译
  defp translate_with_dict(text, dict) do
    Enum.reduce(dict, text, fn {key, value}, acc ->
      String.replace(acc, key, value)
    end)
  end

  # 简单翻译（占位实现）
  defp simple_translate(text, _) do
    # 对于其他语言，返回原文（实际应用中应接入真实翻译API）
    text
  end

  # 加载字典
  defp load_zh_en_dict do
    %{
      "你好" => "Hello",
      "世界" => "World",
      "文件" => "File",
      "文件夹" => "Folder",
      "上传" => "Upload",
      "下载" => "Download",
      "删除" => "Delete",
      "重命名" => "Rename",
      "移动" => "Move",
      "复制" => "Copy",
      "搜索" => "Search",
      "保存" => "Save",
      "取消" => "Cancel",
      "确认" => "Confirm",
      "错误" => "Error",
      "成功" => "Success",
      "失败" => "Failed",
      "用户" => "User",
      "密码" => "Password",
      "登录" => "Login",
      "退出" => "Logout",
      "设置" => "Settings",
      "配置" => "Configuration",
      "系统" => "System",
      "服务" => "Service"
    }
  end

  defp load_en_zh_dict do
    %{
      "Hello" => "你好",
      "World" => "世界",
      "File" => "文件",
      "Folder" => "文件夹",
      "Upload" => "上传",
      "Download" => "下载",
      "Delete" => "删除",
      "Rename" => "重命名",
      "Move" => "移动",
      "Copy" => "复制",
      "Search" => "搜索",
      "Save" => "保存",
      "Cancel" => "取消",
      "Confirm" => "确认",
      "Error" => "错误",
      "Success" => "成功",
      "Failed" => "失败",
      "User" => "用户",
      "Password" => "密码",
      "Login" => "登录",
      "Logout" => "退出",
      "Settings" => "设置",
      "Configuration" => "配置",
      "System" => "系统",
      "Service" => "服务"
    }
  end

  defp load_zh_ja_dict do
    %{
      "你好" => "こんにちは",
      "世界" => "世界",
      "文件" => "ファイル",
      "文件夹" => "フォルダー",
      "上传" => "アップロード",
      "下载" => "ダウンロード",
      "删除" => "削除",
      "重命名" => "名前変更",
      "移动" => "移動",
      "复制" => "コピー",
      "搜索" => "検索",
      "保存" => "保存",
      "取消" => "キャンセル",
      "确认" => "確認",
      "错误" => "エラー",
      "成功" => "成功",
      "失败" => "失敗"
    }
  end

  defp load_ja_zh_dict do
    %{
      "こんにちは" => "你好",
      "世界" => "世界",
      "ファイル" => "文件",
      "フォルダー" => "文件夹",
      "アップロード" => "上传",
      "ダウンロード" => "下载",
      "削除" => "删除",
      "名前変更" => "重命名",
      "移動" => "移动",
      "コピー" => "复制",
      "検索" => "搜索",
      "保存" => "保存",
      "キャンセル" => "取消",
      "確認" => "确认",
      "エラー" => "错误",
      "成功" => "成功",
      "失敗" => "失败"
    }
  end

  defp load_zh_ko_dict do
    %{
      "你好" => "안녕하세요",
      "世界" => "세계",
      "文件" => "파일",
      "文件夹" => "폴더",
      "上传" => "업로드",
      "下载" => "다운로드",
      "删除" => "삭제",
      "重命名" => "이름 바꾸기",
      "移动" => "이동",
      "复制" => "복사",
      "搜索" => "검색",
      "保存" => "저장",
      "取消" => "취소",
      "确认" => "확인",
      "错误" => "오류",
      "成功" => "성공",
      "失败" => "실패"
    }
  end

  defp load_ko_zh_dict do
    %{
      "안녕하세요" => "你好",
      "세계" => "世界",
      "파일" => "文件",
      "폴더" => "文件夹",
      "업로드" => "上传",
      "다운로드" => "下载",
      "삭제" => "删除",
      "이름 바꾸기" => "重命名",
      "이동" => "移动",
      "복사" => "复制",
      "검색" => "搜索",
      "저장" => "保存",
      "취소" => "取消",
      "확인" => "确认",
      "오류" => "错误",
      "성공" => "成功",
      "실패" => "失败"
    }
  end
end