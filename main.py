from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from supabase import create_client
import requests
import shutil
from os import environ
from typing import List
from datetime import timedelta
from datetime import datetime as _datetime

# 環境変数の値を取得
str_SupabaseUrl = environ['SUPABASE_URL']
str_SupabaseKey = environ['SUPABASE_KEY']
str_WordsApiKey = environ['WORDSAPI_KEY']

objPath_DistDir   = Path(__file__).parent / 'public'    # 公開ディレクトリ
# 注 ↑このディレクトリの中身は空であるものとして以下進める
objPath_StaticDir = Path(__file__).parent / 'static'    # 静的コンテンツディレクトリ
objPath_TmplDir   = Path(__file__).parent / 'templates' # テンプレートディレクトリ

# 曜日情報のリスト
# 注 要素の順番はday_id=0, 1, 2, 3, 4, 5, 6に対応
lst_Days = [
    { "slug": "sun", "label": "Sun.", },
    { "slug": "mon", "label": "Mon.", },
    { "slug": "tue", "label": "Tue.", },
    { "slug": "wed", "label": "Wed.", },
    { "slug": "thu", "label": "Thu.", },
    { "slug": "fri", "label": "Fri.", },
    { "slug": "sat", "label": "Sat.", }, 
]

# ジャンル→品詞(英語表記)の変換テーブル
# 注 品詞(英語表記)はWordsApiに準拠。
#    ジャンルとして存在しないものはコメントにしている。
dst_Genre2PosEn = {
    '冠詞':   'definite article',
    '副詞':   'adverb',
  # '文字':   'letter',
  # '不定詞': 'to',
    '名詞':   'noun',
    '前置詞': 'preposition',
    '形容詞': 'adjective',
    '動詞':   'verb',
    '接続詞': 'conjunction',
  # '間投詞': 'interjection',
  # '未分類': 'unclassified',
  # '限定詞': 'determiner',
    '代名詞': 'pronoun',
  # '数詞':   'number',
  # '否定詞': 'not',
  # '例外':   'ex',
}

# DB接続のクライアントを用意
obj_DbClient = create_client(str_SupabaseUrl, str_SupabaseKey)

# ページレンダリング用のコンテキストデータを用意
obj_RenderContext = Environment(loader=FileSystemLoader(objPath_TmplDir), trim_blocks=False)
obj_RenderContext.globals['lst_Days'] = lst_Days    # コンテキストに曜日情報のリストをグローバルとして格納

def non_Render(
    str_TemplateName: str,      # テンプレート名 (例 index.tpl)
    objPath_Output: Path,       # 書き出し先のファイルパス (公開ディレクトリ以下である想定)
    dct_RenderParams: dict,     # レンダリングのパラメータ
):
    """ページレンダリングして書き出し"""

    # ページレンダリング
    obj_Template = obj_RenderContext.get_template(str_TemplateName)
    str_Output = obj_Template.render(**dct_RenderParams)
    # 参考 extendsの方法→ https://www.python.ambitious-engineer.com/archives/809

    # 書き出し
    with objPath_Output.open('wt') as objFile_Dest:
        objFile_Dest.write(str_Output)

def str_FetchPronunciation(
    str_Word: str,  # 英単語
    str_PosEn: str  # 品詞(英語表記)
) -> str:           # -> 発音
    """Words APIを使って英単語の発音を取得"""

    try:
        # APIから情報を取得(生データと呼ぶ)
        str_ApiUrl = f'https://wordsapiv1.p.rapidapi.com/words/{str_Word}/pronunciation'
        objResp_Raw = requests.get(str_ApiUrl, headers={
            'X-RapidAPI-Key': str_WordsApiKey,
            'X-RapidAPI-Host': 'wordsapiv1.p.rapidapi.com',
        })

        # 生データをJSONパース
        try:
            dct_Resp = objResp_Raw.json()
        except requests.exceptions.JSONDecodeError:
            return ""       # パースに失敗した場合は空文字を返す

        # 辞書型であることを確認
        if isinstance(dct_Resp, list):  # リスト型になってしまっている場合は最初の要素を取り出す
            dct_Resp = dct_Resp[0]
        if isinstance(dct_Resp, dict):  # 辞書型の場合はスルー
        # 注 ↑elifだと取り出したものを検査できないためifにしている
            pass
        else:                           # 辞書型でない場合は空文字を返す
            return ""

        # pronunctiationキーの値を取得
        dct_Pron = dct_Resp.get('pronunciation')    # 注 getメソッドはキーが見つからなければNoneを返す
        if dct_Pron is None:  # pronunctiationキーがない場合
            return ""         # 空文字を返す
        
        # pronunctiationキーの値が辞書型であることを確認
        if isinstance(dct_Pron, str):       # 文字列型になってしまっている場合はそれをそのまま返す
            return dct_Pron
        if not isinstance(dct_Pron, dict):  # 辞書形でない場合は空文字を返す
            return ""

        # 発音を取得
        str_Ret = (
            dct_Pron.get(str_PosEn) # 品詞に対応する発音を取得
            or dct_Pron.get('all')  # (↑失敗なら) "all"キーとして登録されている発音を取得
            or ""                   # (↑失敗なら) 空文字
        )

        return str_Ret

    # フェールセーフ処理(余程でない限りここには来ない想定)
    except:
        return ""

def non_MakeEnptyDistDir():
    """公開ディレクトリ(空)を作成"""
    
    objPath_DistDir.mkdir(exist_ok=False)

def non_GenerateTopPage():
    """トップページを生成"""

    # 本日のdayIdを取得
    objDtm_Now = _datetime.now() + timedelta(hours=+9)  # 日本時間(+9:00)に変換
    int_TodayId = (objDtm_Now.weekday() + 1) % 7        # dayIdに変換
    # 注 <datetime object>.weekday() -> 0(月曜), ..., 6(日曜)

    # トップページをレンダリング
    objPath_RenderOutput = objPath_DistDir / 'index.html'
    dct_RenderParams = {
        'int_TodayId': int_TodayId,
    }
    non_Render('index.tpl', objPath_RenderOutput, dct_RenderParams)

def non_GenerateBunchDir():
    """曜日束のページを格納するディレクトリを生成"""
    
    # 公開ディレクトリの中にbunchディレクトリを作成
    objPath_TargetDir = objPath_DistDir / 'bunch'
    objPath_TargetDir.mkdir()
    for dct_Day in lst_Days:
        str_TargetDaySlug = dct_Day["slug"]
        objPath_TargetDir = objPath_DistDir / f'bunch/{str_TargetDaySlug}'
        objPath_TargetDir.mkdir()

    # すべての束のメタ情報をDBから取得
    lst_Bunches = [{}, {}, {}, {}, {}, {}, {}]  # それぞれの束のメタ情報を格納するリストを用意
    # 注 ↑はday_id=0, 1, 2, 3, 4, 5, 6に対応
    objResp_Db_0 = (    # 参考 https://supabase.com/docs/reference/python/select
        obj_DbClient
        .table('bunches')
        .select('*')
        .order('day_id')
        .execute()
    )
    for obj_CardEntry in objResp_Db_0.data:     # DBから取得したデータを上記リストに格納
        int_DayId: int = obj_CardEntry['day_id']
        str_UpdatedAt_Raw: str = obj_CardEntry['updated_at']
        objDtm_UpdatedAt = _datetime.strptime(str_UpdatedAt_Raw, r'%Y-%m-%d')
        lst_Bunches[int_DayId]['updated_at'] = objDtm_UpdatedAt
        # 注 ↑の処理はbunchesにday_id=0〜6のレコードが格納されている前提で実装している

    # 各曜日の束のページを生成
    for int_DayId, dct_Day in enumerate(lst_Days):  # 各曜日に対して処理
        # この曜日の束に属する全カードをDBから取得
        objResp_Db_1 = (    # 参考 https://supabase.com/docs/reference/python/rpc
            obj_DbClient
            .rpc('bunch', params={'_day_id': int_DayId})
            .order('number')
            .execute()
        )
        lst_Cards: List[dict] = objResp_Db_1.data

        # 各カードに発音の情報を追加
        for int_CardIndex in range(len(lst_Cards)):
            # カードから単語とジャンルを取得
            dct_Card = lst_Cards[int_CardIndex]
            str_Word = dct_Card['question']
            str_Genre = dct_Card['genre']

            # APIで発音を取得
            str_PosEn = dst_Genre2PosEn[str_Genre]
            str_Pron = str_FetchPronunciation(str_Word, str_PosEn)

            # pronキーとして発音の情報を追加
            lst_Cards[int_CardIndex]['pron'] = str_Pron

        # 束を更新した日付を取得
        dct_Bunch = lst_Bunches[int_DayId]
        objDtm_UpdatedAt = dct_Bunch['updated_at']
        str_Date = objDtm_UpdatedAt.strftime(r'%Y年%-m月%-d日')
        # 注 %-m %-d で月日を1桁で表現できる。ただしUnix環境に依存しており、Windowsなら %#m %#d らしい。
        #    参考 https://stackoverflow.com/questions/904928/python-strftime-date-without-leading-0#answer-2073189

        # ページレンダリングして書き出し
        str_TargetDaySlug = dct_Day['slug']
        objPath_RenderOutput = objPath_DistDir / f'bunch/{str_TargetDaySlug}/index.html'
        dct_RenderParams = {
            'lst_Cards': lst_Cards,
            'str_UpdatedDate': str_Date,
            'int_TargetDayId': int_DayId,
        }
        non_Render('bunch.tpl', objPath_RenderOutput, dct_RenderParams)

def non_GenerateStaticDir() -> None:
    """静的コンテンツディレクトリを生成"""

    # 静的コンテンツディレクトリを公開ディレクトリにコピー
    shutil.copytree(objPath_StaticDir, objPath_DistDir / objPath_StaticDir.name)

if __name__ == '__main__':
    # 公開ディレクトリ(空)を作成
    non_MakeEnptyDistDir()

    # 公開ディレクトリのコンテンツを生成
    non_GenerateTopPage()       # トップページを生成
    non_GenerateBunchDir()      # 曜日束のページを格納するディレクトリを生成
    non_GenerateStaticDir()     # 静的コンテンツディレクトリを生成