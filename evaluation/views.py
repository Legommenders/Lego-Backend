import json
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from common.auth import Auth
from evaluation.models import Evaluation, Tag


class EvaluationView(View):
    def get(self, request):
        signature = request.GET.get('signature')
        if signature:
            evaluation = get_object_or_404(Evaluation, signature=signature)
            return JsonResponse(evaluation.json())

        evaluations = [evaluation.json() for evaluation in Evaluation.objects.all()]
        return JsonResponse(evaluations, safe=False)

    @Auth.require_login
    def post(self, request):
        try:
            data = json.loads(request.body)
            evaluation = Evaluation.create_or_update(**data)
            return JsonResponse(evaluation.json(), status=201)
        except (TypeError, ValidationError) as e:
            return JsonResponse({"error": str(e)}, status=400)

    @Auth.require_login
    def delete(self, request):
        try:
            data = json.loads(request.body)
            Evaluation.remove(data['signature'])
            return HttpResponse(status=204)
        except KeyError:
            return JsonResponse({"error": "Signature is required"}, status=400)


class TagView(View):
    def get(self, request):
        tags = [tag.json() for tag in Tag.objects.all()]
        return JsonResponse(tags, safe=False)

    @Auth.require_login
    def post(self, request):
        try:
            data = json.loads(request.body)
            tag = Tag.create_or_get(data['name'])
            return JsonResponse(tag.json(), status=201)
        except (KeyError, ValidationError) as e:
            return JsonResponse({"error": str(e)}, status=400)

    @Auth.require_login
    def delete(self, request):
        try:
            data = json.loads(request.body)
            Tag.remove(data['name'])
            return HttpResponse(status=204)
        except KeyError:
            return JsonResponse({"error": "Tag name is required"}, status=400)
