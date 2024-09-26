from django.shortcuts import render
from rest_framework import pagination
from rest_framework.viewsets import ModelViewSet


# Create your views here.
class DefaultLimitOffsetPagination(pagination.LimitOffsetPagination):
    max_limit = 20
    default_limit = 10

# class PreSetModelAPI(ModelViewSet):
#     queryset = models.PreSetModelData.objects.all()
#     pagination_class = DefaultLimitOffsetPagination
#     permission_classes = []
#     serializer_class = serializers.StructurePreSet
#
#     def list(self, request, *args, **kwargs):
#         response = super().list(request, *args, **kwargs)
#         response.headers.setdefault("Access-Control-Allow-Origin", "*")
#         return response