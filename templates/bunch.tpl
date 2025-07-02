{% extends 'base.tpl' %}
{% block title %}{{ lst_Days[int_TargetDayId]['name'] }}'s Bunch&nbsp;|&nbsp;週7英単語{% endblock %}
{% block content %}
  <div class="container">
    <div class="row pb-3 pb-md-4 pt-1 pt-md-0">
      <h1 class="col-md-8 py-0 px-3 px-md-1 m-0 fw-bold text-nowrap" style="font-family: 'Montserrat', sans-serif; font-weight: 700;">{{ lst_Days[int_TargetDayId]['name'] }}'s Bunch</h1>
      <p class="col-md-4 text-end pt-2 px-3 px-md-1 mt-auto mb-0">
        <i class="bi bi-arrow-repeat"></i>
        {{ str_UpdatedDate }}
      </p>
    </div>
  </div>
  {% for dct_Card in lst_Cards %}
  <section class="bg-secondary my-2 border-0 rounded-4 p-3 px-md-4" >
    <a class="text-reset text-decoration-none px-0" data-bs-toggle="collapse" href="#card{{ dct_Card['number'] }}" role="button" aria-expanded="false" aria-controls="card{{ dct_Card['number'] }}">
      <div class="container p-0">
        <div class="d-flex justify-content-between">
          <div class="fs-6 px-1 border border-light border-1 rounded-2 my-auto">{{ dct_Card['genre'] }}</div>
          <div class="fs-7 p-0 pe-1 lh-sm">{{ dct_Card['number'] }}</div>
        </div>
      </div>
      <div class="fs-1" style="font-family: 'Montserrat', sans-serif; font-weight: 500;">{{ dct_Card['question'] }}</div>
      <div class="fs-6">/<span style="font-family: 'Lora', serif;">{{ dct_Card['pron'] }}</span>/</div>
    </a>

    <div class="collapse px-0 fs-4" id="card{{ dct_Card['number'] }}">
      <hr class="my-2 bg-white"/>
      {{ dct_Card['answer'] }}
    </div>
  </section>
  {% endfor %}
{% endblock %}