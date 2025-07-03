# ![ヘッダー画像](https://raw.githubusercontent.com/ky5bass/shu7-eitango/refs/heads/main/docs/img/header.svg)

ウェブサイト [週7英単語](https://shu7-eitango.com) のプロジェクト (Release 2) です。

※*旧プロジェクト: [shu7-eitango](https://github.com/ky5bass/shu7-eitango)*

# DB構築時の履歴

Supabaseを利用して以下の手順でDBを構築した。

1. 下記の構成でテーブルを作成。

    ![supabase-schema-geigrvpwgxfwniiosmxv](https://github.com/user-attachments/assets/a44b54d8-babd-477b-a269-86d5c8240304)

    <details>
    <summary>DDLによる詳細</summary>
    
    ```sql
    -- WARNING: This schema is for context only and is not meant to be run.
    -- Table order and constraints may not be valid for execution.

    CREATE TABLE public.bunches (
    day_id smallint NOT NULL UNIQUE,
    updated_at date NOT NULL,
    CONSTRAINT bunches_pkey PRIMARY KEY (day_id)
    );
    CREATE TABLE public.cards (
    number smallint NOT NULL,
    day_id smallint NOT NULL,
    quiz_id smallint NOT NULL,
    CONSTRAINT cards_pkey PRIMARY KEY (number, day_id),
    CONSTRAINT cards_quiz_id_fkey FOREIGN KEY (quiz_id) REFERENCES public.quizzes(id)
    );
    CREATE TABLE public.deleted_quizzes (
    quiz_id smallint NOT NULL,
    deleted_at date NOT NULL,
    CONSTRAINT deleted_quizzes_pkey PRIMARY KEY (quiz_id),
    CONSTRAINT deleted_quizzes_quiz_id_fkey FOREIGN KEY (quiz_id) REFERENCES public.quizzes(id)
    );
    CREATE TABLE public.genres (
    id smallint NOT NULL UNIQUE,
    card_count smallint NOT NULL,
    name text NOT NULL,
    CONSTRAINT genres_pkey PRIMARY KEY (id)
    );
    CREATE TABLE public.quizzes (
    id smallint NOT NULL,
    genre_id smallint NOT NULL,
    question text,
    answer text,
    CONSTRAINT quizzes_pkey PRIMARY KEY (id),
    CONSTRAINT quizzes_genre_id_fkey FOREIGN KEY (genre_id) REFERENCES public.genres(id)
    );
    ```
    </details>

1. 下記SQLスクリプトを実行し、ファンクションを作成。
    <details>
    <summary><code>1_set_functions.sql</code></summary>

    ```sql
    /******************************************************************************
    * @file    3_set_functions.sql
    * @brief   ファンクションをセッティング
    * @auther  YASUDA Kanta
    * @date    2024/11/22 新規作成
    * @par     
    * Copyright (c) 2024 YASUDA Kanta All rights reserved.
    ******************************************************************************/

    /* 既に定義されているファンクションを削除 */
    DROP FUNCTION IF EXISTS "update_cards"(integer);
    DROP FUNCTION IF EXISTS "bunch"(integer);
    /* 注 CREATE OR REPLACE では引数の名前が違う場合は置き換えられないためDROPで対処している。 */
    /*    また、本SQLはDB初期状態で実行することを想定しているので削除の必要はないが念のため。  */

    /******************************************************************************
    * @fn      update_cards
    * @brief   指定した曜日のcardsレコードを更新する
    * @param   _day_id: 対象の曜日(day)のid
    * @return  
    * @detail  呼び出し方の例  SELECT update_cards(1);
    ******************************************************************************/
    CREATE FUNCTION "update_cards"(in "_day_id" integer)
    /* 注 引数の型をsmallintではなくintegerにしているのは  */
    /*    smallintにすると呼び出し時にCASTが必要になるため */
    RETURNS VOID
    LANGUAGE plpgsql
    AS $$
    BEGIN
    /* ↓が本プロシージャの中身の処理 */

        /* 指定したday_idをもつレコードをcardsテーブルから削除 */
        DELETE FROM "cards" WHERE "day_id" = "_day_id";

        /* cardsにレコードを追加 */
        INSERT INTO cards ("number", "day_id", "quiz_id")
        /* 注 ↓の出力結果を追加する */
            SELECT 
                row_number() OVER() AS "number",
                /* 注 row_number()を使うには必ずOVERが要る */
                "_day_id" AS "day_id",
                "id" AS "quiz_id"
            FROM
                /* shuffled_quizzesとしてサブクエリを用意                       */
                /* (その名の通りシャッフルしたquizzesであるが、                 */
                /*  ジャンルごとにシャッフルしてジャンルごとに連番をつけている) */
                (
                    SELECT 
                        "id",
                        "genre_id",
                        row_number() OVER (PARTITION BY "genre_id" ORDER BY random()) AS "num_in_genre"
                    FROM
                        "quizzes"
                    /* deleted_quizzesにはあるレコードを除外 */
                    WHERE
                        NOT EXISTS (
                            SELECT
                                *
                            FROM
                                deleted_quizzes 
                            WHERE
                                "quizzes"."id" = "deleted_quizzes"."quiz_id"
                        )
                    /* 注 NOT EXISTS()で相関サブクエリを使っている           */
                    /*    参考 https://style.potepan.com/articles/25337.html */
                ) AS "shuffled_quizzes"
            WHERE
                "num_in_genre" <= (SELECT "card_count" FROM "genres" WHERE "genres"."id"="shuffled_quizzes"."genre_id" LIMIT 1)
            ORDER BY
                "genre_id";
        
        /* 指定したday_idのbunches.updated_atレコードを更新 */
        UPDATE "bunches"
            SET "updated_at" = CAST((NOW() AT TIME ZONE 'Asia/Tokyo') AS date)
            WHERE "day_id" = "_day_id";
        /* 注 `CAST((NOW() AT TIME ZONE 'Asia/Tokyo') AS date)`で現在日付(日本時間)を取得できる */
        /*    参考 タイムゾーンから時刻取得→ https://qiita.com/anzai323/items/2621137f1cc1579aa7d1 */
        /*    参考 TimestampをDateにする→  https://qiita.com/akidroid/items/ed9f296cced170d78b3f */

    EXCEPTION
        WHEN others THEN
            RAISE EXCEPTION 'An error occurred in function update_cards: %', sqlerrm;
    END;
    $$;

    /******************************************************************************
    * @fn      bunch
    * @brief   指定した曜日の束のテーブルを取得
    * @param   _day_id: 対象の曜日(day)のid
    * @return  束のテーブル
    *            列: number    smallint
    *                genre     text
    *                question  text
    *                answer    text
    * @detail  - 呼び出し方の例  SELECT * FROM  bunch(1);
    *            ※ SELECT bunch(1); とすると1列になってしまう！
    *          - 4_set_cards.sqlなどでcardsテーブルをセッティングしたあとに
    *            呼び出すことが想定されている！
    ******************************************************************************/
    CREATE FUNCTION "bunch"(in "_day_id" integer)
    /* 注 引数の型をsmallintではなくintegerにしているのは  */
    /*    smallintにすると呼び出し時にCASTが必要になるため */
    RETURNS TABLE(
        "number"   smallint, 
        "genre"    text, 
        "question" text, 
        "answer"   text
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN query
        SELECT "C"."number", "G"."name" AS "genre", "Q"."question", "Q"."answer"
        /* 注 TABLE関数で同名の列を作成しているので、以下①のように "*". 無しで書くとエラーになる。 */
        /*    エラー詳細として表示されるのは以下②のとおり。                                        */
        /*    ① SELECT "number", "G"."name" AS "genre", "question", "answer"                       */
        /*    ② PL/pgSQL 変数もしくはテーブルのカラム名のどちらかを参照していた可能性があります。  */
        FROM "cards" AS "C"
        LEFT JOIN "quizzes" AS "Q" ON ("C"."quiz_id"  = "Q"."id")
        LEFT JOIN "genres"  AS "G" ON ("Q"."genre_id" = "G"."id")
        WHERE "C"."day_id" = CAST("_day_id" AS smallint)
    /* WHERE "C"."day_id" = "_day_id" ↑CASTしなくても通るが念のため */
        ORDER BY "C"."number";
    END;
    $$;

    /* 参照 https://www.exceedsystem.net/2021/03/29/how-to-return-table-from-stored-functions-in-postgresql/ */
    /*      ↑BEGIN〜ENDを使ってファンクションを定義するようすが記述されている貴重なサイト                   */
    ```
    </details>

1. 下記SQLスクリプトを実行し、初期のカードデータを挿入。
    <details>
    <summary><code>2_set_cards.sql</code></summary>

    ```sql
    /******************************************************************************
    * @file    4_set_cards.sql
    * @brief   cardsテーブルにレコードをセッティング
    * @auther  YASUDA Kanta
    * @date    2024/11/22 新規作成
    * @par     
    * Copyright (c) 2024 YASUDA Kanta All rights reserved.
    ******************************************************************************/

    /* データベースを切り替え             */
    /* \c "sh7ndb";                       */
    /* 注 1_*.sqlで切り替え済みのため不要 */

    /* cardsテーブルに各day_idのレコードを挿入 */
    SELECT update_cards(0);
    SELECT update_cards(1);
    SELECT update_cards(2);
    SELECT update_cards(3);
    SELECT update_cards(4);
    SELECT update_cards(5);
    SELECT update_cards(6);
    /* 注 ↑は曜日に関する規定に依存していることに注意すること。                                          */
    /*    たしかに、cardsテーブルのidカラムをとってきて各レコードについて繰り返し処理するのは可能だろう。 */
    /*    ただ、考えるのが面倒だし、余程でない限り曜日に関する規定は変わらないはず。処理速度も速い。      */
    ```
    </details>

1. 下記SQLスクリプトを実行し、cronジョブを作成
    <details>
    <summary><code>3_set_cron_jobs.sql</code></summary>

    ```sql
    /******************************************************************************
    * @file    5_set_cron_jobs.sql
    * @brief   cronジョブをセッティング
    * @auther  YASUDA Kanta
    * @date    2024/11/28 新規作成
    * @par     
    * @detail  拡張機能 pg_cron を有効にしておく必要がある。
    *          有効にする方法はコチラ→ https://supabase.com/docs/guides/database/extensions#enable-and-disable-extensions
    * Copyright (c) 2024 YASUDA Kanta All rights reserved.
    ******************************************************************************/

    /* cronジョブ: set-bunch-of-today のスケジューリングを解除 (cronジョブを削除) */
    SELECT cron.unschedule('set-bunch-of-today');
    /* 注 ↑cronジョブが存在しないとエラーになるので必要に応じてコメントアウト/コメントを切り替えてほしい */

    /* cronジョブ: set-bunch-of-today を設定 */
    SELECT
        cron.schedule(
            'set-bunch-of-today', /* ←cronジョブ名 */
            '45 20 * * *',         /* 毎日 世界標準時20:45(日本時間5:45) */
            $$
            SELECT
                "update_cards"(
                    /* integer型にキャスト */
                    CAST(
                        /* 現在の曜日(0-6)を取得 */
                        EXTRACT(DOW FROM (NOW() AT TIME ZONE 'Asia/Tokyo'))
                        /* 注 `EXTRACT(DOW FROM 時刻)`で曜日を取得できる(日→0, 月→1, …) */
                        /* 参考 https://www.postgresql.jp/document/7.2/user/functions-datetime.html */
                    AS integer)
                );
            $$
        );
    /* 参考 https://supabase.com/docs/guides/database/extensions/pg_cron */

    ```
    </details>

# 初回ローカル環境構築時の履歴

zsh (MacBook) で下記のコマンドを実行してローカル環境を初構築した。

```zsh
# ベースとなるgitリポジトリをクローン
git clone git@github.com:ky5bass/shu7-eitango.git shu7-eitango-r2
cd shu7-eitango-r2

# プロジェクト名を変更
vi package-lock.json    # ファイル編集(shu7-nihongo→shu7-eitangoに置換)
vi package.json         # 同上
vi wrangler.toml        # 同上

# dependenciesをインストール
npm install             # dependenciesをインストール
npm audit fix           # 脆弱性のあるdependenciesを更新

# 本プロジェクト向けにコンテンツを修正
vi src/index.ts
vi src/__STATIC_CONTENT_MANIFEST.d.ts
vi static/css/bootstrap_custom.css
cp /path/to/new_logo.svg ./static/img/logo.svg
vi templates/base.tpl
vi templates/bunch.tpl
vi templates/index.tpl
vi main.py
vi README.md
vi requirements.txt

# Cloudflareにデプロイ
npx wrangler login
mkdir public            # 公開ディレクトリを用意(無いとデプロイ失敗)
npx wrangler deploy
```