from collections import OrderedDict
import json
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Case, IntegerField, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .forms import PaperSearchForm, ReadingRecordForm, SignupForm
from .models import ExtensionToken, Paper, PaperSummary, ReadingRecord, SearchHistory
from .services.ai import summarize_abstract
from .services.pubmed import find_paper_for_extension, search_papers as pubmed_search
from .tokens import authenticate_extension_token, issue_extension_token, revoke_extension_token


def home(request):
    return render(
        request,
        "home.html",
        {
            "paper_count": Paper.objects.count(),
            "reading_count": ReadingRecord.objects.count(),
        },
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("papers:search")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Paper Shelf에 오신 것을 환영합니다.")
            return redirect("papers:search")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def search_papers(request):
    results = []
    search_period = None
    form = PaperSearchForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        keyword = form.cleaned_data["keyword"]
        days = form.cleaned_data["days"]
        max_results = form.cleaned_data["max_results"]
        SearchHistory.objects.create(
            user=request.user, keyword=keyword, days=days
        )

        try:
            items, start_date, end_date = pubmed_search(
                keyword, days, max_results
            )
            search_period = (start_date, end_date)
            ids = []

            for item in items:
                paper, _ = Paper.objects.update_or_create(
                    pmid=item["pmid"],
                    defaults={
                        "title": item["title"],
                        "authors": item["authors"],
                        "journal": item["journal"],
                        "publication_date": item["publication_date"],
                        "doi": item["doi"],
                        "pubmed_url": item["pubmed_url"],
                        "abstract": item["abstract"],
                    },
                )
                ids.append(paper.id)

            if ids:
                ordering = Case(
                    *[
                        When(pk=pk, then=position)
                        for position, pk in enumerate(ids)
                    ],
                    output_field=IntegerField(),
                )
                results = list(
                    Paper.objects.filter(pk__in=ids)
                    .select_related("summary")
                    .order_by(ordering)
                )

            if not results:
                messages.info(request, "해당 기간에 검색된 논문이 없습니다.")
        except Exception as exc:
            messages.error(
                request, f"PubMed 검색 중 오류가 발생했습니다: {exc}"
            )

    recent_searches = request.user.search_history.all()[:5]
    read_paper_ids = set(
        request.user.reading_records.values_list("paper_id", flat=True)
    )
    return render(
        request,
        "papers/search.html",
        {
            "form": form,
            "results": results,
            "search_period": search_period,
            "recent_searches": recent_searches,
            "read_paper_ids": read_paper_ids,
        },
    )


@login_required
def paper_detail(request, pk):
    paper = get_object_or_404(
        Paper.objects.select_related("summary"), pk=pk
    )
    record = ReadingRecord.objects.filter(
        user=request.user, paper=paper
    ).first()
    form = ReadingRecordForm(instance=record) if record else None
    return render(
        request,
        "papers/paper_detail.html",
        {"paper": paper, "record": record, "record_form": form},
    )


def _redirect_after_post(request, paper):
    next_url = request.POST.get("next", "").strip()
    if next_url:
        return redirect(next_url)
    return redirect("papers:detail", pk=paper.pk)


@login_required
@require_POST
def generate_summary(request, pk):
    paper = get_object_or_404(Paper, pk=pk)

    try:
        result = summarize_abstract(
            paper.title, paper.abstract, paper.journal
        )
        PaperSummary.objects.update_or_create(
            paper=paper,
            defaults={
                "research_question": result.research_question,
                "why_it_matters": result.why_it_matters,
                "study_design": result.study_design,
                "study_population": result.study_population,
                "main_results": result.main_results,
                "easy_explanation": result.easy_explanation,
                "limitations": result.limitations,
                "beginner_takeaway": result.beginner_takeaway,
                "difficult_terms": result.difficult_terms,
                "source": "PubMed Abstract",
                "model_name": settings.GEMINI_MODEL,
                "status": "success",
                "error_message": "",
            },
        )
        messages.success(request, "초보자용 AI 요약을 만들었습니다.")
    except Exception as exc:
        PaperSummary.objects.update_or_create(
            paper=paper,
            defaults={"status": "failed", "error_message": str(exc)},
        )
        messages.error(request, str(exc))

    return _redirect_after_post(request, paper)


@login_required
@require_POST
def mark_read(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    _, created = ReadingRecord.objects.get_or_create(
        user=request.user,
        paper=paper,
        defaults={
            "read_at": timezone.now(),
            "source_url": request.POST.get("source_url")
            or paper.pubmed_url,
        },
    )

    if created:
        messages.success(
            request, "논문 한 권이 내 책장에 추가되었습니다."
        )
    else:
        messages.info(request, "이미 내 책장에 있는 논문입니다.")

    return _redirect_after_post(request, paper)


@login_required
@require_POST
def update_reading_record(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    record = get_object_or_404(
        ReadingRecord, user=request.user, paper=paper
    )
    form = ReadingRecordForm(request.POST, instance=record)

    if form.is_valid():
        form.save()
        messages.success(request, "독서 기록을 수정했습니다.")
    else:
        messages.error(request, "입력값을 확인해주세요.")

    return redirect("papers:detail", pk=paper.pk)


@login_required
@require_POST
def remove_reading_record(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    ReadingRecord.objects.filter(
        user=request.user, paper=paper
    ).delete()
    messages.success(request, "책장에서 논문을 제거했습니다.")
    return redirect("papers:bookshelf")


def _reading_streak(records):
    dates = sorted(
        {timezone.localtime(record.read_at).date() for record in records},
        reverse=True,
    )
    if not dates:
        return 0

    today = timezone.localdate()
    if dates[0] not in {today, today - timedelta(days=1)}:
        return 0

    streak = 1
    for previous, current in zip(dates, dates[1:]):
        if previous - current == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


@login_required
def bookshelf(request):
    records = list(
        request.user.reading_records.select_related(
            "paper", "paper__summary"
        ).all()
    )
    grouped = OrderedDict()

    for record in records:
        local_date = timezone.localtime(record.read_at)
        key = local_date.strftime("%Y-%m")
        grouped.setdefault(
            key,
            {
                "label": local_date.strftime("%Y년 %m월"),
                "records": [],
            },
        )["records"].append(record)

    today = timezone.localdate()
    month_count = sum(
        1
        for record in records
        if timezone.localtime(record.read_at).year == today.year
        and timezone.localtime(record.read_at).month == today.month
    )
    journal_count = len(
        {record.paper.journal for record in records if record.paper.journal}
    )

    return render(
        request,
        "papers/bookshelf.html",
        {
            "grouped_records": grouped.values(),
            "total_count": len(records),
            "month_count": month_count,
            "journal_count": journal_count,
            "streak": _reading_streak(records),
        },
    )


@login_required
def extension_settings(request):
    token_record = ExtensionToken.objects.filter(user=request.user).first()
    return render(
        request,
        "papers/extension_settings.html",
        {
            "token_record": token_record,
            "generated_token": request.session.pop("generated_extension_token", ""),
            "site_url": request.build_absolute_uri("/").rstrip("/"),
        },
    )


@login_required
@require_POST
def generate_extension_token(request):
    raw_token = issue_extension_token(request.user)
    request.session["generated_extension_token"] = raw_token
    messages.success(
        request,
        "새 연결 토큰을 만들었습니다. 이 화면을 벗어나기 전에 복사해주세요.",
    )
    return redirect("papers:extension_settings")


@login_required
@require_POST
def revoke_extension_token_view(request):
    revoke_extension_token(request.user)
    messages.success(request, "Chrome 확장 프로그램 연결을 해제했습니다.")
    return redirect("papers:extension_settings")


def _cors_json(payload, status=200):
    response = JsonResponse(payload, status=status)
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response["Access-Control-Max-Age"] = "86400"
    return response


def _extension_user(request):
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    return authenticate_extension_token(authorization[7:])


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_save_reading_record(request):
    if request.method == "OPTIONS":
        return _cors_json({"ok": True})

    user = _extension_user(request)
    if user is None:
        return _cors_json(
            {"ok": False, "error": "연결 토큰이 없거나 올바르지 않습니다."},
            status=401,
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _cors_json(
            {"ok": False, "error": "요청 데이터 형식이 올바르지 않습니다."},
            status=400,
        )

    pmid = str(payload.get("pmid") or "").strip()
    doi = str(payload.get("doi") or "").strip()
    title = str(payload.get("title") or "").strip()
    source_url = str(payload.get("source_url") or "").strip()
    note = str(payload.get("note") or "").strip()[:5000]

    if not any([pmid, doi, title]):
        return _cors_json(
            {"ok": False, "error": "PMID, DOI 또는 논문 제목이 필요합니다."},
            status=400,
        )

    try:
        paper_data = find_paper_for_extension(pmid=pmid, doi=doi, title=title)
    except Exception as exc:
        return _cors_json(
            {"ok": False, "error": f"PubMed 확인 중 오류가 발생했습니다: {exc}"},
            status=502,
        )

    if paper_data is None:
        return _cors_json(
            {
                "ok": False,
                "error": "PubMed에서 논문을 확인하지 못했습니다. PubMed 페이지에서 다시 시도하거나 PMID를 확인해주세요.",
            },
            status=404,
        )

    paper, _ = Paper.objects.update_or_create(
        pmid=paper_data["pmid"],
        defaults={
            "title": paper_data["title"],
            "authors": paper_data["authors"],
            "journal": paper_data["journal"],
            "publication_date": paper_data["publication_date"],
            "doi": paper_data["doi"],
            "pubmed_url": paper_data["pubmed_url"],
            "abstract": paper_data["abstract"],
        },
    )

    read_at = timezone.now()
    submitted_read_at = str(payload.get("read_at") or "").strip()
    if submitted_read_at:
        parsed = parse_datetime(submitted_read_at)
        if parsed is not None:
            read_at = parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)

    record, created = ReadingRecord.objects.get_or_create(
        user=user,
        paper=paper,
        defaults={
            "read_at": read_at,
            "note": note,
            "source_url": source_url or paper.pubmed_url,
        },
    )

    if not created:
        changed = False
        if note and record.note != note:
            record.note = note
            changed = True
        if source_url and record.source_url != source_url:
            record.source_url = source_url
            changed = True
        if changed:
            record.save(update_fields=["note", "source_url", "updated_at"])

    return _cors_json(
        {
            "ok": True,
            "created": created,
            "message": (
                "논문 한 권을 내 책장에 추가했습니다."
                if created
                else "이미 책장에 있는 논문입니다. 메모가 있으면 업데이트했습니다."
            ),
            "paper": {
                "pmid": paper.pmid,
                "title": paper.title,
                "journal": paper.journal,
            },
            "bookshelf_url": request.build_absolute_uri(
                reverse("papers:bookshelf")
            ),
        }
    )
