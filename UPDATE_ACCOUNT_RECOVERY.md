{% extends 'base.html' %}
{% block title %}안내 메일 확인 — Paper Shelf{% endblock %}
{% block content %}
<section class="auth-card">
  <p class="eyebrow">CHECK YOUR EMAIL</p>
  <h1>이메일을 확인해주세요</h1>
  <p>입력한 이메일과 일치하는 계정이 있다면 아이디 안내 메일을 보냈습니다.</p>
  <p class="muted">메일이 보이지 않으면 스팸함을 확인하고, 가입할 때 사용한 다른 이메일도 시도해보세요.</p>
  <a class="button primary" href="{% url 'login' %}">로그인으로 돌아가기</a>
</section>
{% endblock %}
