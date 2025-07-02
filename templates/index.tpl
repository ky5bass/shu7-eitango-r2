{% extends 'base.tpl' %}
{% block title %}週7英単語{% endblock %}
{% block content %}
  <div class="fs-5 pt-1 pb-3 max-vw-20">
    <img src="/static/img/main_visual.svg" class="img-fluid w-100 py-5" transition-style="in:wipe:curtain" alt="週7英単語 メインビジュアル">
    <div transition-style="in:fade">
      <p class="text-center fs-4 py-2">週7英単語は、毎日の英単語学習を目的としたブラウザ型暗記カードです。</p>
      <p class="text-center fs-4 py-2">曜日ごとにカードの束（Bunch）を用意しています。その曜日の午前6時になると自動で内容が更新されます。</p>
      <div class="d-grid col-sm-10 col-lg-8 mx-auto py-2">
        {% set str_todayBunchAbsPath = '/bunch/' ~ lst_Days[int_TodayId]['slug'] %} {# 引数absoluteとして渡す変数str_todayBunchAbsPathを設定 #}
        <a class="btn btn-secondary align-baseline fs-3 px-2 rounded-4" href="{{ str_todayBunchAbsPath }}" style="font-family: 'Montserrat', sans-serif; font-weight: 700;">
          Go to Today's Bunch
          <i class="bi bi-rocket-takeoff-fill"></i>
        </a>
      </div>
      <br>
      <p class="text-center fs-6">※更新について、品詞ごとに決まった数だけデータベースから無作為抽出しておこなっています。そのため、同じカードが連日収録される場合があることをご了承ください。</p>
      <p class="text-center fs-6">
        ※単語の日本語訳は&nbsp;
        <a class="text-reset" href="https://www.jamsystem.com/ancdic/index.html" target="_blank">
          ANC英和頻出辞典
          <i class="bi bi-box-arrow-up-right"></i>
        </a>
        &nbsp;に、発音は&nbsp;
        <a class="text-reset" href="https://www.wordsapi.com/" target="_blank">
          WordsAPI
          <i class="bi bi-box-arrow-up-right"></i>
        </a>
        &nbsp;によっています。
      </p>
    </div>
  </div>
{% endblock %}